#!/usr/bin/python

# Version : 1.2
# This plugin compares the contents of /etc/fstab and /proc/mounts and
# will report any difference and will monitor and report the status
# of each mout point.

import subprocess
import optparse
import sys

# Script Variables
filesystem_list=['ext4','ext3','ext2','nfs','xfs']

config_file = "/proc/mounts"
config_file1 = "/etc/fstab"

mountpoint_list=[]
mountpoint_list1=[]

flag = 0
messages = []
status_code = 0
rw_access =""

# Function for testing the  Write Access for a MountPoint
def check_mountpoint(path):
  command = "cd "+path+" && "+"touch wTeSt"
  output,error = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).communicate()
  if not error:
    command1 = " cd "+path+" && "+"rm -rf wTeSt"
    subprocess.Popen(command1,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True).communicate()
    return True
  else:
    return False

# Parser class for Taking the arguments for the command line.
parser = optparse.OptionParser()
parser.add_option('-w','--warningthreshold',dest='wthreshold',type='int',help='Warning threshold in terms of Usage Percentage.')
parser.add_option('-c','--criticalthreshold',dest='cthreshold',type='int',help='Critical threshold in terms of Usage Percentage.')
parser.add_option('-i', '--ignore-mountpoint-list', dest='ignoremountpoint', default="",help='List of Mountpoints to ignore check(comma separated).')
(options, args) = parser.parse_args()
warning_threshold = options.wthreshold
critical_threshold = options.cthreshold
ignoremountpoint = options.ignoremountpoint
ignoremountpoint_list = ignoremountpoint.split(',')

# Validating the Parser options
if (warning_threshold is None) or (critical_threshold is None):
  print '\nWarning threshold and Critical threshold are mandatory.\n'
  parser.print_help()
  sys.exit(3)

# Getting the Mount Points from /etc/fstab"
output1 = open(config_file1,'r')
for line1 in output1:
  if len(line1.strip()) != 0  and line1[0] != "#":
    b = (" ".join(line1.split())).split(' ')
    if b[2] in filesystem_list and b[1] not in ignoremountpoint_list:
      mountpoint_list1.append(b[1])

# Getting the Mount Points from /proc/mounts
output = open(config_file,'r')
for line in output:
  a = line.split(' ')
  if a[2] in filesystem_list and a[1] not in ignoremountpoint_list:
    mountpoint_list.append(a[1])

differ_mounts = []
# Comparing the Mount points from both file
if len(mountpoint_list1) > len(mountpoint_list):
  differ_mounts = list(set(mountpoint_list1)-set(mountpoint_list))
check_mountpoint_list = mountpoint_list1

# Getting the Disk usge of Mount Point
for mountpoint in check_mountpoint_list:
  cmd = "df -Th -P "+mountpoint
  proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
  output, err = proc.communicate()
  if output:
    output = output.split()
    FileSystem = output[8]
    Type = output[9]
    Size = output[10]
    Used = output[11]
    Avail = output[12]
    UsedPercent = output[13]
    FreePercent = str(100-(int(UsedPercent[:-1])))+"%"
    MountPoint = output[14]
    cmd1 = "df -i -P "+mountpoint
    proc1 = subprocess.Popen(cmd1,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
    output1, err1 = proc1.communicate()
    if output1:
      free_inodes = int(output1.split()[10])
      inode_percent = int(output1.split()[11][:-1])
      if (int(inode_percent) >= critical_threshold):
        flag = 1
        status_code = 2
        messages.append("CRITICAL - free Inodes: %s  %s (%s" % (MountPoint,free_inodes,(100-inode_percent))+"%)")
      elif (int(inode_percent) >= warning_threshold):
        flag = 1
        if status_code != 2:
          status_code = 1
          messages.append("WARNING - free Inodes: %s  %s (%s" % (MountPoint,free_inodes,(100-inode_percent))+"%)")
    else:
      flag = 1
      messages.append("CRITICAL - Unable to retrieve  the Inode information of "+mountpoint)
      status_code = 2
      continue

    if MountPoint:
      result = check_mountpoint(MountPoint)
      if result == False:
        rw_access = "(RO)"

    if (int(UsedPercent[:-1]) >= critical_threshold):
      flag = 1
      status_code = 2
      messages.append("CRITICAL - free space: %s%s  %s (%s" % (MountPoint,rw_access,Avail,FreePercent)+")")
    elif (int(UsedPercent[:-1]) >= warning_threshold):
      flag = 1
      if status_code != 2:
        status_code = 1
        messages.append("WARNING - free space: %s%s %s (%s" % (MountPoint,rw_access,Avail,FreePercent)+")")

  if err:
    flag = 1
    messages.append("CRITICAL - Unable to retrieve  the Disk usage Information of "+mountpoint)
    status_code = 2
  rw_access = ""
if len(differ_mounts) != 0:
  flag = 1
  messages.append("CRITICAL - Inconsistent Mount Point detected "+",".join(differ_mounts))
  status_code = 2


if flag > 0:
        for message in messages:
                print message
else:
        print 'OK - All are under threshold values'

sys.exit(status_code)
