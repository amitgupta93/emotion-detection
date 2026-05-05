import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, request, jsonify
from flask_cors import CORS
import warnings
warnings.filterwarnings("ignore")

from fer import FER
import cv2
import numpy as np
import base64

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize detector globally for performance
detector = FER(mtcnn=False)

@app.route('/api/health')
@app.route('/health')
def health():
    return jsonify({"status": "alive"})

@app.route('/api/detect', methods=['POST'])
@app.route('/detect', methods=['POST'])
def detect_emotion():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': 'No image data'}), 400
            
        image_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        results = detector.detect_emotions(img)
        
        if results:
            res = results[0]
            emotions = res['emotions']
            dominant_emotion = max(emotions, key=emotions.get)
            box = res['box']
            
            return jsonify({
                'status': 'success',
                'emotion': dominant_emotion,
                'scores': {k: float(v) for k, v in emotions.items()},
                'region': {
                    'x': int(box[0]),
                    'y': int(box[1]),
                    'w': int(box[2]),
                    'h': int(box[3])
                }
            })
        else:
            return jsonify({
                'status': 'no_face',
                'message': 'No face detected'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

# For Vercel, we need to export the app as 'app'
# No need for app.run() in serverless
