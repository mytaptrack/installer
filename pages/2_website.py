import streamlit as st
import boto3
from components.auth import auth_check
auth_check()

from components.utils import bottom_bar, apply_styles
apply_styles()

if 'website' not in st.session_state['config']['env']:
    st.session_state['config']['env']['website'] = {
        'google': None,
        'username': True,
        'sign_up': True
    }

print(f'Domain name {st.session_state['config']['env']['domain']['name']}')
if st.session_state['config']['env']['domain']['name'] != '':
    print('Domain name is set')
    if st.checkbox('Publicly host website with this domain?', value=st.session_state['config']['env']['deploy']['website']):
        st.session_state['config']['env']['deploy']['website'] = True
        st.session_state['config']['env']['domain']['sub']['website']['public'] = True

        if 'behavior' not in st.session_state['config']['env']['domain']['sub']['website']:
            st.session_state['config']['env']['domain']['sub']['website']['behavior'] = {
                'name': '',
                'subdomain': '',
                'cert': '',
            }
        behavior_config = st.session_state['config']['env']['domain']['sub']['website']['behavior']
        behavior_config['subdomain'] = st.text_input('Enter the behavior tracking subdomain', value=behavior_config['subdomain'])
        behavior_config['name'] = f"{behavior_config['subdomain']}.{st.session_state['config']['env']['domain']['name']}"
        behavior_config['cert'] = st.session_state['config']['env']['domain']['sub']['api']['cert']
        st.session_state['config']['env']['domain']['sub']['website']['name'] = behavior_config['name']
        st.write(f"Behavior domain: {behavior_config['name']}")

        if 'manage' not in st.session_state['config']['env']['domain']['sub']['website']:
            st.session_state['config']['env']['domain']['sub']['website']['manage'] = {
                'name': '',
                'subdomain': '',
                'cert': '',
            }
        
        manage_config = st.session_state['config']['env']['domain']['sub']['website']['manage']
        manage_config['subdomain'] = st.text_input('Enter the management subdomain', value=manage_config['subdomain'])
        manage_config['name'] = f"{manage_config['subdomain']}.{st.session_state['config']['env']['domain']['name']}"
        manage_config['cert'] = st.session_state['config']['env']['domain']['sub']['api']['cert']
        st.write(f"Management domain: {manage_config['name']}")

    else:
        print('Not public web')
        st.session_state['config']['env']['deploy']['website'] = False
        st.session_state['config']['env']['domain']['sub']['website']['public'] = False

        st.session_state['config']['env']['domain']['sub']['website']['name'] = st.text_input('Enter the website domain name', value=st.session_state['config']['env']['domain']['sub']['website']['name'])
        st.session_state['config']['env']['domain']['sub']['website']['subdomain'] = ''
        st.session_state['config']['env']['domain']['sub']['website']['cert'] = ''
        st.session_state['config']['env']['domain']['sub']['website']['manage'] = None
        st.session_state['config']['env']['domain']['sub']['website']['behavior'] = None
else:
    if st.session_state['config']['env']['deploy']['website'] == None:
        print('Setting default web deploy value')
        st.session_state['config']['env']['deploy']['website'] = False

    st.session_state['config']['env']['deploy']['website'] = st.checkbox('Publicly host website?', value= st.session_state['config']['env']['deploy']['website'] == True)
    if not st.session_state['config']['env']['deploy']['website']:
        st.session_state['config']['env']['deploy']['website'] = True
        st.session_state['config']['env']['domain']['sub']['website']['name'] = st.text_input('Enter the website domain name', value=st.session_state['config']['env']['domain']['sub']['website']['name'])
    # else:
    #     st.session_state['config']['env']['deploy']['website'] = False
  
st.session_state['config']['env']['website']['username'] = st.checkbox('Use username authentication', value=st.session_state['config']['env']['website']['username'])

google_conf = st.session_state['config']['env']['website']['google']

if st.checkbox('Use gmail authentication', value=google_conf != None):
    if google_conf == None:
        google_conf = {
            'client_id': '',
            'client_secret_name': '',
            'scopes': 'profile email openid'
        }
        st.session_state['config']['env']['website']['google'] = google_conf

    client_id = st.text_input("Enter your google client id", value=google_conf['client_id'])
    client_secret = st.text_input("Enter your google client secret", type='password', value=google_conf['client_secret'])
    if client_secret != google_conf['client_secret']:
        # Create secrets manager client
        client = boto3.client('secretsmanager')

        # Save secrets manager at /<env>/website/google/secret
        client.create_secret(
            Name=f"/{st.session_state['config']['env']['name']}/website/google/secret",
            SecretString=client_secret
        )
        st.session_state['config']['env']['website']['google']['client_secret_name'] = f"/{st.session_state['config']['env']['name']}/website/google/secret"


    scopes = st.text_input("Enter your google redirect uri", value=google_conf['redirect_uri'])
    st.session_state['config']['env']['deploy']['website']['google'] = {
        'client_id': st.text_input("Enter your google client id", value=google_conf['client_id']),
        'client_secret': st.text_input("Enter your google client secret", type='password', value=google_conf['client_secret']),
        'redirect_uri': st.text_input("Enter your google redirect uri", value=google_conf['redirect_uri'])
    }
else: 
    # Remove google from config
    st.session_state['config']['env']['website']['google'] = None

bottom_bar('website')
