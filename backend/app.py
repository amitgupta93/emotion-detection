import os
import sys

# Suppress TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import warnings
warnings.filterwarnings("ignore")

try:
    # Try both import styles for FER
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

# Set static folder to frontend directory correctly for Localhost
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.join(os.path.dirname(current_dir), 'frontend')

app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
CORS(app)

# Initialize detector globally for stability
print("Initializing AI Model (FER)...")
detector = FER(mtcnn=False)
print("AI Model Ready!")

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/health')
def health():
    return jsonify({"status": "alive", "mode": "localhost"})

@app.route('/detect', methods=['POST'])
def detect_emotion():
    try:
        data = request.json
        if not data or 'image' not in data:
            return jsonify({'status': 'error', 'message': 'No image data'}), 400
            
        image_data = data['image'].split(',')[1]
        nparr = np.frombuffer(base64.b64decode(image_data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'status': 'error', 'message': 'Invalid image'}), 400

        # Detect emotions
        results = detector.detect_emotions(img)
        
        if results:
            res = results[0]
            emotions = res['emotions']
            dominant_emotion = max(emotions, key=emotions.get)
            box = res['box'] # [x, y, w, h]
            
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

# Catch-all route for static files
@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    # Use 0.0.0.0 so you can access from mobile via Computer IP
    print("Starting Localhost Server...")
    app.run(host='0.0.0.0', port=5000, debug=True)
