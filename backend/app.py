import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logs

from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
warnings.filterwarnings("ignore") # Suppress warnings

from deepface import DeepFace
import cv2
import numpy as np
import base64
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}) # Explicitly allow all origins

@app.route('/health')
def health():
    return jsonify({"status": "alive"})

@app.route('/')
def index():
    return """
    <html>
        <body style="font-family: sans-serif; text-align: center; padding-top: 50px; background: #0f172a; color: white;">
            <h1>Emotion AI Backend is Running</h1>
            <p>This is the API server. To see the actual App UI, please go to:</p>
            <a href="http://localhost:8000" style="color: #6366f1; font-size: 20px; text-decoration: none; border: 1px solid #6366f1; padding: 10px 20px; border-radius: 5px;">Open App UI (Port 8000)</a>
        </body>
    </html>
    """

@app.route('/detect', methods=['POST'])
def detect_emotion():
    try:
        data = request.json
        image_data = data['image'].split(',')[1]
        
        # Decode base64 image
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Save temporary image for DeepFace (it prefers file paths or numpy arrays)
        # DeepFace.analyze can take numpy array directly
        results = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
        
        if results:
            # DeepFace returns a list of results (one for each face)
            res = results[0]
            dominant_emotion = res['dominant_emotion']
            # Convert float32 to standard float for JSON serialization
            emotion_scores = {k: float(v) for k, v in res['emotion'].items()}
            face_region = res['region'] # Get face coordinates
            
            # DeepFace emotion keys are slightly different (e.g., 'happy', 'sad', etc.)
            return jsonify({
                'status': 'success',
                'emotion': dominant_emotion,
                'scores': emotion_scores,
                'region': face_region
            })
        else:
            return jsonify({
                'status': 'no_face',
                'message': 'No face detected'
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error detail: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    # DeepFace might download models on first run
    print("Starting Emotion Detection Server...")
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
