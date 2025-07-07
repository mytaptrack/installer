import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3
from components.encryption import encryption_settings
from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()
from components.utils import generate_api_key

ssm = boto3.client('ssm', config=st.session_state['b3config'])
kms = boto3.client('kms', config=st.session_state['b3config'])

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
    if st.button('Create Token Encryption Key'):
        # Create the key
        ssm.put_parameter(
            Name=st.session_state['config']['env']['app']['secrets']['tokenKey']['name'],
            Value=generate_api_key(128),
            Type='SecureString',
            Overwrite=True
        )
        st.success('Encryption key created')
    print(e)
    st.stop()

if st.checkbox('Customize encryption'):
    # Get list of kms keys and aliases
    encryption_settings()

bottom_bar('encryption')
