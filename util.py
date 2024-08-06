import os
import boto3

def configure_internal_manager_ip(private_ips):
    return f'ip-{private_ips[0].replace(".", "-")}'

def get_downloads_folder():
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
    return downloads_folder

def get_login_user_name():
    return os.getlogin()

# get pem file name
def get_pem_file_name(region):
    pem_file = f"{get_login_user_name()}-{region}"
    return pem_file

def get_full_pem_file_path(region):
    pem_file = f"{get_pem_file_name(region=region)}.pem"
    full_path = os.path.join(get_downloads_folder(), pem_file)
    return os.getenv("PEM_FILE", full_path)

# check if a pem in download folder exist
# given input is a aws region, the pem file name is like "xiuliyun-us-east-1.pem" 
def check_pem_exist(region):
    pem_file = get_full_pem_file_path(region)
    if os.path.exists(pem_file):
        return True
    else:
        return False
    

def is_credential_valid():
    # Create an STS client
    sts_client = boto3.client('sts')

    try:
        # Call the get_caller_identity method to verify the credentials
        response = sts_client.get_caller_identity()

        # If the call is successful, the credentials are valid
        print("Credentials are valid.")
        print(f"User ID: {response['UserId']}")
        print(f"Account ID: {response['Account']}")
        print(f"ARN: {response['Arn']}")
        return True

    except Exception as e:
        # If an exception is raised, the credentials are invalid
        print("Credentials are invalid.")
        print(e)
        return False

# use Ec2Manager to create a key pair if pem file doesn't exist
def create_pem_file_if_not_there(region, ec2):
    filename = get_pem_file_name(region)
    if check_pem_exist(region=region):
        print(f"pem file {filename} already exists")
    else:
        print(ec2.create_key_pair(filename))

def get_os_roles():
    roles = os.getenv("OPENSEARCH_NODE_ROLES").split(",")
    return roles