# endpoint.rb
# This class is used to generate the hash of all organizations and spaces present in the 
# user account.
require 'colorize'
require 'json'
class Endpoint
	# constructor
	def initialize(curl_command,curl_path,api_url,access_token)
		@curl_command = curl_command
		@curl_path = curl_path
		@Api_url = api_url
		@access_token = access_token
		@organizations_hash=Hash.new
		@spaces_hash=Hash.new
	end
	#This method is used to return a hash which contains the all organizations present in user account.
	#This will return a hash "@organizations_hash" which contains the information about all spaces.
	#{"name_of_the_organization" => {"name_of_the_organization","guid"}}
	def get_allorganizations()
		Dir.chdir @curl_path
		url = "\"#{@Api_url}/v2/organizations\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allorganizations_hash = JSON.parse(command_output)
		if allorganizations_hash.has_key?("error_code")
			puts allorganizations_hash["error_code"].red
		else
			no_of_organizations=allorganizations_hash["resources"].length
			for i in 0..(no_of_organizations-1)
				hash1=Hash.new
				hash1["name"] = allorganizations_hash["resources"][i]["entity"]["name"]
				hash1["guid"] = allorganizations_hash["resources"][i]["metadata"]["guid"]
				@organizations_hash[(allorganizations_hash["resources"][i]["entity"]["name"]).upcase]=hash1
			end
		end
	end
	#This method is used to return a hash which contains the all spaces present in user account.
	#This will return a hash "@spaces_hash" which contains the information about all spaces.
	#{"name_of_the_space" => {"name_of_the_space","guid"}}
	def get_allspaces()
		Dir.chdir @curl_path
		url = "\"#{@Api_url}/v2/spaces\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allservices_hash = JSON.parse(command_output)
		if allservices_hash.has_key?("error_code")
			puts allservices_hash["error_code"].red
		else
			no_of_services=allservices_hash["resources"].length
			for i in 0..(no_of_services-1)
				hash2=Hash.new
				hash2["name"] = allservices_hash["resources"][i]["entity"]["name"]
				hash2["guid"] = allservices_hash["resources"][i]["metadata"]["guid"]
				@spaces_hash[(allservices_hash["resources"][i]["entity"]["name"]).upcase]=hash2
			end
		end
	end
	def main(organization_name,space_name)
		get_allorganizations()
		get_allspaces()
		@organization_name = organization_name
		@boolean_organization=@organizations_hash.has_key?(@organization_name.upcase)
		if @boolean_organization == true
			puts "Organization found".green
			@space_name = space_name
			@boolean_space = @spaces_hash.has_key?(@space_name.upcase)
			if @boolean_space == true
				puts "Space found".green
			else
				abort("Space Not found".red)
			end
		else
			abort("Organization Not found".red)
		end
	end
	def space_hash()
		return @spaces_hash
	end
end
