import streamlit as st

def link(display_name: str, url: str):
    st.markdown(f"""
        <a href="{url}" target="notarget" style="margin-bottom: 10px"> 
            {display_name}
        </a>
    """, unsafe_allow_html=True)
    st.write("")
