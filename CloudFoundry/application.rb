# application.rb
# This ruby program is used check if the application is present in space or not.
# If application is not present, then it will create that application.
# If application is present, delete that application and creat again.
# project_path is the name of the folder to which we copy the files from zip_path to project_path including the last directory in the zip_path
# so the last directory in zip_path + project_directory+ becomes the directory in which there is application files.
# project_directory is the directory in in which project files are there.
require 'io/console'
require 'json'
require 'colorize'
require 'fileutils'
class Application
	#constructor 
	def initialize(curl_command,curl_path,application_name,access_token,api_url,zip_path,project_directory,git_url)
		@curl_command = curl_command
		@curl_path = curl_path
		@application_name = application_name
		@access_token = access_token
		@Api_url = api_url
		@zip_path = zip_path
		@git_url = git_url
		@project_directory = project_directory
		list1= @zip_path.split('/')
		@project_path = @project_directory+"/"+list1[list1.length-1]
	end
	def clean_zip_path()
		Dir.chdir @zip_path   
		Dir.entries('.').each do 
			|item|
			if item != "." and item !=".." and item !="master.zip"
				FileUtils.rm_rf(item)
			end
		end
	end
	#This method is used to download the project folder from the git and will extract the 
	#project name from the git url and we will use this name to create the application.
	def get_project_from_git()
		Dir.chdir @zip_path
		#puts "Enter the Git project URL(HTTPS)"
		wget_command = "wget #{@git_url}"
		puts "Downloading from the GIT to #{@zip_path}".green
		output = system(wget_command)
		if output == true
			puts "Successfully downloaded the source from git".green
			copy()
		else
			abort("Problem in downloading the source from git".red)
		end
	end
	#If project folder is not found locally, download it from the git.
	#this method will initiate the project folder download from git and return the project name.
	def not_found_zip()
		puts "Project zip Not Found Locally".green
		get_project_from_git()
	end
	#If project folder found locally, then push this project fodler.
	#This method will return a project name if it exists.
	def found_zip()
		puts "Project zip Found locally".green
		copy()
	end
	# copy the zip file from zip directory to the project directory.
	def copy()
		Dir.chdir @zip_path
		FileUtils.cp_r @zip_path,@project_path
	end
	#This method is used to check if the source zip is present in the local system or not.
	def folder_name()
		Dir.chdir @zip_path
		clean_zip_path()
		zip = Dir['*.zip']
		if zip.length != 0
			found_zip()
		else
			not_found_zip()
		end
	end
	# This method is used to delete all the folder that are in the project directory.
	def clean()
		Dir.chdir @project_directory    
		Dir.entries('.').each do 
			|item|
			if item != "." and item !=".."
				FileUtils.rm_rf(item)
			end
		end
	end
	#This method is used to check if the application is present or not.
	#If application is present, delete that and create again.
	#IF application is not present, then create the application.
	def check_for_app(application_name)
		Dir.chdir @curl_path
		url = "\"#{@Api_url}/v2/apps\""+" -X GET \ -H \"Authorization: bearer #{@access_token}\""
		command_output  = `#{@curl_command} -s #{url}`
		allapps_hash = JSON.parse(command_output)
		if allapps_hash.has_key?("error_code")
			puts allapps_hash["error_code"].red
		else
			no_of_apps=allapps_hash["resources"].length
			count = 0
			for i in 0..(no_of_apps-1)
				application_name1 = allapps_hash["resources"][i]["entity"]["name"]
				if application_name1 == application_name
					delete_app(application_name)
					count = count+1
					break
				end
			end
			if count == 0 or count ==1
				clean()
				folder_name()
				Dir.chdir @project_path
				zip_file = Dir["*.zip"]
				command = system("unzip -q #{zip_file[0]}")
				if command == true
					puts "Project zip is Successfully extracted.".green
				else
					abort("Project zip extraction is failed.".red)
				end
				Dir.entries('.').each do 
					|item|
					if item != "." and item != ".." and item != zip_file[0]
						@project_name = item
					end	
				end
				create_app(application_name)
			end
		end
	end
	#This method is used to create the particular application.
	def create_app(application_name)
		Dir.chdir "#{@project_path}/#{@project_name}"
		create_code = system("cf push #{application_name} --no-start")
		if create_code == true
			puts "Successfully created Application.".green
		else
			abort("There is a problem in Creation of Application.".red)
		end
	end
	#This method is used to delete the particular application.
	def delete_app(application_name)
		delete_code = system("cf delete #{application_name} -f -r")
		if delete_code == true
			puts "#{application_name} is deleted and creating app again".green
		else
			abort("Problem in deleting the application.".red)
		end
	end
	def delete_orphan_route()
		puts "Deleting the Orphaned routes".green
		delete_orphan_code = system("cf delete-orphaned-routes -f")
		if delete_orphan_code == true
			puts "Successfully deleted all Orphaned routes".green
		else
			puts "Error occured while deleting the Orphaned routes".red
		end
	end
end
