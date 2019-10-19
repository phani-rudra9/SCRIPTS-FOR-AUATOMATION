# bind.rb
# @author Vinodh kumar Basavani
# This will bind the applicaton to the service instance.
class Bind
	#This method will bind the application to the service instance.
	def binding_service_to_app(application,service)
		output = system("cf bind-service #{application} #{service}")
		if output == true
			puts "#{application} is successfully binded to #{service}".green
		else
			abort("Application binding is failed".red)
		end
	end
end
