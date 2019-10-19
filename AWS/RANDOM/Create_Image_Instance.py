import sys
import time
import optparse
from boto import ec2
import time
import datetime

ts=time.time()
st = str(datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d-%H-%M-%S'))

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
region=""

user_data_script="""#!/bin/bash
mkdir /opt/Test"""

parser = optparse.OptionParser()
parser.add_option('--instance_name',help='provide the name of the instance',type='str',dest='instance_name')
(options,args) = parser.parse_args()
instance_name=options.instance_name

connection_ec2=ec2.connect_to_region(region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
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
    print vars(instance)
    if instance.tags.has_key('Name') and (instance.state=="running" or instance.state=="stopped"):
      if instance.tags['Name']==instance_name:
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

if found==True:
  image_id=create_image(connection_ec2,instance_id,name,description,block_device_mapping)
  try:
    reservation=connection_ec2.run_instances(image_id=image_id,subnet_id=subnet_id,key_name=key_name,instance_type=instance_type,instance_profile_name=instance_profile,security_group_ids=[security_group_id],user_data=user_data_script)
    instance = reservation.instances[0]
    status = instance.update()
    print "Instance creation started."
    while status == 'pending':
      time.sleep(5)
      sys.stdout.write(".")
      sys.stdout.flush()
      status = instance.update()
    sys.stdout.write("\n")
    if status == 'running':
      instance.add_tag("Name",instance_name)
      pritn "Instance Creation completed."
    else:
      print "Error occured while creating instance."
  except Exception as e:
    print e
    print "Error occured while creating an instance."
else:
  print "Given instance not found."
