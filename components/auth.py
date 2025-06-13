import streamlit as st

def auth_check():
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if st.session_state['authenticated'] == False:
        st.error('Please login to continue')
        st.switch_page('./mytaptrack_installer.py')
