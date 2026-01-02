# TECHNICAL DESIGN DOCUMENT

## Executive Summary
A full-stack, open-source system enabling anyone to analyze, compare, and benchmark YouTube audio: the hackathon entry automates download, speech-only segmentation, fast transcription, and real-world performance analysis. Clear web and CLI flows prioritize transparency, ease of demo, and reproducibility. All core logic uses open-source models (no paid APIs), and the code is structured for rigorous testing and rapid extension. Judges and engineers can trust results, rerun them, and adapt the platform for further innovation.

---

## 1️⃣ Project Overview

### Why This Matters
YouTube auto-captions are ubiquitous but often inaccurate—misleading accessibility, moderation, and analytics. This project empowers users to quantify and improve real-world ASR/caption quality at scale, using only free/open tools. The platform’s transparency and extensibility make it valuable beyond the hackathon setting.

### Problem Statement
Enable direct, unbiased comparison of YouTube's own speech captions with open, high-accuracy ASR—by automating robust download, segmentation, and transcript analysis with only local, open-source methods. Provide both a UI and reproducible CLI for maximum accessibility and judge trust.

### Hackathon Track Selected
The YouTube Miner (Data Pipeline)

### High-Level Solution Summary
- **Backend (Python)**: Implements an offline pipeline: downloads, voice segmenting (VAD), chunking, ASR transcription, caption download/alignment, multi-metric comparison.
- **Frontend (React/TypeScript)**: Clean web interface for submissions, monitoring, and results. Designed to plug into backend via REST API.
- **Testing**: Automatic test coverage for all pipeline stages (Pytest), and UI logic/components (Jest).

### Key Features and Capabilities
- YouTube audio/captions download (yt-dlp)
- Silence/music removal and speech-only chunking (Silero VAD)
- Transcription with Whisper-Tiny (faster-whisper)
- Comparison: Open ASR (Whisper) vs native YouTube captions (surface, semantic, metrics/text)
- Web UI for submitting, monitoring and viewing results
- Modular design and strict test coverage ease extensions, re-use, and audit

---

## 2️⃣ System Architecture

### High-Level Architecture Description
#### Full-stack (UI/Frontend-first) Flow

![System Architecture Flow Chart](../image/FlowChart.png)

#### Processing Flow

![Processing Flow Model](../image/Model.png)

#### (Alternate) CLI Flow

![CLI Flow Chart](../image/CLIFlowChart.png)

### Backend API Architecture

The backend exposes a RESTful API built with FastAPI, providing endpoints for pipeline execution, status monitoring, and result retrieval.

#### API Endpoints

**Pipeline Execution:**
- `POST /run` - Start a new pipeline run
  - Request body: `{youtube_url: str, language: str, model_size: str, chunk_index?: int}`
  - Response: `{run_id: str, message: str}`
  - Triggers background pipeline execution (download, VAD, chunking)

**Status Monitoring:**
- `GET /status/{run_id}` - Get current status of a pipeline run
  - Response: `{run_id: str, step: str, error_message?: str}`
  - Steps: "downloading", "vad", "chunking", "done", "error"

**Results & Chunk Processing:**
- `GET /result/{run_id}` - Get run results and metadata
  - Response: `{run_id: str, webm_url?: str, wav_url?: str, caption_url?: str, chunkFiles: str[], transcript_url?: str}`
  - Returns URLs for accessing output files via static file serving

- `POST /result/{run_id}/process_chunk` - Process a specific chunk for transcription and comparison
  - Request body: `{chunk_path: str}`
  - Response: `{compare_text: str, similarity_percent: float, transcript_url: str}`
  - Performs on-demand transcription and comparison for selected chunk

**Static File Serving:**
- `GET /output/*` - Serve output files (audio, chunks, transcripts, captions)
  - Files are served from `output/` directory
  - Enables direct download/access to pipeline artifacts

**Disabled Endpoints:**
- `GET /download/{run_id}` - Currently disabled (returns 404)
- `GET /history` - History endpoint not registered (stub exists in codebase)

#### Middleware & Configuration

**CORS Middleware:**
- Configured to allow all origins (`allow_origins=["*"]`)
- Enables frontend-backend communication from any domain
- Supports all HTTP methods and headers

**Static File Mounting:**
- `/output` directory mounted as static file server
- Enables direct URL access to generated files
- Files organized by run_id: `output/{run_id}/`

---

## 3️⃣ Setup & Deployment Instructions

### Prerequisites
- **Backend**: Python 3.9+, pip, ffmpeg
- **Frontend**: Node.js (18+), npm or yarn

### Backend Setup

**Recommended: Use Virtual Environment**
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

**Install Dependencies:**
```bash
pip install -r requirements.txt
# or, if missing:
pip install yt-dlp faster-whisper torch librosa numpy soundfile webvtt-py sentence-transformers scikit-learn fastapi uvicorn
```

**Complete Dependency List:**
- `torch` - PyTorch for ML models
- `soundfile` - Audio file I/O operations
- `webvtt-py` - WebVTT caption parsing
- `faster-whisper` - Whisper ASR implementation
- `sentence-transformers` - Semantic similarity computation
- `scikit-learn` - Machine learning utilities (cosine similarity)
- `fastapi` - Web framework for REST API
- `uvicorn` - ASGI server for FastAPI
- `numpy` - Numerical operations (used in chunker, comparator, VAD)
- `librosa` - Audio processing (transitive dependency)
- `torchaudio` - Audio utilities for PyTorch (used in VAD, dynamically imported)

**System Dependencies:**
- `ffmpeg` - Must be in PATH for audio conversion
- Python 3.9+ required

**Configuration Files:**
- `pytest.ini` - Pytest configuration (sets `pythonpath = .` for test discovery)
- `backend/config.py` - Centralized configuration defaults

**Backend Directory Structure:**
```
backend/
├── api/              # FastAPI endpoint routers
│   ├── run.py        # Pipeline execution endpoint
│   ├── status.py     # Status checking endpoint
│   ├── result.py     # Results and chunk processing endpoints
│   ├── download.py   # Download endpoint (disabled)
│   └── history.py    # History endpoint (not registered)
├── services/         # Core service layer
│   ├── pipeline_wrapper.py  # Pipeline orchestration wrapper
│   ├── run_manager.py       # Run lifecycle management
│   └── storage.py           # State persistence
├── models/           # Pydantic schemas
│   └── schemas.py    # Request/response models
├── tests/            # Backend Pytest suite
│   └── fake_ch/      # Test audio chunks
├── runs/             # Run state storage (JSON files)
├── htmlcov/          # Test coverage reports
├── Dockerfile        # Backend Docker configuration
├── main.py           # FastAPI app initialization
├── config.py         # Centralized configuration
└── requirements.txt  # Backend dependencies
```

**Run from CLI:**
```bash
python -m src.main "<youtube_url>" [--output-dir DIR] [--chunk-duration 30] [--select-chunk 0]
```

**Run Backend API Server:**
```bash
uvicorn backend.main:app --reload
```
- API available at `http://localhost:8000`
- Interactive docs at `http://localhost:8000/docs`

### Frontend Setup
```bash
cd frontend
npm install
npm start
```
- App runs on localhost:3000 by default

### Docker Setup (Optional – For Reproducible Deployment)

**Docker is provided as an optional, production-style deployment method. It enables consistent environments and easy reproduction of results on any machine. However, local (native) setup is safer, fastest, and recommended for active development and live hackathon demos.**

#### Prerequisites
- Docker Desktop (Mac/Windows) or Docker Engine (Linux)
- (Optional) Docker Compose for multi-service orchestration

#### 1. Frontend Only (Step-by-Step)

**Step 1: Navigate to frontend directory**
```bash
cd frontend
```

**Step 2: Build the Docker image**
```bash
docker build -t youtube-miner-frontend .
```
- This creates a multi-stage build:
  - Stage 1: Installs dependencies and builds the React app
  - Stage 2: Serves the built app using nginx with API proxy configuration
- Includes `nginx.conf` for proxying API requests to backend service
- Build time: ~2-5 minutes (first time, subsequent builds are faster with cache)

**Step 3: Run the container**
```bash
docker run -d -p 3000:80 --name youtube-miner-frontend youtube-miner-frontend
```
- `-d`: Run in detached mode (background)
- `-p 3000:80`: Map host port 3000 to container port 80
- `--name`: Assign a name to the container for easy management

**Step 4: Verify the container is running**
```bash
docker ps
```
- Should show `youtube-miner-frontend` container running

**Step 5: Access the frontend**
- Open browser: `http://localhost:3000`
- Frontend UI should be accessible

**Useful Docker commands for frontend:**
```bash
# View container logs
docker logs youtube-miner-frontend

# Stop the container
docker stop youtube-miner-frontend

# Start stopped container
docker start youtube-miner-frontend

# Remove the container
docker rm youtube-miner-frontend

# Remove the image
docker rmi youtube-miner-frontend
```

**Note:** The frontend Docker image includes `nginx.conf` which automatically proxies API requests (`/api/*`, `/run`, `/status/*`, `/result/*`) to the backend service. When using docker-compose, the nginx proxy connects to the backend container via Docker network. For standalone frontend container, ensure backend is accessible at the configured proxy target.

#### 2. Backend Only (Step-by-Step)

**Step 1: Navigate to project root directory**
```bash
# Must build from project root (not backend/) because Dockerfile needs access to both backend/ and src/ directories
cd "The YouTube Miner"
# Or use relative path from your current location
```

**Step 1a: Verify you're in the correct directory**
```bash
# Check that you can see these files/directories:
ls backend/ src/ requirements.txt pytest.ini
# Should list: backend, pytest.ini, requirements.txt, src
```
**Note:** Docker cannot copy files outside the build context. Since backend needs `src/` directory (which is at project root), we must build from project root. The Dockerfile is in `backend/` for organization, but build command uses `-f` flag.

**Step 2: Build the Docker image**
```bash
docker build -f backend/Dockerfile -t youtube-miner-backend .
```
- `-f backend/Dockerfile`: Specifies Dockerfile location (in `backend/` directory)
- `.`: Build context is project root (allows access to both `backend/` and `src/` directories)
- **Important:** Make sure you're in the project root directory (should see `backend/`, `src/`, `requirements.txt` in current directory)
- Includes system dependencies: `ffmpeg`, `curl`, `wget`, `ca-certificates` (required for yt-dlp)
- Installs Python dependencies including `yt-dlp` with `--upgrade` flag for latest version
- Build time: ~5-10 minutes (first time, includes downloading Python base image and all dependencies)

**Step 3: Run the container**
```bash
docker run -d -p 8000:8000 --name youtube-miner-backend youtube-miner-backend
```
- `-d`: Run in detached mode (background)
- `-p 8000:8000`: Map host port 8000 to container port 8000
- `--name`: Assign a name to the container for easy management

**Step 4: Verify the container is running**
```bash
docker ps
```
- Should show `youtube-miner-backend` container running

**Step 5: Check container logs**
```bash
docker logs youtube-miner-backend
```
- Should show FastAPI startup messages
- Look for: `Uvicorn running on http://0.0.0.0:8000`

**Step 6: Access the backend API**
- API base URL: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

**Useful Docker commands for backend:**
```bash
# View container logs
docker logs youtube-miner-backend

# Follow logs in real-time
docker logs -f youtube-miner-backend

# Stop the container
docker stop youtube-miner-backend

# Start stopped container
docker start youtube-miner-backend

# Remove the container
docker rm youtube-miner-backend

# Remove the image
docker rmi youtube-miner-backend

# Execute command inside running container
docker exec -it youtube-miner-backend bash
```

**Note:** 
- First run will download ML models (Whisper, Silero VAD) which can take several minutes
- Model downloads are cached in the container
- The backend creates `output/` and `backend/runs/` directories automatically
- System dependencies (`curl`, `wget`, `ca-certificates`) are included to support yt-dlp downloads
- yt-dlp is installed with `--upgrade` flag to ensure latest version for YouTube compatibility
- For persistent storage, consider mounting volumes: `docker run -v $(pwd)/output:/app/output ...`

#### 3. Full Stack: Backend & Frontend Together (Step-by-Step)

**Step 1: Navigate to project root directory**
```bash
cd "/Users/amit.senger/Documents/Cursor/The YouTube Miner"
# Or use relative path from your current location
```

**Step 1a: Verify docker-compose.yml exists**
```bash
ls docker-compose.yml
# Should show: docker-compose.yml
```

**Step 2: Clean up existing containers (if any)**
```bash
# Check for existing containers with same names
docker ps -a | grep youtube-miner

# Remove existing containers if they exist (optional, docker compose will handle this)
docker rm -f youtube-miner-backend youtube-miner-frontend 2>/dev/null || true
```
**Note:** If you previously ran backend or frontend individually, containers with the same names may exist. Docker Compose will fail if container names conflict. Remove them first or use `docker compose down` to clean up.

**Step 3: Build and start all services**
```bash
docker compose up --build
```
- **Note:** Use `docker compose` (with space), not `docker-compose` (with hyphen)
- `--build`: Forces rebuild of images (use on first run or after code changes)
- Starts both backend and frontend services
- Runs in foreground (logs visible in terminal)
- Press `Ctrl+C` to stop all services

**Step 3a: Run in detached mode (background)**
```bash
docker compose up --build -d
```
- `-d`: Runs containers in detached mode (background)
- Services continue running after terminal closes

**Step 4: Verify services are running**
```bash
docker compose ps
```
- Should show both `youtube-miner-backend` and `youtube-miner-frontend` as "Up"

**Step 5: Access the application**
- **Backend API:** `http://localhost:8000`
- **Backend API Docs:** `http://localhost:8000/docs`
- **Frontend UI:** `http://localhost:3000`

**Useful docker compose commands:**
```bash
# View logs from all services
docker compose logs

# View logs from specific service
docker compose logs backend
docker compose logs frontend

# Follow logs in real-time
docker compose logs -f

# Stop all services
docker compose stop

# Start stopped services
docker compose start

# Stop and remove containers
docker compose down

# Stop, remove containers, and remove volumes
docker compose down -v

# Clean up and rebuild (useful if containers conflict)
docker compose down && docker compose up --build

# Rebuild specific service
docker compose build backend
docker compose build frontend

# Restart specific service
docker compose restart backend
docker compose restart frontend
```

**Configuration Details:**
- **Backend:** Exposed on port 8000, with volumes for `output/` and `backend/runs/` directories
- **Frontend:** Exposed on port 3000 (mapped to container port 80)
- **Dependencies:** Frontend depends on backend (waits for backend to be ready)
- **Health Checks:** Both services include health checks for monitoring
- **Restart Policy:** Services restart automatically unless stopped manually
- **Volumes:** Output and run state directories are persisted on host machine

#### 4. Notes / Troubleshooting

**Docker Daemon Not Running:**
- **Error:** `Cannot connect to the Docker daemon at unix://.../docker.sock. Is the docker daemon running?`
- **Solution:** 
  - On macOS/Windows: Start Docker Desktop application
  - On Linux: Start Docker service: `sudo systemctl start docker`
  - Verify Docker is running: `docker ps` (should not show connection error)

**Common Docker Issues:**
- **ffmpeg:** Must be accessible inside container. Backend Dockerfile includes ffmpeg installation.
- **yt-dlp download failures:** Backend Dockerfile includes `curl`, `wget`, and `ca-certificates` for network operations. If issues persist, check container network connectivity and ensure yt-dlp is up-to-date (Dockerfile uses `--upgrade` flag).
- **Frontend API 404 errors:** Frontend Dockerfile includes `nginx.conf` for API proxy. Ensure backend service is running and accessible. When using docker-compose, nginx proxies to `http://backend:8000` via Docker network.
- **Port already in use:** If port 3000 (frontend) or 8000 (backend) is already in use, stop the existing container or use a different port: `docker run -p 3001:80 ...`
- **Build context error:** Make sure you're in the correct directory (`frontend/` for frontend, project root for backend) and include `.` at the end of build command
- **Permission denied:** On Linux, you may need `sudo` or add your user to docker group: `sudo usermod -aG docker $USER`

**Performance & Model Downloads:**
- **First-run model downloads:** Expect initial Whisper/Silero model downloads; these can be time-consuming on first startup in Docker as well as local host.
- **Performance:** Docker execution may have performance overhead; Whisper and VAD can be significantly slower compared to native local runs, especially if Docker is limited on system RAM or CPU.
- **Local dev is preferred:** Use local install for speed and quick iteration; Docker is best for reproducibility and demo consistency.
- **Model/cache persistence:** For large models, you may wish to map model/cache directories as Docker volumes to avoid re-downloading models on each new container run.

### Testing

The project includes comprehensive test suites for both backend and frontend components. This section provides detailed testing instructions, coverage reporting, and troubleshooting.

#### Backend Testing (Pytest)

**Run all backend tests:**
```bash
# Make sure virtual environment is activated
pytest backend/tests/
```

**Run specific test file:**
```bash
pytest backend/tests/test_api.py
pytest backend/tests/test_downloader.py
pytest backend/tests/test_vad.py
pytest backend/tests/test_chunker.py
pytest backend/tests/test_transcriber.py
pytest backend/tests/test_comparator.py
```

**Run tests with verbose output:**
```bash
pytest backend/tests/ -v
```

**Generate coverage report:**
```bash
# Install pytest-cov if not already installed
pip install pytest-cov

# Run tests with coverage
pytest --cov=src --cov=backend --cov-report=html:backend/htmlcov backend/tests/

# View coverage report
# Open backend/htmlcov/index.html in your browser
```

**Backend Test Files:**
- `backend/tests/test_api.py` - FastAPI endpoint integration tests
- `backend/tests/test_downloader.py` - Audio/caption download tests
- `backend/tests/test_vad.py` - Voice Activity Detection tests
- `backend/tests/test_chunker.py` - Audio chunking tests
- `backend/tests/test_transcriber.py` - Whisper transcription tests
- `backend/tests/test_comparator.py` - Transcript comparison tests

**Note:** Some tests use mock data from `backend/tests/fake_ch/` directory. Ensure test audio files are available if needed. Place test WAV files in `tests/` as needed. All `test_*.py` files are automatically discovered and runnable.

#### Frontend Testing (Jest + React Testing Library)

**Run all frontend tests:**
```bash
cd frontend
npm test
```

**Run tests in watch mode (interactive):**
```bash
cd frontend
npm test -- --watch
```

**Run tests once (non-interactive):**
```bash
cd frontend
npm test -- --watchAll=false
```

**Run tests with coverage:**
```bash
cd frontend
npm test -- --coverage --watchAll=false

# Coverage report will be generated in frontend/coverage/
# Open frontend/coverage/lcov-report/index.html in your browser
```

**Run specific test file:**
```bash
cd frontend
npm test -- App.test.tsx
npm test -- services/api.test.ts
```

**Frontend Test Files:**
- `frontend/src/App.test.tsx` - Main app component tests
- `frontend/src/components/ProgressStepper.test.tsx` - Progress stepper component tests
- `frontend/src/pages/run.test.tsx` - Run page tests
- `frontend/src/pages/components/PipelineStepper.test.tsx` - Pipeline stepper tests
- `frontend/src/pages/results/runId.test.tsx` - Results page tests
- `frontend/src/services/api.test.ts` - API service tests

All `*.test.tsx` and `*.test.ts` files are automatically discovered by Jest.

#### Running All Tests

**Run both backend and frontend tests:**

```bash
# Terminal 1: Backend tests
pytest backend/tests/ -v

# Terminal 2: Frontend tests
cd frontend
npm test -- --watchAll=false
```

#### Test Coverage

**Backend Coverage:**
- Coverage reports are generated in `backend/htmlcov/`
- Open `backend/htmlcov/index.html` to view detailed coverage
- Reports include line-by-line coverage, missing lines, and coverage percentages

**Frontend Coverage:**
- Coverage reports are generated in `frontend/coverage/`
- Open `frontend/coverage/lcov-report/index.html` to view detailed coverage
- Reports include statement, branch, function, and line coverage metrics

#### Troubleshooting Tests

- **Backend tests fail with import errors:** Ensure you're in the project root directory and virtual environment is activated
- **Frontend tests fail:** Make sure `npm install` has been run in the frontend directory
- **Coverage not generating:** Install `pytest-cov` for backend: `pip install pytest-cov`
- **Tests timeout:** Some ML model tests may take longer; increase timeout if needed
- **Module not found errors:** Verify all dependencies are installed from `requirements.txt`
- **Test files not discovered:** Ensure test files follow naming convention (`test_*.py` for backend, `*.test.tsx` for frontend)

### Notes / Troubleshooting
- **ffmpeg**: Must be in PATH; missing ffmpeg will cause audio conversion fail.
- **Model download**: Silero/Whisper models auto-download (first run = slower, GPU optional)
- **Locale & Language**: Pipeline defaults to English (settable per run)
- **Sample size/model speed**: Whisper-Tiny is fast; use larger models for accuracy at the cost of speed/compute.
- **Known issues**: ML models (Silero VAD, Whisper) may require significant RAM; check system resources for heavy runs.

---

## 4️⃣ Code Explanation

### Folder Structure

```
/ (root)
├── backend/
│   ├── api/              # FastAPI endpoint routers
│   │   ├── run.py        # POST /run endpoint
│   │   ├── status.py     # GET /status/{run_id} endpoint
│   │   ├── result.py     # GET /result/{run_id}, POST /result/{run_id}/process_chunk
│   │   ├── download.py   # GET /download/{run_id} (disabled)
│   │   └── history.py    # GET /history (not registered)
│   ├── services/         # Core service layer
│   │   ├── pipeline_wrapper.py  # Wraps pipeline modules for API use
│   │   ├── run_manager.py       # Manages run lifecycle, threading
│   │   └── storage.py           # JSON-based state persistence
│   ├── models/           # Pydantic schemas
│   │   └── schemas.py    # Request/response models
│   ├── tests/            # Backend Pytest suite
│   │   └── fake_ch/      # Test audio chunks
│   ├── runs/             # Run state storage (JSON files)
│   ├── htmlcov/          # Test coverage reports
│   ├── Dockerfile        # Backend Docker configuration
│   ├── main.py           # FastAPI app initialization
│   ├── config.py         # Centralized configuration
│   └── requirements.txt  # Backend dependencies
├── src/                  # Core pipeline modules (shared by CLI and API)
│   ├── downloader.py      # Audio/caption download
│   ├── vad.py            # Voice Activity Detection (Silero)
│   ├── chunker.py        # Audio chunking
│   ├── transcriber.py    # Whisper transcription
│   ├── comparator.py     # Transcript comparison
│   └── main.py           # CLI entry point
├── frontend/             # React/TypeScript frontend
│   ├── src/
│   │   ├── pages/        # Main views (run, results, history)
│   │   ├── components/   # Reusable UI components
│   │   ├── services/     # API integration layer
│   │   └── theme.ts      # Material-UI theme
│   ├── Dockerfile        # Frontend Docker configuration
│   ├── nginx.conf        # Nginx proxy configuration for API
│   └── coverage/         # Frontend test coverage
├── output/               # Pipeline output (audio, chunks, transcripts)
├── pytest.ini            # Pytest configuration
├── requirements.txt      # Root Python dependencies
└── doc/
    ├── TECHNICAL_DESIGN.md   # This document
    └── System_Architecture.md
```

### Major Files & Responsibilities

#### Backend API Layer (`backend/`)

**FastAPI Application:**
- `backend/main.py` - FastAPI app initialization
  - Configures CORS middleware (allows all origins)
  - Mounts `/output` directory as static file server
  - Registers API routers: run, status, result, download
  - Creates output directory if missing

**API Endpoints (`backend/api/`):**
- `backend/api/run.py` - Pipeline execution endpoint
  - `POST /run` - Accepts RunRequest, starts background pipeline
  - Returns RunResponse with run_id
  - Delegates to `run_manager.start_pipeline_run()`

- `backend/api/status.py` - Status monitoring endpoint
  - `GET /status/{run_id}` - Returns current pipeline step and error status
  - Uses `run_manager.get_run_status()`

- `backend/api/result.py` - Results and chunk processing
  - `GET /result/{run_id}` - Returns metadata and file URLs for run outputs
  - `POST /result/{run_id}/process_chunk` - On-demand chunk transcription/comparison
  - Handles chunk path resolution and comparison result formatting

- `backend/api/download.py` - Download endpoint (currently disabled, returns 404)
- `backend/api/history.py` - History endpoint (not registered in app, stub for future use)

#### Backend Services Layer (`backend/services/`)

- `backend/services/pipeline_wrapper.py` - Pipeline orchestration wrapper
  - `run_initial_pipeline()` - Phase 1: Downloads audio/captions, runs VAD, creates chunks
  - `process_chunk_for_comparison()` - Phase 2: Transcribes chunk and compares with captions
  - `prepare_new_output_dir()` - Creates run-specific output directories
  - Raises `PipelineRunError` for pipeline failures
  - Uses config defaults from `backend/config.py`

- `backend/services/run_manager.py` - Run lifecycle management
  - `start_pipeline_run()` - Creates run_id, initializes state, starts background thread
  - `background_run()` - Thread target function executing pipeline asynchronously
  - `get_run_status()` - Retrieves current step and error status
  - `get_run_result()` - Retrieves pipeline result metadata
  - `get_all_runs()` - Lists all runs (for future history feature)
  - Manages in-memory `run_states` dictionary
  - Generates run_id as `run_{timestamp}`

- `backend/services/storage.py` - State persistence
  - `save_run_state()` - Persists run state to JSON file in `backend/runs/`
  - `load_run_state()` - Loads run state from JSON file
  - `run_state_path()` - Generates file path for run_id
  - Ensures `backend/runs/` directory exists

#### Configuration System (`backend/config.py`)

- Centralized configuration defaults:
  - Audio processing: `DEFAULT_SAMPLE_RATE`, `DEFAULT_CHUNK_DURATION`, `DEFAULT_CHUNK_TOLERANCE`
  - Output directories: `DEFAULT_OUTPUT_DIR`, `DEFAULT_RUNS_DIR`
  - Language/model: `DEFAULT_LANGUAGE`, `DEFAULT_MODEL_SIZE`, `LANGUAGE_MODEL_MAP`
  - File naming: `AUDIO_FILENAME`, `CAPTIONS_FILENAME`, `TRANSCRIPT_FILENAME`, etc.
  - Pipeline steps: `PIPELINE_STEPS` list
  - Helper function: `get_model_size_for_language()` - Maps language codes to recommended model sizes

#### Models/Schemas (`backend/models/schemas.py`)

- Pydantic models for API request/response validation:
  - `RunRequest` - Pipeline start request (youtube_url, language, model_size, chunk_index)
  - `RunResponse` - Pipeline start response (run_id, message)
  - `StatusResponse` - Status check response (run_id, step, error_message, logs)
  - `ResultResponse` - Result retrieval response (run_id, transcript, similarity_percent, metrics)
  - `RunItem`, `HistoryResponse` - For future history feature

#### Core Pipeline Modules (`src/`)

- `src/downloader.py` - Audio and caption download
  - `download_audio()` - Uses yt-dlp and ffmpeg to download and convert audio
  - `download_captions()` - Downloads YouTube captions in specified language
  - `extract_captions_text()` - Extracts plain text from VTT/SRT files
  - `extract_aligned_captions()` - Aligns captions with audio timestamps

- `src/vad.py` - Voice Activity Detection
  - `run_silero_vad()` - Uses Silero VAD model via torch.hub
  - Detects speech segments, filters silence/music
  - Returns list of (start_time, end_time) tuples

- `src/chunker.py` - Audio chunking
  - `create_speech_chunks()` - Concatenates speech segments into ~30s chunks
  - Saves chunks as WAV files in chunks directory
  - Returns list of (chunk_path, offset) tuples

- `src/transcriber.py` - Whisper transcription
  - `transcribe_chunk()` - Uses faster-whisper to transcribe audio chunk
  - Supports multiple model sizes (tiny, small, base, medium, large)
  - Handles language specification and compute type

- `src/comparator.py` - Transcript comparison
  - `compare_transcripts()` - Compares Whisper transcript with YouTube captions
  - Computes semantic similarity using sentence-transformers
  - Computes surface similarity using difflib
  - Generates detailed comparison report

- `src/main.py` - CLI entry point
  - Parses command-line arguments
  - Orchestrates full pipeline execution
  - Handles error reporting and output

#### Frontend (`frontend/src/`)

- `frontend/src/pages/` - Main navigation/views
  - `run.tsx` - Pipeline submission form with language/model selection
  - `results/[runId].tsx` - Results display page
  - `index.tsx` - Landing/home page
  - `components/PipelineStepper.tsx` - Progress indicator component

- `frontend/src/components/` - Reusable UI components
  - `ProgressStepper.tsx` - Material-UI stepper for pipeline progress

- `frontend/src/services/api.ts` - API integration layer
  - `runPipeline()` - POST to `/api/run` to start pipeline
  - `getStatus()` - GET `/api/status/{runId}` to check status
  - `getResult()` - GET `/api/result/{runId}` to retrieve results
  - `processChunk()` - POST to `/api/result/{runId}/process_chunk` for chunk processing
  - `getHistory()` - GET `/api/history` (for future use)
  - Handles fetch requests and error responses

- `frontend/src/theme.ts` - Material-UI theme configuration

#### Test Cases

**Backend (`backend/tests/`):**
- `test_api.py` - FastAPI endpoint integration tests (mocked pipeline)
- `test_downloader.py` - Audio/caption download tests
- `test_vad.py` - Voice Activity Detection tests
- `test_chunker.py` - Audio chunking tests
- `test_transcriber.py` - Whisper transcription tests (mocked models)
- `test_comparator.py` - Transcript comparison tests

**Frontend (`frontend/src/`):**
- `*.test.tsx` - Component and page tests using Jest and React Testing Library
- `services/api.test.ts` - API service function tests

### Core Workflows (Step-by-Step)

**High-Level Flow:**
- Input → Download → VAD → Chunk → Transcribe → Caption → Compare → Output reporting
- All flows, error paths, and edge cases covered by modular functions/test routines

### Core Workflows (Detailed)

The system implements a **two-phase pipeline architecture** optimized for web API usage:

#### Phase 1: Initial Pipeline (Background Execution)

**Trigger:** `POST /run` endpoint receives request

1. **Run Initialization:**
   - Generate run_id: `run_{timestamp}` (e.g., `run_1767248560`)
   - Create run state in memory and persist to `backend/runs/{run_id}.json`
   - Start background thread for async execution

2. **Background Thread Execution:**
   - Step: "downloading"
     - Download audio using `yt-dlp` (bestaudio format, fallback to mp4)
     - Convert to WAV using `ffmpeg` at 16kHz sample rate
     - Download captions in specified language (.vtt or .srt)
   - Step: "vad"
     - Run Silero VAD on audio to detect speech segments
     - Filter out silence and music
   - Step: "chunking"
     - Concatenate speech segments
     - Split into ~30s chunks (±5s tolerance)
     - Save chunks as WAV files in `output/{run_id}/chunks/`
   - Step: "done"
     - Save result metadata (output_dir, run_id)
     - Persist state to JSON file

3. **Error Handling:**
   - On any pipeline error, set step to "error"
   - Store error message in run state
   - Persist error state to JSON file
   - Raise `PipelineRunError` exception (caught by background thread)

#### Phase 2: On-Demand Chunk Processing

**Trigger:** `POST /result/{run_id}/process_chunk` endpoint receives chunk_path

1. **Chunk Selection:**
   - User selects chunk from list returned by `GET /result/{run_id}`
   - Frontend sends chunk_path to process_chunk endpoint

2. **Transcription:**
   - Load Whisper model (size specified in run args)
   - Transcribe selected chunk
   - Save transcript to `output/{run_id}/whisper_transcript.txt`

3. **Comparison:**
   - Load YouTube captions from run output directory
   - Extract caption text matching chunk time window
   - Compute semantic similarity (sentence-transformers)
   - Compute surface similarity (difflib)
   - Generate comparison report: `output/{run_id}/comparison.txt`

4. **Response:**
   - Return comparison text, similarity percentage, transcript URL

#### State Management

**In-Memory State:**
- `run_states` dictionary in `run_manager.py`
- Key: run_id, Value: `{step, error, result, args}`
- Updated during pipeline execution

**Persistent State:**
- JSON files in `backend/runs/{run_id}.json`
- Saved after each step update
- Loaded on server restart (if needed)
- Contains: step, error, result, args

**Run ID Generation:**
- Format: `run_{unix_timestamp}`
- Example: `run_1767248560`
- Ensures uniqueness and chronological ordering

#### Error Handling

**Pipeline Errors:**
- `PipelineRunError` - Custom exception for pipeline failures
- Caught in `background_run()` function
- Error message stored in run state
- Step set to "error"
- State persisted to JSON file

**API Errors:**
- HTTP 404 for missing runs
- HTTP 400 for invalid requests (missing chunk_path)
- HTTP 500 for pipeline execution errors
- Error messages returned in response body

#### Background Execution Mechanism

**Threading Approach:**
- `threading.Thread` used for async pipeline execution
- Main thread returns immediately with run_id
- Background thread executes pipeline independently
- No blocking of API server

**State Updates:**
- Step updates via `update_step_fn` callback
- Updates both in-memory dict and JSON file
- Frontend polls `/status/{run_id}` to track progress

### API Integration Details

#### Frontend-Backend Communication

**API Base Path:**
- Frontend makes requests to `/api/*` endpoints
- Backend serves API at `http://localhost:8000`
- CORS enabled for cross-origin requests

**Request/Response Flow:**

1. **Start Pipeline:**
   ```
   Frontend: POST /api/run
   Body: {youtube_url, language, model_size, chunk_index}
   → Backend: {run_id, message}
   ```

2. **Check Status:**
   ```
   Frontend: GET /api/status/{runId}
   → Backend: {run_id, step, error_message}
   ```
   - Frontend polls this endpoint every few seconds
   - Updates UI based on step value

3. **Get Results:**
   ```
   Frontend: GET /api/result/{runId}
   → Backend: {run_id, webm_url, wav_url, caption_url, chunkFiles[], transcript_url}
   ```
   - Returns URLs for accessing output files
   - Files served via `/output/*` static file mount

4. **Process Chunk:**
   ```
   Frontend: POST /api/result/{runId}/process_chunk
   Body: {chunk_path}
   → Backend: {compare_text, similarity_percent, transcript_url}
   ```
   - Triggered when user selects a chunk
   - Performs transcription and comparison on-demand

**Request/Response Formats:**
- All requests use JSON (`Content-Type: application/json`)
- Responses use Pydantic models for validation
- Error responses include HTTP status codes and error messages

### Design Rationale
- **Why Modular/Testable?**
  - Each stage (download, segmentation, ASR, etc) is an isolated, mock/testable unit for ease of dev, debug, and hackathon reliability.
  - Service/module boundaries allow adaptation and API/CLI dual use with minimal friction.
  - End-to-end testability enables incremental improvements and regression safety.

---

## 5️⃣ Assumptions & Design Decisions

### Explicit Assumptions
- Runs in local dev or hackathon cloud VMs (no paid/proprietary dependencies)
- Sample/test data placement described
- Frontend-backend integration fully implemented via REST API

### Trade-offs
- Chose speed (modularity, OSS models, test-first) over "big-data" scale
- All logic: single-node, stateless for demo

### Design Decisions

**Two-Phase Pipeline Architecture:**
- **Rationale:** Separates time-consuming operations (download/VAD/chunking) from on-demand operations (transcription/comparison)
- **Benefits:** 
  - Users can see chunks immediately after Phase 1 completes
  - Transcription only runs for selected chunks (saves compute)
  - Better user experience with progressive results
- **Trade-off:** Requires two API calls (initial run + chunk processing) instead of one

**Background Threading Approach:**
- **Rationale:** Pipeline operations can take minutes; blocking API would timeout
- **Implementation:** Uses Python `threading.Thread` for async execution
- **Benefits:**
  - API responds immediately with run_id
  - Multiple runs can execute concurrently
  - Simple implementation without external job queue
- **Trade-off:** In-memory state lost on server restart (mitigated by JSON persistence)

**JSON-Based State Persistence:**
- **Rationale:** Simple, file-based storage without database dependency
- **Implementation:** Each run state stored as `backend/runs/{run_id}.json`
- **Benefits:**
  - No database setup required
  - Human-readable state files
  - Easy debugging and inspection
- **Trade-off:** Not suitable for high-concurrency production (sufficient for hackathon scope)

**Configuration Centralization:**
- **Rationale:** Single source of truth for all default values
- **Implementation:** `backend/config.py` exports constants and helper functions
- **Benefits:**
  - Easy to modify defaults without searching codebase
  - Consistent values across CLI and API
  - Documented configuration options
- **Trade-off:** Requires importing config module (minimal overhead)

### Limitations
- No distributed job queue/celery; not multi-tenant (hackathon scope)
- State persistence is file-based (JSON), not suitable for high-concurrency production
- Background threading approach limits scalability compared to proper job queue systems

### Future Improvement Scope
- Add batch / multi-chunk flows, richer reporting, true full-stack API+UI
- Dockerize for single-command deploy
- Extend to more languages, cloud+production scaling

### Intentional Non-Goals
- No paid APIs or hosted models (absolutely OSS-only)
- No persistent DB, user auth, or multi-user job queue
- No speaker diarization or video/image handling
- No proprietary transcription/AI solutions
- No analytics/telemetry: privacy/portability by default

---

## Document Relationships

For information about document relationships, usage patterns, and navigation between [`README.md`](../README.md), [TECHNICAL_DESIGN.md](TECHNICAL_DESIGN.md), and [System_Architecture.md](System_Architecture.md), see the **Documentation** section in [`README.md`](../README.md).

---


