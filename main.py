import json, boto3, csv, os
from utils import *
from client import *
import os

bucket_name = ""

    
s3_client = boto3.client('s3')

org_client = boto3.client('organizations')
account_ids = get_account_list(org_client)


upload_account_ids_to_s3(account_ids, bucket_name)

sso_admin_client = boto3.client('sso-admin')

instance_arn = get_sso_instance_arn(sso_admin_client)


csv_headers = ['Saml_Provider_Name', 'Role_Name', 'Attached_Managed_Policies', 'Custom_Policy','IdPMetadataFileName']

for account_id in account_ids:
    sso_data = []
    permission_sets = sso_admin_client.list_permission_sets_provisioned_to_account(InstanceArn=instance_arn, AccountId=account_id)
    if len(permission_sets) > 1:
            permission_sets_arns = permission_sets['PermissionSets']
            sso_data = get_sso_account_data(permission_sets_arns, account_id, sso_admin_client, instance_arn)
            upload_custom_policy_to_s3(permission_sets_arns, bucket_name, account_id, sso_admin_client, instance_arn)

    filename = 'extracted-data/' + account_id + '.csv'
    with open(filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = csv_headers)
        writer.writeheader()
        writer.writerows(sso_data)
