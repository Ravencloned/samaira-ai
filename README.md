# SamairaAI - Indian Financial Literacy Companion 🪷

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0.0-orange" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10+-blue" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

<p align="center">
  <strong>Aapka Personal Financial Companion - Simple Hinglish Mein! 💰</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#api-documentation">API Docs</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## 🌟 About

**SamairaAI** is a production-ready, voice-first conversational AI designed to make financial literacy accessible to every Indian family. Speaking naturally in Hinglish (Hindi + English), Samaira helps users understand savings, investments, and government schemes without intimidating jargon.

> "Har parivaar ke liye financial freedom!" 🙏

## ✨ Features

### 🎙️ Voice-First Experience
- **Speech-to-Text**: Whisper-powered transcription optimized for Hinglish
- **Text-to-Speech**: Natural voice responses (Edge TTS / Azure / ElevenLabs)
- **Spacebar Recording**: Press spacebar to toggle voice input
- **Conversation Mode**: Hands-free voice interaction

### 💬 Intelligent Conversations (ChatGPT-like Experience)
- **Streaming Responses**: Real-time word-by-word responses with SSE
- **Markdown Rendering**: Beautiful formatted responses with lists, bold, headers
- **Suggested Questions**: Context-aware follow-up suggestions
- **Chat History**: Persisted conversation history in sidebar
- **User Intelligence**: Learns user preferences and goals over time
- **MCP Memory**: Model Context Protocol for persistent context

### 📊 Financial Tools
- **SIP Calculator**: Mutual fund investment projections
- **RD Calculator**: Recurring deposit maturity calculations  
- **SIP vs RD Comparison**: Side-by-side analysis with visual charts
- **Goal Planning**: Education, wedding, home, retirement calculators
- **Bank Rate Comparison**: Live FD/RD rates from major banks

### 🏛️ Government Schemes Education
- PPF (Public Provident Fund) with current rates
- SSY (Sukanya Samriddhi Yojana)
- NPS (National Pension System)
- PMJJBY, PMSBY insurance schemes
- Senior Citizen Savings Schemes

### 🛡️ Safety & Compliance
- Never recommends specific stocks or funds
- Always adds educational disclaimers
- Suggests professional advisors for complex decisions
- Input validation and safety checks

### 🔧 Production Features
- **Structured Logging**: Request tracing with correlation IDs
- **Health Checks**: `/health` endpoint with service status
- **Connection Monitoring**: Auto-reconnect with visual indicators
- **Error Handling**: Graceful errors with retry logic
- **Toast Notifications**: User feedback for all actions

## 🏗️ Architecture

```
samaira-ai/
├── backend/
│   ├── main.py                 # FastAPI app with middleware
│   ├── api/routes/
│   │   ├── chat.py            # Chat endpoints (streaming + non-streaming)
│   │   ├── voice.py           # Voice transcription & TTS
│   │   ├── session.py         # Session management
│   │   ├── banks.py           # Bank rates API
│   │   └── memory.py          # MCP memory endpoints
│   ├── core/
│   │   ├── conversation.py    # Orchestrator (intent → context → LLM)
│   │   ├── intent.py          # Hinglish intent detection
│   │   ├── safety.py          # Safety checks & disclaimers
│   │   └── state.py           # Session state management
│   ├── services/
│   │   ├── llm_service.py     # LLM abstraction (Groq/Gemini)
│   │   ├── tts_service.py     # TTS abstraction (Edge/Azure/ElevenLabs)
│   │   ├── whisper_asr.py     # Whisper transcription
│   │   └── user_intelligence.py # User profiling
│   ├── financial/
│   │   ├── calculators.py     # SIP, RD, FD calculators
│   │   ├── knowledge_base.py  # Curated financial knowledge
│   │   └── schemes.py         # Government schemes info
│   └── memory/
│       ├── mcp.py             # Model Context Protocol
│       └── storage.py         # Persistent storage
├── frontend/
│   ├── index.html             # Main UI
│   ├── app.js                 # Chat logic with retry
│   ├── voice.js               # Voice recording
│   └── styles.css             # Premium UI styles
└── tests/
    ├── test_calculators.py
    ├── test_intents.py
    └── test_safety.py
```

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- ffmpeg (for audio processing)
- Groq API key (FREE at https://console.groq.com/keys)

### Installation

```bash
# Clone the repository
git clone https://github.com/Ravencloned/samaira-ai.git
cd samaira-ai

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
copy .env.example .env  # Then edit with your API keys
```

### Environment Variables

Create a `.env` file in the root directory:

```env
# LLM Provider (groq recommended - FREE)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here

# Optional: Google Gemini (fallback)
GEMINI_API_KEY=your_gemini_key_here

# TTS (edge is FREE and works great for Hinglish)
TTS_PROVIDER=edge

# Optional: Premium TTS
AZURE_SPEECH_KEY=your_azure_key
AZURE_SPEECH_REGION=centralindia
ELEVENLABS_API_KEY=your_elevenlabs_key

# Server
DEBUG=true
PORT=8000
```

### Run the Server

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Open http://localhost:8000 in your browser.

## 📡 API Documentation

### Health Check
```http
GET /health
```
Returns service status and uptime.

### Chat (Streaming)
```http
POST /api/chat/stream
Content-Type: application/json

{
  "message": "SIP kya hai?",
  "session_id": "optional-session-id"
}
```
Returns Server-Sent Events (SSE) stream.

### Chat (Non-Streaming)
```http
POST /api/chat
Content-Type: application/json

{
  "message": "SIP kya hai?",
  "session_id": "optional-session-id"
}
```

### Voice Chat
```http
POST /api/voice/chat
Content-Type: multipart/form-data

audio: <audio file>
session_id: optional
```

### Calculate
```http
POST /api/calculate
Content-Type: application/json

{
  "calc_type": "sip",
  "amount": 5000,
  "years": 10,
  "rate": 12.0
}
```

### Session
```http
POST /api/session/create    # Create new session
GET /api/session/{id}       # Get session info
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_calculators.py -v

# Test API manually
python test_api.py
```

## 🚢 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Azure Web App

1. Create Azure Web App (Python 3.10)
2. Set environment variables in Configuration
3. Deploy via GitHub Actions or Azure CLI

### Render

1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

## 🎬 Demo

**Try asking:**
- "SIP aur RD mein kya difference hai?"
- "Meri beti 5 saal ki hai, uski padhai ke liye savings kaise karun?"
- "PPF ke baare mein batao"
- "Emergency fund kitna hona chahiye?"
- "HDFC aur SBI FD rates compare karo"

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python 3.10+) |
| LLM | Groq (Llama 3.3 70B) - FREE |
| ASR | OpenAI Whisper |
| TTS | Edge TTS (FREE) / Azure / ElevenLabs |
| Frontend | Vanilla JS + CSS |
| Markdown | marked.js |
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Get FREE API keys**

   **Groq (Required - FREE):**
   - Go to https://console.groq.com/keys
   - Create account and get API key
   - 30 requests/minute FREE!

   **ElevenLabs (Optional - FREE):**
   - Go to https://elevenlabs.io
   - Create account for natural TTS
   - 10,000 characters/month FREE!

5. **Configure environment**
```bash
# Edit .env file with your keys:
GROQ_API_KEY=gsk_your_key_here
LLM_PROVIDER=groq

# Optional for better voice:
ELEVENLABS_API_KEY=your_key_here
TTS_PROVIDER=elevenlabs
```

6. **Run the server**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

7. **Open the app**
```
http://localhost:8000/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key (FREE) | Required |
| `LLM_PROVIDER` | LLM provider (`groq` or `gemini`) | `groq` |
| `GEMINI_API_KEY` | Google Gemini API key (backup) | Optional |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key (FREE tier) | Optional |
| `TTS_PROVIDER` | TTS provider (`elevenlabs` or `browser`) | `browser` |
| `WHISPER_MODEL` | Whisper model size | `small` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |

### Whisper Models
- `tiny`: Fastest, lowest accuracy
- `base`: Good balance for English
- `small`: **Recommended** for Hinglish
- `medium`: Better accuracy, slower
- `large`: Best accuracy, requires GPU

## 📁 Project Structure

```
samaira-ai/
├── backend/
│   ├── api/
│   │   └── routes/          # API endpoints (chat, voice, session)
│   ├── config/              # Settings & configuration
│   ├── core/                # Core business logic & state management
│   ├── financial/           # Calculators & government schemes
│   ├── prompts/             # LLM system prompts
│   ├── services/            # LLM, Whisper, TTS integrations
│   │   ├── groq_client.py   # Groq/Llama 3 client
│   │   ├── gemini_client.py # Google Gemini client
│   │   ├── llm_service.py   # Unified LLM interface
│   │   ├── elevenlabs_tts.py# Natural TTS
│   │   └── whisper_asr.py   # Speech recognition
│   └── main.py              # FastAPI application entry
├── frontend/
│   ├── index.html           # Modern ChatGPT-like UI
│   ├── styles.css           # Premium styling + dark mode
│   ├── app.js               # Streaming, markdown, TTS
│   └── voice.js             # Voice recording handler
├── .env                     # Your API keys (create from .env.example)
├── requirements.txt         # Python dependencies
└── README.md
```

## 🚀 Usage

### Chat Interface
Type your question or click the microphone button to speak. SamairaAI will respond in Hinglish with helpful financial education.

### Voice Commands
1. Click the green microphone button 🎤
2. Speak your question in Hindi, English, or Hinglish
3. Click again to stop recording
4. Wait for the AI response (with audio playback)

### Quick Actions
Use the preset buttons on the welcome screen:
- 📊 SIP vs RD - Compare investment options
- 🎓 Education Planning - Plan for children's education
- 🏛️ Govt Schemes - Learn about PPF, SSY, NPS
- 💰 Emergency Fund - Build your safety net

## 🤝 Contributing

Contributions are welcome! 

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Google Gemini team for the powerful LLM API
- OpenAI for Whisper speech recognition
- The Indian fintech community for inspiration

---

<p align="center">
  Made with ❤️ for Indian families
</p>

<p align="center">
  <sub>⚠️ Disclaimer: SamairaAI provides educational information only, not financial advice. Please consult certified advisors for investment decisions.</sub>
</p>
