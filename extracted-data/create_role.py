import boto3
import csv
import json


sts_client = boto3.client('sts')
iam_client = boto3.client('iam')

account_id = sts_client.get_caller_identity().get('Account')
print("Working on Account ID -", account_id)


print('Creating Customer Managed Policies -')

json_file_names = []
with open(f'{account_id}.csv', 'r') as file:
    csvFile = csv.reader(file)
    for line in csvFile:
        if '.json' in line[-2]:
            json_file_names.append(line[-2])
    for jsonf in json_file_names:
        with open(jsonf, 'r') as js:
            jsonstr = json.load(js)
            jsonstr = json.dumps(jsonstr)
            policyname = jsonf[:-5]
            policyname = f'sso-policy-{policyname}'
            response = iam_client.create_policy(
                PolicyName=policyname, PolicyDocument=jsonstr)
            print('Custom Policy', policyname, 'created.')


print('Creating Identity Providers -')

with open(f'{account_id}.csv', 'r') as file:
    csvFile = csv.reader(file)
    next(csvFile, None)
    for line in csvFile:
        idp_name = line[-1]
        idp_name = idp_name.split('.')
        idp_name = idp_name[0]
        idp_name = f'IdP-{idp_name}'
        with open(line[-1], 'r') as metadata:
            metadata = metadata.read()
            response = iam_client.create_saml_provider(
                Name=idp_name, SAMLMetadataDocument=metadata)
            print("Created IdP", idp_name)


print('Creating Roles -')

with open(f'{account_id}.csv', 'r') as file:
    csvFile = csv.reader(file)
    next(csvFile, None)
    for line in csvFile:
        role_name = line[-1]
        role_name = role_name.split('.')
        role_name = role_name[0]
        assume_role = json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Federated": f"arn:aws:iam::{account_id}:saml-provider/IdP-{role_name}"
                    },
                    "Action": "sts:AssumeRoleWithSAML",
                    "Condition": {
                        "StringEquals": {
                            "SAML:aud": "https://signin.aws.amazon.com/saml"
                        }
                    }
                }
            ]
        })

        role_name = f'Role-{role_name}'
        response = iam_client.create_role(
            RoleName=role_name, AssumeRolePolicyDocument=assume_role)
        print('Role', role_name, 'created.')


print('Attaching policies to roles-')

with open('Attributes.csv', 'a') as writerfile:
    csvWriter = csv.writer(writerfile)
    with open(f'{account_id}.csv', 'r') as file:
        csvFile = csv.reader(file)
        next(csvFile, None)
        for line in csvFile:
            role_name = line[-1]
            role_name = role_name.split('.')
            role_name = role_name[0]
            application_name = role_name
            idp_name = f'IdP-{role_name}'
            role_name = f'Role-{role_name}'
            if '.json' in line[-2]:
                custom_policy_name = (line[-2])[:-5]
                custom_policy_name = f'sso-policy-{custom_policy_name}'
                custom_policy_arn = f'arn:aws:iam::{account_id}:policy/{custom_policy_name}'
                response = iam_client.attach_role_policy(
                    RoleName=role_name, PolicyArn=custom_policy_arn)
                print('Policy', custom_policy_name,
                      'attached to role', role_name)
            if len(line[2]) > 0:
                managed_policies = ((line[2])[1:-1]).split(',')
                for item in managed_policies:
                    item = item.strip()
                    item = item.strip("'")
                    if len(item) > 0:
                        managed_policy_arn = f'arn:aws:iam::aws:policy/{item}'
                        print(managed_policy_arn)
                        response = iam_client.attach_role_policy(
                            RoleName=role_name, PolicyArn=managed_policy_arn)
                        print('Policy', item, 'attached to role', role_name)

            role_arn = f'arn:aws:iam::{account_id}:role/{role_name}'
            idp_arn = f'arn:aws:iam::{account_id}:saml-provider/{idp_name}'
            csvWriter.writerow(
                [account_id, application_name, role_arn, idp_arn])
