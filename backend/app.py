import os
import sys

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import warnings
warnings.filterwarnings("ignore")

try:
    try:
        from fer import FER
    except ImportError:
        from fer.fer import FER
    import cv2
    import numpy as np
    import base64
except ImportError as e:
    print(f"Error importing libraries: {e}")
    sys.exit(1)

# Absolute path setup
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

print(f"Base Directory: {BASE_DIR}")
print(f"Frontend Directory: {FRONTEND_DIR}")

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')
CORS(app)

# Lazy load detector
detector = None

def get_detector():
    global detector
    if detector is None:
        print("Loading AI Model...")
        detector = FER(mtcnn=False)
        print("AI Model Loaded!")
    return detector

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    return jsonify({"status": "alive", "backend": "Render"})

@app.route('/detect', methods=['POST'])
def detect_emotion():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': 'No image data'}), 400
            
        image_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        det = get_detector()
        results = det.detect_emotions(img)
        
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
                    'x': int(box[0]), 'y': int(box[1]), 'w': int(box[2]), 'h': int(box[3])
                }
            })
        else:
            return jsonify({'status': 'no_face', 'message': 'No face detected'})
            
    except Exception as e:
        print(f"Detection Error: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

# Catch-all route for other static files
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"Starting server on port {port}...")
    app.run(host='0.0.0.0', port=port)
