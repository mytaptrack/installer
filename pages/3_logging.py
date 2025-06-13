import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3

from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

s3 = boto3.client('s3')

account_id = st.session_state['account_id']

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

bottom_bar('./pages/2_website.py', './pages/4_encryption.py')
