# start.rb
# This class is used for starting the application name.
class Start
	def start(application_name)
		puts "#{application_name} is going to start".green
		command = system("cf start #{application_name}")
		if command == true
			puts "#{application_name} is successfully started.".green
		else
			abort("Application is not started".red)
		end
	end
end
