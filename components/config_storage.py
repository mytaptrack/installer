import boto3
import yaml
import streamlit as st

s3 = boto3.client('s3')

def get_account_bucket(account_id: str):
    env_bucket_name = f'mytaptrack-{account_id}-environments'
    return env_bucket_name

def is_account_bootstrapped(account_id: str):
    env_bucket_name = get_account_bucket(account_id=account_id)
    env_bucket = False
    buckets = s3.list_buckets()
    print(f"Buckets: {buckets}")
    for bucket in buckets['Buckets']:
        if env_bucket_name == bucket['Name']:
            env_bucket = True
            break
    
    return env_bucket   

def bootstrap_region(account_id: str, region: str):
    bucket_name = get_account_bucket(account_id=account_id)

    # Check if bucket exists
    if not is_account_bootstrapped(account_id=account_id):
        s3.create_bucket(ACL='private', Bucket=bucket_name, CreateBucketConfiguration={ 'LocationConstraint': region })
    s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration={ 'Status': 'Enabled' })

def load_config(account_id: str, region: str, environment: str):
    env_bucket_name = get_account_bucket(account_id=account_id)

    # Check to see if S3 configuration file exists {name}.yml
    config_file_name = f'{region}/{environment}.yml'

    try:
        config_object = s3.get_object(Bucket=env_bucket_name, Key=config_file_name)

        # load configuration content from yml format to st.session_state['config']
        result = yaml.safe_load(config_object['Body'].read().decode('utf-8'))

        return result
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return None

def save_config(account_id: str, region: str, environment: str, config: dict):
    env_bucket_name = get_account_bucket(account_id=account_id)

    # Check to see if S3 configuration file exists {name}.yml
    config_file_name = f'{region}/{environment}.yml'

    s3.put_object(Bucket=env_bucket_name, Key=config_file_name, Body=yaml.dump(config))

def save():
    # Save configuration to S3
    save_config(account_id=st.session_state['account_id'], region=st.session_state['config']['env']['region']['primary'], environment=st.session_state['config']['env']['name'], config=st.session_state['config'])

    # Write to ./config.yml
    print(f"Saving configuration to ./config.yml: {st.session_state['config']}")
    with open('./cicd/config.yml', 'w') as f:
        yaml.dump(st.session_state['config'], f)
