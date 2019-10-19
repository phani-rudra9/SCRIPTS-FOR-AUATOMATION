# service.rb
# This ruby program is used to check if the service instance is present or not.
# First check if service is present in market place or not. if present then will be proceed as follows.
# If service instance is present, check which applications are binded to this particular service instance and unbind all of them and delete
# that service instance and create again.
# IF service instance is not present, then create the service instance.
require 'json'
require 'colorize'
require 'io/console'
class Service
	#constructor
	def initialize(curl_command,curl_path,organization_name,space_name,api_url,access_token,spaces_hash)
		@curl_command = curl_command
		@curl_path = curl_path
		@organization_name = organization_name
		@space_name = space_name
		@Api_url = api_url
		@access_token = access_token
		@spaces_hash = spaces_hash
	end
	#To delete a service instance we must first unbind the service instances from ther applications.
	#unbinding of the service_instance from all applications is done using this method.
	def unbind_service_instance(service_instance)
		Dir.chdir @curl_path
		url = "\"#{@Api_url}/v2/service_instances\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allservicesinstances_hash = JSON.parse(command_output)
		if allservicesinstances_hash.has_key?("error_code")
			puts allservicesinstances_hash["error_code"].red
		else
			no_of_services_instances=allservicesinstances_hash["resources"].length
			for i in 0..(no_of_services_instances-1)
				guid = allservicesinstances_hash["resources"][i]["metadata"]["guid"]
				if  allservicesinstances_hash["resources"][i]["entity"]["name"] == service_instance
					guid = allservicesinstances_hash["resources"][i]["metadata"]["guid"]
					url1 = "\"#{@Api_url}/v2/service_instances/#{guid}/service_bindings\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
					command_output1  = `#{@curl_command} -s #{url1}`
					a = JSON.parse(command_output1)
					l = a["resources"].length
					for j in 0..(l-1)
						app_id = a["resources"][j]["entity"]["app_guid"]
						Dir.chdir @curl_path
						url2 = "\"#{@Api_url}/v2/apps\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
						command_output2  = `#{@curl_command} -s #{url2}`
						b = JSON.parse(command_output2)
						m = b["resources"].length
						for k in 0..(m-1)
							if b["resources"][k]["metadata"]["guid"]==app_id
								app_name = b["resources"][k]["entity"]["name"]
								y = system("cf unbind-service #{app_name} #{service_instance}")
								if y ==true
									puts "Service is successfully unbinded from #{app_name}".green
								else
									abort("Unbinding of service is failed".red)
								end
							end
						end
					end
				end
			end
		end
	end
	#This method is used to create a new service instance.
	#service_instance is the name of the service instance
	#service_name is the service that we found in our market place.
	def create_service_instance(service_instance,service_name)
		command = "cf create-service #{service_name} #{@service_plan} #{service_instance}"
		output = system(command)
		if output == true
			puts "#{service_instance} is created Successfully.".green
		else
			abort("Error occured while creating the #{service_instance} service instance.".red)
		end
	end
	#This method is used to delete the service instance by providing
	#the name of the service instance.
	def delete_service_instance(service_instance)
		unbind_service_instance(service_instance)
		puts "Deleting the service Instance".green
		output = system("cf delete-service #{service_instance} -f")
		if output == true
			puts "#{service_instance} is deleted successfully".green
		else
			abort("Error occured while deleting the #{service_instance} service instance.".red)
		end
	end
	#This method is used to check existence of the service instance.
	#If service instance is present , delete that and create again.
	#IF service instance is not present, create the service instance.
	def check_for_service_instance(service_instance)
		Dir.chdir @curl_path
		url = "\"#{@Api_url}/v2/service_instances\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allservicesinstances_hash = JSON.parse(command_output)
		if allservicesinstances_hash.has_key?("error_code")
			puts allservicesinstances_hash["error_code"].red
		else
			no_of_services_instances=allservicesinstances_hash["resources"].length
			count = 0
			for i in 0..(no_of_services_instances-1)
				if allservicesinstances_hash["resources"][i]["entity"]["name"]==service_instance
					delete_service_instance(service_instance)
					count = count+1
					break
				end
			end
			if count==1 or count==0
				create_service_instance(service_instance,@service_name)
			end
		end
	end
	#This method is used to check if the service is present in market place or not in a particular space.
	#if service is not present in space, notify that serivce is not found and again prompt for
	#entering both service name and space.
	def check_for_service_in_marketplace(service_name,space_name)
		Dir.chdir @curl_path
		guid = @spaces_hash[space_name.upcase]["guid"]
		url = "\"#{@Api_url}/v2/spaces/#{guid}/services\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allservices_hash = JSON.parse(command_output)
		if allservices_hash.has_key?("error_code")
			puts allservices_hash["error_code"].red
		else
			no_of_services=allservices_hash["resources"].length
			count = 0
			count1 = 0
			hash1 = Hash.new
			for k in 0..(no_of_services-1)
				if (allservices_hash["resources"][k]["entity"]["label"]).include?service_name
					hash1[count1] = k
					puts "#{count1} : #{allservices_hash["resources"][k]["entity"]["label"]}".green
					count1 = count1+1
				end
			end
			if count1 == 0
				abort("No such service found in market place".red)
			end
			puts "Choose the service from the market place.".yellow
			print "Enter the number corresponding to your required service::".yellow
			service_id = hash1[gets.chomp.to_i]
			@service_name = allservices_hash["resources"][service_id]["entity"]["label"]
			for i in 0..(no_of_services-1)
				if (allservices_hash["resources"][i]["entity"]["label"])==@service_name
					puts "using the service #{@service_name}".green
					guid1 = allservices_hash["resources"][i]["metadata"]["guid"]
					Dir.chdir @curl_path
					url1 = "\"#{@Api_url}/v2/services/#{guid1}/service_plans\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
					command_output1  = `#{@curl_command} -s #{url1}`
					allservices_hash3 = JSON.parse(command_output1)
					no_of_services3=allservices_hash3["resources"].length
					puts "Availiable service plans are:::".green
					hash2= Hash.new
					count2=0
					for j in 0..(no_of_services3-1) 
						hash2[count2]=j
						puts "#{count2} : #{allservices_hash3["resources"][j]["entity"]["name"]}".green
						count2 = count2 +1
					end
					puts "Choose the service plan to create a service instance.".yellow
					print "Enter the number corresponding to your required service plan::".yellow
					service_plan_id =hash2[gets.chomp.to_i]
					puts ""
					@service_plan = allservices_hash3["resources"][service_plan_id]["entity"]["name"]
					return true
					count = count+1
					break
				end
			end
			if count==no_of_services
				abort("Service not found in Market place".red)
				return false
			end
		end
	end
	#This is the main method where execution starts.
	def main()
		# This is the service name to check in market place
		print "Enter the service name to check in market place:".yellow
		@service_name = gets.chomp
		puts ""
		result = check_for_service_in_marketplace(@service_name,@space_name)
		if result == true
			# This is the service instance name
			print "Enter the service instance name to create a new service:".yellow
			@service_instance = gets.chomp
			puts ""
			check_for_service_instance(@service_instance)
		end
	end
	#return method
	def service_instance()
		return @service_instance
	end
end
