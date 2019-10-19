# check.rb
# @author Vinodh kumar Basavani
# This class is used to push the data to the webpage and again pull the data from the application.
# And compares the data.
class Check
	#This method will push the data to the started application.
	def initialize(api_url,curl_command,curl_path,dummy_directory,application_name)
		@api_url = api_url
		@curl_command = curl_command
		@curl_path = curl_path
		@dummy_directory=dummy_directory
		@application_name = application_name
	end
	#This method is used to push the data to the application url
	def push_data()
		if @api_url[4] != "s"
			@app ="https://"+@application_name+".run"+@api_url[17..@api_url.length]
		else
			@app="https://"+@application_name+".run"+@api_url[18..@api_url.length]
		end
		Dir.chdir @curl_path
		put_command = system("#{@curl_command} -X PUT #{@app}/foo -d \"data=Application is UP and RUNNING successfully.\"")
		if put_command == true
			puts "\nSuccessfully uploaded the data to application".green
		else
			abort("Error occured while uploading data to application".red)
		end
	end
	#This method will pull the data from the started application.
	def get_data()
		# change directory to some dummy path to save the intermediate files.
		Dir.chdir @curl_path
		get_command = system("#{@curl_command} -s -X GET #{@app}/foo")
		puts ""
		if get_command == true
			puts "OK".green
		else
			puts "Error occured while Retrieving the data from the application".red
		end
	end
end
