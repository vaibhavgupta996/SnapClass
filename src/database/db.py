from src.database.config import supabase
import bcrypt
import uuid

def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

def check_pss(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(), hashed.encode())

def check_teacher_exists(username):
    response=supabase.table("teachers").select("username").eq("username",username).execute()
    return len(response.data)>0

def create_teacher(username,password,name):
    data={"username":username, "password":hash_pass(password), "name":name}
    response=supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username,password):
    response=supabase.table("teachers").select("*").eq("username",username).execute()
    if response.data:
        teacher=response.data[0]
        if check_pss(password,teacher['password']):
            return teacher
    return None

def get_all_students():
    response=supabase.table('students').select("*").execute()
    return response.data

def create_student(new_name,face_embedding=None,voice_embedding=None):
    data={'name':new_name, 'face_embedding':face_embedding, 'voice_embedding':voice_embedding}
    response=supabase.table('students').insert(data).execute()
    return response.data

def create_subject(subject_code,name,section,teacher_id):
    data={"subject_code":subject_code, "name":name, "section":section, "teacher_id":teacher_id}
    response=supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subjects(teacher_id):
    response=supabase.table('subjects').select("*, subject_students(count), attendence_logs(timestamp)").eq("teacher_id", teacher_id).execute()
    subjects=response.data
    
    for sub in subjects:
        sub['total_students']=sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendence = sub.get('attendence_logs', [])
        unique_sessions = len(set(log['timestamp'] for log in attendence))
        sub['total_classes']=unique_sessions
        
        sub.pop('subject_students', None)
        sub.pop('attendence_logs', None)
        
    return subjects

def enroll_student_to_subject(student_id, subject_id):
    data={'student_id':student_id, "subject_id":subject_id}
    response=supabase.table('subject_students').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id, subject_id):
    response=supabase.table('subject_students').delete().eq('student_id', student_id).eq('subject_id', subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    response=supabase.table('subject_students').select('*, subjects(*)').eq('student_id',student_id).execute()
    return response.data

def get_student_attendance(student_id):
    response=supabase.table('attendence_logs').select('*, subjects(*)').eq('student_id',student_id).execute()
    return response.data

def create_attendance(logs):
    response=supabase.table('attendence_logs').insert(logs).execute()
    return response.data

def get_attendance_for_teacher(teacher_id):
    response=supabase.table('attendence_logs').select("*, subjects!inner(*)").eq('subjects.teacher_id', teacher_id).execute()
    return response.data

def get_enrolled_students_by_subject(subject_id: int):
    try:
        response = supabase.table('subject_students').select("*, students(*)").eq('subject_id', subject_id).execute()
        return response.data or []
    except Exception as e:
        print(f"Error fetching enrolled students: {e}")
        return []
    
def get_session_attendance_details(teacher_id: int, subject_id: int, timestamp: str):
    try:
        res = (
            supabase.table('attendence_logs')
            .select("student_id, is_present, status, excuse_note, timestamp, students(student_id, name)")
            .eq('subject_id', subject_id)
            .eq('timestamp', timestamp)
            .execute()
        )
        
        output = []
        for r in (res.data or []):
            st_info = r.get('students') or {}
            sid = r.get('student_id') or st_info.get('student_id')
            sname = st_info.get('name') or f"Student #{sid}"
            is_p = bool(r.get('is_present', False))
            st_val = r.get('status') or ('Present' if is_p else 'Absent')
            
            output.append({
                "student_id": sid,
                "Name": sname,
                "Status": st_val,
                "is_present": is_p,
                "excuse_note": r.get('excuse_note')
            })
        return output
    except Exception as e:
        print(f"Error fetching session details: {e}")
        return []
    
# --- Leave Management & Manual Override ---
def update_student_attendance_status(subject_id: int, student_id: int, timestamp: str, status: str, excuse_note: str = None):
    try:
        is_pres = (status == "Present")
        res = supabase.table('attendence_logs').update({
            "status": status,
            "is_present": is_pres,
            "excuse_note": excuse_note if excuse_note and excuse_note.strip() else None
        }).eq('subject_id', subject_id).eq('student_id', student_id).eq('timestamp', timestamp).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Error updating status: {e}")
        return False

# --- Teacher Broadcast Notices ---
def create_notice(subject_id: int, teacher_id: int, title: str, message: str, doc_url: str = None):
    try:
        res = supabase.table('subject_notices').insert({
            "subject_id": subject_id,
            "teacher_id": teacher_id,
            "title": title,
            "message": message,
            "doc_url": doc_url
        }).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Error creating notice: {e}")
        return False

def get_student_notices(student_id: int):
    try:
        enrolled = supabase.table('subject_students').select("subject_id").eq('student_id', student_id).execute()
        sub_ids = [s['subject_id'] for s in (enrolled.data or [])]
        if not sub_ids:
            return []
        
        notices = supabase.table('subject_notices').select("*, subjects(name, subject_code)").in_('subject_id', sub_ids).order('created_at', desc=True).execute()
        return notices.data or []
    except Exception as e:
        print(f"Error fetching student notices: {e}")
        return []

def upload_notice_attachment(file_bytes, file_name: str):
    """Uploads document/file to Supabase Storage and returns clean public URL string."""
    try:
        clean_name = file_name.replace(" ", "_")
        unique_file_path = f"{uuid.uuid4().hex[:8]}_{clean_name}"
        
        # Upload file directly as raw bytes
        res = supabase.storage.from_("notice_attachments").upload(
            path=unique_file_path,
            file=file_bytes,
            file_options={"content-type": "application/octet-stream", "upsert": "true"}
        )
        
        # Get public url safely
        public_url = supabase.storage.from_("notice_attachments").get_public_url(unique_file_path)
        
        if isinstance(public_url, dict):
            return public_url.get('publicUrl') or public_url.get('public_url')
        return str(public_url)
    except Exception as e:
        print(f"[SnapClass Storage Error]: {e}")
        return None
    
def clear_all_notices_by_teacher(teacher_id: int, subject_id: int = None):
    try:
        query = supabase.table('subject_notices').delete().eq('teacher_id', teacher_id)
        if subject_id:
            query = query.eq('subject_id', subject_id)
        query.execute()
        return True
    except Exception as e:
        print(f"Error clearing notices: {e}")
        return False