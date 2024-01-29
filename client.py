import boto3


def get_client(service_name):
    return boto3.client(service_name)


def get_cross_acc_session(role_arn, role_name):
    sts_client = boto3.client('sts')
    sts_connection = sts_client.assume_role(RoleArn=role_arn, RoleSessionName=role_name)
    return sts_connection['Credentials']


def get_cross_acc_client(service_name, credentials):
    return boto3.client(service_name, aws_access_key_id=credentials['AccessKeyId'], aws_secret_access_key=credentials['SecretAccessKey'], aws_session_token=credentials['SessionToken'])
