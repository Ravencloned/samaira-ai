/**
 * SamairaAI - Voice Input Handler
 * Handles microphone recording and voice-to-text functionality
 */

// Voice Recording State
const VoiceState = {
    isRecording: false,
    mediaRecorder: null,
    audioChunks: [],
    stream: null
};

// Initialize voice functionality
document.addEventListener('DOMContentLoaded', initVoice);

function initVoice() {
    const micBtn = document.getElementById('mic-btn');
    const recordingStatus = document.getElementById('recording-status');
    
    // Check for microphone support
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Microphone not supported');
        micBtn.disabled = true;
        micBtn.title = 'Microphone not supported in this browser';
        return;
    }
    
    // Click to toggle recording (better for mobile)
    micBtn.addEventListener('click', () => {
        if (VoiceState.isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
    
    console.log('Voice input initialized');
}

async function startRecording() {
    if (VoiceState.isRecording) return;
    
    const micBtn = document.getElementById('mic-btn');
    const recordingStatus = document.getElementById('recording-status');
    
    try {
        // Request microphone access
        VoiceState.stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });
        
        // Create MediaRecorder
        VoiceState.mediaRecorder = new MediaRecorder(VoiceState.stream, {
            mimeType: getSupportedMimeType()
        });
        
        VoiceState.audioChunks = [];
        
        VoiceState.mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                VoiceState.audioChunks.push(event.data);
            }
        };
        
        VoiceState.mediaRecorder.onstop = handleRecordingComplete;
        
        // Start recording
        VoiceState.mediaRecorder.start();
        VoiceState.isRecording = true;
        
        // Update UI
        micBtn.classList.add('recording');
        recordingStatus.classList.remove('hidden');
        
        console.log('Recording started');
        
    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Microphone access denied. Please allow microphone access to use voice input.');
    }
}

function stopRecording() {
    if (!VoiceState.isRecording) return;
    
    const micBtn = document.getElementById('mic-btn');
    const recordingStatus = document.getElementById('recording-status');
    
    // Stop recording
    if (VoiceState.mediaRecorder && VoiceState.mediaRecorder.state !== 'inactive') {
        VoiceState.mediaRecorder.stop();
    }
    
    // Stop all tracks
    if (VoiceState.stream) {
        VoiceState.stream.getTracks().forEach(track => track.stop());
    }
    
    VoiceState.isRecording = false;
    
    // Update UI
    micBtn.classList.remove('recording');
    recordingStatus.classList.add('hidden');
    
    console.log('Recording stopped');
}

async function handleRecordingComplete() {
    if (VoiceState.audioChunks.length === 0) {
        console.warn('No audio recorded');
        return;
    }
    
    // Create audio blob
    const mimeType = getSupportedMimeType();
    const audioBlob = new Blob(VoiceState.audioChunks, { type: mimeType });
    
    // Check if audio is too short (likely accidental click)
    if (audioBlob.size < 1000) {
        console.warn('Recording too short, ignoring');
        return;
    }
    
    console.log('Audio recorded:', audioBlob.size, 'bytes');
    
    // Send to backend for processing
    await processVoiceInput(audioBlob);
}

async function processVoiceInput(audioBlob) {
    // Show chat area
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatMessages = document.getElementById('chat-messages');
    
    welcomeScreen.classList.add('hidden');
    chatMessages.classList.remove('hidden');
    
    // Show processing indicator
    showTyping(true);
    
    try {
        // Create form data
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        if (AppState.sessionId) {
            formData.append('session_id', AppState.sessionId);
        }
        
        // Send to voice chat endpoint
        const response = await fetch(`${API_BASE}/voice/chat`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Hide typing indicator
        showTyping(false);
        
        // Update session ID
        if (data.session_id) {
            AppState.sessionId = data.session_id;
        }
        
        // Show transcript as user message
        if (data.transcript) {
            addMessageToUI('user', data.transcript);
        }
        
        // Show AI response
        addMessageToUI('ai', data.response, {
            intent: data.intent,
            handoffRequested: data.handoff_requested,
            ttsText: data.tts_text
        });
        
        // Speak response
        if (AppState.ttsEnabled && data.tts_text) {
            speakText(data.tts_text);
        }
        
    } catch (error) {
        console.error('Error processing voice:', error);
        showTyping(false);
        addMessageToUI('ai', 'Maaf kijiye, aapki awaaz process karne mein problem hui. Kya aap phir se try kar sakte hain?');
    }
}

// Utility function to get supported audio mime type
function getSupportedMimeType() {
    const types = [
        'audio/webm;codecs=opus',
        'audio/webm',
        'audio/ogg;codecs=opus',
        'audio/mp4',
        'audio/wav'
    ];
    
    for (const type of types) {
        if (MediaRecorder.isTypeSupported(type)) {
            return type;
        }
    }
    
    return 'audio/webm'; // Fallback
}

// Alternative: Click-to-record mode (toggle recording)
function toggleRecordingMode() {
    const micBtn = document.getElementById('mic-btn');
    
    // Remove push-to-talk listeners
    micBtn.removeEventListener('mousedown', startRecording);
    micBtn.removeEventListener('mouseup', stopRecording);
    micBtn.removeEventListener('mouseleave', stopRecording);
    
    // Add click toggle listener
    micBtn.addEventListener('click', () => {
        if (VoiceState.isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });
}

// Export for use in app.js
window.VoiceState = VoiceState;
window.startRecording = startRecording;
window.stopRecording = stopRecording;
