# main.rb
# Main file for starting the execution of all classes.
require_relative 'application'
require_relative 'service'
require_relative 'bind'
require_relative 'start'
require_relative 'check'
require_relative 'endpoint'
require 'colorize'
require 'fileutils'
#This method is used to generate the token from UAA server by providing the UAA url and 
#usename and password.
def get_access_token()
	if @api_url[4] != "s"
		temp = @api_url[10..@api_url.length]
		@uaa_target = "https://uaa#{temp}"
	else
		temp=@api_url[11..@api_url.length]
		@uaa_target = "https://uaa#{temp}"
	end
	Dir.chdir @home_directory
	FileUtils.rm_rf(".uaac.yml")
	system("uaac target #{@uaa_target} --skip-ssl-validation >> /dev/null")
	print "Enter email:".yellow
	@uaa_username = gets.chomp
	print "Enter password:".yellow
	@uaa_password = STDIN.noecho(&:gets).chomp
	puts ""
	command = system("uaac token get #{@uaa_username} #{@uaa_password}")
	if command != true
		puts ""
		abort("Invalid Credentials.".red)
	else 
		puts "Token generated Successfully.".green
	end
	Dir.chdir @home_directory
	if Dir.glob(".uaac.yml") != '.uaac.yml'
		filehandler = File.open('.uaac.yml','r')
		for line in filehandler do
			if line[6..17]=="access_token"
				length_line = line.length
				@access_token = line[20..length_line]
			end
		end
	else
		abort("Unable to get Token.".red)
	end
end
#This method is used to prompt for getting api url and return the api url.
def get_api_url()
	print "Enter the API URL(include http:// or https://)::".yellow
	@api_url = gets.chomp
end
#This method is used to login into cloud foundry account using api url, username, password,
#organization name, space name.
def cf_login()
	command = system("cf login -a  #{@api_url} -u #{@uaa_username} -p #{@uaa_password} -o #{@organization_name} -s #{@space_name}")
	if command == true
		puts "Successfully loggned on as #{@uaa_username}".green
	else
		abort("Invalid credentials".red)
	end
end
# This is the main method for the automation of application deployment in cloud foundry.
def main()
	@home_directory="/home/ubuntu"
	@curl_path ="/usr/bin"
	@curl_command = "curl"
	@dummy_directory="/opt/cloudfoundry/dummy"
	@project = "redis"
	@zip_path = "/opt/cloudfoundry/gitzip/#{@project}"
	@project_directory = "/opt/cloudfoundry/project"
	@git_url ="https://github.com/pivotal-cf/cf-redis-example-app/archive/master.zip"
	get_api_url()
	get_access_token()
	print "Enter the Organization name:".yellow
	@organization_name = gets.chomp
	print "Enter the Space name:".yellow
	@space_name = gets.chomp
	endpoint = Endpoint.new(@curl_command,@curl_path,@api_url,@access_token)
	endpoint.main(@organization_name,@space_name)
	space_hash = endpoint.space_hash   # since it is needed in service class for checking the service in market place for a particular space.
	cf_login()
	print "Enter the application name:".yellow
	@application_name = gets.chomp
	application = Application.new(@curl_command,@curl_path,@application_name,@access_token,@api_url,@zip_path,@project_directory,@git_url)
	application.delete_orphan_route()
	application.check_for_app(@application_name)
	service = Service.new(@curl_command,@curl_path,@organization_name,@space_name,@api_url,@access_token,space_hash)
	service.main()
	@service_instance_name = service.service_instance
	bind = Bind.new
	bind.binding_service_to_app(@application_name,@service_instance_name)
	start_obj = Start.new
	start_obj.start(@application_name)
	check = Check.new(@api_url,@curl_command,@curl_path,@dummy_directory,@application_name)
	check.push_data()
	check.get_data()
end

# Execution of the whole program starts here.
if __FILE__ == $0
	main()
end
