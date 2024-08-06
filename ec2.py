import boto3
from botocore.exceptions import ClientError
from util import get_full_pem_file_path

class Ec2Manager:
    def __init__(self, region):
        self.region = region
        self.ec2 = boto3.client('ec2', region_name=region)

    def list_instances(self):
        """
        Lists all running and stopped EC2 instances in the current region.
        """
        try:
            response = self.ec2.describe_instances()
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] in ['running', 'stopped']:
                        instances.append({
                            'InstanceId': instance['InstanceId'],
                            'InstanceState': instance['State']['Name'],
                            'Instance': instance
                        })
            return instances
        except ClientError as e:
            print(f"Error listing instances: {e}")
            return []

    def get_instance_ids(self, status):
        instances = self.list_instances()
        return [i["InstanceId"] for i in instances if i["InstanceState"] == status]

    def stop_instance(self, instance_id):
        """
        Stops the specified EC2 instance.
        """
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            print(f"Stopped instance {instance_id}")
        except ClientError as e:
            print(f"Error stopping instance {instance_id}: {e}")

    def terminate_all(self):
        ids = self.get_instance_ids("running")
        for id in ids:
            self.terminate_instance(id)

    def describe_instances(self, instance_types):
        try:
            response = self.ec2.describe_instance_types(InstanceTypes=instance_types)
            return response
        except ClientError as e:
            print(f"Error describing instances: {e}")


    def get_memory_of_instances(self, instance_types):
        response = self.describe_instances(instance_types=instance_types)
        memory = {}
        for instance_type in response['InstanceTypes']:
            memory[instance_type['InstanceType']] = instance_type['MemoryInfo']['SizeInMiB']
        return memory


    def terminate_instance(self, instance_id):
        """
        Terminates the specified EC2 instance.
        """
        try:
            self.ec2.terminate_instances(InstanceIds=[instance_id])
            print(f"Terminated instance {instance_id}")
        except ClientError as e:
            print(f"Error terminating instance {instance_id}: {e}")

    def get_instance_status(self, instance_id):
        """
        Returns the current status of the specified EC2 instance.
        """
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            return response['Reservations'][0]['Instances'][0]['State']['Name']
        except ClientError as e:
            print(f"Error getting instance status: {e}")
            return None

    # get free ubuntu 22.04 ami id
    def retrieve_ami_id(self):
        try:
            response = self.ec2.describe_images(
                Owners=['099720109477'],
                Filters=[
                    {
                        'Name': 'name',
                        'Values': ['ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*']
                    },
                    {
                        'Name': 'state',
                        'Values': ['available']
                    },
                    {
                        'Name': 'is-public',
                        'Values': ['true']
                    }
                ]
            )
            return response['Images'][0]['ImageId']
        except ClientError as e:
            print(f"Error retrieving AMI ID: {e}")
            return None

    # create ec2 key pairs and download pem file
    def create_key_pair(self, key_name):
        try:
            response = self.ec2.create_key_pair(KeyName=key_name)
            with open(get_full_pem_file_path(self.region), "w") as f:
                f.write(response['KeyMaterial'])
            print(f"Key pair '{key_name}' created and saved to {key_name}.pem")
        except ClientError as e:
            print(f"Error creating key pair: {e}")

    def get_public_ip(self):
        instances = self.list_instances()
        for instance in instances:
            if instance['InstanceState'] == 'running':
                return instance['Instance']['PublicIpAddress']