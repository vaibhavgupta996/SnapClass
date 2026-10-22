from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io
import librosa
import streamlit as st

@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()

def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        wav = preprocess_wav(audio)
        if len(wav) == 0:
            return None
        embedding = encoder.embed_utterance(wav)
        # Normalize vector
        embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
        return embedding.tolist()
    except Exception as e:
        st.error(f"Voice Recognition Error: {e}")
        return None

def identify_speaker(new_embedding, candidate_dict, threshold=0.38):
    if new_embedding is None or not candidate_dict:
        return None, 0.0
    
    best_sid = None
    best_score = -1.0
    new_emb_np = np.array(new_embedding)
    new_emb_norm = new_emb_np / (np.linalg.norm(new_emb_np) + 1e-10)
    
    for sid, stored_embedding in candidate_dict.items():
        if stored_embedding:
            stored_emb_np = np.array(stored_embedding)
            stored_norm = stored_emb_np / (np.linalg.norm(stored_emb_np) + 1e-10)
            
            # Normalized Cosine Similarity
            similarity = float(np.dot(new_emb_norm, stored_norm))
            
            if similarity > best_score:
                best_score = similarity
                best_sid = sid
                
    if best_score >= threshold:
        return best_sid, best_score
    
    return None, best_score

def process_bulk_audio(audio_bytes, candidate_dict, threshold=0.38):
    try:
        encoder = load_voice_encoder()
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)
        
        if len(audio) < sr * 0.3:
            return {}
        
        # Non-silent speech segments split
        segments = librosa.effects.split(audio, top_db=18, frame_length=1024, hop_length=256)
        
        audio_chunks = []
        if len(segments) > 0:
            for start, end in segments:
                # 0.3s se bada koi bhi sound chunk (Present, Yes, Present Sir)
                if (end - start) >= sr * 0.3:
                    audio_chunks.append(audio[start:end])
        
        # Fallback overlapping windows agar split ek hi bada chunk de
        if len(audio_chunks) <= 1 and len(audio) > sr * 1.0:
            audio_chunks = []
            window_size = int(sr * 1.0)
            step_size = int(sr * 0.5)
            for i in range(0, len(audio) - window_size + 1, step_size):
                audio_chunks.append(audio[i : i + window_size])

        identified_results = {}
        
        for chunk in audio_chunks:
            wav = preprocess_wav(chunk)
            if len(wav) == 0:
                continue
            embedding = encoder.embed_utterance(wav)
            embedding = embedding / (np.linalg.norm(embedding) + 1e-10)
            
            sid, score = identify_speaker(embedding, candidate_dict, threshold=threshold)
            if sid is not None:
                sid_int = int(sid)
                if sid_int not in identified_results or score > identified_results[sid_int]:
                    identified_results[sid_int] = score
                    
        return identified_results
    
    except Exception as e:
        st.error(f"Bulk Process Error: {e}")
        return {}