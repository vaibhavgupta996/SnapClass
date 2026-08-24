import dlib
import numpy as np
import face_recognition_models
import streamlit as st
from src.database.db import get_all_students

@st.cache_resource
def load_dlib_models():
    detector = dlib.get_frontal_face_detector()
    sp = dlib.shape_predictor(
        face_recognition_models.pose_predictor_model_location()
    )
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec

def get_face_embedding(image_np):
    detector, sp, facerec = load_dlib_models()
    faces = detector(image_np, 1)
    
    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, 1)
        encodings.append(np.array(face_descriptor))
    return encodings

def train_classifier():
    return True

def predict_attendence(class_image_np, threshold=0.50):
    encodings = get_face_embedding(class_image_np)
    detected_student = {}
    
    student_db = get_all_students()
    if not student_db or len(encodings) == 0:
        return detected_student, [], len(encodings)

    valid_students = [s for s in student_db if s.get('face_embedding') is not None]
    all_student_ids = [s['student_id'] for s in valid_students]

    if not valid_students:
        return detected_student, [], len(encodings)

    for encoding in encodings:
        best_sid = None
        min_distance = float('inf')
        
        for student in valid_students:
            stored_emb = np.array(student['face_embedding'])
            distance = np.linalg.norm(stored_emb - encoding)
            
            if distance < min_distance:
                min_distance = distance
                best_sid = student['student_id']
                
        # Jab face sach mein match hoga tabhi detect karega
        if min_distance <= threshold and best_sid is not None:
            detected_student[best_sid] = True
            
    return detected_student, all_student_ids, len(encodings)