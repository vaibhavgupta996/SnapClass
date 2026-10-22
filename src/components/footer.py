import streamlit as st

def footer_home():
    st.markdown(
        """
        <div style="width: 100%; margin-top: 3rem; display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 0.85rem; color: #CBD5E1; text-align: center;">
            <span>Crafted with</span>
            <span style="color: #F43F5E;">❤️</span>
            <span>by <b style="color: #FFFFFF;">VB Gupta</b></span>
        </div>
        """, 
        unsafe_allow_html=True
    )

def footer_dashboard():
    st.markdown(
        """
        <div style="width: 100%; margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid rgba(255, 255, 255, 0.1); display: flex; justify-content: center; align-items: center; gap: 6px; font-size: 0.85rem; color: #94A3B8; text-align: center;">
            <span>Crafted with</span>
            <span style="color: #F43F5E;">❤️</span>
            <span>by <b style="color: #FFFFFF;">VB Gupta</b></span>
        </div>
        """, 
        unsafe_allow_html=True
    )