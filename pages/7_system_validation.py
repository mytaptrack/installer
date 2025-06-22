import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

from components.utils import generate_api_key
from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

st.write('### System Tests')

env = st.session_state['config']['env']
if st.checkbox('Do you want to configure system tests?', value= 'testing' in env and env['testing'] is not None):
    if st.session_state['config']['env']['testing'] is None:
        st.session_state['config']['env']['testing'] = {
            'admin': {
                'email': '',
                'password': generate_api_key(12),
                'name': 'Testing Admin'
            },
            'nonadmin': {
                'email': '',
                'password': generate_api_key(12),
                'name': 'Testing User'
            }
        }
    st.session_state['config']['env']['testing']['admin']['email'] = st.text_input('Administrator email', value= st.session_state['config']['env']['testing']['admin']['email'])
    st.session_state['config']['env']['testing']['admin']['password'] = st.text_input('Administrator password', type='password', value=st.session_state['config']['env']['testing']['admin']['password'])
    st.session_state['config']['env']['testing']['admin']['name'] = st.text_input('Administrator name', value=st.session_state['config']['env']['testing']['admin']['name'])

    st.divider()

    st.session_state['config']['env']['testing']['nonadmin']['email'] = st.text_input('Non-admin email', value=st.session_state['config']['env']['testing']['nonadmin']['email'])
    st.session_state['config']['env']['testing']['nonadmin']['password'] = st.text_input('Non-admin password', type='password', value=st.session_state['config']['env']['testing']['nonadmin']['password'])
    st.session_state['config']['env']['testing']['nonadmin']['name'] = st.text_input('Non-admin name', value=st.session_state['config']['env']['testing']['nonadmin']['name'])

else:
    st.session_state['config']['env']['testing'] = None


bottom_bar('system validation')
