# 🎤 Microphone Troubleshooting Guide

## Common Issue: "Could not access microphone"

This error occurs when the browser cannot access your microphone. Here's how to fix it:

---

## ✅ Quick Fix Steps

### 1. **Grant Microphone Permission**
   - Look for the **🔒 lock icon** or **🎤 microphone icon** in your browser's address bar (left side)
   - Click it and select **"Allow microphone access"**
   - Refresh the page and try again

   **Chrome/Edge:**
   ```
   Address Bar → 🔒 → Site Settings → Microphone → Allow
   ```

   **Firefox:**
   ```
   Address Bar → 🔒 → Permissions → Microphone → Allow
   ```

### 2. **Check Microphone Connection**
   - Verify your microphone is **physically connected** to your computer
   - Test it in other apps (Windows Voice Recorder, Discord, etc.)
   - Windows: Settings → System → Sound → Input → Test your microphone

### 3. **Close Competing Apps**
   - Some apps (Zoom, Teams, Skype) may block microphone access
   - **Close ALL other apps** using the microphone
   - Then try again

### 4. **Use a Supported Browser**
   - ✅ **Chrome** (Recommended)
   - ✅ **Edge** (Recommended)
   - ✅ **Firefox**
   - ❌ Internet Explorer (Not supported)
   - ⚠️ Safari (Limited support)

### 5. **Check Windows Microphone Privacy Settings**
   1. Press `Win + I` to open Windows Settings
   2. Go to **Privacy → Microphone**
   3. Make sure:
      - "Allow apps to access your microphone" is **ON**
      - "Allow desktop apps to access your microphone" is **ON**

---

## 🚀 Testing Instructions

### **Regular Voice Mode:**
1. Open the app at `http://localhost:8000`
2. Click the **🎤 microphone button**
3. When prompted, click **"Allow"** for microphone access
4. Speak your message
5. Click **⏹️ stop button** when done

### **Real-Time Voice Mode (⚡):**
1. Click the **⚡ lightning bolt** button to enable real-time mode
2. Click the **🎤 microphone button**
3. When prompted, click **"Allow"** for microphone access
4. Start speaking - your voice will stream live!
5. Click **🎤** again to stop

---

## 🔍 Detailed Error Messages

The app now shows **specific error messages** to help diagnose the issue:

| Error | Meaning | Solution |
|-------|---------|----------|
| **Permission Denied** | You clicked "Block" on the permission prompt | Click 🔒 in address bar → Allow microphone |
| **No Microphone Found** | No mic detected on your computer | Connect a microphone and refresh |
| **Microphone In Use** | Another app is using the microphone | Close Zoom/Teams/Skype and try again |
| **Browser Not Supported** | Your browser doesn't support WebRTC | Use Chrome or Edge |

---

## 🛠️ Advanced Troubleshooting

### Check Browser Console
1. Press `F12` to open Developer Tools
2. Go to **Console** tab
3. Look for microphone-related errors
4. Common errors:
   - `NotAllowedError` → Permission denied
   - `NotFoundError` → No microphone detected
   - `NotReadableError` → Microphone in use by another app

### Test Microphone in Browser
1. Open `chrome://settings/content/microphone` (Chrome)
2. Check if your microphone is listed
3. Make sure it's not blocked for `localhost`

### Reset Browser Permissions
1. Go to browser settings
2. Search for "Site Settings" or "Permissions"
3. Find `http://localhost:8000`
4. Reset permissions
5. Refresh and grant access again

---

## 💡 Pro Tips

- **Use headphones** to prevent echo/feedback
- **Reduce background noise** for better transcription
- **Speak clearly** in Hindi/English (Hinglish supported!)
- **Wait for the mic to activate** before speaking
- The **⚡ real-time mode** provides the best experience for natural conversations

---

## 📞 Still Having Issues?

If none of these solutions work:

1. **Restart your browser** completely
2. **Restart your computer** (fixes most audio driver issues)
3. **Update your browser** to the latest version
4. **Check antivirus/firewall** - they might be blocking microphone access
5. **Try a different microphone** if available

---

## ✨ What's New

Your SamairaAI now has **enhanced microphone error handling**:
- ✅ Clear, actionable error messages
- ✅ Browser compatibility checks
- ✅ Permission status detection
- ✅ Hardware detection
- ✅ Conflict detection with other apps

The app will **guide you step-by-step** if something goes wrong!

---

**Happy conversing! 🪷**
