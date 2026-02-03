# SamairaAI - Indian Financial Literacy Companion 🪷

<p align="center">
  <strong>Aapka Personal Financial Companion - Simple Hinglish Mein! 💰</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#demo">Demo</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#contributing">Contributing</a>
</p>

---

## 🌟 About

**SamairaAI** is a voice-first conversational AI designed to make financial literacy accessible to every Indian family. Speaking naturally in Hinglish (Hindi + English), Samaira helps users understand savings, investments, and government schemes without the intimidating jargon.

> "Har parivaar ke liye financial freedom!" 🙏

## ✨ Features

### 🎙️ Voice-First Experience
- **Speech-to-Text**: Whisper-powered transcription for Hinglish
- **Text-to-Speech**: Natural voice responses with Hindi pronunciation
- **Click-to-Record**: Simple voice input interface

### 💬 Intelligent Conversations
- **Context-Aware**: Remembers your goals and preferences throughout the conversation
- **Hinglish Native**: Speaks naturally like a friendly financial advisor
- **Educational Focus**: Explains concepts simply with relatable examples

### 📊 Financial Tools
- **SIP Calculator**: Mutual fund investment projections
- **RD Calculator**: Recurring deposit maturity calculations  
- **SIP vs RD Comparison**: Side-by-side analysis
- **Goal Planning**: Education, wedding, retirement calculators

### 🏛️ Government Schemes Education
- PPF (Public Provident Fund)
- SSY (Sukanya Samriddhi Yojana)
- NPS (National Pension System)
- EPF (Employee Provident Fund)
- Senior Citizen Schemes

### 🛡️ Safety & Compliance
- Never recommends specific stocks or funds
- Always adds educational disclaimers
- Suggests professional advisors for complex decisions

## 🎬 Demo

**Try asking:**
- "SIP aur RD mein kya difference hai?"
- "Meri beti 5 saal ki hai, uski padhai ke liye savings kaise karun?"
- "PPF ke baare mein batao"
- "Emergency fund kitna hona chahiye?"

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **LLM**: Google Gemini 2.0 Flash
- **Speech Recognition**: OpenAI Whisper
- **Session Management**: In-memory store

### Frontend
- **UI**: Vanilla HTML/CSS/JavaScript
- **Voice**: Web Speech API
- **Design**: Mobile-first responsive

### AI/ML
- **Language Model**: Gemini for conversational AI
- **ASR**: Whisper (small model optimized for Hinglish)
- **TTS**: Browser Web Speech API with Hindi voice support

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- ffmpeg (for audio processing)
- Google Gemini API key

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/samaira-ai.git
cd samaira-ai
```

2. **Set up Python environment**
```bash
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

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

5. **Run the server**
```bash
cd backend
uvicorn main:app --reload --port 8000
```

6. **Open the app**
```
http://localhost:8000/
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `WHISPER_MODEL` | Whisper model size | `small` |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `true` |

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
│   ├── services/            # Gemini, Whisper, TTS integrations
│   └── main.py              # FastAPI application entry
├── frontend/
│   ├── index.html           # Main chat UI
│   ├── styles.css           # Modern responsive styling
│   ├── app.js               # Chat logic & TTS
│   └── voice.js             # Voice recording handler
├── .env.example             # Environment template
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
