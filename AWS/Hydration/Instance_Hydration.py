#!/usr/bin/python

import boto.ec2 as ec2 
import boto.cloudformation as cf 
import re 
import sys 
import json 
import time 
import os
import datetime 
from datetime import datetime
import subprocess

AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
aws_region = "us-east-1" 

snapshot_dict = {} 
additional_tags_ebs = {} 
latest_ami_id = "" 

# cloud formation template file name.
file_name = 'Cloud_Formation_Template.json' 

# instance_list contains the names of the instances which are same as the cloud formation template resource names. 
instance_list = ["TestInstance1","TestInstance2"] 

# volume_list contains the names of the volumes which are same as the cloud formation template resource names. 
volume_list = ["TestVolume1","TestVolume2"] 

# instance_filter retrieves the instances for which we need to create a new instance. 
instance_filter = {'tag:Name':['TestInstance1','TestInstance2']} 

# image_filter to find the latest ami id with the given filter. 
image_filter = {'root-device-name':'/dev/sda1'}

################################################################################################################ 

# Method to return the dictionary of tags assigned to a resource starts here.

def get_resource_tags(connection,resource_id): 
        resource_tags = {} 
        if resource_id: 
                tags = connection.get_all_tags({'resource_id':resource_id}) 
                for tag in tags: 
                        resource_tags[tag.name]=tag.value 
        return resource_tags
    
# Method to return the dictionary of tags assigned to a resource ends here. 

################################################################################################################ 

# Method to set the tags to a resource starts here. 
def set_resource_tags(resource,tags): 
        for tag_key,tag_value in tags.iteritems(): 
                if (tag_key not in resource.tags or resource.tags[tag_key] != tag_value):
			if not(tag_key.startswith('aws:')):
                       		resource.add_tag(tag_key,tag_value)
                        
# Method to set the tags to a resource ends here.

################################################################################################################# 

# Creating Snapshot for Running instances with the given filter starts here. 
def create_snapshots(connection): 
        global snapshot_dict 
        global instance_filter 
        global additional_tags_ebs
        reservations = connection.get_all_instances(filters=instance_filter)
        for reservation in reservations: 
                for instance in reservation.instances: 
                        instance_name=instance.tags['Name'] 
                        block_devices = instance.block_device_mapping 
                        for device in block_devices: 
                                result = re.match(r'^/dev/sdb$',device) 
                                if result is not None: 
                                        volume = block_devices[device] 
                                        tags_to_add = get_resource_tags(connection,volume.volume_id) 
                                        volume_name = tags_to_add['Name'] 
                                        tags_to_add['LastAttachInstance']=instance.id
                                        additional_tags_ebs[volume_name]=[{'Key':'LastAttachInstance','Value':instance.id},{'Key':'LastAttachTime','Value':volume.attach_time}] 
                                        tags_to_add['LastAttachTime']=volume.attach_time 
                                        description = "Snapshot for "+volume_name 
                                        print ("Snapshot creation is starting for "+volume_name+" which is attached to "+instance_name)
                                        print ("#######################################################################################")
                                        try: 
                                                snapshot = connection.create_snapshot(volume.volume_id,description) 
                                                set_resource_tags(snapshot, tags_to_add) 
                                                while True: 
                                                        time.sleep(5) 
                                                        snapshot_instance = connection.get_all_snapshots(snapshot_ids=[snapshot.id])[0] 
                                                        snapshot_status = snapshot_instance.status 
                                                        if snapshot_status == "completed" or snapshot_status == "error": 
                                                                break 
                                                if snapshot_dict.has_key(volume_name): 
                                                        snapshot_dict[volume_name].append(snapshot.id) 
                                                else: 
                                                        snapshot_dict[volume_name]=[snapshot.id] 
                                                if snapshot_status == "completed": 
                                                        print ("Snapshot is created for "+volume_name+" which is attached to "+instance_name) 
                                                        print ("###############################################################################") 
                                                else: 
                                                        print ("Snapshot creation failed for "+volume_name+" which is attached to "+instance_name)
                                                        print ("###############################################################################")
                                        except Exception as e: 
                                                print (e) 
                                                print ("###############################################################################")
                                                exit() 
        print (snapshot_dict)
        
# Creatig Snapshot for Running instances with the given filter ends here.

################################################################################################################# 

# Getting the latest ami id and creation date with the given filter starts here. 
def get_latest_ami_id(connection): 
    global latest_ami_id 
    global image_filter
    index=0
    images = connection.get_all_images(filters=image_filter) 
	if len(images) == 1: 
		index = 0 
    else: 
	compare_date = images[0].creationDate 
        compare_date_obj = datetime.strptime(compare_date,"%Y-%m-%dT%H:%M:%S.%fZ") 
        for i in range(1,len(images)):
            creation_date=images[i].creationDate 
            datetime_obj=datetime.strptime(creation_date,"%Y-%m-%dT%H:%M:%S.%fZ") 
            if datetime_obj >= compare_date_obj: 
		compare_date_obj = datetime_obj 
                index = i 
    latest_ami_id = images[index].id 
    latest_ami_created_date = images[index].creationDate
	        
# Getting the latest ami id and creation date with the given filter ends here. 

################################################################################################################### 

# Modifying the snapshot id's and ami id's and adding the new dynamic tags for volumes in the cloud formation template starts here. 
def update_cf_template(): 
        global file_name 
        global instance_list 
        global volume_list 
        global snapshot_dict
	print instance_list
	print volume_list
	print snapshot_dict
        snapshot_names = snapshot_dict.keys()
        with open(file_name,'r') as f: 
                data = json.load(f) 
                try: 
                        for instance in instance_list: 
                                data['Resources'][instance]['Properties']['ImageId']=latest_ami_id 
                                for volume in volume_list: 
                                        tags = data['Resources'][volume]['Properties']['Tags'] 
                                        for tag in tags: 
                                                if tag['Key']=='Name': 
                                                        volume_search = tag['Value'] 
                                                        break
                                        if snapshot_dict.has_key(volume_search): 
                                                data['Resources'][volume]['Properties']['SnapshotId']=snapshot_dict[volume_search][0] 
                                        for i in range(len(tags)): 
                                                if tags[i]['Key']=='LastAttachInstance': 
                                                        if additional_tags_ebs.has_key(volume_search): 
                                                                for new_tag_0 in additional_tags_ebs[volume_search]: 
                                                                        if new_tag_0['Key']=='LastAttachInstance': 
                                                                                data['Resources'][volume]['Properties']['Tags'][i]['Value']=new_tag_0['Value'] 
                                                                                break 
                                                if tags[i]['Key']=='LastAttachTime': 
                                                        if additional_tags_ebs.has_key(volume_search): 
                                                                for new_tag_1 in additional_tags_ebs[volume_search]: 
                                                                        if new_tag_1['Key']=='LastAttachTime':
                                                                                data['Resources'][volume]['Properties']['Tags'][i]['Value']=new_tag_1['Value'] 
                                                                                break 
                finally: 
                        f.close() 
                        os.remove(file_name) 
        print (data)
        with open(file_name,'w') as f: 
                try: 
                        json.dump(data,f,indent=4) 
                finally: 
                        f.close()
                        
# Modifying the snapshot id's and ami id's and adding the new dynamic tags for volumes in the cloud formation template ends here.

######################################################################################################################################## 

# Creating a cloud formation stack starts here.

def create_stack(connection,stack_name,template_body,tags,parameters,update=False,timeout_in_minutes=10): 
    try: 
        if update:
            stack_id = connection.update_stack(stack_name, 
                template_body = template_body, 
                timeout_in_minutes = timeout_in_minutes, 
                tags = tags, 
                parameters = parameters) 
        else: 
            stack_id = connection.create_stack(stack_name, 
                template_body = template_body, 
                timeout_in_minutes = timeout_in_minutes, 
                tags = tags, 
                parameters = parameters) 
    except Exception as e: 
        print (e.message)
        raise e 
    status = None 
    print ("######################################################")
    if update: 
        print ("Stack is updating") 
    else: 
        print ("Stack is creating")
    while True: 
        time.sleep(5) 
        stack_instance = connection.describe_stacks(stack_id)[0] 
        status = stack_instance.stack_status 
        sys.stdout.write('.') 
        sys.stdout.flush() 
        if 'CREATE_COMPLETE' in status or 'UPDATE_COMPLETE' in status: 
            break 
        if 'CREATE_FAILED' in status or 'ROLLBACK_IN_PROGRESS' in status or 'ROLLBACK_COMPLETE' in status: 
            break 
    print ("\n") 
    if (status == "CREATE_COMPLETE") or (status == "UPDATE_COMPLETE"): 
        if update: 
          print ("Stack is updated successfully.")
        else: 
          print ("Stack is created sucessfully.") 
    else: 
        if update:
          print ("Stack updation failed.")
          exit()
        else: 
          print ("Stack creation failed.") 
          exit()
# Deleting the older stack
def delete_stack(connection_cf,stack_name):
  stack_list=connection_cf.list_stacks(stack_status_filters=['CREATE_COMPLETE'])
  for stack in stack_list:
    if (stack.stack_name).startswith('T3Hydration'):
      if stack.stack_name != stack_name:
        try:
          delete_stack(connection_cf,stack.stack_name)
        except Exception as e:
          print "Error occurred while deleting the stack."
          print e

# Creating a cloud formation stack ends here.


# Main functions starts here.
connection_ec2 = ec2.connect_to_region(aws_region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY) 
connection_cf = cf.connect_to_region(aws_region,aws_access_key_id=AWS_ACCESS_KEY_ID,aws_secret_access_key=AWS_SECRET_ACCESS_KEY) 
timestr = time.strftime("%Y%m%d")
stack_name="T3Hydration-"+str(timestr)
create_snapshots(connection_ec2) 
get_latest_ami_id(connection_ec2)
update_cf_template() 
with open(file_name,'r') as f:  
	tags = {'Name':stack_name}
	create_stack(connection_cf,stack_name,f.read(),tags,[])
#delete_stack(connection_cf,stack_name)

