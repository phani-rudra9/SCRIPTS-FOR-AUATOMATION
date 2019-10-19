import boto.ec2.elb
import boto.ec2 as ec2
from boto.ec2.elb import HealthCheck
import optparse


parser = optparse.OptionParser()
parser.add_option('--source_loadbalancer_name',help='provide the name of the source loadbalancer to this key',type='str',dest='source_loadbalancer_name')
parser.add_option('--target_loadbalancer_name',help='provide the name of the target loadbalancer to this key',type='str',dest='target_loadbalancer_name')
(options,args) = parser.parse_args()

source_loadbalancer_name=options.source_loadbalancer_name
target_loadbalancer_name=options.target_loadbalancer_name

aws_access_key_id=""
aws_secret_access_key=""
region=""
elb_connection = boto.ec2.elb.connect_to_region(region,aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
def loadbalancer_operation(elb_connection,source_loadbalancer_name,target_loadbalancer_name):
    try:
        loadbalancer=elb_connection.get_all_load_balancers(load_balancer_names=[source_loadbalancer_name])[0]
        print loadbalancer
        zones=loadbalancer.availability_zones
#       ports=loadbalancer.listeners
        security_groups=loadbalancer.security_groups
        scheme=loadbalancer.scheme
        subnets=loadbalancer.subnets
        healthcheck=loadbalancer.health_check
        print zones
        ports=[(80, 8080, 'HTTP', 'HTTP')]
        print security_groups
        print scheme
        print subnets
        print healthcheck
        print "Load Balancer Found."
        try:
          lb=elb_connection.create_load_balancer(target_loadbalancer_name, zones, ports,security_groups=security_groups,scheme=scheme)
          lb.configure_health_check(healthcheck)
          print "Load balancer created."
        except Exception as e:
          print e
    except Exception as e:
        print "Error occured while trying to connect to loadbalancer."
        print e
loadbalancer_operation(elb_connection,source_loadbalancer_name,target_loadbalancer_name)
