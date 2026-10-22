import streamlit as st
import numpy as np
from PIL import Image
import time
import pandas as pd
from datetime import datetime

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.pipelines.face_pipeline import predict_attendence, get_face_embedding, train_classifier, check_liveness
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_students, 
    create_student, 
    get_student_subjects, 
    get_student_attendance, 
    unenroll_student_to_subject,
    get_student_notices
)
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card


@st.dialog("Class Notices & Resources")
def show_student_notices_dialog(student_id: int):
    # CSS for compact image preview and clean card
    st.markdown("""
        <style>
            .notice-img-box {
                display: flex;
                justify-content: center;
                align-items: center;
                margin: 10px 0;
                background: rgba(0, 0, 0, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 8px;
            }
            .notice-img-box img {
                max-height: 220px !important;
                max-width: 100% !important;
                object-fit: contain !important;
                border-radius: 8px;
            }
        </style>
    """, unsafe_allow_html=True)

    all_notices = get_student_notices(student_id)
    dismissed = st.session_state.get(f"dismissed_notices_{student_id}", set())
    
    # Filter out dismissed notices
    active_notices = [n for n in all_notices if n.get('notice_id') not in dismissed]

    # Top header bar inside dialog with clear action
    col_t1, col_t2 = st.columns([2.5, 1.3], vertical_alignment="center")
    with col_t1:
        st.caption(f"Showing {len(active_notices)} active announcement{'s' if len(active_notices) != 1 else ''}")
    with col_t2:
        if active_notices:
            if st.button("Clear Notices", type="tertiary", use_container_width=True, icon=":material/clear_all:"):
                all_ids = {n.get('notice_id') for n in all_notices if n.get('notice_id')}
                st.session_state[f"dismissed_notices_{student_id}"] = all_ids
                st.toast("All notices cleared from your feed!", icon="🧹")
                time.sleep(0.4)
                st.rerun()

    st.divider()

    if not active_notices:
        st.info("No notices or resources published yet.")
        return
        
    for n in active_notices:
        with st.container(border=True):
            st.markdown(f"### {n.get('title', 'Notice')}")
            sub_info = n.get('subjects', {}) or {}
            date_str = str(n.get('created_at', ''))[:10]
            st.caption(f"Course: {sub_info.get('name', 'Course')} (`{sub_info.get('subject_code', '-')}`) | 📅 {date_str}")
            
            st.write(n.get('message', ''))
            
            # Safe doc_url extraction
            doc_url = n.get('doc_url')
            if isinstance(doc_url, dict):
                doc_url = doc_url.get('publicUrl') or doc_url.get('public_url')
                
            if doc_url and str(doc_url).strip() and str(doc_url).strip().lower() != "none":
                clean_url = str(doc_url).strip()
                lower_url = clean_url.lower()
                
                # Check if file is an image - render in controlled size container
                is_img = any(lower_url.endswith(ext) or (ext in lower_url and "?" in lower_url) for ext in ['.png', '.jpg', '.jpeg', '.webp'])
                if is_img:
                    st.markdown(f"""
                        <div class="notice-img-box">
                            <img src="{clean_url}" alt="Attachment Preview" />
                        </div>
                    """, unsafe_allow_html=True)
                
                st.link_button("📎 View / Download Document", clean_url, use_container_width=True)
                
        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


@st.dialog("Attendance History")
def student_attendance_history_dialog(subject_name: str, subject_code: str, subject_logs: list):
    st.subheader(f"{subject_name} ({subject_code})")
    
    if not subject_logs:
        st.info("No attendance recorded for this subject yet.")
        return

    sorted_logs = sorted(
        subject_logs, 
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    
    table_data = []
    present_count = 0
    total_count = len(sorted_logs)
    
    for item in sorted_logs:
        ts = item.get('timestamp')
        formatted_date = datetime.fromisoformat(ts).strftime("%d %b %Y, %I:%M %p") if ts else "N/A"
        is_pres = bool(item.get('is_present', False))
        st_val = item.get('status', 'Present' if is_pres else 'Absent')
        excuse = item.get('excuse_note')
        
        if is_pres:
            present_count += 1
            status_text = "✅ Present"
        elif "Duty" in str(st_val) or "Medical" in str(st_val):
            status_text = f"📋 {st_val}"
        else:
            status_text = "❌ Absent"
            
        if excuse:
            status_text += f" ({excuse})"
            
        table_data.append({
            "Lecture Date & Time": formatted_date,
            "Status": status_text
        })
        
    absent_count = total_count - present_count
    attendance_percentage = (present_count / total_count * 100) if total_count > 0 else 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Classes", total_count)
    m2.metric("Attended", present_count)
    m3.metric("Missed", absent_count)
    m4.metric("Attendance %", f"{attendance_percentage:.1f}%")
    
    st.divider()
    st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)


def render_75_percent_calculator(attended: int, total: int):
    if total == 0:
        st.caption("No lectures conducted yet.")
        return

    pct = (attended / total * 100.0)
    if pct >= 75.0:
        safe_bunks = int((attended - 0.75 * total) / 0.75)
        st.markdown(f"""
            <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 12px; padding: 8px 12px; margin-bottom: 10px;">
                <span style="color: #34D399; font-weight: 700; font-size: 0.85rem;">🟢 Safe: {pct:.1f}%</span>
                <span style="color: #CBD5E1; font-size: 0.8rem; margin-left: 6px;">Can miss <b>{safe_bunks}</b> more class{'es' if safe_bunks != 1 else ''}.</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        needed = int(np.ceil((0.75 * total - attended) / 0.25))
        st.markdown(f"""
            <div style="background: rgba(244, 63, 94, 0.12); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: 12px; padding: 8px 12px; margin-bottom: 10px;">
                <span style="color: #FB7185; font-weight: 700; font-size: 0.85rem;">🔴 Shortage: {pct:.1f}%</span>
                <span style="color: #CBD5E1; font-size: 0.8rem; margin-left: 6px;">Attend next <b>{needed}</b> classes to reach 75%.</span>
            </div>
        """, unsafe_allow_html=True)


def student_dashboard():
    student_data = st.session_state.get('student_data', {})
    student_id = student_data.get('student_id')
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {student_data.get('name', 'Student')}")
        if st.button("Logout", type='secondary', key='student_logout_btn'):
            st.session_state.clear()
            st.session_state['login_type'] = None
            st.rerun()
            
    st.write("")

    # --- Unread Notice Badge Calculation ---
    all_notices = get_student_notices(student_id)
    dismissed = st.session_state.get(f"dismissed_notices_{student_id}", set())
    active_notices = [n for n in all_notices if n.get('notice_id') not in dismissed]

    last_seen_ts = st.session_state.get(f"last_seen_notice_{student_id}", "1970-01-01T00:00:00")
    unread_count = 0
    for n in active_notices:
        created = n.get('created_at', '')
        if created and str(created) > str(last_seen_ts):
            unread_count += 1

    # Mobile App Style Floating Badge CSS
    if unread_count > 0:
        st.markdown(f"""
            <style>
                div:has(> button[key="student_notice_btn"]) {{
                    position: relative !important;
                }}
                div:has(> button[key="student_notice_btn"])::after {{
                    content: "{unread_count if unread_count < 100 else '99+'}";
                    position: absolute;
                    top: -6px;
                    right: -6px;
                    background: linear-gradient(135deg, #EF4444, #DC2626);
                    color: #FFFFFF;
                    font-size: 0.72rem;
                    font-weight: 800;
                    height: 20px;
                    min-width: 20px;
                    line-height: 20px;
                    padding: 0 5px;
                    text-align: center;
                    border-radius: 9999px;
                    border: 2px solid #0B0F19;
                    box-shadow: 0 0 10px rgba(239, 68, 68, 0.7);
                    pointer-events: none;
                    z-index: 99;
                    animation: pulse-badge 2s infinite ease-in-out;
                }}
                @keyframes pulse-badge {{
                    0% {{ transform: scale(1); }}
                    50% {{ transform: scale(1.15); }}
                    100% {{ transform: scale(1); }}
                }}
            </style>
        """, unsafe_allow_html=True)

    top_c1, top_c2, top_c3 = st.columns([2.3, 1.4, 1.3], vertical_alignment='center')
    with top_c1:
        st.header('Your Enrolled Subjects')
        
    with top_c2:
        # Simple clean button text, badge sits on top-right corner automatically
        if st.button('Notice Board', key="student_notice_btn", type="secondary", use_container_width=True, icon=':material/campaign:'):
            st.session_state[f"last_seen_notice_{student_id}"] = datetime.now().isoformat()
            show_student_notices_dialog(student_id)
            
    with top_c3:
        if st.button('Enroll Subject', type='primary', use_container_width=True, icon=':material/add:'):
            enroll_dialog()
            
    st.divider()
    
    with st.spinner('Loading your enrolled subjects...'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)
        
    stats_map = {}
    subject_logs_map = {}
    for log in logs:
        sid = log.get('subject_id')
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}
            subject_logs_map[sid] = []
        
        stats_map[sid]['total'] += 1
        subject_logs_map[sid].append(log)
        if log.get('is_present'):
            stats_map[sid]['attended'] += 1
            
    if subjects:
        cols = st.columns(2)
        for i, sub_node in enumerate(subjects):
            sub = sub_node['subjects']
            sid = sub['subject_id']
            stats = stats_map.get(sid, {"total": 0, "attended": 0})
            current_sub_logs = subject_logs_map.get(sid, [])
            
            def make_card_actions(subject_id, subject_name, subject_code, logs_data, att_count, tot_count):
                def callback():
                    render_75_percent_calculator(att_count, tot_count)
                    btn_c1, btn_c2 = st.columns(2)
                    with btn_c1:
                        if st.button('View History', key=f"hist_{subject_id}", type='secondary', use_container_width=True, icon=':material/calendar_month:'):
                            student_attendance_history_dialog(subject_name, subject_code, logs_data)
                    with btn_c2:
                        if st.button('Unenroll', type='tertiary', use_container_width=True, icon=':material/delete_forever:', key=f"unenroll_{subject_id}"):
                            unenroll_student_to_subject(student_id, subject_id)
                            st.toast(f"Unenrolled from {subject_name} successfully!")
                            st.rerun()
                return callback
            
            with cols[i % 2]:
                subject_card(
                    name=sub['name'],
                    code=sub['subject_code'],
                    section=sub.get('section', '-'),
                    stats=[
                        ('📅', 'Total', stats['total']),
                        ('✅', 'Attended', stats['attended'])
                    ],
                    footer_callback=make_card_actions(sid, sub['name'], sub['subject_code'], current_sub_logs, stats['attended'], stats['total'])
                )
    else:
        st.info("You are not enrolled in any subjects yet.")
    
    footer_dashboard()


def student_screen():
    style_background_dashboard()
    style_base_layout()
    
    if "show_registration" not in st.session_state:
        st.session_state.show_registration = False
    
    if st.session_state.get('student_data'):
        student_dashboard()
        return
    
    _, center_col, _ = st.columns([1, 2.3, 1])
    with center_col:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            top_c1, top_c2 = st.columns([2.2, 1], vertical_alignment='center')
            with top_c1:
                header_dashboard()
            with top_c2:
                if st.button("Back", type='tertiary', key='student_back_btn', icon=":material/arrow_back:", use_container_width=True):
                    st.session_state.clear()
                    st.session_state['login_type'] = None
                    st.rerun()

            st.divider()

            st.markdown("""
                <div style="text-align: center; margin-bottom: 16px;">
                    <h2 style="font-size: 1.5rem; font-weight: 700; color: #FFFFFF; margin: 0;">Student FaceID Login</h2>
                    <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Look straight into the camera to authenticate</p>
                </div>
            """, unsafe_allow_html=True)
            
            photo_source = st.camera_input("Capture live face")
            
            if photo_source:
                img = np.array(Image.open(photo_source))
                
                with st.spinner('Checking Liveness & Biometrics...'):
                    # 1. Anti-Spoofing / Liveness Check
                    is_live, liveness_msg = check_liveness(img)
                    if not is_live:
                        st.error(f"Anti-Spoofing Alert: {liveness_msg} ⚠️")
                    else:
                        detected, all_ids, num_faces = predict_attendence(img)
                        
                        if num_faces == 0:
                            st.warning('Face not detected clearly. Ensure proper lighting!')
                        elif num_faces > 1:
                            st.warning('Multiple faces detected. Please stand alone in front of camera.')
                        else:
                            if detected:
                                student_id = list(detected.keys())[0]
                                all_students = get_all_students()
                                student = next((s for s in all_students if s['student_id'] == student_id), None)
                                
                                if student:
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = student
                                    st.toast(f"Welcome Back, {student['name']}! 👋🏻")
                                    time.sleep(0.8)
                                    st.rerun()
                            else:
                                st.info('Face profile not recognized! Please register below.')
                                st.session_state.show_registration = True
                            
            if st.session_state.show_registration:
                st.divider()
                st.markdown("""
                    <div style="text-align: center; margin-bottom: 14px;">
                        <h3 style="font-size: 1.3rem; font-weight: 700; color: #FFFFFF; margin: 0;">Register New Profile</h3>
                    </div>
                """, unsafe_allow_html=True)
                
                new_name = st.text_input("Full Name", placeholder='e.g. Vaibhav Gupta')
                
                st.caption("Optional: Voice Enrollment")
                audio_data = None
                try:
                    audio_data = st.audio_input('Record: "I am present, My name is [Your Name]"')
                except Exception:
                    st.caption('Microphone not supported on this browser.')
                    
                if st.button('Complete Registration', type='primary', use_container_width=True, icon=':material/check:'):
                    if not new_name.strip():
                        st.warning("Please enter your name!")
                    elif not photo_source:
                        st.warning("Please capture a live photo first.")
                    else:
                        with st.spinner('Extracting Facial Descriptors...'):
                            img = np.array(Image.open(photo_source))
                            encodings = get_face_embedding(img)
                            if encodings:
                                face_emb = encodings[0].tolist()
                                voice_emb = None
                                if audio_data:
                                    voice_emb = get_voice_embedding(audio_data.read())
                                
                                response_data = create_student(new_name.strip(), face_embedding=face_emb, voice_embedding=voice_emb)
                                if response_data:
                                    train_classifier()
                                    st.session_state.is_logged_in = True
                                    st.session_state.user_role = 'student'
                                    st.session_state.student_data = response_data[0]
                                    st.session_state.show_registration = False
                                    st.toast(f'Profile Created! Welcome, {new_name}!')
                                    time.sleep(1)
                                    st.rerun()
                            else:
                                st.error("Failed to extract face features. Check lighting and try again.")
                                
        footer_dashboard()