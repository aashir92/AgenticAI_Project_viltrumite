# Agentic AI Video Pipeline 🎬

> An end-to-end **Visual Novel Video Generator** powered by LangGraph, Groq LLM, Pollinations.ai (free image generation), and MoviePy — with a live React frontend, WebSocket progress streaming, and a natural-language **Edit Agent** with multi-level undo.

---

## What It Does

| Stage | What Happens |
|-------|-------------|
| **Story Agent** | Groq LLM generates a structured story (characters, scenes, dialogue) |
| **Audio Agent** | Gender-aware TTS (Windows SAPI5 Zira/David) creates per-line WAV files |
| **Image Gen** | Pollinations.ai (free, no API key) generates character sprites + scene backgrounds |
| **BG Removal** | `rembg` cuts characters out for transparent PNG overlays |
| **Video Agent** | MoviePy composites animated Ken-Burns backgrounds + characters + lip-sync into MP4 |
| **Edit Agent** | LangGraph node classifies natural-language edits via Groq LLM, applies them, persists versioned state snapshots |

---

## Architecture

```
┌─────────────┐  WebSocket   ┌─────────────────────────────────┐
│  React UI   │◄────────────►│  FastAPI Backend  (port 8001)   │
└─────────────┘              └──────┬──────────────────────────┘
                                    │ LangGraph orchestrator
          ┌─────────────────────────┼──────────────────────┐
          ▼                         ▼                       ▼
    Story Agent             Audio Agent              Video Agent
    (Groq LLM)              (pyttsx3 TTS)       (MoviePy + PIL + rembg)
          │                         │                       │
          └──────────── data/outputs/{job_id}/ ─────────────┘
                                    │
                          Edit Agent (LangGraph)
                          StateManager → data/state_versions/{job_id}/
```

---

## Features

- ✅ **100% free** — Pollinations.ai (no key), Groq free tier, rembg (local)
- ✅ **Animated backgrounds** — Ken-Burns pan/zoom with vignette + contrast boost
- ✅ **Gender-aware TTS** — female characters get Zira voice automatically
- ✅ **Turn-wise character rendering** — only the speaker is visible per line
- ✅ **Lip-sync mouth overlay** — amplitude-based open/close at face position
- ✅ **Video trims to exact dialogue length** — no silent tail
- ✅ **Natural-language Edit Agent** — 10 intent types, Groq classification
- ✅ **Multi-level undo** — in-memory stack + disk-persisted JSON snapshots
- ✅ **66 tests** — unit (45) + integration (21) all passing

---

## Project Structure

```
.
├── agents/
│   ├── audio_agent/        # Gender-aware TTS agent
│   ├── edit_agent/         # LangGraph edit + undo agent + tests
│   ├── orchestrator/       # LangGraph pipeline graph
│   ├── story_agent/        # Groq story generator
│   └── video_agent/        # MoviePy compositor
├── backend/
│   ├── app.py              # FastAPI app
│   ├── routes/             # REST + WebSocket endpoints
│   └── services/           # Pipeline orchestration service
├── frontend/               # React + TypeScript UI
├── mcp/tools/              # Image gen, TTS, compositor tools
├── shared/
│   ├── schemas/            # Pydantic models for all data contracts
│   └── utils/              # Logger, JSON helpers, settings
├── state_manager/          # Versioned state persistence (history.json + v_N.json)
├── tests/
│   ├── unit/               # Schema + VideoAgent helper tests (45 tests, no API)
│   └── integration/        # Live Groq LLM edit agent tests (21 tests)
├── scripts/
│   └── demo_edit_agent.py  # Scripted 11-step Edit Agent demo
├── data/
│   ├── outputs/{job_id}/   # Generated audio, images, video per job
│   └── state_versions/{job_id}/ # Versioned state snapshots (v_1.json, v_2.json, …)
├── .env                    # API keys (not committed)
├── requirements.txt
└── SETUP_AND_RUN.md        # Full setup guide
```

---

## Quick Start

See **[SETUP_AND_RUN.md](SETUP_AND_RUN.md)** for the full from-scratch guide.

```bash
# 1. Clone & create environment
conda create -n agenticai python=3.10 -y
conda activate agenticai
pip install -r requirements.txt

# 2. Add your API key
cp .env.example .env
# Edit .env: set GROQ_API_KEY=your_key

# 3. Start backend
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8001

# 4. Start frontend (new terminal)
cd frontend && npm install && npm run dev
```

Open **http://localhost:5173** and start generating!

---

## Running Tests

```bash
conda activate agenticai

# Unit tests (no API key needed, ~5s)
python -m pytest tests/unit/ -v

# Edit agent unit tests (no API key needed, ~3s)
python -m pytest agents/edit_agent/tests/ -v

# Integration tests (requires GROQ_API_KEY, ~60s)
python -m pytest tests/integration/ -v

# All tests at once
python -m pytest tests/ agents/edit_agent/tests/ -v
```

---

## Edit Agent Demo

```bash
conda activate agenticai
python scripts/demo_edit_agent.py
```

Runs 11 scripted edits through the live Groq LLM — character changes, audio emotion, script rewrites, subtitles, music, and two consecutive undos — and prints classification results + state snapshots.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | **Yes** | Groq API key (free at [console.groq.com](https://console.groq.com)) |
| `GROQ_MODEL` | No | Default: `llama-3.3-70b-versatile` |
| `FRONTEND_ORIGIN` | No | Default: `http://localhost:5173` |

---

## License

MIT