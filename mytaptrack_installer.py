import streamlit as st
import boto3
from botocore.config import Config
import os

from components.config_storage import bootstrap_region, is_account_bootstrapped, load_config, save_config
from components.utils import apply_styles

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

apply_styles()

if 'authenticated' not in st.session_state:
    password = st.text_input('Password', type='password')
    if password == os.environ['PASSWORD']:
        st.session_state['authenticated'] = True
    else:
        if password != '':
            st.error('Invalid password')
        st.stop()

# Get the account id that we're connected to
account_id = boto3.client("sts").get_caller_identity()["Account"]
st.session_state['account_id'] = account_id

st.title('Mytaptrack Installer')

if not st.session_state.get('config'):
    st.session_state['config'] = {
        'env': {
            'name': '',
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
if 'config' in st.session_state and 'region' in st.session_state['config']['env'] and 'primary' in st.session_state['config']['env']['region']:
    index = regions.index(st.session_state['config']['env']['region']['primary'])

if index == 0:
    # Find default AWS region stored in environment variable AWS_DEFAULT_REGION
    if 'AWS_DEFAULT_REGION' in os.environ:
        index = regions.index(os.environ['AWS_DEFAULT_REGION'])

primary = st.selectbox('Primary AWS Region', regions, index=index)
st.session_state['config']['env']['region']['primary'] = primary

if st.checkbox('Include a second disaster recovery region?'):
    secondary = st.selectbox('Secondary AWS Region', regions)
    st.session_state['config']['env']['region']['regions'] = f'{primary}, {secondary}'
else:
    st.session_state['config']['env']['region']['regions'] = primary

if not primary:
    st.stop()

st.session_state['b3config'] = Config(region_name=primary)

# Create route53 client
route53 = boto3.client('route53', config=st.session_state['b3config'])
s3 = boto3.client('s3', config=st.session_state['b3config'])
acm = boto3.client('acm', config=st.session_state['b3config'])
ses = boto3.client('ses', config=st.session_state['b3config'])
sns = boto3.client('sns', config=st.session_state['b3config'])
ssm = boto3.client('ssm', config=st.session_state['b3config'])
kms = boto3.client('kms', config=st.session_state['b3config'])
codebuild = boto3.client('codebuild', config=st.session_state['b3config'])

# Check environment bucket to see if it exists
created = is_account_bootstrapped(account_id)

if st.button('Bootstrap region'):
    bootstrap_region(account_id, primary)
    st.success('Environment bucket created')
    created = True

if not created:
    st.stop()

if 'config' in st.session_state and 'env' in st.session_state['config'] and 'name' in st.session_state['config']['env']:
    name = st.session_state['config']['env']['name']

name = st.text_input('Environment Name (dev, test, prod)', value=name)

if not name:
    st.stop()

st.session_state['config']['env']['name'] = name

# Check to see if S3 configuration file exists {name}.yml
saved_config = load_config(account_id=account_id, region=primary, environment=name)
if saved_config:
    # load configuration content from yml format to st.session_state['config']
    st.session_state['config'] = saved_config
    st.success('Configuration loaded')

st.divider()

col1, col2, col3 = st.columns(3)

with col2:
    if st.button('Save Updates', key='save_updates_2'):
        save_config(account_id=account_id, region=primary, environment=name, config=st.session_state['config'])
        st.success('Configuration saved')

with col3:
    if st.button('Next >', type='primary'):
        save_config(account_id=account_id, region=primary, environment=name, config=st.session_state['config'])
        st.switch_page('./pages/1_domains.py')
