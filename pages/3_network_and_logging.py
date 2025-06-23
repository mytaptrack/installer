import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3

from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

s3 = boto3.client('s3', config=st.session_state['b3config'])
ec2 = boto3.client('ec2', config=st.session_state['b3config'])

account_id = st.session_state['account_id']

st.write('## System Configuration')

st.write('### Networking')

if st.checkbox("Restrict systems to execute in a VPC?", value= st.session_state['config']['env']['vpc'] != None):
    print(f"VPC: {st.session_state['config']['env']['vpc']}")
    if not st.session_state['config']['env']['vpc']:
        st.session_state['config']['env']['vpc'] = {
            'id': '',
            'subnets': {
                'a': None,
                'b': None
            }
        }

    # Get VPCs
    vpcs = ec2.describe_vpcs()['Vpcs']
    vpc_lookup = [{ 'id': None, 'name': ''}]
    print(f"VPCs: {vpcs}")
    vpc_index = 0
    for vpc in vpcs:

        # If tags are present try to get the name of the vpc
        if 'Tags' in vpc:
            vpc_names = [tag['Value'] for tag in vpc['Tags'] if tag['Key'] == 'Name']
            # Set vpc name
            vpc_name = vpc_names[0] if vpc_names else vpc['VpcId']

        # If vpc is default vpc and name is not set, set it to default
        if vpc['IsDefault']:
            vpc_name = 'Default VPC'
        
        # If name not set, set it to 'No Name'
        if not vpc_name:
            vpc_name = 'No Name'

        # Add vpc to lookup
        vpc_lookup.append({
            'id': vpc['VpcId'],
            'name': vpc_name + ' - ' + vpc['VpcId']
        })

        if st.session_state['config']['env']['vpc']['id'] == vpc['VpcId']:
            vpc_index = len(vpc_lookup) - 1
            print(f'VPC found at {vpc_index}')

    print(f"VPC Index: {vpc_index}")
    # Get list of names
    vpc_names = [vpc['name'] for vpc in vpc_lookup]

    # Select VPC
    vpc_name = st.selectbox("Select the VPC", vpc_names, index=vpc_index)

    if vpc_name:
        # Get VPC id from name
        st.session_state['config']['env']['vpc']['id'] = [vpc['id'] for vpc in vpc_lookup if vpc['name'] == vpc_name][0]

        # Get subnets
        subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [st.session_state['config']['env']['vpc']['id']]}])['Subnets']
        print(f'Subnets: {subnets}')
        subnet_lookup = []
        for subnet in subnets:
            subnet_name = ''

            # If tags are present try to get the name of the subnet
            if 'Tags' in subnet:
                subnet_names = [tag['Value'] for tag in subnet['Tags'] if tag['Key'] == 'Name']
                # Set subnet name
                subnet_name = subnet_names[0] if subnet_names else subnet['SubnetId']

            # If name not set, set it to 'No Name'
            if not subnet_name:
                subnet_name = 'No Name'

            # Add subnet to lookup
            subnet_lookup.append({
                'id': subnet['SubnetId'],
                'name': subnet_name + ' - ' + subnet['SubnetId']
            })
        
        # Get list of names
        subnet_names = [subnet['name'] for subnet in subnet_lookup]

        # If subnet a is set, get the index of the subnet
        subnet_a_index = 0
        if st.session_state['config']['env']['vpc']['subnets']['a']:
            subnet_a_index = subnet_names.index([subnet['name'] for subnet in subnet_lookup if subnet['id'] == st.session_state['config']['env']['vpc']['subnets']['a']][0])

        # Have user select first subnet
        subnet_name_a = st.selectbox("Select the first subnet", subnet_names, index=subnet_a_index)
        if subnet_name_a:
            # Get subnet id from name
            st.session_state['config']['env']['vpc']['subnets']['a'] = [subnet['id'] for subnet in subnet_lookup if subnet['name'] == subnet_name_a][0]

        # If subnet b is set, get the index of the subnet
        subnet_b_index = 1
        if st.session_state['config']['env']['vpc']['subnets']['b']:
            subnet_b_index = subnet_names.index([subnet['name'] for subnet in subnet_lookup if subnet['id'] == st.session_state['config']['env']['vpc']['subnets']['b']][0])
        
        # Have user select second subnet
        subnet_name_b = st.selectbox("Select the second subnet", subnet_names, index=subnet_b_index)
        if subnet_name_b:
            # Get subnet id from name
            st.session_state['config']['env']['vpc']['subnets']['b'] = [subnet['id'] for subnet in subnet_lookup if subnet['name'] == subnet_name_b][0]

        # Check if subnet a and b are the same
        if st.session_state['config']['env']['vpc']['subnets']['a'] == st.session_state['config']['env']['vpc']['subnets']['b']:
            st.error('Subnets must be different. Until this is changed the VPC will not be used.')
else:
    st.session_state['config']['env']['vpc'] = None

st.write('### Logging')
if st.checkbox("Use non-default logging bucket"):
    st.session_state['config']['env']['regional']['logging']['bucket'] = st.text_input("Enter the logging bucket name", value=st.session_state['config']['env']['regional']['logging']['bucket'])
else:
    bucketName = f'mtt-{account_id}-{st.session_state['config']['env']['region']['primary']}-logs'
    
    # Check to see if there is a default logging bucket
    buckets = s3.list_buckets()
    for bucket in buckets['Buckets']:
        if bucket['Name'] == bucketName:
            st.session_state['config']['env']['regional']['logging']['bucket'] = bucket['Name']
            break
    
    if not st.session_state['config']['env']['regional']['logging']['bucket']:
        st.error('Default logging bucket not found')

        if st.button('Create Logging Bucket'):
            # Create logging bucket
            s3.create_bucket(
                Bucket=bucketName,
                CreateBucketConfiguration={
                    'LocationConstraint': st.session_state['config']['env']['region']['primary']
                }
            )
            st.session_state['config']['env']['regional']['logging']['bucket'] = bucketName
            st.success('Logging bucket created')
    else:
        st.success('Account logging bucket found')


st.write('Chatbots are useful when supporting mytaptrack as errors and specific alerts can be sent to the chatbot')
if st.checkbox("Use chatbot messaging", value= st.session_state['config']['env']['chatbot'] is not None ):
    if st.session_state['config']['env']['chatbot'] is None:
        st.session_state['config']['env']['chatbot'] = {
            'arn': ''
        }
    
    st.session_state['config']['env']['chatbot']['arn'] = st.text_input('Enter the chatbot arn', value= st.session_state['config']['env']['chatbot']['arn'])
else:
    st.session_state['config']['env']['chatbot'] = None

if not st.session_state['config']['env']['regional']['logging']['bucket']:
    st.stop()

bottom_bar('network and logging')
