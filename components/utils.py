import secrets
import string
import streamlit as st
from components.config_storage import save

def generate_api_key(length=32):
    """Generates a random API key using secrets module."""
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key

def apply_styles():
    # Create Style sheet
    with open('./styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    with st.sidebar:
        st.logo('./sm-text-logo.gif', size='large')

def bottom_bar(prev: str, next: str):
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        if prev != '' and st.button('< Previous', type='primary'):
            save()
            st.switch_page(prev)

    with col2:
        if st.button('Save'):
            save()
            st.rerun()

    with col3:
        if next != '' and st.button('Next >', type='primary'):
            save()
            st.switch_page(next)