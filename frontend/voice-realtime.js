/**
 * SamairaAI - Real-Time Voice Handler with WebSocket Streaming
 * Provides near-duplex conversation with streaming STT, LLM, and TTS
 */

// Real-Time Voice State
const RTVoiceState = {
    ws: null,
    isConnected: false,
    isStreaming: false,
    isSpeaking: false,
    audioContext: null,
    audioWorkletNode: null,
    mediaStream: null,
    audioQueue: [],  // Queue of TTS audio buffers to play
    currentSourceNode: null,
    realtimeEnabled: false,
    partialTranscript: '',
    sessionId: null
};

// Initialize Real-Time Voice
function initRealtimeVoice() {
    const micBtn = document.getElementById('mic-btn');
    const rtToggle = document.getElementById('realtime-toggle');
    
    if (!micBtn) return;
    
    // Add realtime toggle button if not exists
    if (!rtToggle && navigator.mediaDevices) {
        const toggle = document.createElement('button');
        toggle.id = 'realtime-toggle';
        toggle.className = 'icon-btn';
        toggle.title = 'Toggle Real-Time Conversation';
        toggle.innerHTML = '⚡';
        toggle.addEventListener('click', toggleRealtimeMode);
        micBtn.parentNode.insertBefore(toggle, micBtn);
    }
    
    // IMPORTANT: Store the original mic click handler
    const originalMicHandler = micBtn.onclick;
    
    // Override mic button click handler to route to correct mode
    micBtn.onclick = null; // Clear any existing handlers
    micBtn.removeEventListener('click', handleRealtimeMicClick); // Remove if already added
    
    micBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        e.stopPropagation();
        
        if (RTVoiceState.realtimeEnabled) {
            // Use real-time streaming
            await handleRealtimeMicClick();
        } else {
            // Use regular voice mode
            if (typeof toggleRecording === 'function') {
                toggleRecording();
            } else if (originalMicHandler) {
                originalMicHandler.call(micBtn, e);
            }
        }
    });
}

// Toggle between regular and real-time mode
function toggleRealtimeMode() {
    RTVoiceState.realtimeEnabled = !RTVoiceState.realtimeEnabled;
    const toggle = document.getElementById('realtime-toggle');
    
    if (RTVoiceState.realtimeEnabled) {
        toggle.classList.add('active');
        toggle.title = 'Real-Time Mode: ON';
        showToast('info', 'Real-Time Mode', 'Streaming conversation enabled ⚡');
    } else {
        toggle.classList.remove('active');
        toggle.title = 'Real-Time Mode: OFF';
        if (RTVoiceState.ws) {
            RTVoiceState.ws.close();
            RTVoiceState.ws = null;
        }
    }
}

// Handle mic click in real-time mode
async function handleRealtimeMicClick() {
    if (!RTVoiceState.realtimeEnabled) {
        // Fall back to old voice mode
        if (typeof toggleRecording === 'function') {
            toggleRecording();
        }
        return;
    }
    
    if (RTVoiceState.isStreaming) {
        stopRealtimeStreaming();
    } else {
        await startRealtimeStreaming();
    }
}

// Start real-time voice streaming
async function startRealtimeStreaming() {
    console.log('[RT] Starting real-time streaming...');
    console.log('[RT] Protocol:', window.location.protocol);
    console.log('[RT] Host:', window.location.host);
    
    try {
        // Check if browser supports getUserMedia
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('❌ Your browser does not support microphone access.\n\nPlease use Chrome, Firefox, or Edge.');
        }
        
        // Warn about HTTP (some browsers block mic on HTTP except localhost)
        if (window.location.protocol === 'http:' && !window.location.hostname.includes('localhost') && !window.location.hostname.includes('127.0.0.1')) {
            console.warn('[RT] ⚠️ Running on HTTP - some browsers may block microphone access');
            showToast('warning', 'Security Warning', 'For best results, use HTTPS or localhost');
        }
        
        // Show loading state
        showVoiceStatus('🎤 Requesting microphone access...');
        console.log('[RT] Requesting microphone permission...');
        
        // Request microphone access - SIMPLE AND ROBUST
        let stream;
        try {
            stream = await navigator.mediaDevices.getUserMedia({
                audio: true  // Start with simplest possible constraint
            });
            
            console.log('[RT] ✅ Microphone access granted!');
            console.log('[RT] Stream tracks:', stream.getAudioTracks().length);
            
            RTVoiceState.mediaStream = stream;
            
        } catch (micError) {
            console.error('[RT] ❌ Microphone error:', micError);
            console.error('[RT] Error name:', micError.name);
            console.error('[RT] Error message:', micError.message);
            
            let errorMsg = 'Could not access microphone';
            
            if (micError.name === 'NotAllowedError' || micError.name === 'PermissionDeniedError') {
                errorMsg = '🔒 Microphone permission denied!\n\n' +
                           'To fix this:\n' +
                           '1. Look for the 🔒 or 🎤 icon in your browser address bar\n' +
                           '2. Click it and select "Allow microphone"\n' +
                           '3. Refresh the page (F5) and try again';
            } else if (micError.name === 'NotFoundError') {
                errorMsg = '🎤 No microphone detected!\n\n' +
                           'Please:\n' +
                           '1. Connect a microphone to your computer\n' +
                           '2. Check Windows Sound settings\n' +
                           '3. Refresh the page and try again';
            } else if (micError.name === 'NotReadableError') {
                errorMsg = '⚠️ Microphone is already in use!\n\n' +
                           'Please close:\n' +
                           '• Zoom, Teams, Discord, Skype\n' +
                           '• Other browser tabs using microphone\n' +
                           '• Any recording software';
            } else if (micError.name === 'OverconstrainedError') {
                errorMsg = '⚠️ Microphone configuration issue!\n\n' +
                           'Your microphone doesn\'t support the required settings.\n' +
                           'Try refreshing the page.';
            } else {
                errorMsg = `❌ Microphone Error:\n${micError.message}\n\nCheck browser console (F12) for details.`;
            }
            
            throw new Error(errorMsg);
        }
        
        // Initialize AudioContext
        try {
            RTVoiceState.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('[RT] AudioContext created:', RTVoiceState.audioContext.sampleRate, 'Hz');
        } catch (audioError) {
            console.error('[RT] AudioContext error:', audioError);
            throw new Error('❌ Failed to initialize audio system.\n\nTry refreshing the page.');
        }
        
        // Connect WebSocket
        showVoiceStatus('🔌 Connecting to server...');
        await connectVoiceWebSocket();
        
        // Start audio processing
        showVoiceStatus('🎙️ Initializing audio pipeline...');
        await setupAudioProcessing();
        
        // Success!
        RTVoiceState.isStreaming = true;
        updateMicButton(true);
        showVoiceStatus('🎤 Listening...');
        
        console.log('[RT] ✅ Real-time streaming started successfully!');
        showToast('success', 'Connected', '⚡ Real-time voice streaming active');
        
    } catch (error) {
        console.error('[RT] ❌ Failed to start streaming:', error);
        
        // Show user-friendly error
        if (typeof showToast === 'function') {
            showToast('error', 'Cannot Start Microphone', error.message);
        } else {
            alert('Microphone Error:\n\n' + error.message);
        }
        
        // Clean up
        stopRealtimeStreaming();
    }
}

// Stop real-time streaming
function stopRealtimeStreaming() {
    RTVoiceState.isStreaming = false;
    
    // Stop media stream
    if (RTVoiceState.mediaStream) {
        RTVoiceState.mediaStream.getTracks().forEach(track => track.stop());
        RTVoiceState.mediaStream = null;
    }
    
    // Close WebSocket
    if (RTVoiceState.ws) {
        RTVoiceState.ws.send(JSON.stringify({ type: 'stop' }));
        RTVoiceState.ws.close();
        RTVoiceState.ws = null;
        RTVoiceState.isConnected = false;
    }
    
    // Stop audio playback
    if (RTVoiceState.currentSourceNode) {
        RTVoiceState.currentSourceNode.stop();
        RTVoiceState.currentSourceNode = null;
    }
    
    // Close audio context
    if (RTVoiceState.audioContext) {
        RTVoiceState.audioContext.close();
        RTVoiceState.audioContext = null;
    }
    
    updateMicButton(false);
    hideVoiceStatus();
    
    console.log('[RT] Real-time streaming stopped');
}

// Connect to voice WebSocket
async function connectVoiceWebSocket() {
    return new Promise((resolve, reject) => {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            // WebSocket endpoint: router prefix is /api, endpoint is /ws/voice
            const wsUrl = `${protocol}//${window.location.host}/api/ws/voice`;
            
            console.log('[RT] Connecting to WebSocket:', wsUrl);
            
            RTVoiceState.ws = new WebSocket(wsUrl);
            
            RTVoiceState.ws.onopen = () => {
                console.log('[RT] ✅ WebSocket connected successfully');
                RTVoiceState.isConnected = true;
                
                // Send start message with session ID
                RTVoiceState.sessionId = AppState?.sessionId || null;
                const startMsg = {
                    type: 'start',
                    session_id: RTVoiceState.sessionId
                };
                
                console.log('[RT] Sending start message:', startMsg);
                RTVoiceState.ws.send(JSON.stringify(startMsg));
                
                resolve();
            };
            
            RTVoiceState.ws.onmessage = handleWebSocketMessage;
            
            RTVoiceState.ws.onerror = (error) => {
                console.error('[RT] ❌ WebSocket error:', error);
                reject(new Error('Failed to connect to server. Please check your internet connection.'));
            };
            
            RTVoiceState.ws.onclose = (event) => {
                console.log('[RT] WebSocket closed:', event.code, event.reason);
                RTVoiceState.isConnected = false;
                
                if (RTVoiceState.isStreaming) {
                    showToast('warning', 'Disconnected', 'Connection to server lost');
                    stopRealtimeStreaming();
                }
            };
            
            // Timeout after 10 seconds
            setTimeout(() => {
                if (!RTVoiceState.isConnected) {
                    RTVoiceState.ws?.close();
                    reject(new Error('Connection timeout. Server may be down or unreachable.'));
                }
            }, 10000);
            
        } catch (err) {
            console.error('[RT] ❌ WebSocket setup error:', err);
            reject(new Error('Failed to initialize WebSocket: ' + err.message));
        }
    });
}

// Handle WebSocket messages
function handleWebSocketMessage(event) {
    const message = JSON.parse(event.data);
    const type = message.type;
    
    switch (type) {
        case 'session':
            // Update session ID
            RTVoiceState.sessionId = message.session_id;
            AppState.sessionId = message.session_id;
            localStorage.setItem('samaira-session-id', message.session_id);
            break;
        
        case 'vad_state':
            // Voice activity detection state
            if (message.state === 'speech') {
                showVoiceStatus('🎤 Listening...');
            } else if (message.state === 'silence') {
                showVoiceStatus('🤔 Processing...');
            }
            break;
        
        case 'stt_partial':
            // Partial transcription (not used in current faster-whisper, but ready)
            RTVoiceState.partialTranscript = message.text;
            showPartialTranscript(message.text);
            break;
        
        case 'stt_final':
            // Final transcription
            const userText = message.text;
            if (userText.trim()) {
                addMessage('user', userText);
                RTVoiceState.partialTranscript = '';
                showVoiceStatus('🤖 AI is thinking...');
            }
            break;
        
        case 'llm_chunk':
            // LLM streaming token
            handleLLMChunk(message.text);
            break;
        
        case 'tts_chunk':
            // TTS audio chunk
            handleTTSChunk(message.audio, message.format);
            break;
        
        case 'turn_done':
            // Turn complete
            showVoiceStatus('✓ Turn complete');
            setTimeout(() => {
                showVoiceStatus('🎤 Ready to listen...');
            }, 1000);
            break;
        
        case 'error':
            console.error('[RT] Server error:', message.message);
            showToast('error', 'Voice Error', message.message);
            break;
    }
}

// Setup audio processing (capture and stream PCM)
async function setupAudioProcessing() {
    const source = RTVoiceState.audioContext.createMediaStreamSource(RTVoiceState.mediaStream);
    
    const sampleRate = RTVoiceState.audioContext.sampleRate;
    const targetSampleRate = 16000;
    
    console.log('[RT] Setting up audio processing:', sampleRate, 'Hz →', targetSampleRate, 'Hz');
    
    // Use ScriptProcessor - 4096 is a safe buffer size for most browsers
    const bufferSize = 4096;
    const processor = RTVoiceState.audioContext.createScriptProcessor(bufferSize, 1, 1);
    
    // Resampling buffer
    let resampleBuffer = [];
    const resampleRatio = targetSampleRate / sampleRate;
    const targetChunkSize = 480; // 30ms at 16kHz
    
    processor.onaudioprocess = (e) => {
        if (!RTVoiceState.isConnected || !RTVoiceState.ws) return;
        
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Simple resampling (linear interpolation)
        for (let i = 0; i < inputData.length; i++) {
            const targetIndex = i * resampleRatio;
            const index0 = Math.floor(targetIndex);
            const index1 = Math.ceil(targetIndex);
            const fraction = targetIndex - index0;
            
            // Linear interpolation
            const sample0 = inputData[Math.min(i, inputData.length - 1)];
            const sample1 = inputData[Math.min(i + 1, inputData.length - 1)];
            const resampledValue = sample0 * (1 - fraction) + sample1 * fraction;
            
            resampleBuffer.push(resampledValue);
        }
        
        // Send chunks of 30ms (480 samples at 16kHz)
        while (resampleBuffer.length >= targetChunkSize) {
            const chunk = resampleBuffer.splice(0, targetChunkSize);
            
            // Convert float32 to int16 PCM
            const pcm16 = new Int16Array(chunk.length);
            for (let i = 0; i < chunk.length; i++) {
                const s = Math.max(-1, Math.min(1, chunk[i]));
                pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }
            
            // Send as base64
            const bytes = new Uint8Array(pcm16.buffer);
            const base64 = btoa(String.fromCharCode(...bytes));
            
            if (RTVoiceState.ws && RTVoiceState.ws.readyState === WebSocket.OPEN) {
                RTVoiceState.ws.send(JSON.stringify({
                    type: 'audio_chunk',
                    data: base64
                }));
            }
        }
    };
    
    source.connect(processor);
    processor.connect(RTVoiceState.audioContext.destination);
    
    RTVoiceState.audioWorkletNode = processor;
    console.log('[RT] Audio processing pipeline connected');
}

// Handle LLM chunk (stream to chat)
let currentAIMessage = null;
let fullAIResponse = '';

function handleLLMChunk(text) {
    fullAIResponse += text;
    
    if (!currentAIMessage) {
        // Create new AI message bubble
        currentAIMessage = createMessageElement('ai', '');
        elements.chatMessages.appendChild(currentAIMessage);
    }
    
    // Update with streaming content
    updateMessageContent(currentAIMessage, fullAIResponse);
    scrollToBottom();
}

// Handle TTS chunk (play audio)
async function handleTTSChunk(audioBase64, format) {
    try {
        // Decode base64 to ArrayBuffer
        const binaryString = atob(audioBase64);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
        }
        
        // Decode MP3 to AudioBuffer
        const audioBuffer = await RTVoiceState.audioContext.decodeAudioData(bytes.buffer);
        
        // Add to queue and play
        RTVoiceState.audioQueue.push(audioBuffer);
        
        if (!RTVoiceState.isSpeaking) {
            playNextTTSChunk();
        }
        
    } catch (error) {
        console.error('[RT] Failed to decode TTS chunk:', error);
    }
}

// Play next TTS chunk from queue
function playNextTTSChunk() {
    if (RTVoiceState.audioQueue.length === 0) {
        RTVoiceState.isSpeaking = false;
        currentAIMessage = null;
        fullAIResponse = '';
        return;
    }
    
    RTVoiceState.isSpeaking = true;
    showVoiceStatus('🔊 AI is speaking...');
    
    const audioBuffer = RTVoiceState.audioQueue.shift();
    const source = RTVoiceState.audioContext.createBufferSource();
    source.buffer = audioBuffer;
    source.connect(RTVoiceState.audioContext.destination);
    
    source.onended = () => {
        RTVoiceState.currentSourceNode = null;
        playNextTTSChunk();  // Play next chunk
    };
    
    RTVoiceState.currentSourceNode = source;
    source.start();
}

// Show partial transcript (live feedback)
function showPartialTranscript(text) {
    let partialEl = document.getElementById('partial-transcript');
    if (!partialEl) {
        partialEl = document.createElement('div');
        partialEl.id = 'partial-transcript';
        partialEl.className = 'partial-transcript';
        elements.chatMessages.appendChild(partialEl);
    }
    partialEl.textContent = text;
    partialEl.style.display = text ? 'block' : 'none';
}

// UI helper functions
function updateMicButton(isActive) {
    const micBtn = document.getElementById('mic-btn');
    if (micBtn) {
        if (isActive) {
            micBtn.classList.add('recording');
        } else {
            micBtn.classList.remove('recording');
        }
    }
}

function showVoiceStatus(message) {
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
    statusEl.textContent = message;
    statusEl.style.display = 'block';
}

function hideVoiceStatus() {
    const statusEl = document.getElementById('voice-status');
    if (statusEl) {
        statusEl.style.display = 'none';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initRealtimeVoice);

// Export for use in app.js if needed
window.RTVoiceState = RTVoiceState;
window.startRealtimeStreaming = startRealtimeStreaming;
window.stopRealtimeStreaming = stopRealtimeStreaming;
