/**
 * SamairaAI - Premium Chat Application
 * Features: Streaming responses, Markdown rendering, Voice I/O, Dark mode
 */

// ===== CONFIGURATION =====
const API_BASE = '/api';
const ENABLE_STREAMING = true;

// ===== APPLICATION STATE =====
const AppState = {
    sessionId: null,
    isProcessing: false,
    messages: [],
    chatHistory: JSON.parse(localStorage.getItem('samaira-chat-history') || '[]'),
    ttsEnabled: true,
    currentTheme: 'light',
    usePremiumTTS: false  // Will check if ElevenLabs available
};

// ===== DOM ELEMENTS =====
const elements = {};

// ===== INITIALIZATION =====
document.addEventListener('DOMContentLoaded', () => {
    initElements();
    initTheme();
    initEventListeners();
    createSession();
    loadChatHistory();
    checkTTSProvider();
    
    console.log('🪷 SamairaAI initialized');
});

function initElements() {
    elements.welcomeScreen = document.getElementById('welcome-screen');
    elements.chatMessages = document.getElementById('chat-messages');
    elements.chatArea = document.getElementById('chat-area');
    elements.messageInput = document.getElementById('message-input');
    elements.sendBtn = document.getElementById('send-btn');
    elements.micBtn = document.getElementById('mic-btn');
    elements.newChatBtn = document.getElementById('new-chat-btn');
    elements.sidebar = document.getElementById('sidebar');
    elements.sidebarOverlay = document.getElementById('sidebar-overlay');
    elements.menuToggle = document.getElementById('menu-toggle');
    elements.themeToggle = document.getElementById('theme-toggle');
    elements.chatHistory = document.getElementById('chat-history');
}

function initTheme() {
    const savedTheme = localStorage.getItem('samaira-theme') || 'light';
    setTheme(savedTheme);
}

function initEventListeners() {
    // Send message
    elements.sendBtn.addEventListener('click', handleSend);
    
    // Enter to send (Shift+Enter for new line)
    elements.messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });
    
    // Auto-resize textarea
    elements.messageInput.addEventListener('input', autoResizeTextarea);
    
    // New chat
    elements.newChatBtn.addEventListener('click', startNewChat);
    
    // Sidebar toggle (mobile)
    elements.menuToggle.addEventListener('click', toggleSidebar);
    elements.sidebarOverlay.addEventListener('click', toggleSidebar);
    
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);
}

// ===== SESSION MANAGEMENT =====
async function createSession() {
    try {
        const response = await fetch(`${API_BASE}/session/create`, { method: 'POST' });
        const data = await response.json();
        AppState.sessionId = data.session_id;
        console.log('Session created:', AppState.sessionId);
    } catch (error) {
        console.error('Session creation failed:', error);
    }
}

async function startNewChat() {
    // Save current chat to history if has messages
    if (AppState.messages.length > 0) {
        saveChatToHistory();
    }
    
    // Reset state
    AppState.messages = [];
    AppState.sessionId = null;
    
    // Reset UI
    elements.chatMessages.innerHTML = '';
    elements.chatMessages.classList.add('hidden');
    elements.welcomeScreen.classList.remove('hidden');
    elements.messageInput.value = '';
    autoResizeTextarea();
    
    // Create new session
    await createSession();
    
    // Close sidebar on mobile
    elements.sidebar.classList.remove('open');
}

function saveChatToHistory() {
    if (AppState.messages.length === 0) return;
    
    const firstUserMessage = AppState.messages.find(m => m.role === 'user');
    const title = firstUserMessage ? 
        firstUserMessage.content.substring(0, 35) + (firstUserMessage.content.length > 35 ? '...' : '') : 
        'New conversation';
    
    // Don't add duplicate
    if (AppState.chatHistory.length > 0 && AppState.chatHistory[0].id === AppState.sessionId) {
        return;
    }
    
    AppState.chatHistory.unshift({
        id: AppState.sessionId,
        title: title,
        messages: [...AppState.messages],
        timestamp: new Date().toISOString()
    });
    
    // Keep only last 20 chats
    AppState.chatHistory = AppState.chatHistory.slice(0, 20);
    
    // Persist to localStorage
    localStorage.setItem('samaira-chat-history', JSON.stringify(AppState.chatHistory));
    
    updateChatHistoryUI();
}

function loadChatHistory() {
    updateChatHistoryUI();
}

function updateChatHistoryUI() {
    if (!elements.chatHistory) return;
    
    if (AppState.chatHistory.length === 0) {
        elements.chatHistory.innerHTML = `
            <div class="empty-history">
                <p>Koi purani chats nahi hain</p>
            </div>
        `;
        return;
    }
    
    elements.chatHistory.innerHTML = AppState.chatHistory.map(chat => {
        const date = new Date(chat.timestamp);
        const timeStr = formatTimeAgo(date);
        
        return `
            <div class="chat-history-item" data-id="${chat.id}" onclick="loadChat('${chat.id}')">
                <div class="chat-history-title">💬 ${escapeHtml(chat.title)}</div>
                <div class="chat-history-time">${timeStr}</div>
            </div>
        `;
    }).join('');
}

function formatTimeAgo(date) {
    const now = new Date();
    const diff = now - date;
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);
    
    if (mins < 1) return 'Abhi';
    if (mins < 60) return `${mins} min pehle`;
    if (hours < 24) return `${hours} ghante pehle`;
    if (days < 7) return `${days} din pehle`;
    return date.toLocaleDateString('hi-IN');
}

async function loadChat(chatId) {
    const chat = AppState.chatHistory.find(c => c.id === chatId);
    if (!chat) return;
    
    // Load messages
    AppState.sessionId = chat.id;
    AppState.messages = [...chat.messages];
    
    // Show chat area
    elements.welcomeScreen.classList.add('hidden');
    elements.chatMessages.classList.remove('hidden');
    
    // Render messages
    elements.chatMessages.innerHTML = '';
    for (const msg of AppState.messages) {
        const role = msg.role === 'assistant' ? 'ai' : 'user';
        addMessageToUI(role, msg.content);
    }
    
    // Close sidebar on mobile
    elements.sidebar.classList.remove('open');
}

function addMessageToUI(role, content, suggestions = null) {
    const messageElement = createMessageElement(role, content, suggestions);
    elements.chatMessages.appendChild(messageElement);
    scrollToBottom();
}

// ===== MESSAGE HANDLING =====
async function handleSend() {
    const message = elements.messageInput.value.trim();
    if (!message || AppState.isProcessing) return;
    
    // Clear input
    elements.messageInput.value = '';
    autoResizeTextarea();
    
    // Send message
    await sendMessage(message);
}

function sendExample(text) {
    elements.messageInput.value = text;
    handleSend();
}

async function sendMessage(message) {
    // Show chat area
    elements.welcomeScreen.classList.add('hidden');
    elements.chatMessages.classList.remove('hidden');
    
    // Add user message
    addMessage('user', message);
    
    // Show typing indicator
    const typingId = showTypingIndicator();
    AppState.isProcessing = true;
    
    try {
        if (ENABLE_STREAMING) {
            await sendMessageStreaming(message, typingId);
        } else {
            await sendMessageNormal(message, typingId);
        }
    } catch (error) {
        console.error('Send error:', error);
        removeTypingIndicator(typingId);
        addMessage('ai', 'Maaf kijiye, kuch technical issue aa gaya. Please try again.');
    } finally {
        AppState.isProcessing = false;
    }
}

async function sendMessageStreaming(message, typingId) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            session_id: AppState.sessionId
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let fullText = '';
    let messageElement = null;
    let metadata = {};
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            
            try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'session') {
                    AppState.sessionId = data.session_id;
                } else if (data.type === 'content') {
                    // Remove typing indicator on first content
                    if (!messageElement) {
                        removeTypingIndicator(typingId);
                        messageElement = createMessageElement('ai', '');
                        elements.chatMessages.appendChild(messageElement);
                    }
                    
                    fullText += data.text;
                    updateMessageContent(messageElement, fullText);
                    scrollToBottom();
                } else if (data.type === 'done') {
                    metadata = data;
                } else if (data.type === 'error') {
                    throw new Error(data.message);
                }
            } catch (e) {
                // Ignore parse errors for incomplete chunks
            }
        }
    }
    
    // Final update with full content and suggestions
    if (messageElement) {
        updateMessageContent(messageElement, fullText, metadata.suggested_questions);
        
        // Save to state
        AppState.messages.push({
            role: 'assistant',
            content: fullText,
            ttsText: metadata.tts_text
        });
        
        // TTS
        if (AppState.ttsEnabled && metadata.tts_text) {
            speakText(metadata.tts_text);
        }
    }
}

async function sendMessageNormal(message, typingId) {
    const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: message,
            session_id: AppState.sessionId
        })
    });
    
    const data = await response.json();
    
    removeTypingIndicator(typingId);
    
    if (data.session_id) {
        AppState.sessionId = data.session_id;
    }
    
    addMessage('ai', data.response, data.suggested_questions);
    
    if (AppState.ttsEnabled && data.tts_text) {
        speakText(data.tts_text);
    }
}

// ===== UI FUNCTIONS =====
function addMessage(role, content, suggestions = null) {
    addMessageToUI(role, content, suggestions);
    
    // Save to state
    AppState.messages.push({ role: role === 'ai' ? 'assistant' : 'user', content });
    
    // Auto-save to history after user's first message gets a response
    if (role === 'ai' && AppState.messages.length === 2) {
        saveChatToHistory();
    }
}

function createMessageElement(role, content, suggestions = null) {
    const wrapper = document.createElement('div');
    wrapper.className = `message-wrapper ${role}`;
    
    const avatar = role === 'user' ? '👤' : '🪷';
    
    wrapper.innerHTML = `
        <div class="message ${role}">
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">
                <div class="message-text"></div>
                ${role === 'ai' ? `
                    <div class="message-actions">
                        <button class="message-action-btn" onclick="copyMessage(this)" title="Copy">📋</button>
                        <button class="message-action-btn" onclick="speakMessage(this)" title="Read aloud">🔊</button>
                    </div>
                    <div class="suggested-questions"></div>
                ` : ''}
            </div>
        </div>
    `;
    
    // Render content
    const textEl = wrapper.querySelector('.message-text');
    if (role === 'ai') {
        textEl.innerHTML = renderMarkdown(content);
    } else {
        textEl.textContent = content;
    }
    
    // Add suggestions
    if (suggestions && suggestions.length > 0) {
        const suggestionsEl = wrapper.querySelector('.suggested-questions');
        if (suggestionsEl) {
            suggestionsEl.innerHTML = suggestions.map(q => 
                `<button class="suggested-question" onclick="sendExample('${escapeHtml(q)}')">${q}</button>`
            ).join('');
        }
    }
    
    return wrapper;
}

function updateMessageContent(element, content, suggestions = null) {
    const textEl = element.querySelector('.message-text');
    if (textEl) {
        textEl.innerHTML = renderMarkdown(content);
    }
    
    if (suggestions && suggestions.length > 0) {
        const suggestionsEl = element.querySelector('.suggested-questions');
        if (suggestionsEl) {
            suggestionsEl.innerHTML = suggestions.map(q => 
                `<button class="suggested-question" onclick="sendExample('${escapeHtml(q)}')">${q}</button>`
            ).join('');
        }
    }
}

function renderMarkdown(text) {
    if (typeof marked === 'undefined') {
        // Fallback if marked.js not loaded
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
    
    // Configure marked for safe rendering
    marked.setOptions({
        breaks: true,
        gfm: true,
        sanitize: false
    });
    
    return marked.parse(text);
}

function showTypingIndicator() {
    const id = 'typing-' + Date.now();
    const wrapper = document.createElement('div');
    wrapper.className = 'message-wrapper ai';
    wrapper.id = id;
    
    wrapper.innerHTML = `
        <div class="message ai">
            <div class="message-avatar">🪷</div>
            <div class="message-content">
                <div class="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    
    elements.chatMessages.appendChild(wrapper);
    scrollToBottom();
    
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function scrollToBottom() {
    elements.chatArea.scrollTop = elements.chatArea.scrollHeight;
}

function autoResizeTextarea() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

// ===== THEME =====
function toggleTheme() {
    const newTheme = AppState.currentTheme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
}

function setTheme(theme) {
    AppState.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('samaira-theme', theme);
    
    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');
    
    if (theme === 'dark') {
        icon.textContent = '☀️';
        text.textContent = 'Light mode';
    } else {
        icon.textContent = '🌙';
        text.textContent = 'Dark mode';
    }
}

// ===== SIDEBAR =====
function toggleSidebar() {
    elements.sidebar.classList.toggle('open');
}

// ===== MESSAGE ACTIONS =====
function copyMessage(btn) {
    const content = btn.closest('.message-content').querySelector('.message-text').textContent;
    navigator.clipboard.writeText(content).then(() => {
        btn.textContent = '✓';
        setTimeout(() => btn.textContent = '📋', 1500);
    });
}

function speakMessage(btn) {
    const content = btn.closest('.message-content').querySelector('.message-text').textContent;
    speakText(content);
}

// ===== TTS =====
let ttsVoices = [];
let selectedVoice = null;
let audioContext = null;

const phoneticCorrections = {
    // Common Hindi verbs
    'hai': 'hay',
    'hain': 'hain',
    'mein': 'main',
    'hoti': 'ho-tee',
    'hota': 'ho-taa',
    'kijiye': 'kee-jee-yay',
    'chahiye': 'chaa-hee-yay',
    'karein': 'ka-rain',
    'karna': 'kar-naa',
    'karo': 'ka-ro',
    'sakti': 'sak-tee',
    'sakta': 'sak-taa',
    'sakte': 'sak-tay',
    'milta': 'mil-taa',
    'milti': 'mil-tee',
    'milne': 'mil-nay',
    
    // Pronouns and possessives
    'aapka': 'aap-kaa',
    'aapki': 'aap-kee',
    'aapko': 'aap-ko',
    'tumhare': 'tum-haa-ray',
    'tumhari': 'tum-haa-ree',
    'mera': 'may-raa',
    'meri': 'may-ree',
    
    // Question words
    'kaise': 'kai-say',
    'kya': 'kyaa',
    'kahan': 'ka-haan',
    'kitna': 'kit-naa',
    'kitne': 'kit-nay',
    
    // Common adjectives/adverbs
    'bahut': 'ba-hut',
    'accha': 'ach-chaa',
    'achha': 'ach-chaa',
    'acha': 'ach-chaa',
    'bada': 'ba-daa',
    'badi': 'ba-dee',
    'chota': 'cho-taa',
    'choti': 'cho-tee',
    'aasaan': 'aa-saan',
    'mushkil': 'mush-kil',
    'sahi': 'sa-hee',
    'galat': 'ga-lat',
    'jaldi': 'jal-dee',
    'dheere': 'dhee-ray',
    'zaroor': 'za-roor',
    'zaruri': 'za-roo-ree',
    
    // Financial Hindi terms
    'paisa': 'pai-saa',
    'paise': 'pai-say',
    'rupaye': 'ru-pa-yay',
    'rupiya': 'ru-pee-yaa',
    'bachat': 'ba-chat',
    'nivesh': 'ni-vesh',
    'faayda': 'faa-ee-daa',
    'fayda': 'faa-ee-daa',
    'nuksaan': 'nuk-saan',
    'nuksan': 'nuk-saan',
    'byaj': 'byaaj',
    'bima': 'bee-maa',
    'lakshya': 'laksh-ya',
    'salah': 'sa-laah',
    'sambhavana': 'sam-bhaa-va-naa',
    
    // Greetings
    'namaste': 'na-mas-tay',
    'namaskar': 'na-mas-kaar',
    'dhanyavaad': 'dhan-ya-vaad',
    'shukriya': 'shuk-ri-yaa',
    
    // Conversation starters/fillers
    'dekho': 'day-kho',
    'dekh': 'daykh',
    'suno': 'su-no',
    'bolo': 'bo-lo',
    'batao': 'ba-taa-o',
    'bataiye': 'ba-taa-ee-yay',
    'samjho': 'sam-jho',
    'samjhiye': 'sam-jhi-yay',
    'dekhiye': 'day-khi-yay',
    'suniye': 'su-ni-yay',
    'dijiye': 'dee-ji-yay',
    'lijiye': 'lee-ji-yay',
    'rakhiye': 'ra-khi-yay',
    'jaaniye': 'jaa-ni-yay',
    'sochiye': 'so-chi-yay',
    
    // Connectors
    'aur': 'aur',
    'ya': 'yaa',
    'lekin': 'lay-kin',
    'magar': 'ma-gar',
    'isliye': 'is-li-yay',
    'kyunki': 'kyun-ki',
    'agar': 'a-gar',
    'toh': 'toh',
    'to': 'toh',
    'phir': 'phir',
    'matlab': 'mat-lab',
    'yaani': 'yaa-nee',
    'jaise': 'jai-say',
    
    // Time words
    'pehle': 'peh-lay',
    'baad': 'baad',
    'abhi': 'ab-hee',
    'hamesha': 'ha-may-shaa',
    'kabhi': 'kab-hee',
    'saal': 'saal',
    'mahina': 'ma-hee-naa',
    
    // Reaction words
    'wah': 'waah',
    'arre': 'ar-ray',
    'haan': 'haan',
    'nahi': 'na-hee',
    'nahin': 'na-heen',
    'bilkul': 'bil-kul',
    'shayad': 'shaa-yad',
    
    // Relationship words
    'beta': 'bay-taa',
    'beti': 'bay-tee',
    'bhai': 'bhaai',
    'behen': 'be-hen',
    'didi': 'dee-dee',
    'masi': 'maa-see',
    'parivaar': 'pa-ri-vaar',
    'bachche': 'bach-chay',
    'bachchi': 'bach-chee',
    
    // Financial acronyms  
    'SIP': 'sip',
    'RD': 'aar dee',
    'PPF': 'pee pee eff',
    'NPS': 'en pee ess',
    'EMI': 'ee em aai',
    'FD': 'eff dee',
    'MF': 'em eff',
    'ELSS': 'ee el es es',
    'ITR': 'aai tee aar',
    'TDS': 'tee dee es',
    'GST': 'jee es tee',
    'PAN': 'pan card',
    'KYC': 'kay why see',
    'SSY': 'sukanya samridhi',
    'EPF': 'ee pee eff',
    
    // Symbols and numbers
    '₹': 'rupees',
    'lakh': 'laakh',
    'lakhs': 'laakhs',
    'crore': 'karor',
    'crores': 'karors',
    
    // Samaira specific
    'Samaira': 'Sa-mai-raa',
    'SamairaAI': 'Sa-mai-raa A I'
};

async function checkTTSProvider() {
    try {
        const response = await fetch(`${API_BASE}/tts/status`);
        const data = await response.json();
        AppState.usePremiumTTS = data.elevenlabs_available;
        console.log('TTS Provider:', AppState.usePremiumTTS ? 'ElevenLabs' : 'Browser');
    } catch (e) {
        AppState.usePremiumTTS = false;
    }
}

async function speakText(text) {
    // Stop any current speech first
    if (window.stopSpeaking) {
        window.stopSpeaking();
    }
    
    // Set speaking state
    if (window.VoiceState) {
        window.VoiceState.isSpeaking = true;
    }
    if (window.updateVoiceStatusUI) {
        window.updateVoiceStatusUI('🔊 Speaking...');
    }
    
    // Try premium TTS first
    if (AppState.usePremiumTTS) {
        try {
            const response = await fetch(`${API_BASE}/tts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            });
            const data = await response.json();
            
            if (data.success && data.audio) {
                playAudioBase64(data.audio);
                return;
            }
        } catch (e) {
            console.log('Premium TTS failed, using browser:', e);
        }
    }
    
    // Fallback to browser TTS
    speakWithBrowser(text);
}

function playAudioBase64(base64Audio) {
    const audio = new Audio(`data:audio/mp3;base64,${base64Audio}`);
    
    // Track audio element for interruption
    if (window.VoiceState) {
        window.VoiceState.currentAudio = audio;
    }
    
    audio.onended = () => {
        if (window.VoiceState) {
            window.VoiceState.currentAudio = null;
        }
        // Trigger conversation mode callback
        if (window.onSpeechComplete) {
            window.onSpeechComplete();
        }
    };
    
    audio.onerror = () => {
        if (window.VoiceState) {
            window.VoiceState.currentAudio = null;
            window.VoiceState.isSpeaking = false;
        }
        if (window.updateVoiceStatusUI) {
            window.updateVoiceStatusUI('');
        }
    };
    
    audio.play().catch(e => {
        console.log('Audio playback failed:', e);
        if (window.VoiceState) {
            window.VoiceState.isSpeaking = false;
        }
        if (window.updateVoiceStatusUI) {
            window.updateVoiceStatusUI('');
        }
    });
}

function speakWithBrowser(text) {
    if (!('speechSynthesis' in window)) {
        if (window.VoiceState) window.VoiceState.isSpeaking = false;
        if (window.updateVoiceStatusUI) window.updateVoiceStatusUI('');
        return;
    }
    
    speechSynthesis.cancel();
    
    let cleanText = text;
    
    // Step 1: Remove ALL emojis first (prevents TTS reading emoji names)
    cleanText = cleanText.replace(/[\u{1F300}-\u{1F9FF}]/gu, '');
    cleanText = cleanText.replace(/[\u{2600}-\u{26FF}]/gu, '');
    cleanText = cleanText.replace(/[\u{2700}-\u{27BF}]/gu, '');
    cleanText = cleanText.replace(/[\u{1F600}-\u{1F64F}]/gu, '');
    cleanText = cleanText.replace(/[\u{1F680}-\u{1F6FF}]/gu, '');
    cleanText = cleanText.replace(/[\u{1FA00}-\u{1FAFF}]/gu, '');
    
    // Step 2: Apply phonetic corrections for Hindi words
    for (const [word, replacement] of Object.entries(phoneticCorrections)) {
        const regex = new RegExp(`\\b${word}\\b`, 'gi');
        cleanText = cleanText.replace(regex, replacement);
    }
    
    // Step 3: Clean markdown and formatting
    cleanText = cleanText
        .replace(/\*\*/g, '')
        .replace(/\*/g, '')
        .replace(/^#+\s*/gm, '')
        .replace(/^[-*•]\s*/gm, '')
        .replace(/^\d+\.\s*/gm, '')
        .replace(/\n/g, '. ')
        .replace(/\s+/g, ' ')
        .trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    
    // Track utterance for interruption
    if (window.VoiceState) {
        window.VoiceState.currentUtterance = utterance;
    }
    
    const voice = getBestVoice();
    if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
    }
    
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    
    // Handle speech end for conversation mode
    utterance.onend = () => {
        if (window.VoiceState) {
            window.VoiceState.currentUtterance = null;
        }
        if (window.onSpeechComplete) {
            window.onSpeechComplete();
        }
    };
    
    utterance.onerror = () => {
        if (window.VoiceState) {
            window.VoiceState.currentUtterance = null;
            window.VoiceState.isSpeaking = false;
        }
        if (window.updateVoiceStatusUI) {
            window.updateVoiceStatusUI('');
        }
    };
    
    speechSynthesis.speak(utterance);
}

function getBestVoice() {
    if (selectedVoice) return selectedVoice;
    
    const voices = ttsVoices.length > 0 ? ttsVoices : speechSynthesis.getVoices();
    
    // Priority order for best Indian pronunciation:
    // 1. Microsoft Neerja (Hindi) - best for Hinglish
    // 2. Microsoft Heera (Hindi) 
    // 3. Any hi-IN female voice
    // 4. Any hi-IN voice
    // 5. Microsoft Indian English voices (Neerja Online, Ravi)
    // 6. Any en-IN female voice
    // 7. Any en-IN voice
    // 8. Google UK English Female (decent Hindi pronunciation)
    // 9. Any female English voice
    // 10. Any English voice
    
    selectedVoice = 
        voices.find(v => v.name.includes('Neerja') && v.lang === 'hi-IN') ||
        voices.find(v => v.name.includes('Heera') && v.lang === 'hi-IN') ||
        voices.find(v => v.lang === 'hi-IN' && v.name.toLowerCase().includes('female')) ||
        voices.find(v => v.lang === 'hi-IN') ||
        voices.find(v => v.name.includes('Neerja')) ||
        voices.find(v => v.name.includes('Microsoft') && v.lang === 'en-IN') ||
        voices.find(v => v.lang === 'en-IN' && v.name.toLowerCase().includes('female')) ||
        voices.find(v => v.lang === 'en-IN') ||
        voices.find(v => v.name.includes('Google UK English Female')) ||
        voices.find(v => v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
        voices.find(v => v.lang.startsWith('en')) ||
        voices[0];
    
    if (selectedVoice) {
        console.log('🔊 Selected voice:', selectedVoice.name, selectedVoice.lang);
    }
    
    return selectedVoice;
}

if ('speechSynthesis' in window) {
    ttsVoices = speechSynthesis.getVoices();
    speechSynthesis.onvoiceschanged = () => {
        ttsVoices = speechSynthesis.getVoices();
        selectedVoice = null;
        getBestVoice();
    };
}

// ===== UTILITIES =====
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML.replace(/'/g, "\\'");
}

// ===== EXPORTS FOR GLOBAL ACCESS =====
window.sendExample = sendExample;
window.copyMessage = copyMessage;
window.speakMessage = speakMessage;
window.speakText = speakText;
window.loadChat = loadChat;
window.AppState = AppState;
