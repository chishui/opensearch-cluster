import os
import sys
import boto3
import json
import click
from ec2 import Ec2Manager
from cf import CloudFormationManager
from util import get_pem_file_name, get_full_pem_file_path, is_credential_valid, create_pem_file_if_not_there, configure_internal_manager_ip, get_os_roles
from ssh_client import SshClient
from dotenv import load_dotenv

load_dotenv()

@click.group()
def cli():
    """This is a command line interface for several functions."""
    pass

def create_cloudformation_stack(stack_name, parameters):
    # Create the stack
    response = cf.create_stack(StackName=stack_name, TemplateBody=template_body, Parameters=parameters)


def get_ssh_client(ip, region):
    client = create_ssh_client(ip, "ubuntu", get_full_pem_file_path(region))

# Use Ec2Manager to terminate the running instances
# use click to run this function with parameters
region = os.getenv("AWS_REGION", "us-east-1")
ec2 = Ec2Manager(region)

@click.command()
def terminate_instances():
    ec2.terminate_all()


def create_ec2(instance_prefix):
    create_pem_file_if_not_there(region, ec2=ec2)
    cf = CloudFormationManager(region=region)

    stack_name = os.getenv("CF_STACK_NAME", "opensearch-cluster");
    if cf.stack_exists(region, stack_name):
        # delete stack first
        cf.delete_stack(stack_name)

    ami_id = ec2.retrieve_ami_id()

    # Define parameters
    parameters = [
        {'ParameterKey': 'KeyName', 'ParameterValue': get_pem_file_name(region)},
        {'ParameterKey': 'ImageId', 'ParameterValue': ami_id},
        {'ParameterKey': 'VolumeSize', 'ParameterValue': os.getenv("EBS_VOLUME_SIZE", "30")},
        {'ParameterKey': 'InstanceType', 'ParameterValue': os.getenv("INSTANCE_TYPE")},
        {'ParameterKey': 'OpenSearchVersion', 'ParameterValue': os.getenv("OPENSEARCH_VERSION")},
        {'ParameterKey': 'OpenSearchAdminPassword', 'ParameterValue': os.getenv("ADMIN_PASSWORD")},
        {'ParameterKey': 'InstanceName', 'ParameterValue': instance_prefix}
    ]

    # Read the CloudFormation template
    with open("ec2.yaml", 'r') as file:
        template_body = file.read()
        cf.create_stack(stack_name, template_body=template_body, parameters=parameters)


def get_jvm_file(new_memory):
    filename = 'jvm.options.bak'
    target_filename = filename + "_updated"
    with open('resources/' + filename, 'r') as jvm_file:
        jvm_options = jvm_file.read()
        allocate_memory_str = str(int(new_memory)) + 'g'
        jvm_options = jvm_options.replace('-Xms1g', '-Xms' + allocate_memory_str)
        jvm_options = jvm_options.replace('-Xmx1g', '-Xmx' + allocate_memory_str)
        with open(target_filename , 'w') as tmp_jvm:
            tmp_jvm.write(jvm_options)
    return target_filename


def get_yml_file(manager_ip, node_count, region):
    filename = 'opensearch.yml'
    target_filename = filename + "_updated"
    with open('resources/' + 'opensearch.yml', 'r') as yml_file:
        content = yml_file.read()
        content = content.replace("cluster.initial_cluster_manager_nodes: []",
                                 f"""cluster.initial_cluster_manager_nodes: ["{manager_ip}"]""")
        content = content.replace("discovery.seed_hosts: []",
                                 f"""discovery.seed_hosts: ["{manager_ip}.{region}.compute.internal"]""")
        content = content.replace("node.max_local_storage_nodes: 1",
                                 f"""node.max_local_storage_nodes: {str(node_count)}""")
        content = content.replace("node.roles: []",
                                 f"""node.roles: {get_os_roles()}""")
        with open(target_filename, 'w') as f:
            f.write(content)
    return target_filename

MAX_MEMORY = 32

@click.command()
def create_opensearch_cluster():
    # check credentials
    if not is_credential_valid():
        return
    
    # create ec2
    prefix = os.getenv("INSTANCE_NAME_PREFIX", "opensearch")
    #create_ec2(prefix)
    # retrieve newly created instances
    instances = ec2.list_instances()
    just_created_instances = []
    for instance in instances:
        for item in instance['Instance']['Tags']:
            if item['Key'] == 'Name' and item['Value'].startswith(prefix):
                just_created_instances.append(instance)

    # create local jvm.options and opensearch.yml files
    private_ips = get_ips(just_created_instances, is_private=True)
    manager_ip = configure_internal_manager_ip(private_ips)
    node_count = len(private_ips)
    memory = get_memory(os.getenv("INSTANCE_TYPE"))
    print(private_ips, manager_ip, node_count, memory)
    jvm_file = get_jvm_file(min(memory, MAX_MEMORY))
    yml_file = get_yml_file(manager_ip, node_count, region)
    print(jvm_file, yml_file)

    # upload files
    root_dir = os.getenv("ROOT_DIR", "/home/ubuntu")
    cluster_base_dir = os.getenv("CLUSTER_BASE_DIR")
    cluster_dir = f"{root_dir}/{cluster_base_dir}"
    public_ips = get_ips(just_created_instances, is_public=True)
    print(cluster_dir, public_ips)
    ssh_clients = {}
    for public_ip in public_ips:
        ssh_client = SshClient(public_ip, "ubuntu", get_full_pem_file_path(region))
        ssh_clients[public_ip] = ssh_client
        ssh_client.upload_file(jvm_file, f"{cluster_dir}/config/jvm.options")
        ssh_client.upload_file(yml_file, f"{cluster_dir}/config/opensearch.yml")
        ssh_client.upload_file("launch.sh", f"{cluster_dir}/launch.sh")

    # launch cluster
    for client in ssh_clients.values():
        client.execute(f"chmod +x {cluster_dir}/launch.sh")
        client.execute(f'bash {cluster_dir}/launch.sh -s -- {os.getenv("ADMIN_PASSWORD")}')



def get_ips(instances, is_private=False, is_public=False):
    if is_private:
        return [instance['Instance']['PrivateIpAddress'] for instance in instances]
    if is_public:
        return [instance['Instance']['PublicIpAddress'] for instance in instances]


def get_memory(instance_type):
    memory = ec2.get_memory_of_instances(instance_types=[instance_type])[instance_type]
    print(memory)
    return int(memory/1024)//2

# Add commands to the CLI
cli.add_command(terminate_instances)
cli.add_command(create_opensearch_cluster)

if __name__=="__main__":
    cli()

