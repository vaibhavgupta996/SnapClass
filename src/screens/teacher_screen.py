import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import time

from src.ui.base_layout import style_background_dashboard, style_base_layout
from src.components.header import header_dashboard
from src.components.footer import footer_dashboard
from src.database.db import (
    check_teacher_exists, 
    create_teacher, 
    teacher_login, 
    get_teacher_subjects, 
    get_attendance_for_teacher,
    get_enrolled_students_by_subject,
    get_session_attendance_details,
    unenroll_student_to_subject,
    create_notice,
    update_student_attendance_status,
    upload_notice_attachment,
    clear_all_notices_by_teacher
)
from src.components.dialog_create_subject import create_subject_dialog
from src.components.dialog_shared_subject import share_subject_dialog
from src.components.subject_card import subject_card
from src.components.dialog_add_photos import add_photos_dialog
from src.pipelines.face_pipeline import predict_attendence
from src.database.config import supabase
from src.components.dialog_attendance_result import attendance_result_dialog
from src.components.dialog_voice_attendance import voice_attendance_dialog
from src.utils.security import validate_password_strength


def teacher_screen():
    style_background_dashboard()
    style_base_layout()
    
    if "teacher_data" in st.session_state and st.session_state.teacher_data:
        teacher_dashboard()
    elif st.session_state.get('teacher_login_type') == "register":
        teacher_screen_register()
    else:
        teacher_screen_login()


def teacher_dashboard():
    teacher_data = st.session_state.teacher_data
    c1, c2 = st.columns(2, vertical_alignment='center', gap='large')
    with c1:
        header_dashboard()
    with c2:
        st.subheader(f"Welcome, {teacher_data['name']}")
        if st.button("Logout", type='secondary', key='teacher_logout_btn', shortcut="control+backspace"):
            st.session_state.clear()
            st.rerun()
            
    st.write("")
    
    if "current_teacher_tab" not in st.session_state:
        st.session_state.current_teacher_tab = "Take_Attendence"
        
    tab1, tab2, tab3, tab4 = st.columns(4)
    with tab1:
        t1_type = "primary" if st.session_state.current_teacher_tab == 'Take_Attendence' else "tertiary"
        if st.button('Take Attendance', type=t1_type, use_container_width=True, icon=':material/ar_on_you:'):
            st.session_state.current_teacher_tab = "Take_Attendence"
            st.rerun()

    with tab2:
        t2_type = "primary" if st.session_state.current_teacher_tab == 'Manage_Subjects' else "tertiary"
        if st.button('Manage Subjects', type=t2_type, use_container_width=True, icon=':material/book_ribbon:'):
            st.session_state.current_teacher_tab = 'Manage_Subjects'
            st.rerun()    

    with tab3:
        t3_type = "primary" if st.session_state.current_teacher_tab == 'Attendence_Records' else "tertiary"
        if st.button('Attendance Records', type=t3_type, use_container_width=True, icon=':material/cards_stack:'):
            st.session_state.current_teacher_tab = 'Attendence_Records'
            st.rerun() 

    with tab4:
        t4_type = "primary" if st.session_state.current_teacher_tab == 'Enrolled_Students' else "tertiary"
        if st.button('Enrolled Students', type=t4_type, use_container_width=True, icon=':material/group:'):
            st.session_state.current_teacher_tab = 'Enrolled_Students'
            st.rerun()
            
    st.divider()
            
    if st.session_state.current_teacher_tab == "Take_Attendence":
        teacher_tab_take_attendence()
    elif st.session_state.current_teacher_tab == "Manage_Subjects":
        teacher_tab_manage_students()
    elif st.session_state.current_teacher_tab == "Attendence_Records":
        teacher_tab_attendence_records()
    elif st.session_state.current_teacher_tab == "Enrolled_Students":
        teacher_tab_enrolled_students()
         
    footer_dashboard()


def teacher_tab_take_attendence():
    teacher_id = st.session_state.teacher_data['teacher_id']
    st.header('Take AI Attendance')
    
    if 'attendance_images' not in st.session_state:
        st.session_state.attendance_images = []
        
    subjects = get_teacher_subjects(teacher_id)
    if not subjects:
        st.warning("You haven't created any subjects yet! Please create one to begin.")
        return
    
    subject_options = {f"{s['name']} ({s['subject_code']})": s['subject_id'] for s in subjects}
    col1, col2 = st.columns([3, 1], vertical_alignment='bottom')
    
    with col1:
        selected_subject_label = st.selectbox('Select Subject', options=list(subject_options.keys()))
        
    with col2:
        if st.button('Add Photos', type='primary', icon=':material/photo_prints:', use_container_width=True):
            add_photos_dialog()
            
    selected_subject_id = subject_options[selected_subject_label]
    st.divider()
    
    if st.session_state.attendance_images:
        st.subheader('Uploaded Classroom Photos')
        gallery_cols = st.columns(4)
        for idx, img in enumerate(st.session_state.attendance_images):
            with gallery_cols[idx % 4]:
                st.image(img, use_container_width=True, caption=f'Photo {idx + 1}')
            
    has_photos = bool(st.session_state.attendance_images)  
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button('Clear Photos', use_container_width=True, type='tertiary', icon=':material/delete:', disabled=not has_photos):
            st.session_state.attendance_images = []
            st.rerun()
            
    with c2:
        if st.button('Run Face Analysis', use_container_width=True, type='secondary', icon=':material/analytics:', disabled=not has_photos):
            with st.spinner('Deep Scanning Classroom Photos...'):
                all_detected_ids = {}
                
                for idx, img in enumerate(st.session_state.attendance_images):
                    img_np = np.array(img.convert('RGB'))
                    detected, _, _ = predict_attendence(img_np)
                    if detected:
                        for sid in detected.keys():
                            student_id = int(sid)
                            all_detected_ids.setdefault(student_id, []).append(f"Photo {idx + 1}")
                            
                enrolled_students = get_enrolled_students_by_subject(selected_subject_id)
                
                if not enrolled_students:
                    st.warning('No students enrolled in this course.')
                else:
                    results, attendance_to_log = [], []
                    current_timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                    
                    for node in enrolled_students:
                        student = node['students']
                        sources = all_detected_ids.get(int(student['student_id']), [])
                        is_present = len(sources) > 0
                        
                        results.append({
                            "Name": student['name'],
                            "ID": student['student_id'],
                            "Source": ", ".join(sources) if is_present else "-",
                            "Status": "✅ Present" if is_present else "❌ Absent"
                        })
                        
                        attendance_to_log.append({
                            'student_id': student['student_id'],
                            'subject_id': selected_subject_id,
                            'timestamp': current_timestamp,
                            'is_present': bool(is_present),
                            'status': 'Present' if is_present else 'Absent',
                            'excuse_note': None
                        })
                        
                    attendance_result_dialog(pd.DataFrame(results), attendance_to_log)
    with c3:
        if st.button('Use Voice Attendance', type='primary', use_container_width=True, icon=':material/mic:'):
            voice_attendance_dialog(selected_subject_id)


def teacher_tab_manage_students():
    teacher_id = st.session_state.teacher_data['teacher_id']
    col1, col2, col3 = st.columns([2.4, 1.3, 1.3], vertical_alignment='center')
    with col1:
        st.header('Manage Subjects')
    
    subjects = get_teacher_subjects(teacher_id)
    
    with col2:
        if st.button('Broadcast Notice', use_container_width=True, type='secondary', icon=':material/campaign:', disabled=not bool(subjects)):
            send_notice_dialog(teacher_id, subjects)
            
    with col3:
        if st.button('Create Subject', use_container_width=True, type='primary', icon=':material/add:'):
            create_subject_dialog(teacher_id)
            
    if subjects:
        for sub in subjects:
            stats = [
                ("👥", "Students", sub.get('total_students', 0)),
                ("🕰️", "Classes", sub.get('total_classes', 0))
            ]
            def make_share_callback(sub_name, sub_code):
                def share_btn():
                    if st.button(f"Share Code: {sub_code}", key=f"share_{sub_code}", icon=":material/share:"):
                        share_subject_dialog(sub_name, sub_code)
                return share_btn
            
            subject_card(
                name=sub['name'],
                code=sub['subject_code'],
                section=sub.get('section', '-'),
                stats=stats, 
                footer_callback=make_share_callback(sub['name'], sub['subject_code'])
            )
    else:
        st.info("No subjects found. Create one above to get started!")


def teacher_tab_enrolled_students():
    st.header('Enrolled Students')
    teacher_id = st.session_state.teacher_data['teacher_id']
    subjects = get_teacher_subjects(teacher_id)
    
    if not subjects:
        st.warning("No subjects found. Create a subject first.")
        return
        
    subject_options = {f"{s['name']} ({s['subject_code']})": s['subject_id'] for s in subjects}
    selected_subject_label = st.selectbox('Select Subject to View Students', options=list(subject_options.keys()), key="enrolled_sub_select")
    selected_subject_id = subject_options[selected_subject_label]
    
    enrolled_data = get_enrolled_students_by_subject(selected_subject_id)
    
    if not enrolled_data:
        st.info("No students enrolled in this subject yet.")
        return
        
    student_list = []
    for item in enrolled_data:
        std = item.get('students', {})
        student_list.append({
            "Student ID": std.get('student_id'),
            "Name": std.get('name'),
            "Face Registered": "✅ Yes" if std.get('face_embedding') is not None else "❌ No",
            "Voice Registered": "✅ Yes" if std.get('voice_embedding') is not None else "❌ No"
        })
        
    df_students = pd.DataFrame(student_list)
    st.caption(f"Total Enrolled: {len(df_students)} students")
    st.dataframe(df_students, use_container_width=True, hide_index=True)


@st.dialog("Session Attendance Details")
def show_session_attendance_dialog(teacher_id: int, subject_id: int, timestamp: str, subject_title: str, formatted_time: str):
    st.markdown("""
        <style>
            div[data-testid="stDialog"] button p {
                white-space: nowrap !important;
                word-break: keep-all !important;
                font-size: 0.82rem !important;
            }
            .att-header {
                color: #94A3B8;
                font-size: 0.8rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding-bottom: 4px;
            }
        </style>
    """, unsafe_allow_html=True)

    head_c1, head_c2 = st.columns([2.5, 2], vertical_alignment='center')
    with head_c1:
        st.markdown(f"**{subject_title}**")
        st.caption(f"📅 {formatted_time}")
        
    records = get_session_attendance_details(teacher_id, subject_id, timestamp)
    if not records:
        st.info("No attendance entries recorded for this session.")
        return

    total = len(records)
    present_cnt = sum(1 for r in records if r.get("is_present") is True or r.get("Status") == "Present")
    absent_cnt = total - present_cnt

    with head_c2:
        m1, m2, m3 = st.columns(3)
        m1.metric("Total", total)
        m2.metric("Present", present_cnt)
        m3.metric("Absent", absent_cnt)

    st.divider()

    # Inline Editor Section
    if st.session_state.get("editing_student_id") is not None:
        target_id = st.session_state.editing_student_id
        target_student = next(
            (r for r in records if r.get('student_id') == target_id), 
            None
        )
        
        if target_student:
            with st.container(border=True):
                st.markdown(f"**Update Status: `{target_student.get('Name')}` (ID: `{target_id}`)**")
                
                status_choices = ["Present", "Absent", "Duty Leave / Medical"]
                curr_status = target_student.get("Status")
                if not curr_status:
                    curr_status = "Present" if target_student.get("is_present") else "Absent"
                
                default_idx = 0 if curr_status == "Present" else (2 if ("Duty" in str(curr_status) or "Medical" in str(curr_status)) else 1)
                
                new_status = st.selectbox("Status", status_choices, index=default_idx, key="override_status_select")
                new_excuse = st.text_input(
                    "Reason / Excuse Note (Optional)", 
                    value=target_student.get("excuse_note") or "", 
                    placeholder="e.g. Sports duty, Medical slip", 
                    key="override_excuse_input"
                )
                
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("Save Changes", type="primary", use_container_width=True, key="save_override_btn"):
                        if update_student_attendance_status(subject_id, target_id, timestamp, new_status, new_excuse):
                            st.toast("Status updated successfully!", icon="✅")
                            st.session_state.editing_student_id = None
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("Failed to update status.")
                with btn_col2:
                    if st.button("Cancel", type="tertiary", use_container_width=True, key="cancel_override_btn"):
                        st.session_state.editing_student_id = None
                        st.rerun()
            st.divider()

    # Table Header (4 Columns)
    h1, h2, h3, h4 = st.columns([1.2, 3.2, 2.4, 1.8], vertical_alignment='center')
    with h1:
        st.markdown("<span class='att-header'>ID</span>", unsafe_allow_html=True)
    with h2:
        st.markdown("<span class='att-header'>Student Name</span>", unsafe_allow_html=True)
    with h3:
        st.markdown("<span class='att-header'>Status</span>", unsafe_allow_html=True)
    with h4:
        st.markdown("<span class='att-header'>Action</span>", unsafe_allow_html=True)
        
    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)

    # 4-Column Student Row Listing
    for idx, r in enumerate(records):
        s_id = r.get('student_id')
        s_name = r.get('Name', 'Unknown Student')
        
        c1, c2, c3, c4 = st.columns([1.2, 3.2, 2.4, 1.8], vertical_alignment="center")
        
        with c1:
            st.code(f"#{s_id}" if s_id is not None else "-", language="")
            
        with c2:
            st.markdown(f"**{s_name}**")
            
        with c3:
            is_p = bool(r.get("is_present", False))
            st_val = r.get("Status") or ("Present" if is_p else "Absent")
            excuse = r.get("excuse_note")
            
            if st_val == "Present" or is_p:
                st.markdown("<span style='color: #34D399; font-weight: 600; font-size: 0.85rem;'>✅ Present</span>", unsafe_allow_html=True)
            elif "Duty" in str(st_val) or "Medical" in str(st_val):
                st.markdown("<span style='color: #60A5FA; font-weight: 600; font-size: 0.85rem;'>📋 Duty/Med</span>", unsafe_allow_html=True)
            else:
                st.markdown("<span style='color: #F87171; font-weight: 600; font-size: 0.85rem;'>❌ Absent</span>", unsafe_allow_html=True)
                
            if excuse:
                st.caption(f"*{excuse}*")
                
        with c4:
            if st.button("Edit", key=f"btn_edit_{s_id}_{idx}", icon=":material/edit:", type="tertiary", use_container_width=True):
                st.session_state.editing_student_id = s_id
                st.rerun()
                
        st.markdown("<div style='margin-bottom: 2px;'></div>", unsafe_allow_html=True)


def teacher_tab_attendence_records():
    st.header('Attendance Records')
    teacher_id = st.session_state.teacher_data['teacher_id']
    records = get_attendance_for_teacher(teacher_id)
    
    if not records:
        st.info("No attendance records found.")
        return
    
    data = []
    for r in records:
        ts = r.get('timestamp')
        st_val = r.get('status')
        is_pres_bool = bool(r.get('is_present', False))
        is_effectively_present = is_pres_bool or (st_val == "Present")
        
        data.append({
            "timestamp_raw": ts,
            "ts_group": ts.split(".")[0] if ts else None,
            "Time": datetime.fromisoformat(ts).strftime("%Y-%m-%d %I:%M %p") if ts else "NA",
            "Subject": r['subjects']['name'],
            "Subject Code": r['subjects']['subject_code'],
            "subject_id": r['subjects']['subject_id'],
            "is_present": is_effectively_present
        })
        
    df = pd.DataFrame(data)
    
    summary = (
        df.groupby(['timestamp_raw', 'ts_group', 'Time', 'Subject', 'Subject Code', 'subject_id'])
        .agg(
            Present_Count=('is_present', 'sum'),
            Total_Count=('is_present', 'count')
        ).reset_index()
    )
    
    summary = summary.sort_values(by='ts_group', ascending=False)
    
    head_c1, head_c2, head_c3, head_c4 = st.columns([3, 3, 2, 2])
    with head_c1:
        st.markdown("**Date & Time**")
    with head_c2:
        st.markdown("**Subject**")
    with head_c3:
        st.markdown("**Attendance**")
    with head_c4:
        st.markdown("**Action**")
    st.divider()

    for idx, row in summary.iterrows():
        c1, c2, c3, c4 = st.columns([3, 3, 2, 2], vertical_alignment='center')
        
        with c1:
            st.write(f"📅 {row['Time']}")
        with c2:
            st.write(f"**{row['Subject']}** (`{row['Subject Code']}`)")
        with c3:
            st.markdown(f"✅ **{row['Present_Count']}** / {row['Total_Count']} Students")
        with c4:
            btn_key = f"view_att_{row['subject_id']}_{idx}"
            if st.button("View List", key=btn_key, type="secondary", use_container_width=True, icon=":material/visibility:"):
                st.session_state.active_session_dialog = {
                    "teacher_id": teacher_id,
                    "subject_id": row['subject_id'],
                    "timestamp": row['timestamp_raw'],
                    "subject_title": f"{row['Subject']} ({row['Subject Code']})",
                    "formatted_time": row['Time']
                }
                st.session_state.editing_student_id = None
                st.rerun()
                
        st.markdown("<div style='margin-bottom: 8px;'></div>", unsafe_allow_html=True)

    if st.session_state.get("active_session_dialog"):
        dlg_params = st.session_state.active_session_dialog
        show_session_attendance_dialog(
            teacher_id=dlg_params["teacher_id"],
            subject_id=dlg_params["subject_id"],
            timestamp=dlg_params["timestamp"],
            subject_title=dlg_params["subject_title"],
            formatted_time=dlg_params["formatted_time"]
        )


@st.dialog("Broadcast Notice to Students")
def send_notice_dialog(teacher_id: int, subjects: list):
    sub_map = {f"{s['name']} ({s['subject_code']})": s for s in subjects}
    selected_label = st.selectbox("Select Subject", list(sub_map.keys()))
    selected_sub = sub_map[selected_label]
    sub_id = selected_sub['subject_id']
    
    title = st.text_input("Notice Title", placeholder="e.g. Unit 2 Assignment / Lab Manual")
    msg = st.text_area("Notice Message / Content", placeholder="Enter announcement text...")
    
    st.markdown("#### Attach Document / Resource")
    upload_tab, link_tab = st.tabs(["📁 Upload File (PDF / Doc / Img)", "🔗 External Web Link"])
    
    with upload_tab:
        uploaded_doc = st.file_uploader("Choose file from your device", type=['pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'])
        
    with link_tab:
        external_link = st.text_input("Or Paste Drive / Resource URL", placeholder="https://drive.google.com/...")
        
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    
    col_pub, col_clr = st.columns([2, 1.2], vertical_alignment="center")
    
    with col_pub:
        if st.button("Publish Notice", type="primary", use_container_width=True, icon=":material/campaign:"):
            if not title.strip() or not msg.strip():
                st.warning("Please provide both title and message.")
            else:
                final_doc_url = None
                with st.spinner("Publishing notice..."):
                    if uploaded_doc is not None:
                        final_doc_url = upload_notice_attachment(uploaded_doc.getvalue(), uploaded_doc.name)
                        if not final_doc_url:
                            st.error("Failed to upload document to storage. Check bucket permissions.")
                            return
                    elif external_link.strip():
                        final_doc_url = external_link.strip()
                        
                    if create_notice(sub_id, teacher_id, title, msg, final_doc_url):
                        st.toast("Notice broadcasted successfully!", icon="📢")
                        time.sleep(0.8)
                        st.rerun()
                    else:
                        st.error("Failed to save notice.")

    with col_clr:
        if st.button("Clear Past Notices", type="tertiary", use_container_width=True, icon=":material/delete:"):
            if clear_all_notices_by_teacher(teacher_id, sub_id):
                st.toast("All past notices for this subject deleted!", icon="🗑️")
                time.sleep(0.8)
                st.rerun()
            else:
                st.error("Failed to clear notices.")


def login_teacher(username, password):
    if not username or not password:
        return False
    teacher = teacher_login(username, password)
    if teacher:
        st.session_state.user_role = 'teacher' 
        st.session_state.teacher_data = teacher
        st.session_state.is_logged_in = True
        return True
    return False


def teacher_screen_login():
    _, center_col, _ = st.columns([1, 2.3, 1])
    
    with center_col:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            top_c1, top_c2 = st.columns([2.2, 1], vertical_alignment='center')
            with top_c1:
                header_dashboard()
            with top_c2:
                if st.button("Back", type='tertiary', key='teacher_back_btn', icon=":material/arrow_back:", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()

            st.divider()

            st.markdown("""
                <div style="text-align: center; margin-bottom: 22px; margin-top: 6px;">
                    <h2 style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; margin: 0;">Teacher Login</h2>
                    <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Enter your credentials to access your dashboard</p>
                </div>
            """, unsafe_allow_html=True)
            
            teacher_username = st.text_input("Username", placeholder="@VBGupta")
            teacher_pass = st.text_input("Password", type='password', placeholder="••••••••")
            
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            
            if st.button('Login', icon=':material/login:', type="secondary", use_container_width=True):
                if login_teacher(teacher_username, teacher_pass):
                    st.toast("Welcome Back!", icon="👋🏻")
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error("Invalid Username or Password ❌")
                    
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            if st.button('New Teacher? Register Here', type="primary", icon=':material/person_add:', use_container_width=True):
                st.session_state.teacher_login_type = 'register'
                st.rerun()
                
        footer_dashboard()


def teacher_screen_register():
    _, center_col, _ = st.columns([1, 2.3, 1])
    
    with center_col:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        with st.container(border=True):
            top_c1, top_c2 = st.columns([2.2, 1], vertical_alignment='center')
            with top_c1:
                header_dashboard()
            with top_c2:
                if st.button("Back", type='tertiary', key='teacher_reg_back_btn', icon=":material/arrow_back:", use_container_width=True):
                    st.session_state.clear()
                    st.rerun()

            st.divider()

            st.markdown("""
                <div style="text-align: center; margin-bottom: 22px; margin-top: 6px;">
                    <h2 style="font-size: 1.6rem; font-weight: 700; color: #FFFFFF; margin: 0;">Create Teacher Account</h2>
                    <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Fill details to register as an educator</p>
                </div>
            """, unsafe_allow_html=True)
            
            teacher_username = st.text_input("Username", placeholder='@VBGupta')
            teacher_name = st.text_input("Full Name", placeholder='Vaibhav Gupta')
            teacher_pass = st.text_input("Password", type='password', placeholder="••••••••")
            teacher_pass_confirm = st.text_input("Confirm Password", type='password', placeholder="••••••••")
            
            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
            
            if st.button('Register Now', icon=':material/check:', type="secondary", use_container_width=True):
                success, message = register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm)
                if success:
                    st.success(message)
                    time.sleep(1.2)
                    st.session_state.teacher_login_type = "login"
                    st.rerun()
                else:
                    st.error(message)
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            
            if st.button('Already have an account? Login', type="primary", icon=':material/login:', use_container_width=True):
                st.session_state.teacher_login_type = "login"
                st.rerun()
                
        footer_dashboard()


def register_teacher(teacher_username, teacher_name, teacher_pass, teacher_pass_confirm):
    if not teacher_username or not teacher_name or not teacher_pass:
        return False, "All fields are required!"
        
    if check_teacher_exists(teacher_username):
        return False, "Username already taken, please choose another."
        
    if teacher_pass != teacher_pass_confirm:
        return False, "Passwords do not match ❌"
        
    # Enforce Strong Password Criteria
    is_valid, validation_msg = validate_password_strength(teacher_pass)
    if not is_valid:
        return False, f"Weak Password: {validation_msg}"
    
    try:
        create_teacher(teacher_username, teacher_pass, teacher_name)
        return True, "Account successfully created! Please log in."
    except Exception:
        return False, "An error occurred during registration. Please try again."