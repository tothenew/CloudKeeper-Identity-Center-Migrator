import csv
from client import get_client


def upload_file_s3(file, bucket_name, bucket_key):
    s3_client = get_client('s3')
    with open(file, 'rb') as data:
        s3_client.upload_fileobj(data, bucket_name, bucket_key)


def get_account_list(client):
    accounts = client.list_accounts()
    account_ids = []
    for account in accounts['Accounts']:
        account_ids.append(account['Id'])
    return account_ids


def upload_account_ids_to_s3(account_ids, bucket_name):
    filename = 'extracted-data/'+'accounts_ids.csv'
    with open(filename, 'w') as csvfile:
        write = csv.writer(csvfile)
        for element in account_ids:
            write.writerow([element])
    bucket_key = 'accounts_ids.csv'
    # upload_file_s3(filename, bucket_name, bucket_key)


def get_sso_instance_arn(client):
    instance_info = client.list_instances()
    instance_arn = instance_info['Instances'][0]['InstanceArn']
    return instance_arn


def underscore_remover(name):
    name_list = list(name)
    name_length = len(name_list)
    for counter in range(name_length):
        if ord(name_list[counter]) == 95:
            name_list[counter] = '-'
    sep = ''
    name_string = sep.join(name_list)
    return name_string


def camelcase_changer(name):
    name_list = list(name)
    name_length = len(name_list)
    camelcasing_index = []
    changed_name = name
    for counter in range(name_length - 1):
        current_char = ord(name_list[counter])
        next_char = ord(name_list[counter+1])
        if (current_char >= 97 and current_char<= 122) and (next_char >= 65 and next_char<= 90):
            camelcasing_index.append(counter)
    if len(camelcasing_index)>0:
        counter = 1
        for index in camelcasing_index:
            name_list.insert(index+counter,'-')
            counter+=1
        sep = ''
        changed_name = sep.join(name_list)
    changed_name = changed_name.lower()
    return changed_name


def get_sso_account_data(permission_sets_arns, account, client, instance_arn):
    sso_info_list=[]
    for permission_set_arn in permission_sets_arns:
        custom_policy_status = 'No'

        permission_set_description = client.describe_permission_set(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn)
        permission_set_name = camelcase_changer(underscore_remover(permission_set_description['PermissionSet']['Name']))
        managed_policies = client.list_managed_policies_in_permission_set(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn)
        policies =[]
        
        for policy in managed_policies['AttachedManagedPolicies']:
            policies.append(policy['Name'])

        custom_policies = client.get_inline_policy_for_permission_set(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn)
        if len(custom_policies['InlinePolicy'])>0:
            custom_policy_status = permission_set_name + '.json'

        sso_data = {}
        sso_data.update({'Saml_Provider_Name': 'aws-sso-'+ permission_set_name+'-'+ account+'-'+'DONOTDELETE'})
        sso_data.update({'Role_Name': permission_set_name})
        sso_data.update({'Attached_Managed_Policies': policies})
        sso_data.update({'Custom_Policy': custom_policy_status})
        sso_info_list.append(sso_data)

    return sso_info_list



def upload_custom_policy_to_s3(permission_sets_arns, bucket_name , account_id, client, instance_arn):
    for permission_set_arn in permission_sets_arns:
        custom_policy = client.get_inline_policy_for_permission_set(InstanceArn=instance_arn, PermissionSetArn=permission_set_arn)
        foldername = account_id
        if len(custom_policy['InlinePolicy'])>0:
            permission_set_description = client.describe_permission_set(InstanceArn = instance_arn, PermissionSetArn= permission_set_arn)
            permission_set_name = camelcase_changer(underscore_remover(permission_set_description['PermissionSet']['Name']))
            file_name = 'extracted-data/' + permission_set_name + '.json'
            bucket_key = foldername + '/' + permission_set_name + '.json'
            with open(file_name, 'w') as outfile:
                outfile.write(custom_policy['InlinePolicy'])
            # upload_file_s3(file_name, bucket_name, bucket_key)
