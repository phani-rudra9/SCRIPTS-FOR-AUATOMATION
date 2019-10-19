import sys
import time
import optparse
from boto import ec2
from boto.ec2.autoscale import LaunchConfiguration
from boto.ec2.autoscale import AutoScalingGroup

import time
import datetime

ts=time.time()
st = str(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S'))

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
region=""

parser = optparse.OptionParser()
parser.add_option('--instance_name',help='name of the instance',type='str',dest='instance_name')
parser.add_option('--autoscaling_group_name',help='name of the autoscaling group',type='str',dest='autoscaling_group_name')
(options,args) = parser.parse_args()
instance_name=options.instance_name
autoscaling_group_name=options.autoscaling_group_name

connection_ec2=ec2.connect_to_region(region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
connection_as=ec2.autoscale.connect_to_region(region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
reservations=connection_ec2.get_all_instances()

def create_image(connection_ec2,instance_id,name,description,block_device_mapping):
  new_image_id=connection_ec2.create_image(instance_id=instance_id,name=name,description=description,block_device_mapping=block_device_mapping)
  image = connection_ec2.get_all_images(image_ids=[new_image_id])[0]
  print "Image Creation Started"
  while image.state == 'pending':
    time.sleep(5)
    sys.stdout.write(".")
    sys.stdout.flush()
    image.update()
  sys.stdout.write("\n")
  if image.state == 'available':
    print "Image Creation completed."
    return new_image_id
  else:
    print "Error occured while creating the image."
    exit()
	
found=False
for reservation in reservations:
  for instance in reservation.instances:
    print instance.tags
    if instance.tags.has_key('Name'):
      if instance.tags['Name']==instance_name and (instance.state=="running" or instance.state=="stopped"):
        block_device_mapping=instance.block_device_mapping
        instance_id=instance.id
        name=st+"-"+instance_name
        description="A Test Image Created From "+instance_name+" Instance."
        subnet_id=instance.subnet_id
        key_name=instance.key_name
        instance_type=instance.instance_type
        instance_profile=instance.instance_profile
        found=True
        security_groups=connection_ec2.get_all_security_groups()
        for securitygroup in security_groups:
          for instanceid in securitygroup.instances():
            if str(instanceid).split(':')[1]==instance_id:
				security_group_id=securitygroup.id

group_list = connection_as.get_all_groups(names=[autoscaling_group_name])
if found==True and len(group_list)!=0:
  image_id=create_image(connection_ec2,instance_id,name,description,block_device_mapping)
  launch_config_name=st+"-lc-"+instance_name
  try:
    lc = LaunchConfiguration(name=launch_config_name,image_id=image_id,key_name=key_name,security_groups=[security_group_id],instance_profile_name=instance_profile,instance_type=instance_type)
    connection_as.create_launch_configuration(lc)
    print "launch configuration created."
  except Exception as e:
    print "Error occured while creating launch configuration."
  group=group_list[0]
  group.launch_config_name=launch_config_name
  group.update()
else:
  print "Given data not found."
