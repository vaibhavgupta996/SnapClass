import streamlit as st

def header_home():
    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f"""
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; margin-bottom: 2rem; margin-top: 1rem;">
            <div style="background: rgba(255, 255, 255, 0.08); padding: 14px; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.15); box-shadow: 0 10px 25px rgba(0,0,0,0.3);">
                <img src="{logo_url}" style="width: 80px; height: 80px; object-fit: contain; display: block;" alt="SnapClass Logo" />
            </div>
            <h1 style="font-size: 2.8rem; font-weight: 800; color: #FFFFFF; letter-spacing: -1px; margin-top: 14px; margin-bottom: 2px; text-align: center; text-shadow: 0 2px 10px rgba(0,0,0,0.3);">
                SNAPCLASS
            </h1>
            <p style="color: #A5B4FC; font-size: 1rem; font-weight: 500; margin: 0; text-align: center;">
                Smart AI Face & Voice Attendance System
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

def header_dashboard():
    logo_url = "https://i.ibb.co/YTYGn5qV/logo.png"
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; gap: 12px; padding: 6px 0;">
            <img src="{logo_url}" style="width: 50px; height: 50px; object-fit: contain; border-radius: 12px; background: rgba(255, 255, 255, 0.08); padding: 4px; border: 1px solid rgba(255, 255, 255, 0.15);" alt="SnapClass Logo" />
            <h2 style="font-size: 1.8rem; font-weight: 800; color: #FFFFFF; margin: 0; line-height: 1;">SNAPCLASS</h2>
        </div>
        """,
        unsafe_allow_html=True
    )