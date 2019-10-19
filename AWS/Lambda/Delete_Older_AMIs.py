from datetime import datetime,timedelta
import boto3
import re

def delete_older_amis(connection,number_of_days,account_id):
	images_deleted=[]
	now=datetime.now()
	compare_datetime=now-timedelta(days=number_of_days)
	#compare_datetime=datetime.strptime("2017-11-16 14:25:02.566000","%Y-%m-%d %H:%M:%S.%f")
	images = list(connection.images.filter(Owners=['self']).all())
	if len(images) == 0:
		print("No AMIs Found to Delete. Hence exiting...")
	else:
	    for i in range(0,len(images)):
		    image_creation_date=images[i].creation_date
		    image_creation_date=datetime.strptime(image_creation_date,"%Y-%m-%dT%H:%M:%S.%fZ")
		    if image_creation_date <= compare_datetime:
			    image_id=images[i].id
			    image_name=images[i].name
			    image_description=images[i].description
			    image_state=images[i].state
			    print(image_state)
			    print(image_id)
			    if image_state=='available':
				    try:
					    images[i].deregister()
					    print("Image Deletion for "+image_name+" is Started.(May take a while for this operation)")
					    images_deleted.append(image_id)
				    except Exception as e:
					    print("Image Deletion for "+image_name+" is still in Progress.")
			    else:
				    print("No images found with status as available")
	if images_deleted:
		for snapshot in list(connection.snapshots.filter(OwnerIds=[account_id]).all()):
			image_id_from_snapshot=snapshot.description.split()[4]
			if image_id_from_snapshot in images_deleted:
				try:
					snapshot.delete()
					print("Deletion of Snapshot corresponding to "+image_id_from_snapshot+" is Started.")
				except Exception as e:
					print("Deletion of Snapshot corresponding to "+image_id_from_snapshot+" is Failed.")
def lambda_handler(event,context):
	aws_region="us-east-1"
	AWS_ACCESS_KEY_ID=""
	AWS_SECRET_ACCESS_KEY=""
	number_of_days=7
	account_id=""
	connection_ec2 = boto3.resource('ec2',aws_region)
	#connection_ec2 = boto3.resource('ec2',aws_region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
	delete_older_amis(connection_ec2,number_of_days,account_id)
