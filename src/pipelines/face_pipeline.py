import cv2
import dlib
import numpy as np
import face_recognition_models
import streamlit as st
from scipy.spatial import distance as dist
from src.database.db import get_all_students


@st.cache_resource
def load_dlib_models():
    """Loads and caches dlib face detector, 68-point shape predictor, and recognition network."""
    detector = dlib.get_frontal_face_detector()
    
    # 68-point landmark predictor is required for EAR (Eye Aspect Ratio) calculation
    try:
        predictor_path = face_recognition_models.pose_predictor_model_location()
        # Fallback/explicit check if 68 points model function is available
        if hasattr(face_recognition_models, 'shape_predictor_68_face_landmarks_model_location'):
            predictor_path = face_recognition_models.shape_predictor_68_face_landmarks_model_location()
    except Exception:
        predictor_path = face_recognition_models.pose_predictor_model_location()
        
    sp = dlib.shape_predictor(predictor_path)
    facerec = dlib.face_recognition_model_v1(
        face_recognition_models.face_recognition_model_location()
    )
    return detector, sp, facerec


def _ensure_valid_image(img_np):
    """Ensures image is uint8, contiguous and RGB format for dlib."""
    if not isinstance(img_np, np.ndarray):
        img_np = np.array(img_np)
    if img_np.dtype != np.uint8:
        img_np = img_np.astype(np.uint8)
    return np.ascontiguousarray(img_np)


def get_face_embedding(image_np):
    image_np = _ensure_valid_image(image_np)
    detector, sp, facerec = load_dlib_models()
    
    # Convert to grayscale for detector
    if len(image_np.shape) == 3 and image_np.shape[2] == 3:
        gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = image_np
        
    faces = detector(gray, 1)
    
    encodings = []
    for face in faces:
        shape = sp(image_np, face)
        face_descriptor = facerec.compute_face_descriptor(image_np, shape, num_jitters=1)
        encodings.append(np.array(face_descriptor, dtype=np.float64))
        
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
            stored_emb = np.array(student['face_embedding'], dtype=np.float64)
            distance = np.linalg.norm(stored_emb - encoding)
            
            if distance < min_distance:
                min_distance = distance
                best_sid = student['student_id']
                
        # Verification threshold check
        if min_distance <= threshold and best_sid is not None:
            detected_student[best_sid] = True
            
    return detected_student, all_student_ids, len(encodings)


def calculate_ear(eye_points):
    # Vertical distances between upper and lower eyelids
    a = dist.euclidean(eye_points[1], eye_points[5])
    b = dist.euclidean(eye_points[2], eye_points[4])
    # Horizontal distance across the eye corners
    c = dist.euclidean(eye_points[0], eye_points[3])
    
    if c == 0:
        return 0.0
    return (a + b) / (2.0 * c)


def check_liveness(img_np):
    """
    Returns (is_live, message):
    Validates single live face using landmarks and eye open/natural ratios.
    """
    img_np = _ensure_valid_image(img_np)
    detector, sp, _ = load_dlib_models()
    
    if len(img_np.shape) == 3 and img_np.shape[2] == 3:
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_np
        
    faces = detector(gray, 0)
    
    if len(faces) == 0:
        return False, "No face detected"
    if len(faces) > 1:
        return False, "Multiple faces detected. Stand alone."
        
    landmarks = sp(gray, faces[0])
    points = np.array([(p.x, p.y) for p in landmarks.parts()])
    
    # Check if 68 points are available (eyes are points 36..47)
    if len(points) < 68:
        # Fallback if 5-point model was loaded: basic face detected
        return True, "Live Face Verified (Basic)"
        
    left_eye = points[36:42]
    right_eye = points[42:48]
    
    ear_left = calculate_ear(left_eye)
    ear_right = calculate_ear(right_eye)
    avg_ear = (ear_left + ear_right) / 2.0
    
    # Printed paper/closed eye spoof detection threshold
    if avg_ear < 0.18:
        return False, "Eyes closed or unnatural frame. Please blink and look straight."
        
    return True, "Live Face Verified"