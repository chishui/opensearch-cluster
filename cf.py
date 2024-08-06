import os
import boto3
from botocore.exceptions import ClientError

class CloudFormationManager:
    def __init__(self, region):
        self.cf = boto3.client('cloudformation', region_name=region)

    def create_stack(self, stack_name, template_body, parameters=None):
        try:
            response = self.cf.create_stack(StackName=stack_name, TemplateBody=template_body, Parameters=parameters, Capabilities=['CAPABILITY_NAMED_IAM'])
            self.wait_for_stack_status(stack_name)
            print(response)
            print(f"Stack '{stack_name}' created successfully!")
        except ClientError as e:
            print(f"Error creating stack: {e}")

    def delete_stack(self, stack_name):
        try:
            response = self.cf.delete_stack(StackName=stack_name)
            # Create a waiter
            waiter = self.cf.get_waiter('stack_delete_complete')
            
            # Wait for the stack to be deleted
            print(f"Waiting for stack {stack_name} to be deleted...")
            waiter.wait(StackName=stack_name)
            print(f"Stack {stack_name} has been successfully deleted.")
        except Exception as e:
            print(f"An error occurred while waiting for the stack to be deleted: {e}")

    def update_stack(self, stack_name, template_body, parameters=None):
        try:
            response = self.cf.update_stack(StackName=stack_name, TemplateBody=template_body, Parameters=parameters)
            print(f"Stack '{stack_name}' updated successfully!")
        except ClientError as e:
            print(f"Error updating stack: {e}")

    def describe_stack(self, stack_name):
        try:
            response = self.cf.describe_stacks(StackName=stack_name)
            return response
        except ClientError as e:
            print(f"Error describing stack: {e}")

    def stack_exists(self, region, stack_name):
        try:
            self.cf.describe_stacks(StackName=stack_name)
            return True
        except ClientError as e:
            if 'does not exist' in str(e):
                return False
            else:
                raise

    def set_stack_parameters(self, stack_name, parameters):
        try:
            response = self.cf.set_stack_parameters(StackName=stack_name, Parameters=parameters)
            print(f"Stack '{stack_name}' parameters updated successfully!")
        except ClientError as e:
            print(f"Error updating stack parameters: {e}")

    def get_stack_outputs(self, stack_name):
        try:
            response = self.cf.get_stack_output(StackName=stack_name)
            return response
        except ClientError as e:
            print(f"Error getting stack outputs: {e}")

    def wait_for_stack_status(self, stack_name, status='CREATE_COMPLETE'):
        waiter = self.cf.get_waiter('stack_create_complete')
        waiter.wait(StackName=stack_name)
