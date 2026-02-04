# SamairaAI - Vercel Deployment

This project is deployed on Vercel with the following configuration:

## Environment Variables (Set in Vercel Dashboard)

1. **GROQ_API_KEY** - Your Groq API key for Llama 4
2. **GEMINI_API_KEY** (optional) - Fallback Gemini API key
3. **LLM_PROVIDER** - Set to "groq" (default)
4. **WHISPER_MODEL** - Set to "base" (lighter model for serverless)
5. **TTS_SERVICE** - Set to "edge" (uses Edge TTS, no API key needed)

## Deployment Instructions

### One-Click Deploy

Click the button below to deploy to Vercel:

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Ravencloned/samaira-ai)

### Manual Deployment

1. **Install Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   vercel
   ```

4. **Set Environment Variables:**
   - Go to your Vercel dashboard
   - Select your project
   - Go to Settings → Environment Variables
   - Add your API keys:
     - `GROQ_API_KEY`: Your Groq API key
     - `GEMINI_API_KEY`: (optional) Your Gemini API key

5. **Redeploy to apply environment variables:**
   ```bash
   vercel --prod
   ```

## Vercel Limitations & Workarounds

### ⚠️ Important Notes:

1. **Real-Time Voice Streaming (WebSocket)**
   - Vercel has limited WebSocket support
   - Real-time voice streaming (`⚡` button) may not work
   - **Workaround:** Use regular voice mode (🎤 button without real-time)

2. **Whisper Model Size**
   - `medium` model is too large for Vercel (>500MB)
   - **Solution:** Using `base` model (smaller, faster, ~150MB)
   - Set `USE_FASTER_WHISPER=false` and `WHISPER_MODEL=base`

3. **Function Timeout**
   - Vercel free tier has 10s timeout
   - Pro tier has 60s timeout
   - Voice transcription should work fine with `base` model

4. **Cold Starts**
   - First request may be slow (5-10s) due to model loading
   - Subsequent requests will be faster

## Recommended Deployment Architecture

For best performance, consider this hybrid approach:

### Option 1: Frontend on Vercel + Backend on Railway/Render
- Deploy frontend (HTML/CSS/JS) on Vercel
- Deploy backend (FastAPI) on Railway/Render
- Update API endpoints in frontend to point to backend URL

### Option 2: Full Stack on Railway/Render
- Deploy everything on Railway/Render
- Better support for WebSockets and long-running processes
- Can use larger Whisper models

### Option 3: Vercel (Current Setup)
- **Best for:** Quick demos, testing
- **Limitations:** No real-time voice, smaller models only
- **Advantages:** Fast deployment, global CDN, easy scaling

## Testing Your Deployment

1. Visit your Vercel URL: `https://your-app.vercel.app`
2. Test text chat first (should work perfectly)
3. Test regular voice mode (🎤 button)
4. Real-time mode (⚡) may not work due to WebSocket limitations

## Post-Deployment Checklist

- [ ] Environment variables set in Vercel dashboard
- [ ] Text chat working
- [ ] Voice input working (regular mode)
- [ ] TTS (voice output) working
- [ ] Check Vercel logs for any errors

## Troubleshooting

### "Module not found" error
- Make sure `requirements.txt` is in project root
- Vercel installs dependencies automatically

### "Function timeout" error
- Using `base` Whisper model should fix this
- Check Vercel function logs

### Voice not working
- Check browser console for errors
- Ensure microphone permissions granted
- Try regular voice mode instead of real-time

### API errors
- Verify environment variables are set correctly
- Check Vercel function logs for details

## Alternative Deployment (Recommended for Full Features)

For full real-time voice streaming support, deploy to:

**Railway** (Recommended):
```bash
# Install Railway CLI
npm install -g railway

# Login
railway login

# Deploy
railway up
```

**Render**:
- Connect GitHub repo
- Select "Web Service"
- Set build command: `pip install -r requirements.txt`
- Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

---

**Questions? Issues?** Check the main README.md or open an issue on GitHub.
