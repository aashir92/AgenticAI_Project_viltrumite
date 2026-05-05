# Setup & Run Guide — Agentic AI Video Pipeline

This guide takes you from **zero to a running pipeline** on a fresh Windows machine.  
Estimated time: **10-15 minutes**.

---

## Prerequisites

Install these before starting:

| Tool | Version | Download |
|------|---------|----------|
| **Miniconda** (or Anaconda) | latest | https://docs.conda.io/en/latest/miniconda.html |
| **Node.js** | 18+ | https://nodejs.org |
| **Git** | latest | https://git-scm.com |
| **ffmpeg** | latest | https://ffmpeg.org/download.html — add to PATH |

> **Windows TTS note**: The audio agent uses Windows built-in SAPI5 voices (Microsoft David & Zira). No install needed — they come with Windows 10/11.

---

## Step 1 — Clone the Repository

```bash
git clone <your-repo-url>
cd "Agentic Project"
```

---

## Step 2 — Create the Conda Environment

```bash
conda create -n agenticai python=3.10 -y
conda activate agenticai
```

---

## Step 3 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs: `fastapi`, `uvicorn`, `langchain`, `langchain-groq`, `langgraph`, `moviepy`, `Pillow`, `rembg`, `scipy`, `pyttsx3`, `pydantic`, `python-dotenv`, `pytest`, `requests`, and more.

> **rembg** (background removal) downloads a ~170 MB model on first run. This is normal — it only downloads once.

---

## Step 4 — Configure Environment Variables

```bash
copy .env.example .env
```

Open `.env` in any text editor and fill in:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile
FRONTEND_ORIGIN=http://localhost:5173
```

**Getting a free Groq API key:**
1. Go to https://console.groq.com
2. Sign up (free)
3. Create an API key under **API Keys**
4. Paste it into `.env`

> Pollinations.ai (image generation) requires **no API key** — it's completely free and automatic.

---

## Step 5 — Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## Step 6 — Run the Backend

Open a terminal in the project root:

```bash
conda activate agenticai
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8001
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8001
INFO:     Application startup complete.
```

> **Keep this terminal open** — the backend runs continuously.

---

## Step 7 — Run the Frontend

Open a **second terminal** in the project root:

```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in XXXms
  -> Local:   http://localhost:5173/
```

---

## Step 8 — Open the App

Open your browser and go to: **http://localhost:5173**

Type any story prompt and click **Generate** — the pipeline will:
1. Generate a story with Groq LLM
2. Create TTS audio for each dialogue line
3. Generate character images via Pollinations.ai
4. Remove backgrounds from character sprites
5. Composite animated video scenes
6. Produce a final MP4 in `data/outputs/{job_id}/video/final_output.mp4`

---

## Running the Tests

Make sure you're in the project root with `agenticai` activated.

### Unit Tests (no API key needed — runs in ~5 seconds)

```bash
conda activate agenticai
python -m pytest tests/unit/ -v
```

Tests covered:
- All Pydantic schemas (validation, boundaries, error cases)
- VideoAgent mouth-ratio math and geometry constants

### Edit Agent Unit Tests (no API key needed — runs in ~3 seconds)

```bash
python -m pytest agents/edit_agent/tests/test_edit_agent.py -v
```

Tests covered:
- EditAgentState apply/undo stack
- Intent classification mocking
- Undo stack isolation between states

### Integration Tests (requires `GROQ_API_KEY` — runs in ~60 seconds)

```bash
python -m pytest tests/integration/ -v
```

Tests covered:
- Live Groq LLM classification for all 10 intent types
- State mutation (character, background, audio, script, duration overrides)
- Multi-level undo chains
- State isolation between independent jobs

### All Tests Together

```bash
python -m pytest tests/ agents/edit_agent/tests/ -v
```

Expected result: **74 passed** (29 edit unit + 45 schema/video unit + 21 integration — but exact count varies with how many integration tests run)

---

## Running the Edit Agent Demo

This runs a scripted 11-step demo showing the Edit Agent in action (live Groq LLM):

```bash
conda activate agenticai
python scripts/demo_edit_agent.py
```

You'll see each edit query classified with intent, confidence, extracted params, and undo stack depth.

---

## Generated Output Files

After a successful generation, look in `data/outputs/{job_id}/`:

```
data/outputs/{job_id}/
├── story_spec.json           # The generated story structure
├── timing_manifest.json      # Per-line audio timing
├── audio/
│   ├── scene1_line0.wav      # TTS audio per dialogue line
│   └── master.wav            # Concatenated master audio
└── video/
    ├── char_Alice_raw.png    # Raw generated character
    ├── char_Alice.png        # Background-removed sprite
    ├── scene1_bg.png         # Generated background
    ├── mouth_overlay.png     # Mouth animation overlay
    └── final_output.mp4      # The final video!
```

Edit history is saved to `data/state_versions/{job_id}/`:
```
data/state_versions/{job_id}/
├── history.json              # Ordered version list
├── v_1.json                  # State after edit 1
├── v_2.json                  # State after edit 2
└── v_3.json                  # State after undo (reverted)
```

---

## Troubleshooting

### `GroqError: The api_key client option must be set`
→ Your `.env` file is missing or `GROQ_API_KEY` is not set. Check Step 4.

### `rembg` download on first run
→ Normal — it downloads the u2net model (~170 MB) once. Just wait.

### `ffmpeg` not found / video encoding errors
→ Install ffmpeg and make sure it's in your system PATH.

### `UnicodeEncodeError` in terminal
→ This is a Windows codepage issue with emoji. The demo script handles this automatically with `sys.stdout.reconfigure(encoding="utf-8")`.

### Port 8001 already in use
→ Kill the existing process: `netstat -ano | findstr 8001`, then `taskkill /PID <pid> /F`

### Frontend can't reach backend (CORS errors)
→ Make sure `FRONTEND_ORIGIN=http://localhost:5173` is set in `.env` and the backend is running on port 8001.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/pipeline/start` | Start video generation |
| `GET` | `/api/pipeline/{job_id}` | Get job status |
| `GET` | `/api/assets/{job_id}/video` | Download final video |
| `POST` | `/api/edit/{job_id}` | Apply a natural-language edit |
| `POST` | `/api/edit/{job_id}/undo` | Undo last edit |
| `WS` | `/ws/progress/{job_id}` | Real-time progress updates |
| `GET` | `/health` | Backend health check |
