import streamlit as st

st.set_page_config(page_title="Mytaptrack Installer", page_icon="./favicon.ico", layout="wide")

from components.utils import bottom_bar
from components.auth import auth_check
auth_check()
from components.utils import apply_styles
apply_styles()

if 'timeout' not in st.session_state['config']['env']['student']['remove']:
    st.session_state['config']['env']['student']['remove']['timeout'] = 90
if 'path' not in st.session_state['config']['env']['regional']['templates']:
    st.session_state['config']['env']['regional']['templates']['path'] = 'templates/'

st.write('### General Configs')
st.session_state['config']['env']['regional']['templates']['path'] = st.text_input("What is the default path to the templates", st.session_state['config']['env']['regional']['templates']['path'])
st.session_state['config']['env']['student']['remove']['timeout'] = st.number_input("How long should the student be removed after?", value=st.session_state['config']['env']['student']['remove']['timeout'])

bottom_bar('general')
