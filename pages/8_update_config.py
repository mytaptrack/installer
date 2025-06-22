
import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

import boto3
import time

from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

codebuild = boto3.client('codebuild')
codepipeline = boto3.client('codepipeline')

st.write('### Update Configuration')

if 'branch' not in st.session_state['config']['env']:
    st.session_state['config']['env']['branch'] = 'main'

st.session_state['config']['env']['branch'] = st.text_input('Enter the back-end branch to deploy', value=st.session_state['config']['env']['branch'])

# Check if the user interface is auto deploy
if st.session_state['config']['env']['deploy']['website']:
    if 'ui_branch' not in st.session_state['config']['env']:
        st.session_state['config']['env']['ui_branch'] = 'main'
    st.session_state['config']['env']['ui_branch'] = st.text_input('Enter the front-end branch to deploy', value=st.session_state['config']['env']['branch'])

if 'deploy' not in st.session_state['config']['env']:
    st.session_state['config']['env']['deploy'] = {
        'website': False,
        'auto': False,
        'day': 'Saturday',
        'time': time.time(0, 0, 0)
    }

st.session_state['config']['env']['deploy']['auto'] = st.checkbox('Automatically update mytaptrack every week', st.session_state['config']['env']['deploy']['auto'])

if st.session_state['config']['env']['deploy']['auto']:
    # Setup radio buttons for Saturday or Sunday updates
    if 'day' not in st.session_state['config']['env']['deploy']:
        st.session_state['config']['env']['deploy']['day'] = 'Saturday'
    if 'time' not in st.session_state['config']['env']['deploy']:
        st.session_state['config']['env']['deploy']['time'] = '00:00:00'
    if 'timezone' not in st.session_state['config']['env']['deploy']:
        st.session_state['config']['env']['deploy']['timezone'] = 0

    on_day = st.session_state['config']['env']['deploy']['day']
    st.session_state['config']['env']['deploy']['day'] = st.radio('Deploy on', ['Saturday', 'Sunday'], index=0 if on_day == 'Saturday' else 1)
    st.session_state['config']['env']['deploy']['timezone'] = st.number_input('Timezone offset', value=st.session_state['config']['env']['deploy']['timezone'])
    
    stored_time =  time.localtime(0)
    if "time" in st.session_state['config']['env']['deploy']:
        # Split time into parts by :
        stored_time = st.session_state['config']['env']['deploy']['time']
        
    # convert stored_time to time data type
    deploy_time = st.time_input('Deploy at', value=stored_time)

    if deploy_time:
        # Convert from local time to gmt
        print(f'Local time: {deploy_time.hour}:{deploy_time.minute}')
        st.session_state['config']['env']['deploy']['time'] = deploy_time

bottom_bar('update config')
