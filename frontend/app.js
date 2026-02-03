/**
 * SamairaAI - Main Application JavaScript
 * Handles chat interface, API communication, and UI state
 */

// API Configuration
const API_BASE = 'http://localhost:8000/api';

// Application State
const AppState = {
    sessionId: null,
    isProcessing: false,
    ttsEnabled: true,
    messages: []
};

// DOM Elements
const elements = {
    welcomeScreen: document.getElementById('welcome-screen'),
    chatMessages: document.getElementById('chat-messages'),
    messageInput: document.getElementById('message-input'),
    sendBtn: document.getElementById('send-btn'),
    micBtn: document.getElementById('mic-btn'),
    newChatBtn: document.getElementById('new-chat-btn'),
    typingIndicator: document.getElementById('typing-indicator'),
    recordingStatus: document.getElementById('recording-status')
};

// Initialize application
document.addEventListener('DOMContentLoaded', initApp);

async function initApp() {
    // Create new session
    await createSession();
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('SamairaAI initialized');
}

function setupEventListeners() {
    // Send button click
    elements.sendBtn.addEventListener('click', handleSend);
    
    // Enter key to send (Shift+Enter for new line)
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // Auto-resize textarea
    elements.messageInput.addEventListener('input', () => {
        elements.messageInput.style.height = 'auto';
        elements.messageInput.style.height = Math.min(elements.messageInput.scrollHeight, 120) + 'px';
    });
    
    // New chat button
    elements.newChatBtn.addEventListener('click', startNewChat);
}

// Session Management
async function createSession() {
    try {
        const response = await fetch(`${API_BASE}/session/create`, {
            method: 'POST'
        });
        const data = await response.json();
        AppState.sessionId = data.session_id;
        console.log('Session created:', AppState.sessionId);
    } catch (error) {
        console.error('Failed to create session:', error);
        // Continue without session - will be created on first message
    }
}

async function startNewChat() {
    // Reset state
    AppState.messages = [];
    AppState.sessionId = null;
    
    // Clear UI
    elements.chatMessages.innerHTML = '';
    elements.chatMessages.classList.add('hidden');
    elements.welcomeScreen.classList.remove('hidden');
    elements.messageInput.value = '';
    
    // Create new session
    await createSession();
}

// Message Handling
async function handleSend() {
    const message = elements.messageInput.value.trim();
    
    if (!message || AppState.isProcessing) return;
    
    // Clear input
    elements.messageInput.value = '';
    
    // Send message
    await sendMessage(message);
}

async function sendMessage(message) {
    // Show chat area, hide welcome
    elements.welcomeScreen.classList.add('hidden');
    elements.chatMessages.classList.remove('hidden');
    
    // Add user message to UI
    addMessageToUI('user', message);
    
    // Show typing indicator
    showTyping(true);
    AppState.isProcessing = true;
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: AppState.sessionId
            })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Update session ID if returned
        if (data.session_id) {
            AppState.sessionId = data.session_id;
        }
        
        // Hide typing indicator
        showTyping(false);
        
        // Add AI response to UI
        addMessageToUI('ai', data.response, {
            intent: data.intent,
            handoffRequested: data.handoff_requested,
            calculationData: data.calculation_data,
            ttsText: data.tts_text
        });
        
        // Speak response if TTS enabled
        if (AppState.ttsEnabled && data.tts_text) {
            speakText(data.tts_text);
        }
        
    } catch (error) {
        console.error('Error sending message:', error);
        showTyping(false);
        addMessageToUI('ai', 'Maaf kijiye, kuch technical issue aa gaya. Kya aap phir se try kar sakte hain?');
    } finally {
        AppState.isProcessing = false;
    }
}

// Example message handler - called from HTML buttons
function sendExample(text) {
    elements.messageInput.value = text;
    handleSend();
}

// UI Functions
function addMessageToUI(type, content, metadata = {}) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    
    const avatar = type === 'user' ? '👤' : '🪷';
    
    // Format content (handle markdown-like formatting)
    const formattedContent = formatMessageContent(content);
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">
            ${formattedContent}
            ${type === 'ai' && metadata.ttsText ? `
                <button class="speaker-btn" onclick="speakText('${escapeForJS(metadata.ttsText)}')" title="Listen">
                    🔊
                </button>
            ` : ''}
        </div>
    `;
    
    // Add calculation card if present
    if (metadata.calculationData && type === 'ai') {
        const calcCard = createCalculationCard(metadata.calculationData);
        messageDiv.querySelector('.message-content').appendChild(calcCard);
    }
    
    // Add handoff banner if requested
    if (metadata.handoffRequested && type === 'ai') {
        const handoffBanner = createHandoffBanner();
        messageDiv.querySelector('.message-content').appendChild(handoffBanner);
    }
    
    elements.chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
    
    // Store message
    AppState.messages.push({ type, content, metadata });
}

function formatMessageContent(content) {
    // Convert markdown-like formatting to HTML
    let formatted = content
        // Bold
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        // Bullet points
        .replace(/^• (.+)$/gm, '<li>$1</li>')
        .replace(/^- (.+)$/gm, '<li>$1</li>')
        // Line breaks
        .replace(/\n\n/g, '</p><p>')
        .replace(/\n/g, '<br>');
    
    // Wrap in paragraph if not already
    if (!formatted.startsWith('<')) {
        formatted = `<p>${formatted}</p>`;
    }
    
    // Wrap list items in ul
    if (formatted.includes('<li>')) {
        formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
    }
    
    return formatted;
}

function createCalculationCard(data) {
    const card = document.createElement('div');
    card.className = 'calc-card';
    
    let bodyContent = '';
    
    if (data.summary_hinglish) {
        bodyContent = `<p>${formatMessageContent(data.summary_hinglish)}</p>`;
    } else if (data.sip && data.rd) {
        // Comparison data
        bodyContent = `
            <table>
                <tr>
                    <td>SIP (${data.sip.rate_of_return}%):</td>
                    <td>₹${formatIndianNumber(data.sip.maturity_value)}</td>
                </tr>
                <tr>
                    <td>RD (${data.rd.rate_of_return}%):</td>
                    <td>₹${formatIndianNumber(data.rd.maturity_value)}</td>
                </tr>
                <tr>
                    <td>Difference:</td>
                    <td>₹${formatIndianNumber(data.difference.amount)}</td>
                </tr>
            </table>
        `;
    } else {
        // Single calculation
        bodyContent = `
            <table>
                <tr>
                    <td>Total Invested:</td>
                    <td>₹${formatIndianNumber(data.total_invested)}</td>
                </tr>
                <tr>
                    <td>Maturity Value:</td>
                    <td>₹${formatIndianNumber(data.maturity_value)}</td>
                </tr>
                <tr>
                    <td>Returns:</td>
                    <td>₹${formatIndianNumber(data.total_returns)} (${data.returns_percentage?.toFixed(1)}%)</td>
                </tr>
            </table>
        `;
    }
    
    card.innerHTML = `
        <div class="calc-header">
            <span class="calc-icon">📊</span>
            <span class="calc-title">Projection (Illustrative)</span>
        </div>
        <div class="calc-body">
            ${bodyContent}
        </div>
    `;
    
    return card;
}

function createHandoffBanner() {
    const banner = document.createElement('div');
    banner.className = 'handoff-banner';
    banner.innerHTML = `
        <p>🤝 Is query ke liye ek certified advisor better guide kar sakte hain.</p>
        <button onclick="requestHandoff()">Connect with Advisor</button>
    `;
    return banner;
}

function requestHandoff() {
    alert('Demo: In production, this would connect you to a human financial advisor.');
}

function showTyping(show) {
    if (show) {
        elements.typingIndicator.classList.remove('hidden');
        scrollToBottom();
    } else {
        elements.typingIndicator.classList.add('hidden');
    }
}

function scrollToBottom() {
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
}

// Utility Functions
function formatIndianNumber(num) {
    if (num === undefined || num === null) return '0';
    
    const number = parseFloat(num);
    
    if (number >= 10000000) {
        return (number / 10000000).toFixed(2) + ' Cr';
    } else if (number >= 100000) {
        return (number / 100000).toFixed(2) + ' L';
    } else {
        return number.toLocaleString('en-IN', { maximumFractionDigits: 0 });
    }
}

function escapeForJS(str) {
    return str.replace(/'/g, "\\'").replace(/\n/g, ' ');
}

// TTS Function (uses Web Speech API)
let ttsVoices = [];
let selectedVoice = null;

// Phonetic corrections for better Hinglish pronunciation
const phoneticCorrections = {
    // Common mispronunciations
    'try': 'traay',
    'kijiye': 'kee-jee-yay',
    'chahiye': 'chaa-hee-yay',
    'samjhiye': 'sam-jhee-yay',
    'bataiye': 'ba-taa-ee-yay',
    'karein': 'ka-rain',
    'sakti': 'sak-tee',
    'sakta': 'sak-taa',
    'hoon': 'hoon',
    'hai': 'hay',
    'hain': 'hain',
    'mein': 'main',
    'aapka': 'aap-kaa',
    'aapki': 'aap-kee',
    'zaroor': 'za-roor',
    'zaroori': 'za-roo-ree',
    'pehle': 'peh-lay',
    'baad': 'baad',
    'lagbhag': 'lag-bhag',
    // Financial terms
    'SIP': 'sip',
    'RD': 'aar dee',
    'PPF': 'pee pee eff',
    'NPS': 'en pee ess',
    'EMI': 'ee em aai',
    'FD': 'eff dee',
    'SSY': 'ess ess waai',
    // Numbers and currency
    '₹': 'rupees',
    'L': 'laakh',
    'Cr': 'crore',
    'lakh': 'laakh',
    'crore': 'crore'
};

function speakText(text) {
    if (!('speechSynthesis' in window)) {
        console.warn('Text-to-speech not supported');
        return;
    }
    
    // Cancel any ongoing speech
    speechSynthesis.cancel();
    
    // Apply phonetic corrections
    let cleanText = text;
    
    // Apply all phonetic corrections (case-insensitive for words)
    for (const [word, replacement] of Object.entries(phoneticCorrections)) {
        const regex = new RegExp(`\\b${word}\\b`, 'gi');
        cleanText = cleanText.replace(regex, replacement);
    }
    
    // Additional cleanup
    cleanText = cleanText
        .replace(/\*\*/g, '')  // Remove markdown bold
        .replace(/\n/g, '. ')  // Convert newlines to pauses
        .replace(/\s+/g, ' ')  // Normalize spaces
        .trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Get best voice for Hinglish
    const voice = getBestVoice();
    if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
    }
    
    // Adjust speech parameters for clarity
    utterance.rate = 0.9;   // Slightly slower
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    // Add event handlers for debugging
    utterance.onerror = (e) => console.error('TTS Error:', e);
    utterance.onend = () => console.log('TTS completed');
    
    speechSynthesis.speak(utterance);
}

function getBestVoice() {
    if (selectedVoice) return selectedVoice;
    
    const voices = ttsVoices.length > 0 ? ttsVoices : speechSynthesis.getVoices();
    
    // Priority order for Hinglish content:
    // 1. Hindi voice (hi-IN)
    // 2. Indian English (en-IN)
    // 3. Microsoft voices (better quality on Windows)
    // 4. Any English voice
    
    const hindiVoice = voices.find(v => v.lang === 'hi-IN');
    const indianEnglish = voices.find(v => v.lang === 'en-IN');
    const microsoftIndian = voices.find(v => v.name.includes('Microsoft') && v.lang.includes('IN'));
    const googleIndian = voices.find(v => v.name.includes('Google') && v.lang.includes('IN'));
    const anyEnglish = voices.find(v => v.lang.startsWith('en'));
    
    selectedVoice = hindiVoice || microsoftIndian || googleIndian || indianEnglish || anyEnglish || voices[0];
    
    if (selectedVoice) {
        console.log('Selected TTS voice:', selectedVoice.name, selectedVoice.lang);
    }
    
    return selectedVoice;
}

// Stop speaking
function stopSpeaking() {
    if ('speechSynthesis' in window) {
        speechSynthesis.cancel();
    }
}

// Load voices when available
if ('speechSynthesis' in window) {
    // Load voices immediately if available
    ttsVoices = speechSynthesis.getVoices();
    
    speechSynthesis.onvoiceschanged = () => {
        ttsVoices = speechSynthesis.getVoices();
        selectedVoice = null; // Reset to re-select
        console.log('TTS voices loaded:', ttsVoices.length);
        
        // Log available Indian voices for debugging
        const indianVoices = ttsVoices.filter(v => 
            v.lang.includes('IN') || v.lang.includes('hi')
        );
        if (indianVoices.length > 0) {
            console.log('Available Indian voices:', 
                indianVoices.map(v => `${v.name} (${v.lang})`).join(', ')
            );
        }
        
        // Pre-select the best voice
        getBestVoice();
    };
}
