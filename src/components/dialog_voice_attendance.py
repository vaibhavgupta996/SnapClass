import streamlit as st
import pandas as pd
from datetime import datetime
from src.pipelines.voice_pipeline import process_bulk_audio
from src.components.dialog_attendance_result import show_attendance_result
from src.database.config import supabase

@st.dialog('Voice Attendance')
def voice_attendance_dialog(selected_subject_id):
    st.write('Record audio of students saying **"Present Sir / Ma\'am"** or their names.')
    audio_data = st.audio_input("Record classroom audio")
    
    result_container = st.container()

    if st.button('Analyze Audio', use_container_width=True, type='primary'):
        if not audio_data:
            st.warning("Please record audio before analyzing.")
            return

        with st.spinner('Matching voices with enrolled students...'):
            enrolled_res = supabase.table('subject_students').select("*, students(*)").eq('subject_id', selected_subject_id).execute()
            enrolled_students = enrolled_res.data
            
            if not enrolled_students:
                st.warning("No students enrolled in this course.")
                return
                
            candidates_dict = {}
            for s in enrolled_students:
                std = s.get('students')
                if std and std.get('voice_embedding'):
                    candidates_dict[int(std['student_id'])] = std['voice_embedding']
            
            if not candidates_dict:
                st.error('No enrolled students have voice profiles registered.')
                return
            
            audio_bytes = audio_data.read()
            detected_scores = process_bulk_audio(audio_bytes, candidates_dict, threshold=0.38)
            
            results, attendance_to_log = [], []
            current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            
            for node in enrolled_students:
                student = node['students']
                std_id = int(student['student_id'])
                score = detected_scores.get(std_id, 0.0)
                is_present = bool(score > 0)
                
                results.append({
                    "Name": student['name'],
                    "ID": std_id,
                    "Match Score": f"{score:.2f}" if is_present else "-",
                    "Status": "✅ Present" if is_present else "❌ Absent"
                })
                
                attendance_to_log.append({
                    'student_id': std_id,
                    'subject_id': selected_subject_id,
                    'timestamp': current_timestamp,
                    'is_present': bool(is_present)
                })
                
            st.session_state.voice_attendance_results = (pd.DataFrame(results), attendance_to_log)

    # Render results inside the dialog without closing/rerunning
    if st.session_state.get('voice_attendance_results'):
        with result_container:
            st.divider()
            df_results, logs = st.session_state.voice_attendance_results
            show_attendance_result(df_results, logs)