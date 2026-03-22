# 🎬 ReelCraft AI

> Turn your images into AI-powered Instagram Reels with voice narration — built with Flask, ElevenLabs & FFmpeg.

---

## ✨ Features

- 📸 **Upload Images** — Upload multiple images to use as reel frames
- 🎙️ **AI Voice Over** — Type a script; ElevenLabs AI generates a natural voice
- 🎬 **Auto Reel Generation** — FFmpeg stitches images + audio into a 1080×1920 MP4
- 🔄 **Live Status Page** — Auto-refreshes until your reel is ready
- 🖼️ **Gallery** — Browse and watch all generated reels

---

## 🚀 Local Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourname/reelcraft-ai.git
cd reelcraft-ai
```

### 2. Create and activate a virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 5. Set up your API key
Copy `.env.example` to `api.env` and fill in your keys:
```bash
cp .env.example api.env
```
Then edit `api.env`:
```
ELEVENLABS_API_KEY=your_actual_key_here
SECRET_KEY=any_random_string
```
Get your free ElevenLabs key at [elevenlabs.io](https://elevenlabs.io)

### 6. Run the app
Open **two terminals**:

**Terminal 1 — Web server:**
```bash
python main.py
```

**Terminal 2 — Background worker (reel generator):**
```bash
python generate_process.py
```

Open your browser at [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ☁️ Deploy to Render

1. Push your code to GitHub (make sure `api.env` is in `.gitignore`)
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render will read `render.yaml` and create both services automatically
5. In the Render dashboard, add your environment variables:
   - `ELEVENLABS_API_KEY` = your key
   - `SECRET_KEY` = any random string
6. Click **Deploy**

> ⚠️ **Note**: FFmpeg must be available on the deployment server. Render's default Python image includes FFmpeg. If it doesn't, add a `build.sh` that installs it.

---

## 📁 Project Structure

```
DS.web/
├── main.py               # Flask web server
├── generate_process.py   # Background worker (reel generation)
├── text_to_audio.py      # ElevenLabs TTS integration
├── requirements.txt      # Python dependencies
├── Procfile              # Process definitions for deployment
├── render.yaml           # Render.com deployment config
├── .gitignore
├── .env.example
├── templates/
│   ├── base.html         # Shared layout (navbar, footer)
│   ├── index.html        # Home page
│   ├── create.html       # Reel creation form
│   ├── status.html       # Reel processing status
│   └── gallery.html      # Video gallery
├── static/
│   ├── css/
│   │   ├── style.css     # Global styles
│   │   ├── create.css    # Create page styles
│   │   └── gallery.css   # Gallery styles
│   └── reels/            # Generated .mp4 files (auto-created)
└── user_upload/          # Uploaded images (auto-created)
```

---

## 🔧 Tech Stack

| Component | Technology |
|---|---|
| Web Framework | Flask (Python) |
| AI Voice | ElevenLabs API |
| Video Processing | FFmpeg |
| Frontend | Bootstrap 5 + Vanilla CSS |
| Deployment | Render.com |

---

Made with ❤️ by Pushpendra
