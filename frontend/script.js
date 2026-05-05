const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const moodDisplay = document.getElementById('mood-display');
const emojiDisplay = document.getElementById('emoji-display');
const scoresContainer = document.getElementById('scores-container');
const moodHistory = document.getElementById('mood-history');
const moodQuote = document.getElementById('mood-quote');
const liveIndicator = document.getElementById('live-indicator');
const captureBtn = document.getElementById('capture-btn');
const detectionOverlay = document.getElementById('detection-overlay');
const scannerLine = document.getElementById('scanner-line');

// Hosting/API Config
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://127.0.0.1:5000'
    : 'https://your-backend-url.com'; // Change this when hosting backend

let stream = null;
let detectionInterval = null;
let history = [];
let isDetecting = false;
let isProcessing = false;

const moodQuotes = {
    happy: [
        "Happiness is not by chance, but by choice.",
        "The most important thing is to enjoy your life - to be happy.",
        "Smile! It's free therapy."
    ],
    sad: [
        "This too shall pass. Hang in there.",
        "It's okay not to be okay. Take your time.",
        "After every storm, there's a rainbow."
    ],
    angry: [
        "Take a deep breath. Don't let anger control you.",
        "For every minute you are angry, you lose sixty seconds of happiness.",
        "Calmness is a superpower."
    ],
    neutral: [
        "Peace begins with a smile.",
        "Stay balanced, stay focused.",
        "Neutrality is the perfect place for a fresh start."
    ],
    fear: [
        "Courage is not the absence of fear, but the triumph over it.",
        "Everything you've ever wanted is on the other side of fear.",
        "Believe in yourself."
    ],
    surprise: [
        "Life is full of surprises. Embrace them!",
        "Expect the unexpected.",
        "Every day is a new adventure."
    ],
    disgust: [
        "Focus on the positive things around you.",
        "Cleanse your thoughts, cleanse your soul.",
        "Choose beauty over bitterness."
    ]
};

const emotionEmojis = {
    angry: "😠",
    disgust: "🤢",
    fear: "😨",
    happy: "😊",
    sad: "😢",
    surprise: "😲",
    neutral: "😐"
};

const emotionColors = {
    angry: "#ef4444",
    disgust: "#10b981",
    fear: "#8b5cf6",
    happy: "#f59e0b",
    sad: "#3b82f6",
    surprise: "#ec4899",
    neutral: "#6366f1"
};

function updateQuote(emotion) {
    const quotes = moodQuotes[emotion] || moodQuotes['neutral'];
    const randomQuote = quotes[Math.floor(Math.random() * quotes.length)];
    moodQuote.innerHTML = `
        <div class="quote-text">"${randomQuote}"</div>
        <span class="quote-author">- Emotion AI Insight</span>
    `;
}

function addToHistory(emotion) {
    // Only add to history if emotion has changed to avoid "bhar bhar ke" logs
    if (history.length > 0 && history[0].emotion === emotion) return;

    const now = new Date();
    const time = now.getHours().toString().padStart(2, '0') + ":" + 
                 now.getMinutes().toString().padStart(2, '0') + ":" + 
                 now.getSeconds().toString().padStart(2, '0');
    
    history.unshift({ emotion, time });
    if (history.length > 10) history.pop(); // Keep last 10 detections
    
    moodHistory.innerHTML = history.map(item => `
        <li class="history-item">
            <span>${item.emotion.charAt(0).toUpperCase() + item.emotion.slice(1)}</span>
            <span class="history-time">${item.time}</span>
        </li>
    `).join('');
}

async function setupCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        return true;
    } catch (err) {
        console.error("Error accessing camera:", err);
        alert("Camera access denied or not available.");
        return false;
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
}

async function captureAndDetect() {
    if (!isDetecting || isProcessing) return;
    isProcessing = true;
    
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    const imageData = canvas.toDataURL('image/jpeg');
    
    try {
        const response = await fetch(`${API_URL}/detect`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ image: imageData }),
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            updateUI(data.emotion, data.scores);
            drawBox(data.region);
        } else if (data.status === 'no_face') {
            moodDisplay.innerText = "No Face Detected";
            scoresContainer.innerHTML = "";
            detectionOverlay.style.display = 'none';
        }
    } catch (err) {
        console.error("Detection error:", err);
    } finally {
        isProcessing = false;
    }
}

function drawBox(region) {
    if (!region) return;
    
    const videoWidth = video.offsetWidth;
    const videoHeight = video.offsetHeight;
    const naturalWidth = video.videoWidth;
    const naturalHeight = video.videoHeight;
    
    const scaleX = videoWidth / naturalWidth;
    const scaleY = videoHeight / naturalHeight;
    
    detectionOverlay.style.display = 'block';
    detectionOverlay.style.width = (region.w * scaleX) + 'px';
    detectionOverlay.style.height = (region.h * scaleY) + 'px';
    detectionOverlay.style.left = (region.x * scaleX) + 'px';
    detectionOverlay.style.top = (region.y * scaleY) + 'px';
}

function speak(text) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1;
        utterance.pitch = 1;
        window.speechSynthesis.speak(utterance);
    }
}

function updateUI(emotion, scores) {
    if (history.length === 0 || history[0].emotion !== emotion) {
        speak(`You look ${emotion}`);
    }
    moodDisplay.innerText = emotion.charAt(0).toUpperCase() + emotion.slice(1);
    emojiDisplay.innerText = emotionEmojis[emotion] || "✨";
    
    // Update primary color but keep background same
    const color = emotionColors[emotion] || "#6366f1";
    document.documentElement.style.setProperty('--primary', color);

    addToHistory(emotion);
    updateQuote(emotion);

    scoresContainer.innerHTML = '';
    Object.entries(scores).forEach(([emo, score]) => {
        const percentage = (score * 100).toFixed(1);
        const row = document.createElement('div');
        row.className = 'score-row';
        row.innerHTML = `
            <div class="score-label">
                <span>${emo}</span>
                <span>${percentage}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${percentage}%"></div>
            </div>
        `;
        scoresContainer.appendChild(row);
    });
}

startBtn.addEventListener('click', async () => {
    const success = await setupCamera();
    if (success) {
        startBtn.disabled = true;
        stopBtn.disabled = false;
        captureBtn.disabled = false;
        isDetecting = true;
        liveIndicator.classList.add('active');
        scannerLine.style.display = 'block';
        
        // Start detection every 2 seconds (giving backend time)
        detectionInterval = setInterval(captureAndDetect, 2000);
    }
});

stopBtn.addEventListener('click', () => {
    isDetecting = false;
    liveIndicator.classList.remove('active');
    scannerLine.style.display = 'none';
    detectionOverlay.style.display = 'none';
    stopCamera();
    clearInterval(detectionInterval);
    startBtn.disabled = false;
    stopBtn.disabled = true;
    captureBtn.disabled = true;
    moodDisplay.innerText = "Waiting...";
    emojiDisplay.innerText = "✨";
    moodQuote.innerText = "Start detection to get an insight...";
    scoresContainer.innerHTML = "";
});

captureBtn.addEventListener('click', () => {
    const context = canvas.getContext('2d');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Add text overlay to screenshot
    context.font = "30px Arial";
    context.fillStyle = "white";
    context.strokeStyle = "black";
    context.lineWidth = 2;
    const text = `Mood: ${moodDisplay.innerText} ${emojiDisplay.innerText}`;
    context.strokeText(text, 20, 50);
    context.fillText(text, 20, 50);

    const link = document.createElement('a');
    link.download = `emotion-snapshot-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
});
