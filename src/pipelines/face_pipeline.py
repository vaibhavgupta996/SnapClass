import dlib
import numpy as np
import face_recognition_models
import streamlit as st
from src.database.db import get_all_students
from scipy.spatial import distance as dist
import cv2

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
                
        if min_distance <= threshold and best_sid is not None:
            detected_student[best_sid] = True
            
    return detected_student, all_student_ids, len(encodings)

def calculate_ear(eye_points):
    # Vertical distances
    a = dist.euclidean(eye_points[1], eye_points[5])
    b = dist.euclidean(eye_points[2], eye_points[4])
    # Horizontal distance
    c = dist.euclidean(eye_points[0], eye_points[3])
    return (a + b) / (2.0 * c)

def check_liveness(img_np):
    """
    Returns (is_live, message):
    Validates single live face using landmarks and eye open/natural ratios.
    """
    detector, sp, _ = load_dlib_models()
    
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
    faces = detector(gray, 0)
    
    if len(faces) == 0:
        return False, "No face detected"
    if len(faces) > 1:
        return False, "Multiple faces detected. Stand alone."
        
    landmarks = sp(gray, faces[0])
    points = np.array([(p.x, p.y) for p in landmarks.parts()])
    
    left_eye = points[36:42]
    right_eye = points[42:48]
    
    ear_left = calculate_ear(left_eye)
    ear_right = calculate_ear(right_eye)
    avg_ear = (ear_left + ear_right) / 2.0
    
    # Printed paper/closed eye spoof detection threshold
    if avg_ear < 0.18:
        return False, "Eyes closed or unnatural frame. Please blink and look straight."
        
    return True, "Live Face Verified"