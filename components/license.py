import streamlit as st
from components.utils import generate_api_key
import boto3
import datetime

cloudformation = boto3.client('cloudformation')
ssm = boto3.client('ssm')
user_pool_client = boto3.client('cognito-idp')

def register_license(stage: str, name: str, licenseNumber: str, emails: str):
    # Get user pool id from parameter store
    user_pool_id = ssm.get_parameter(Name=f'/{stage}/regional/calc/cognito/userpoolid')['Parameter']['Value']
    print(f'User pool id: {user_pool_id}')

    # Get license admin group id from cognito and if not present create it
    group_name = f'licenses/{licenseNumber}'
    try:
        group_response = user_pool_client.get_group(
            GroupName=group_name,
            UserPoolId=user_pool_id
        )
        print(f'Group response: {group_response}')
    except Exception as e:
        print(f'Error: {e}')

        # Check for resource not found exception
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print('Group not found, creating group')
            group_response = user_pool_client.create_group(
                GroupName=group_name,
                UserPoolId=user_pool_id
            )
            print(f'Group response: {group_response}')
        else:
            st.error(f'Error: {e}')

    # Get todays date as YYYY-MM-DD
    today = datetime.date.today().strftime('%Y-%m-%d')

    # Split emails by comma and add to group
    admins: list[str] = []
    for email in emails.split(','):
        email = email.strip()
        admins.append(email)

    # Add license to dynamodb
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(f'mytaptrack-{stage}-data')
    table.put_item( Item= {
        'pk': 'L',
        'sk': f'P#{licenseNumber}',
        'pksk': f'L#P#{licenseNumber}',
        'license': licenseNumber,
        'version': 1,
        'details': {
            'customer': name,
            'singleCount': 1000000,
            'start': today,
            'emailDomain': '',
            'singleUsed': 0,
            'multiCount': 0,
            'admins': admins,
            'license': licenseNumber,
            'expiration': '3000-01-01',
            'tags': {
                'devices': []
            },
            'features': {
                'snapshot': True,
                'snapshotConfig': {
                    'low': '@frown',
                    'medium': '@meh',
                    'high': '@smile',
                    'measurements': [
                        {'name': '@smile', 'order': 0}, 
                        {'name': '@meh', 'order': 1}, 
                        {'name': '@frown', 'order': 2}
                    ]
                },
                'dashboard': True,
                'browserTracking': True,
                'download': True,
                'duration': True,
                'manage': True,
                'supportChanges': True,
                'schedule': True,
                'devices': True,
                'behaviorTargets': True,
                'response': False,
                'emailTextNotifications': True,
                'manageStudentTemplates': False,
                'manageResponses': False,
                'abc': True,
                'notifications': False,
                'appGroups': False,
                'documents': True,
                'intervalWBaseline': False,
                'displayTags': [],
                'serviceTracking': False,
                'behaviorTracking': True,
                'serviceProgress': False
            }
        }
    })


def register_license_ui(stage: str):
    # Check to see if the core stack exists
    core_stack_name = f'mytaptrack-{stage}'
    try:
        core_stack = cloudformation.describe_stacks(StackName=core_stack_name)
        if core_stack['Stacks'][0]['StackStatus'] in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
            print(f'Core stack: {core_stack}')
            st.success('Deployment stack found')
        else:
            print(f'Core stack: {core_stack}')
            st.error('Deployment stack not found')
            return
    except Exception as e:
        print(f'Error: {e}')
        st.error('Deployment stack not found')
        return

    if 'license' not in st.session_state:
        st.session_state['license'] = generate_api_key(20)

    st.write('### License Registration')
    name = st.text_input('Enter the name for the license')
    st.session_state['license'] = st.text_input('Enter your license key', value=st.session_state['license'])
    admins = st.text_input('Enter your email address (comma delimited)')
    if st.button('Register License'):
        # Call the register_license function
        register_license(stage, name, st.session_state['license'], admins)
        st.success('License registered')
