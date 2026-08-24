import streamlit as st
import numpy as np
from PIL import Image
import time

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.pipelines.face_pipeline import predict_attendence, get_face_embedding, train_classifier
from src.pipelines.voice_pipeline import get_voice_embedding
from src.database.db import (
    get_all_students, 
    create_student, 
    get_student_subjects, 
    get_student_attendance, 
    unenroll_student_to_subject
)
from src.components.dialog_enroll import enroll_dialog
from src.components.subject_card import subject_card

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
    
    c1, c2 = st.columns([3, 1], vertical_alignment='center')
    with c1:
        st.header('Your Enrolled Subjects')
    with c2:
        if st.button('Enroll in Subject', type='primary', use_container_width=True):
            enroll_dialog()
            
    st.divider()
    
    with st.spinner('Loading your enrolled subjects...'):
        subjects = get_student_subjects(student_id)
        logs = get_student_attendance(student_id)
        
    stats_map = {}
    for log in logs:
        sid = log.get('subject_id')
        if sid not in stats_map:
            stats_map[sid] = {"total": 0, "attended": 0}
        
        stats_map[sid]['total'] += 1
        if log.get('is_present'):
            stats_map[sid]['attended'] += 1
            
    if subjects:
        cols = st.columns(2)
        for i, sub_node in enumerate(subjects):
            sub = sub_node['subjects']
            sid = sub['subject_id']
            stats = stats_map.get(sid, {"total": 0, "attended": 0})
            
            def make_unenroll_btn(subject_id, subject_name):
                def callback():
                    if st.button('Unenroll from course', type='tertiary', use_container_width=True, icon=':material/delete_forever:', key=f"unenroll_{subject_id}"):
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
                    footer_callback=make_unenroll_btn(sid, sub['name'])
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
    
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        if st.button("Go back to Home", type='secondary', key='student_back_btn'):
            st.session_state.clear()
            st.session_state['login_type'] = None
            st.rerun()
    
    st.header('Login using FaceID')
    photo_source = st.camera_input("Position your face in the center")
    
    if photo_source:
        img = np.array(Image.open(photo_source))
        
        with st.spinner('AI is scanning...'):
            detected, all_ids, num_faces = predict_attendence(img)
            
            if num_faces == 0:
                st.warning('Face not found!')
            elif num_faces > 1:
                st.warning('Multiple faces detected. Please stand alone in front of the camera.')
            else:
                if detected:
                    student_id = list(detected.keys())[0]
                    all_students = get_all_students()
                    student = next((s for s in all_students if s['student_id'] == student_id), None)
                    
                    if student:
                        st.session_state.is_logged_in = True
                        st.session_state.user_role = 'student'
                        st.session_state.student_data = student
                        st.toast(f"Welcome Back, {student['name']}!")
                        time.sleep(0.8)
                        st.rerun()
                else:
                    st.info('Face not recognized! Please register your profile below.')
                    st.session_state.show_registration = True
                    
    if st.session_state.show_registration:
        with st.container(border=True):
            st.header('Register New Profile')
            new_name = st.text_input("Enter Your Name:", placeholder='E.g. Vaibhav Gupta')
            
            st.subheader('Optional: Voice Enrollment')
            st.info('Enroll your voice for voice attendance.')
            
            audio_data = None
            try:
                audio_data = st.audio_input('Record: "I am present, My name is [Your Name]"')
            except Exception:
                st.error('Microphone access failed or not supported.')
                
            if st.button('Create Account', type='primary', use_container_width=True):
                if not new_name.strip():
                    st.warning("Please enter your name!")
                elif not photo_source:
                    st.warning("Please capture your face using the camera above.")
                else:
                    with st.spinner('Creating Profile...'):
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
                            st.error("Could not extract facial features. Adjust lighting and try again.")
        
    footer_dashboard()