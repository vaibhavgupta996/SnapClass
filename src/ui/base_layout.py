import streamlit as st

def style_base_layout():
    st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
        
        <style>
            #MainMenu, footer, header {
                visibility: hidden !important;
                height: 0px !important;
            }
            
            html, body, [class*="css"], .stApp {
                font-family: 'Outfit', sans-serif !important;
                color: #FFFFFF !important;
            }
            
            .block-container { 
                padding-top: 2rem !important;
                padding-bottom: 2.5rem !important;
                max-width: 950px !important;
            }
            
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Plus Jakarta Sans', sans-serif !important;
                color: #FFFFFF !important;
            }
            
            p, span, label {
                color: #CBD5E1 !important;
            }

            /* --- Unified Modern Glass Card --- */
            div[data-testid="stVerticalBlockBorderWrapper"] {
                background: rgba(13, 20, 36, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.16) !important;
                border-radius: 28px !important;
                backdrop-filter: blur(24px) !important;
                -webkit-backdrop-filter: blur(24px) !important;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 
                            0 0 0 1px rgba(255, 255, 255, 0.08) inset !important;
                padding: 1.5rem !important;
            }

            /* Inputs Inside the Card */
            div[data-baseweb="input"] {
                background: rgba(255, 255, 255, 0.06) !important;
                border: 1px solid rgba(255, 255, 255, 0.18) !important;
                border-radius: 14px !important;
                transition: all 0.2s ease !important;
            }
            
            div[data-baseweb="input"]:focus-within {
                border-color: #6366F1 !important;
                background: rgba(255, 255, 255, 0.1) !important;
                box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.4) !important;
            }

            div[data-baseweb="input"] input {
                color: #FFFFFF !important;
                font-size: 0.95rem !important;
                background: transparent !important;
                border: none !important;
                -webkit-text-fill-color: #FFFFFF !important;
            }

            div[data-baseweb="input"] button {
                color: #A5B4FC !important;
                background: transparent !important;
                border: none !important;
            }

            div[data-baseweb="input"] input::placeholder {
                color: rgba(203, 213, 225, 0.4) !important;
                -webkit-text-fill-color: rgba(203, 213, 225, 0.4) !important;
            }

            /* Buttons */
            .stButton > button {
                border-radius: 14px !important;
                font-weight: 700 !important;
                font-size: 0.95rem !important;
                padding: 0.65rem 1.25rem !important;
                font-family: 'Plus Jakarta Sans', sans-serif !important;
                transition: all 0.25s ease-in-out !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
            }
            
            .stButton > button:hover {
                transform: translateY(-2px) !important;
            }

            .stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%) !important;
                color: #FFFFFF !important;
                box-shadow: 0 8px 20px rgba(79, 70, 229, 0.35) !important;
            }

            .stButton > button[kind="secondary"] {
                background: linear-gradient(135deg, #F43F5E 0%, #E11D48 100%) !important;
                color: #FFFFFF !important;
                box-shadow: 0 8px 20px rgba(244, 63, 94, 0.35) !important;
            }

            .stButton > button[kind="tertiary"] {
                background: rgba(255, 255, 255, 0.08) !important;
                color: #E2E8F0 !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
            }

            div[data-testid="stCameraInput"] {
                background: rgba(255, 255, 255, 0.05) !important;
                border-radius: 20px !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                padding: 12px !important;
            }

            div[data-testid="stDataFrame"] {
                background: rgba(255, 255, 255, 0.05) !important;
                border-radius: 16px !important;
                border: 1px solid rgba(255, 255, 255, 0.12) !important;
                overflow: hidden !important;
            }
            
            /* Streamlit Heading Anchor Link Icons ko hide karne ke liye */
            a.header-anchor, 
            [data-testid="stHeaderActionElements"],
            .st-emotion-cache-15zrgzn,
            .st-emotion-cache-10trblm {
                display: none !important;
                visibility: hidden !important;
            }

            /* Kisi bhi header ke andar a tag ko disable karein */
            h1 a, h2 a, h3 a, h4 a, h5 a, h6 a {
                display: none !important;
            }
        </style>
    """, unsafe_allow_html=True)


def style_background_home():
    st.markdown("""
        <style>
            @keyframes smoothMesh {
                0% {
                    background-position: 0% 0%, 100% 100%, 50% 50%;
                }
                50% {
                    background-position: 50% 80%, 30% 20%, 80% 60%;
                }
                100% {
                    background-position: 0% 0%, 100% 100%, 50% 50%;
                }
            }

            .stApp {
                background-color: #030b14 !important;
                background-image: 
                    radial-gradient(circle at 15% 20%, rgba(0, 150, 190, 0.45) 0%, transparent 55%),
                    radial-gradient(circle at 85% 85%, rgba(136, 19, 79, 0.35) 0%, transparent 55%),
                    radial-gradient(circle at 50% 50%, rgba(10, 37, 64, 0.6) 0%, transparent 70%) !important;
                background-size: 150% 150%, 160% 160%, 100% 100% !important;
                animation: smoothMesh 16s ease-in-out infinite alternate !important;
                min-height: 100vh;
            }
        </style>
    """, unsafe_allow_html=True)


def style_background_dashboard():
    st.markdown("""
        <style>
            @keyframes smoothMeshDashboard {
                0% {
                    background-position: 0% 0%, 100% 100%, 50% 50%;
                }
                50% {
                    background-position: 40% 70%, 20% 30%, 70% 50%;
                }
                100% {
                    background-position: 0% 0%, 100% 100%, 50% 50%;
                }
            }

            .stApp {
                background-color: #040810 !important;
                background-image: 
                    radial-gradient(circle at 10% 15%, rgba(0, 130, 175, 0.35) 0%, transparent 60%),
                    radial-gradient(circle at 90% 90%, rgba(120, 15, 68, 0.3) 0%, transparent 60%),
                    radial-gradient(circle at 50% 50%, rgba(8, 28, 50, 0.5) 0%, transparent 75%) !important;
                background-size: 160% 160%, 150% 150%, 100% 100% !important;
                animation: smoothMeshDashboard 18s ease-in-out infinite alternate !important;
                min-height: 100vh;
            }
        </style>
    """, unsafe_allow_html=True)