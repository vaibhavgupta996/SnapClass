import streamlit as st
from src.components.header import header_home
from src.ui.base_layout import style_base_layout, style_background_home
from src.components.footer import footer_home

def home_screen(): 
    style_background_home()
    style_base_layout()
    header_home()
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 28px; padding: 28px 24px; text-align: center; backdrop-filter: blur(16px); box-shadow: 0 15px 35px rgba(0,0,0,0.25);">
                <div style="display: inline-block; background: rgba(99, 102, 241, 0.25); color: #C7D2FE; border: 1px solid rgba(165, 180, 252, 0.3); border-radius: 9999px; padding: 4px 14px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                    Student Portal
                </div>
                <h2 style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; margin: 0 0 6px 0;">I'm a Student</h2>
                <p style="color: #CBD5E1; font-size: 0.85rem; margin: 0 0 16px 0; min-height: 38px;">
                    Instant FaceID verification & check your attendance records
                </p>
                <div style="height: 150px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
                    <img src="https://i.ibb.co/844D9Lrt/mascot-student.png" style="max-height: 140px; width: auto; object-fit: contain; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.3));" />
                </div>
            </div>
            <div style="height: 12px;"></div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button('Enter Student Portal', type="primary", width="stretch", icon=':material/arrow_outward:'):
            st.session_state['login_type'] = 'student'
            st.rerun()
            
    with col2:
        st.markdown(
            """
            <div style="background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.15); border-radius: 28px; padding: 28px 24px; text-align: center; backdrop-filter: blur(16px); box-shadow: 0 15px 35px rgba(0,0,0,0.25);">
                <div style="display: inline-block; background: rgba(244, 63, 94, 0.25); color: #FECDD3; border: 1px solid rgba(253, 164, 175, 0.3); border-radius: 9999px; padding: 4px 14px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 12px;">
                    Teacher Portal
                </div>
                <h2 style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; margin: 0 0 6px 0;">I'm a Teacher</h2>
                <p style="color: #CBD5E1; font-size: 0.85rem; margin: 0 0 16px 0; min-height: 38px;">
                    Group photo scans, voice analysis & lecture record management
                </p>
                <div style="height: 150px; display: flex; align-items: center; justify-content: center; margin-bottom: 8px;">
                    <img src="https://i.ibb.co/CsmQQV6X/mascot-prof.png" style="max-height: 140px; width: auto; object-fit: contain; filter: drop-shadow(0 8px 16px rgba(0,0,0,0.3));" />
                </div>
            </div>
            <div style="height: 12px;"></div>
            """,
            unsafe_allow_html=True
        )
        
        if st.button('Enter Teacher Portal', type="secondary", width="stretch", icon=':material/arrow_outward:'):
            st.session_state['login_type'] = 'teacher'
            st.rerun()
            
    footer_home()