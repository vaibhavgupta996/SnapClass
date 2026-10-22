import streamlit as st

def subject_card(name, code, section, stats=None, footer_callback=None):
    stats_pills = ""
    if stats:
        pills_list = []
        for icon, label, value in stats:
            pill = f'<div style="display:inline-flex; align-items:center; gap:6px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.15); border-radius:12px; padding:4px 12px; font-size:0.8rem; font-weight:600; color:#F1F5F9; margin-right:8px; margin-bottom:8px;"><span>{icon}</span><span>{label}:</span><b style="color:#818CF8;">{value}</b></div>'
            pills_list.append(pill)
        stats_pills = f'<div style="margin-top:12px; margin-bottom:12px;">{"".join(pills_list)}</div>'

    card_html = (
        f'<div style="background:rgba(255,255,255,0.06); border:1px solid rgba(255,255,255,0.15); '
        f'border-left:6px solid #6366F1; border-radius:20px; padding:18px 20px; margin-bottom:16px; '
        f'backdrop-filter:blur(12px); box-shadow:0 10px 25px rgba(0,0,0,0.2);">'
        f'<h3 style="font-size:1.25rem; font-weight:700; color:#FFFFFF; margin:0 0 6px 0;">{name}</h3>'
        f'<div style="display:flex; align-items:center; gap:8px;">'
        f'<span style="background:rgba(99,102,241,0.25); color:#C7D2FE; border:1px solid rgba(165,180,252,0.3); font-size:0.75rem; font-weight:700; padding:2px 8px; border-radius:6px;">{code}</span>'
        f'<span style="font-size:0.85rem; color:#94A3B8; font-weight:500;">Section {section}</span>'
        f'</div>'
        f'{stats_pills}'
        f'</div>'
    )
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    if footer_callback:
        footer_callback()
        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)