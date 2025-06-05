import streamlit as st
import boto3
import os

from components.config_storage import bootstrap_region, is_account_bootstrapped, load_config, save_config
from components.encryption import encryption_settings
from components.deployment import deployment_ui, deploy_codebuild
from components.license import register_license_ui
from components.notifications import notifications_ui
from components.system_testing import system_testing_ui
from components.html_resources import link

import os

if 'authenticated' not in st.session_state:
    password = st.text_input('Password', type='password')
    if password == os.environ['PASSWORD']:
        st.session_state['authenticated'] = True
        st.session_state['password'] = ''
    else:
        if password != '':
            st.error('Invalid password')
        st.stop()

# Get the account id that we're connected to
account_id = boto3.client("sts").get_caller_identity()["Account"]

st.title('Mytaptrack Installer')

if not st.session_state.get('config'):
    st.session_state['config'] = {
        'env': {
            'name': '',
            'vpc': False,
            'app': {
                'pushSnsArns': {
                    'android': '',
                    'ios': ''
                },
                'secrets': {
                    'tokenKey': {
                        'name': '/regional/token/key',
                        'arn': ''
                    }
                },
            },
            'chatbot': {
                'arn': ''
            },
            'debug': 'false',
            'domain': {
                'hostedzone': {
                    'id': '',
                },
                'name': '',
                'sub': {
                    'device': {
                        'appid': 'mytaptrack',
                        'cert': '',
                        'name': '',
                        'subdomain': '',
                        'apikey': '',
                        'path': '/prod'
                    },
                    'api': {
                        'cert': '',
                        'name': '',
                        'subdomain': '',
                        'path': '/prod'
                    },
                    'website': {
                        'name': '',
                        'subdomain': '',
                        'deploy': ''
                    }
                }
            },
            'region': {
                'primary': '',
                'regions': ''
            },
            'sms': {
                'origin': ""
            },
            'stacks': {
                'core': ''
            },
            'student': {
                'remove': {
                    'timeout': 90
                }
            },
            'system': {
                'email': ''
            },
            'regional': {
                'logging': {
                    'bucket': ''
                },
                'replication': "true",
                'templates': {
                    'path': 'templates/'
                }
            },
            'deploy': {
                'website': False,
                'auto': False
            }
        }
    }

if not st.session_state.get('name'):
    st.session_state['name'] = ''
if not st.session_state.get('step'):
    st.session_state['step'] = 'Environment'

st.write('### Environment')

# Create array with all AWS Regions
regions = ['', 'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2', 'ap-south-1', 'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3', 'ap-southeast-1', 'ap-southeast-2', 'ca-central-1', 'eu-central-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-north-1', 'sa-east-1']

# find the index of the AWS_REGION environment variable
if 'AWS_REGION' in os.environ:
    index = regions.index(os.environ['AWS_REGION'])

primary = st.selectbox('Primary AWS Region', regions)
st.session_state['config']['env']['region']['primary'] = primary

if st.checkbox('Include a second disaster recovery region?'):
    secondary = st.selectbox('Secondary AWS Region', regions)
    st.session_state['config']['env']['region']['regions'] = f'{primary}, {secondary}'
else:
    st.session_state['config']['env']['region']['regions'] = primary

if not primary:
    st.stop()

os.environ['AWS_REGION'] = primary

# Create route53 client
route53 = boto3.client('route53')
s3 = boto3.client('s3')
acm = boto3.client('acm')
ses = boto3.client('ses')
sns = boto3.client('sns')
ssm = boto3.client('ssm')
kms = boto3.client('kms')
codebuild = boto3.client('codebuild')

# Check environment bucket to see if it exists
if not is_account_bootstrapped(account_id):
    created = False
    if st.button('Bootstrap region'):
        bootstrap_region(account_id, primary)
        st.success('Environment bucket created')
        created = True
    
    if not created:
        st.stop()

name = st.text_input('Environment Name (dev, test, prod)')

if not name:
    st.stop()

st.session_state['config']['env']['name'] = name

if st.button('Save Updates'):
    save_config(account_id=account_id, region=primary, environment=name, config=st.session_state['config'])
    st.success('Configuration saved')

# Check to see if S3 configuration file exists {name}.yml
saved_config = load_config(account_id=account_id, region=primary, environment=name)
if saved_config:
    # load configuration content from yml format to st.session_state['config']
    st.session_state['config'] = saved_config
    st.success('Configuration loaded')

st.divider()
st.write('### DNS')
if st.checkbox('Use Route53'):
    domain = st.text_input('Enter the route 53 domain name', value=st.session_state['config']['env']['domain']['name'])
    if domain:
        # Remove spaces before and after domain
        domain = domain.strip()

        st.session_state['config']['env']['domain']['name'] = domain
        hosted_zones = route53.list_hosted_zones()['HostedZones']
        print(f"Hosted Zones: {hosted_zones}")
        route53_name = domain + '.'
        print(f"Domain: {route53_name}")
        for zone in hosted_zones:
            print(f'Zone: "{zone['Name']}" check agains "{route53_name}"')
            if route53_name == zone['Name']:
                print(f"Found hosted zone: {zone['Name']}")
                st.session_state['config']['env']['domain']['hostedzone']['id'] = zone['Id'].split('/')[2]
                break
        
        if not st.session_state['config']['env']['domain']['hostedzone']['id']:
            st.error('Domain hosted zone not found in route 53')
        else:
            st.success('Domain found in route 53')

        # Check certificate manager for a wildcard certificate
        certificates = acm.list_certificates()['CertificateSummaryList']
        print(certificates)
        for cert in certificates:
            if domain in cert['DomainName']:
                st.success('Certificate found')
                st.session_state['config']['env']['domain']['sub']['api']['cert'] = cert['CertificateArn']
                st.session_state['config']['env']['domain']['sub']['device']['cert'] = cert['CertificateArn']
                break
        
        if not st.session_state['config']['env']['domain']['sub']['api']['cert']:
            st.error('Certificate not found in certificate manager')
            
            if st.button('Create Certificate'):
                # Create certificate
                response = acm.request_certificate(
                    DomainName=domain,
                    ValidationMethod='DNS',
                    SubjectAlternativeNames=[domain, '*.' + domain]
                )
                st.session_state['config']['env']['domain']['sub']['api']['cert'] = response['CertificateArn']
                st.session_state['config']['env']['domain']['sub']['device']['cert'] = response['CertificateArn']

                # Check if certificate has been validated
                response = acm.describe_certificate(CertificateArn=response['CertificateArn'])
                if response['Certificate']['Status'] != 'ISSUED':
                    # Add route53 records
                    for record in acm.describe_certificate(CertificateArn=response['CertificateArn'])['Certificate']['DomainValidationOptions']:
                        route53.change_resource_record_sets(
                            HostedZoneId=st.session_state['config']['env']['domain']['hostedzone']['id'],
                            ChangeBatch={
                                'Changes': [
                                    {
                                        'Action': 'UPSERT',
                                        'ResourceRecordSet': {
                                            'Name': record['ResourceRecord']['Name'],
                                            'Type': record['ResourceRecord']['Type'],
                                            'TTL': 300,
                                            'ResourceRecords': [
                                                {
                                                    'Value': record['ResourceRecord']['Value']
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        )

                st.success('Certificate created')
        
        st.divider()

        if st.checkbox('Host website with this domain?'):
            if not st.session_state['config']['env']['domain']['sub']['website']['subdomain']:
                st.session_state['config']['env']['domain']['sub']['website']['subdomain'] = 'web'
            st.session_state['config']['env']['domain']['sub']['website']['subdomain'] = st.text_input('Enter the website subdomain', value=st.session_state['config']['env']['domain']['sub']['website']['subdomain'])
            st.session_state['config']['env']['domain']['sub']['website']['name'] = f"{st.session_state['config']['env']['domain']['sub']['website']['subdomain']}.{st.session_state['config']['env']['domain']['name']}"
            st.write(f"Website domain: {st.session_state['config']['env']['domain']['sub']['website']['name']}")
            st.session_state['config']['env']['domain']['sub']['website']['cert'] = st.session_state['config']['env']['domain']['sub']['api']['cert']
            st.session_state['config']['env']['domain']['sub']['website']['deploy'] = st.checkbox('Deploy website in the cloud?', value=True)
        else:
            st.session_state['config']['env']['domain']['sub']['website']['name'] = st.text_input('Enter the website domain name', value=st.session_state['config']['env']['domain']['sub']['website']['name'])
            st.session_state['config']['env']['domain']['sub']['website']['subdomain'] = ''
            st.session_state['config']['env']['domain']['sub']['website']['cert'] = ''
            st.session_state['config']['env']['domain']['sub']['website']['deploy'] = False

        st.divider()
        if not st.session_state['config']['env']['domain']['sub']['api']['subdomain']:
            st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = 'api'
        st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = st.text_input('Enter the api subdomain', value=st.session_state['config']['env']['domain']['sub']['api']['subdomain'])
        st.session_state['config']['env']['domain']['sub']['api']['name'] = f"{st.session_state['config']['env']['domain']['sub']['api']['subdomain']}.{st.session_state['config']['env']['domain']['name']}"
        st.session_state['config']['env']['domain']['sub']['api']['path'] = st.text_input('Enter the api path', value=st.session_state['config']['env']['domain']['sub']['api']['path'])

        st.divider()
        if not st.session_state['config']['env']['domain']['sub']['device']['subdomain']:
            st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = 'device'
        st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = st.text_input('Enter the device subdomain', value=st.session_state['config']['env']['domain']['sub']['device']['subdomain'])
        st.session_state['config']['env']['domain']['sub']['device']['path'] = st.text_input('Enter the device api path', value=st.session_state['config']['env']['domain']['sub']['device']['path'])
else:
    st.session_state['config']['env']['domain']['name'] = ''
    st.session_state['config']['env']['domain']['hostedzone']['id'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['subdomain'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['name'] = ''
    st.session_state['config']['env']['domain']['sub']['device']['cert'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['name'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['subdomain'] = ''
    st.session_state['config']['env']['domain']['sub']['api']['cert'] = ''

    st.session_state['config']['env']['domain']['sub']['website']['name'] = st.text_input('Enter the website domain name', value=st.session_state['config']['env']['domain']['sub']['website']['name'])

if not st.session_state['config']['env']['domain']['sub']['device']['apikey']:
    st.session_state['config']['env']['domain']['sub']['device']['apikey'] = generate_api_key()

st.session_state['config']['env']['domain']['sub']['device']['apikey'] = st.text_input('Enter the api key to use for the mytaptrack app', value=st.session_state['config']['env']['domain']['sub']['device']['apikey'])

if not st.session_state['config']['env']['domain']['sub']['website']['name']:
    st.stop()

st.divider()

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
    
if not st.session_state['config']['env']['regional']['logging']['bucket']:
    st.stop()
    
st.divider()

st.write('### Encryption')
if st.checkbox('Provide custom parameter store path for token encryption'):
    st.session_state['config']['env']['app']['secrets']['tokenKey']['name'] = st.text_input("Enter your app parameter store encryption key name (/regional/token/key): ", value=st.session_state['config']['env']['app']['secrets']['tokenKey']['name']);
else:
    st.session_state['config']['env']['app']['secrets']['tokenKey']['name'] = '/regional/token/key'

# Check if the key exists
try:
    secret_param = ssm.get_parameter(
        Name=st.session_state['config']['env']['app']['secrets']['tokenKey']['name'],
        WithDecryption=True
    )
    st.session_state['config']['env']['app']['secrets']['tokenKey']['arn'] = secret_param['Parameter']['ARN']
    st.success('Encryption key found')
except Exception as e:
    st.error('Encryption key not found')
    if st.button('Create Encryption Key'):
        # Create the key
        ssm.put_parameter(
            Name=st.session_state['config']['env']['app']['secrets']['tokenKey']['name'],
            Value=generate_api_key(128),
            Type='SecureString',
            Overwrite=True
        )
        st.success('Encryption key created')
    print(e)

if st.checkbox('Customize encryption'):
    # Get list of kms keys and aliases
    encryption_settings()

st.divider()

st.write('### Notifications')
notifications_ui(region=primary)

st.divider()

st.write('### General Configs')
st.session_state['config']['env']['regional']['templates']['path'] = st.text_input("What is the default path to the templates", 'templates/')
st.session_state['config']['env']['student']['remove']['timeout'] = st.number_input("How long should the student be removed after?", value=90)

st.divider()
st.write('### System Tests')

system_testing_ui()

st.divider()

st.write('### Deployments')
deployment_ui()

st.divider()

st.write('### Actions')
if st.button('Save Updates', key='save_updates_2'):
    save_config(account_id=account_id, region=primary, environment=name, config=st.session_state['config'])
    st.success('Configuration saved')

deploy_codebuild(name)

st.divider()
if st.button('Click to register new license'):
    register_license_ui(name)
