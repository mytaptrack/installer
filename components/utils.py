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

page_order = [
    { "name": "start", "file": "mytaptrack_installer.py" },
    { "name": "domains", "file": "pages/1_domains.py" },
    { "name": "website", "file": "pages/2_website.py" },
    { "name": "network and logging", "file": "pages/3_network_and_logging.py" },
    { "name": "encryption", "file": "pages/4_encryption.py" },
    { "name": "notifications", "file": "pages/5_notifications.py" },
    { "name": "general", "file": "pages/6_general.py" },
    { "name": "system validation", "file": "pages/7_system_validation.py" },
    { "name": "update config", "file": "pages/8_update_config.py" },
    { "name": "deploy", "file": "pages/9_deploy.py" }
]

def bottom_bar(name: str):
    st.divider()

    # Get the index of the current page
    current_index = next((i for i, page in enumerate(page_order) if page["name"] == name), -1)

    col1, col2, col3 = st.columns(3)

    with col1:
        if current_index > 0 and st.button('< Previous', type='primary'):
            save()
            st.switch_page(page_order[current_index - 1]["file"])

    with col2:
        if st.button('Save'):
            save()
            st.rerun()

    with col3:
        if current_index < len(page_order) - 1 and st.button('Next >', type='primary'):
            save()
            st.switch_page(page_order[current_index + 1]["file"])