# 🚀 Agentic AI Project - Complete Setup & Running Guide

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Requirements](#system-requirements)
3. [Project Architecture](#project-architecture)
4. [Installation & Setup](#installation--setup)
5. [Running the Application](#running-the-application)
6. [API Documentation](#api-documentation)
7. [Troubleshooting](#troubleshooting)
8. [Project Structure](#project-structure)

---

## 📺 Project Overview

This is an **AI-Powered Animated Video Generation System** that automatically creates animated videos from text prompts. The system orchestrates multiple specialized AI agents to:

1. **Generate stories** from user prompts (plot, dialogue, scene structure)
2. **Produce audio** with text-to-speech and background music
3. **Create visuals** with AI-generated images and animations
4. **Render final videos** with synchronized audio and visuals
5. **Allow post-production edits** via an interactive edit agent

### 🎯 Key Features
- ✅ End-to-end automated video generation
- ✅ Real-time progress tracking with WebSocket
- ✅ Multi-agent orchestration with LangGraph
- ✅ Intelligent post-production editing
- ✅ State management with undo/redo capabilities
- ✅ Full-stack application (Python backend + React frontend)

---

## 🖥️ System Requirements

### Prerequisites
- **Python 3.9 or higher** - Backend runtime
- **Node.js 16 or higher** - Frontend build and development
- **FFmpeg** - Video processing (must be in system PATH)
- **Git** (optional) - Version control
- **4GB+ RAM** - For AI model inference
- **Internet connection** - For API calls (Groq, HuggingFace)

### API Keys Required
You'll need accounts and API keys for:
1. **Groq API** - For LLM (text generation)
   - Sign up: https://console.groq.com
   - Get key from API keys section
2. **HuggingFace** - For image generation and processing
   - Sign up: https://huggingface.co
   - Get token from settings/tokens section

---

## 🏗️ Project Architecture

### High-Level Data Flow
```
User Prompt 
    ↓
Frontend (React UI)
    ↓ HTTP/WebSocket
Backend (FastAPI)
    ↓
Orchestrator (LangGraph Workflow)
    ├─ Story Agent (Generate story structure)
    ├─ Audio Agent (Generate dialogue & audio)
    ├─ Video Agent (Generate visuals & render)
    └─ Edit Agent (Post-production edits)
    ↓
Tools (LLM, Vision, Audio, Video, System)
    ↓
Final Video Output
```

### Technology Stack
| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend API | FastAPI + Uvicorn | REST API & WebSocket |
| Orchestration | LangGraph | State machine workflow |
| Agent Framework | LangChain | AI agent implementation |
| LLM | Groq API (llama-3.3-70b) | Text generation |
| Vision AI | Hugging Face (SDXL) | Image generation |
| Audio | Coqui TTS | Text-to-speech |
| Video | MoviePy + FFmpeg | Video composition |
| Frontend | React 18 + TypeScript + Vite | User interface |

### Directory Structure
```
Agentic Project/
├── backend/                  # FastAPI backend
│   ├── app.py               # Main application
│   ├── routes/              # API endpoints
│   ├── services/            # Business logic
│   └── websocket/           # WebSocket handlers
├── agents/                  # AI agents
│   ├── story_agent/         # Story generation
│   ├── audio_agent/         # Audio production
│   ├── video_agent/         # Video rendering
│   ├── edit_agent/          # Post-production editing
│   └── orchestrator/        # Workflow coordination
├── mcp/                     # Tool abstraction layer
│   ├── tools/               # Audio, video, vision, LLM tools
│   ├── base_tool.py        # Tool interface
│   └── tool_registry.py    # Tool management
├── state_manager/          # State & version control
├── shared/                 # Shared schemas & utilities
│   ├── schemas/            # Data models
│   ├── constants/          # Constants
│   └── utils/              # Utility functions
├── frontend/               # React application
│   ├── src/               # React components
│   ├── index.html         # HTML entry point
│   └── package.json       # Node dependencies
├── data/                   # Data storage (generated)
│   ├── outputs/           # Generated videos
│   ├── temp/              # Temporary files
│   └── state_versions/    # State snapshots
├── scripts/               # Startup scripts
├── requirements.txt       # Python dependencies
└── Readme.md             # Project readme
```

---

## 📦 Installation & Setup

### Step 1: Clone or Extract Project
```bash
cd "c:\Users\HP\Desktop\FAST\8th-sem\Agentic AI\project\Agentic Project\Agentic Project"
```

### Step 2: Install FFmpeg
**Windows (using Chocolatey):**
```powershell
choco install ffmpeg
```

**Windows (Manual Installation):**
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add to PATH environment variable
4. Verify: `ffmpeg -version` in terminal

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# Mac (Homebrew)
brew install ffmpeg
```

### Step 3: Create Environment File
Create a `.env` file in the project root:
```env
# Groq API Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# HuggingFace Configuration
HUGGINGFACE_API_KEY=your_huggingface_token_here
HF_IMAGE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
HF_REMOVE_BG_MODEL=briaai/RMBG-1.4

# TTS Configuration
TTS_MODEL_NAME=tts_models/en/vctk/vits

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_ORIGIN=http://localhost:5173
```

### Step 4: Install Python Dependencies
```powershell
# Navigate to project root if not already there
cd "c:\Users\HP\Desktop\FAST\8th-sem\Agentic AI\project\Agentic Project\Agentic Project"

# Create virtual environment (optional but recommended)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import langchain; import fastapi; print('✓ All dependencies installed')"
```

### Step 5: Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

### Step 6: Verify Installation
```powershell
# Check Python packages
pip list | findstr fastapi langchain langchain-groq

# Check Node packages
cd frontend && npm list react && cd ..

# Check FFmpeg
ffmpeg -version
```

---

## ▶️ Running the Application

### Option A: Using Provided Scripts (Recommended for Windows)

**Terminal 1 - Start Backend:**
```powershell
# From project root
.\scripts\start_backend.ps1
```

**Terminal 2 - Start Frontend:**
```powershell
# From project root
.\scripts\start_frontend.ps1
```

**Terminal 3 - Monitor Logs (Optional):**
```powershell
Get-Content "data/logs.txt" -Wait
```

### Option B: Manual Start (All Platforms)

**Terminal 1 - Start Backend:**
```bash
# Windows PowerShell
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

# Linux/Mac
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

### Step: Access the Application

Once both services are running:

1. **Frontend Application**
   - URL: http://localhost:5173
   - You should see the video generation interface

2. **Backend API**
   - Health Check: http://localhost:8000/health
   - API Docs (Swagger): http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **Monitor Real-time Progress**
   - Backend logs will show: "Phase: Story Generation" → "Audio Production" → "Video Rendering"
   - Frontend displays real-time progress bar

---

## 🔄 Typical Workflow

1. **Open Frontend** (http://localhost:5173)
2. **Enter Prompt** - Describe the video you want to generate
3. **Submit** - Click "Generate Video"
4. **Monitor Progress**
   - Watch real-time progress on frontend
   - Backend logs show agent execution
5. **Wait for Completion** - Can take 2-10 minutes depending on complexity
6. **View Generated Video** - Auto-plays when ready
7. **Edit (Optional)** - Use edit panel for post-production changes
8. **Download/Save** - Save the final video

---

## 📚 API Documentation

### REST Endpoints

#### Start Video Generation
```
POST /api/pipeline/start
Content-Type: application/json

Request:
{
  "prompt": "Create a 60-second story about a space explorer discovering a new planet"
}

Response:
{
  "job_id": "job_12345",
  "status": "queued",
  "message": "Video generation started"
}
```

#### Get Job Status
```
GET /api/pipeline/{job_id}

Response:
{
  "job_id": "job_12345",
  "status": "in_progress",
  "current_phase": "video_generation",
  "progress": 75,
  "events": [
    {
      "timestamp": "2024-01-20T10:30:00",
      "phase": "story_generation",
      "message": "Story structure generated successfully"
    }
  ]
}
```

### WebSocket Connection

For real-time progress:
```
WebSocket: ws://localhost:8000/ws/progress/{job_id}

Messages:
{
  "phase": "audio_generation",
  "progress": 45,
  "message": "Generating dialogue audio..."
}
```

### Full API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🛠️ Troubleshooting

### Backend Won't Start

**Error: `ModuleNotFoundError: No module named 'fastapi'`**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error: `Port 8000 already in use`**
```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :8000
kill -9 <PID>

# Or use different port
uvicorn backend.app:app --port 8001
```

**Error: `GROQ_API_KEY not found`**
```bash
# Verify .env file exists in project root with:
# GROQ_API_KEY=your_actual_key
# Restart backend after adding .env
```

### Frontend Won't Start

**Error: `npm: command not found`**
```bash
# Install Node.js from https://nodejs.org
# Or on Windows with chocolatey:
choco install nodejs
```

**Error: `npm ERR! ERESOLVE unable to resolve dependency tree`**
```bash
cd frontend
npm install --legacy-peer-deps
cd ..
```

**Port 5173 already in use**
```bash
cd frontend
npm run dev -- --port 5174  # Use different port
```

### Video Generation Issues

**Error: `FFmpeg not found`**
```bash
# Verify FFmpeg in PATH
ffmpeg -version

# If not found, reinstall and add to PATH
# Windows: setx PATH "%PATH%;C:\ffmpeg\bin"
```

**Error: `CUDA out of memory`**
- Reduce video resolution in shared/constants/__init__.py
- Or reduce DEFAULT_VIDEO_FPS from 24 to 12

**Error: `HuggingFace model download failed`**
```bash
# Ensure internet connection
# Check HuggingFace token: HUGGINGFACE_API_KEY in .env
# Models will download automatically on first use
```

### WebSocket Connection Issues

**Problem: Real-time progress not updating**
- Ensure both backend and frontend are running
- Check browser console for errors (F12 in browser)
- Verify WebSocket URL matches: ws://localhost:8000/ws/progress/{job_id}

---

## 📊 Monitoring & Debugging

### Check Backend Logs
```powershell
# Real-time logs
Get-Content "data/logs.txt" -Wait

# Or from backend startup you'll see:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Press CTRL+C to quit
```

### Check Frontend Logs
- Open browser DevTools: F12 or Right-Click → Inspect
- Check Console tab for errors
- Check Network tab for API requests

### Check Job Status
```bash
# Query job status
curl http://localhost:8000/api/pipeline/job_12345 | python -m json.tool
```

### View Generated Files
```bash
# Output directory
cd data/outputs/{job_id}
ls -la  # Linux/Mac
dir     # Windows
```

---

## 📁 Output Files Location

After generation, files are saved in:
```
data/outputs/{job_id}/
├── story_spec.json           # Generated story structure
├── audio/
│   ├── master_dialogue.wav   # Combined audio track
│   └── timing_manifest.json  # Lip-sync timing info
├── video/
│   ├── final_output.mp4      # Final rendered video
│   ├── background_*.png      # Generated backgrounds
│   └── character_*.png       # Generated character images
└── job_state.json            # Job completion state
```

### Download Generated Video
1. Video auto-plays in frontend when ready
2. Right-click → "Save video as..." to download
3. Or access directly from: `data/outputs/{job_id}/video/final_output.mp4`

---

## 🚀 Advanced Configuration

### Modify Video Parameters
Edit `shared/constants/__init__.py`:
```python
DEFAULT_VIDEO_FPS = 24              # Frames per second
DEFAULT_VIDEO_RESOLUTION = (1280, 720)  # Width x Height
DEFAULT_TARGET_DURATION_SECONDS = 60    # Target video length
```

### Change LLM Model
Edit `.env`:
```env
GROQ_MODEL=mixtral-8x7b-32768  # Or other Groq models
```

### Add Custom Tools
1. Create tool class in `mcp/tools/custom_tools/`
2. Inherit from `base_tool.BaseTool`
3. Register in `mcp/tool_registry.py`

---

## 📞 Support & Resources

### Key Files to Understand
- **Workflow**: `agents/orchestrator/workflow.py`
- **State Management**: `state_manager/state_manager.py`
- **API Endpoints**: `backend/routes/`
- **Agent Logic**: `agents/{agent_name}/agent.py`

### External Resources
- LangChain Docs: https://python.langchain.com
- LangGraph Docs: https://langchain-ai.github.io/langgraph/
- FastAPI Docs: https://fastapi.tiangolo.com
- Groq API: https://console.groq.com

---

## ⚙️ Performance Tips

1. **First Run Takes Longer**
   - Models download automatically (1-2GB total)
   - Subsequent runs are faster

2. **Optimize for Speed**
   - Reduce video resolution in constants
   - Use shorter prompts (fewer scenes = faster)
   - Run on machine with GPU if available

3. **Optimize for Quality**
   - Increase video resolution
   - Use longer, detailed prompts
   - Allow more time for processing

---

## 🔐 Security Notes

1. **Keep API Keys Safe**
   - Never commit `.env` to version control
   - Don't share `.env` file
   - Regenerate keys if exposed

2. **Network Security**
   - Backend runs on `localhost:8000` by default
   - In production, use proper HTTPS and authentication
   - Change `FRONTEND_ORIGIN` for production

---

## 📝 Environment Variables Summary

```env
# Required
GROQ_API_KEY=your_groq_key
HUGGINGFACE_API_KEY=your_hf_token

# Optional (defaults provided)
GROQ_MODEL=llama-3.3-70b-versatile
TTS_MODEL_NAME=tts_models/en/vctk/vits
HF_IMAGE_MODEL=stabilityai/stable-diffusion-xl-base-1.0
HF_REMOVE_BG_MODEL=briaai/RMBG-1.4
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_ORIGIN=http://localhost:5173
```

---

## ✅ Quick Start Checklist

- [ ] Python 3.9+ installed
- [ ] Node.js 16+ installed
- [ ] FFmpeg installed and in PATH
- [ ] Groq API key obtained
- [ ] HuggingFace token obtained
- [ ] `.env` file created with API keys
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Frontend dependencies installed: `npm install` in `frontend/`
- [ ] Backend started: `.\scripts\start_backend.ps1`
- [ ] Frontend started: `.\scripts\start_frontend.ps1`
- [ ] Frontend accessible at http://localhost:5173
- [ ] Backend API docs at http://localhost:8000/docs

---

## 🎬 Example Prompts to Try

1. **Short Story**
   > "Create a 30-second animated story about a cat discovering a mysterious box in an ancient library"

2. **Educational Content**
   > "Generate a 60-second educational video explaining how photosynthesis works"

3. **Fantasy Adventure**
   > "Create an animated fantasy sequence about a knight battling a dragon in a magical kingdom"

---

## 📄 License & Attribution

This project demonstrates:
- LangChain & LangGraph for agent orchestration
- FastAPI for backend API
- React for frontend UI
- Integration with Groq, HuggingFace, and other AI APIs

---

## 🤝 Contributing

To extend this project:
1. Add new agents in `agents/`
2. Register tools in `mcp/tools/`
3. Extend state in `agents/orchestrator/state.py`
4. Add new API routes in `backend/routes/`
5. Update frontend components in `frontend/src/components/`

---

**Last Updated**: January 2025
**Version**: 1.0
**Status**: Production Ready ✅
