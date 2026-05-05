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
# Use mtcnn=False for even more speed/less RAM on Render
detector = FER(mtcnn=False)

@app.route('/health')
def health():
    return jsonify({"status": "alive"})

@app.route('/')
def index():
    return "Emotion AI Backend is Running!"

@app.route('/detect', methods=['POST'])
def detect_emotion():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': 'No image data'}), 400
            
        image_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Detect emotions
        results = detector.detect_emotions(img)
        
        if results:
            # FER returns results in a slightly different format
            res = results[0]
            emotions = res['emotions']
            dominant_emotion = max(emotions, key=emotions.get)
            box = res['box'] # [x, y, w, h]
            
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
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
