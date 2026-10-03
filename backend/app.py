import os
import sys
import cv2
import numpy as np
import base64
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd 

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

app = Flask(__name__, static_folder='../frontend')
CORS(app)

detector = None
is_model_loading = False

def load_model():
    global detector, is_model_loading
    if detector is None and not is_model_loading:
        is_model_loading = True
        try:
            print("\n" + "="*50)
            print("LOADING AI MODELS (Please wait...)")
            print("This might take 30-60 seconds on first run.")
            print("="*50)
            
            from deepface import DeepFace
            dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
            DeepFace.analyze(dummy_img, actions=['emotion'], enforce_detection=False)
            
            detector = DeepFace
            print("="*50)
            print("AI MODELS LOADED SUCCESSFULLY!")
            print("="*50 + "\n")
        except Exception as e:
            print(f"CRITICAL ERROR LOADING MODEL: {e}")
        finally:
            is_model_loading = False

@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)

@app.route('/health')
def health():
    if detector is None:
        return jsonify({"status": "loading", "message": "AI Model is still loading..."})
    return jsonify({"status": "online", "message": "Server is ready"})

@app.route('/status')
def status():
    return jsonify({"status": "online", "message": "Server is running"})

@app.route('/detect', methods=['POST'])
def detect_emotion():
    if detector is None:
        return jsonify({'status': 'loading', 'message': 'AI Model is still loading. Please wait a few seconds.'}), 503
        
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': 'No image data'}), 400

        try:
            image_data = data['image'].split(',')[1]
            nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Image decoding failed: {str(e)}'}), 400

        if img is None:
            return jsonify({'status': 'error', 'message': 'Invalid image format'}), 400

        results = detector.analyze(img, actions=['emotion'], enforce_detection=False)

        if not results:
            return jsonify({'face_detected': False, 'status': 'no_face'})

        res = results[0]
        if res.get('face_confidence', 0) < 0.25:
            return jsonify({'face_detected': False, 'status': 'no_face'})

        emotions = res['emotion']
        region = res['region']
        
        target_emotions = ['happy', 'sad', 'neutral', 'angry', 'surprise', 'fear']
        
        raw_happy = float(emotions.get('happy', 0))
        raw_sad = float(emotions.get('sad', 0))
        raw_neutral = float(emotions.get('neutral', 0))
        raw_angry = float(emotions.get('angry', 0))
        raw_surprise = float(emotions.get('surprise', 0))
        raw_fear = float(emotions.get('fear', 0))
        
        raw_happy *= 1.3
        raw_sad *= 1.2
        raw_angry *= 1.25
        raw_surprise *= 1.4
        raw_fear *= 1.2
        raw_neutral *= 0.7

        emotion_values = [
            ('happy', raw_happy),
            ('sad', raw_sad),
            ('angry', raw_angry),
            ('surprise', raw_surprise),
            ('fear', raw_fear),
            ('neutral', raw_neutral)
        ]
        
        emotion_values.sort(key=lambda x: x[1], reverse=True)
        dominant_emotion = emotion_values[0][0]

        filtered_scores = {k: float(emotions.get(k, 0)) for k in target_emotions}
        total_score = sum(filtered_scores.values())
        if total_score > 0:
            scores = {k: v / total_score for k, v in filtered_scores.items()}
        else:
            scores = {'happy': 0.0, 'sad': 0.0, 'neutral': 1.0, 'angry': 0.0, 'surprise': 0.0, 'fear': 0.0}

        intensity = "normal"
        if dominant_emotion == 'happy' and raw_happy > 50:
            intensity = "high"
        elif dominant_emotion == 'sad' and raw_sad > 40:
            intensity = "high"
        elif raw_neutral < 30:
            intensity = "low"

        print(f"DEBUG: Emotion={dominant_emotion} Happy={raw_happy:.1f} Neutral={raw_neutral:.1f}")

        return jsonify({
            'status': 'success',
            'face_detected': True,
            'emotion': dominant_emotion,
            'intensity': intensity,
            'scores': scores,
            'face': {
                'x': int(region['x']),
                'y': int(region['y']),
                'w': int(region['w']),
                'h': int(region['h'])
            }
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    import threading
    threading.Thread(target=load_model).start()
    
    print("\nEMOTION AI SERVER STARTING...")
    print("URL: http://localhost:8000")
    app.run(host='0.0.0.0', port=8000, debug=False)
