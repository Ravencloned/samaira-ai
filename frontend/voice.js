/**
 * SamairaAI - Voice Input Handler
 * Handles microphone recording and speech-to-text
 */

// Voice State
const VoiceState = {
    isRecording: false,
    isSpeaking: false,
    isProcessing: false,
    conversationMode: true,  // Auto-listen after AI speaks
    mediaRecorder: null,
    audioChunks: [],
    stream: null,
    currentAudio: null,      // ElevenLabs audio element
    currentUtterance: null   // Browser TTS utterance
};

// Stop any ongoing TTS immediately
function stopSpeaking() {
    VoiceState.isSpeaking = false;
    
    // Stop ElevenLabs audio
    if (VoiceState.currentAudio) {
        VoiceState.currentAudio.pause();
        VoiceState.currentAudio.currentTime = 0;
        VoiceState.currentAudio = null;
    }
    
    // Stop browser TTS
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
    }
    VoiceState.currentUtterance = null;
    
    // Update visual state
    updateVoiceStatusUI('');
    console.log('🔇 TTS stopped');
}

// Called when AI finishes speaking (for conversation mode)
function onSpeechComplete() {
    VoiceState.isSpeaking = false;
    updateVoiceStatusUI('');
    
    // Auto-start listening in conversation mode
    if (VoiceState.conversationMode && !VoiceState.isRecording && !VoiceState.isProcessing) {
        setTimeout(() => {
            if (!VoiceState.isRecording && !VoiceState.isSpeaking) {
                startRecording();
            }
        }, 500);  // Small delay before auto-listen
    }
}

// Update visual status indicator
function updateVoiceStatusUI(status) {
    let statusEl = document.getElementById('voice-status');
    if (!statusEl) {
        statusEl = document.createElement('div');
        statusEl.id = 'voice-status';
        statusEl.className = 'voice-status';
        const inputArea = document.querySelector('.input-area');
        if (inputArea) {
            inputArea.parentNode.insertBefore(statusEl, inputArea);
        }
    }
    
    if (status) {
        statusEl.textContent = status;
        statusEl.classList.add('active');
    } else {
        statusEl.classList.remove('active');
        statusEl.textContent = '';
    }
}

// Initialize voice functionality
document.addEventListener('DOMContentLoaded', initVoice);

function initVoice() {
    const micBtn = document.getElementById('mic-btn');
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Microphone not supported');
        if (micBtn) {
            micBtn.disabled = true;
            micBtn.title = 'Microphone not supported';
        }
        return;
    }
    
    // Click to toggle recording
    if (micBtn) {
        micBtn.addEventListener('click', () => {
            // ALWAYS stop TTS first when mic is clicked
            if (VoiceState.isSpeaking) {
                stopSpeaking();
            }
            
            if (VoiceState.isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        });
    }
    
    // Add conversation mode toggle
    const convModeBtn = document.createElement('button');
    convModeBtn.id = 'conv-mode-btn';
    convModeBtn.className = 'conv-mode-btn active';
    convModeBtn.innerHTML = '🔄';
    convModeBtn.title = 'Conversation Mode: ON (auto-listen after AI speaks)';
    convModeBtn.addEventListener('click', () => {
        VoiceState.conversationMode = !VoiceState.conversationMode;
        convModeBtn.classList.toggle('active', VoiceState.conversationMode);
        convModeBtn.title = VoiceState.conversationMode ? 
            'Conversation Mode: ON (auto-listen after AI speaks)' : 
            'Conversation Mode: OFF';
    });
    
    const inputActions = document.querySelector('.input-actions');
    if (inputActions && micBtn) {
        inputActions.insertBefore(convModeBtn, micBtn);
    }
    
    console.log('🎤 Voice input initialized');
}

async function startRecording() {
    if (VoiceState.isRecording) return;
    
    const micBtn = document.getElementById('mic-btn');
    
    try {
        VoiceState.stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 16000
            }
        });
        
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
        
        VoiceState.mediaRecorder.start();
        VoiceState.isRecording = true;
        
        // Update UI
        if (micBtn) {
            micBtn.classList.add('recording');
            micBtn.textContent = '⏹️';
        }
        
        updateVoiceStatusUI('🎤 Listening...');
        console.log('Recording started');
        
    } catch (error) {
        console.error('Recording error:', error);
        alert('Microphone access denied. Please allow microphone access.');
    }
}

function stopRecording() {
    if (!VoiceState.isRecording) return;
    
    const micBtn = document.getElementById('mic-btn');
    
    if (VoiceState.mediaRecorder && VoiceState.mediaRecorder.state !== 'inactive') {
        VoiceState.mediaRecorder.stop();
    }
    
    if (VoiceState.stream) {
        VoiceState.stream.getTracks().forEach(track => track.stop());
    }
    
    VoiceState.isRecording = false;
    
    // Update UI
    if (micBtn) {
        micBtn.classList.remove('recording');
        micBtn.textContent = '🎤';
    }
    
    updateVoiceStatusUI('⏳ Processing...');
    VoiceState.isProcessing = true;
    console.log('Recording stopped');
}

async function handleRecordingComplete() {
    if (VoiceState.audioChunks.length === 0) {
        console.warn('No audio recorded');
        return;
    }
    
    const mimeType = getSupportedMimeType();
    const audioBlob = new Blob(VoiceState.audioChunks, { type: mimeType });
    
    // Ignore very short recordings (accidental clicks)
    if (audioBlob.size < 1000) {
        console.warn('Recording too short');
        return;
    }
    
    console.log('Audio recorded:', audioBlob.size, 'bytes');
    
    await processVoiceInput(audioBlob);
}

async function processVoiceInput(audioBlob) {
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatMessages = document.getElementById('chat-messages');
    const chatArea = document.getElementById('chat-area');
    
    // Show chat area
    if (welcomeScreen) welcomeScreen.classList.add('hidden');
    if (chatMessages) chatMessages.classList.remove('hidden');
    
    // Show typing indicator
    const typingId = 'voice-typing-' + Date.now();
    const typingEl = document.createElement('div');
    typingEl.className = 'message-wrapper ai';
    typingEl.id = typingId;
    typingEl.innerHTML = `
        <div class="message ai">
            <div class="message-avatar">🪷</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
                <small style="color: var(--text-muted);">Processing voice...</small>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingEl);
    if (chatArea) chatArea.scrollTop = chatArea.scrollHeight;
    
    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'recording.webm');
        
        if (window.AppState && window.AppState.sessionId) {
            formData.append('session_id', window.AppState.sessionId);
        }
        
        const response = await fetch('/api/voice/chat', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        
        // Remove typing indicator
        const typing = document.getElementById(typingId);
        if (typing) typing.remove();
        
        // Update session
        if (data.session_id && window.AppState) {
            window.AppState.sessionId = data.session_id;
        }
        
        // Add user message (transcript)
        if (data.transcript) {
            addVoiceMessage('user', data.transcript);
        }
        
        // Add AI response
        addVoiceMessage('ai', data.response, data.suggested_questions);
        
        // Speak response
        if (data.tts_text && window.speakText) {
            window.speakText(data.tts_text);
        }
        
    } catch (error) {
        console.error('Voice processing error:', error);
        
        const typing = document.getElementById(typingId);
        if (typing) typing.remove();
        
        addVoiceMessage('ai', 'Maaf kijiye, aapki awaaz process karne mein problem hui. Please try again.');
    } finally {
        VoiceState.isProcessing = false;
        updateVoiceStatusUI('');
    }
}

function addVoiceMessage(role, content, suggestions = null) {
    const chatMessages = document.getElementById('chat-messages');
    const chatArea = document.getElementById('chat-area');
    
    if (!chatMessages) return;
    
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🪷';
    
    wrapper.innerHTML = `
        <div class="message ${role}">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text">${role === 'ai' ? renderSimpleMarkdown(content) : escapeHtml(content)}</div>
                ${role === 'ai' ? `
                    <div class="message-actions">
                        <button class="message-action-btn" onclick="copyMessage(this)" title="Copy">📋</button>
                        <button class="message-action-btn" onclick="speakMessage(this)" title="Read aloud">🔊</button>
                    </div>
                    <div class="suggested-questions">${suggestions ? suggestions.map(q => 
                        `<button class="suggested-question" onclick="sendExample('${escapeHtml(q)}')">${q}</button>`
                    ).join('') : ''}</div>
                ` : ''}
            </div>
        </div>
    `;
    
    chatMessages.appendChild(wrapper);
    
    if (chatArea) {
        chatArea.scrollTop = chatArea.scrollHeight;
    }
    
    // Save to state
    if (window.AppState) {
        window.AppState.messages.push({ 
            role: role === 'ai' ? 'assistant' : 'user', 
            content 
        });
    }
}

function renderSimpleMarkdown(text) {
    if (typeof marked !== 'undefined') {
        return marked.parse(text);
    }
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

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
    
    return 'audio/webm';
}

// Exports
window.VoiceState = VoiceState;
window.startRecording = startRecording;
window.stopRecording = stopRecording;
window.stopSpeaking = stopSpeaking;
window.onSpeechComplete = onSpeechComplete;
window.updateVoiceStatusUI = updateVoiceStatusUI;
