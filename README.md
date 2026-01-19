# VibeSec

**Test your vibe-coded apps before launch** 🚀

Security and testing platform for AI-generated web applications. Get production-ready with automated SAST, SCA, and detailed readiness scoring.

## key Features

-   **Production Readiness Scoring**: Comprehensive analysis across 6 key domains:
    -   🛡️ **Security**: SAST & SCA scanning for vulnerabilities.
    -   🧪 **Testing**: Detection of test frameworks and coverage.
    -   ⚡ **Performance**: Checks for caching, async patterns, and N+1 queries.
    -   👁️ **Observability**: Logging, monitoring, and health check validation.
    -   🏗️ **Infrastructure**: Docker, CI/CD, and secret management checks.
    -   🔁 **Reliability**: Error handling and retry logic verification.

-   **Automated Scanning**:
    -   **SAST**: Static Application Security Testing using Semgrep.
    -   **SCA**: Software Composition Analysis for dependency vulnerabilities.
    -   **Stack Detection**: Automatic identification of Next.js, Express, FastAPI, and Django projects.

-   **Interactive Dashboard**: Real-time scan progress, score visualization, and detailed finding reports.

## Tech Stack

-   **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Shadcn UI, Recharts, Framer Motion
-   **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Pydantic
-   **Infrastructure**: Redis (Queues), ARQ (Async Jobs), Cloudflare R2 (Storage)
-   **Auth**: Firebase Authentication + GitHub OAuth

## Prerequisites

-   Node.js 18+
-   Python 3.11+
-   Docker & Docker Compose
-   Firebase Project (Auth enabled)
-   GitHub OAuth App

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/adi-7192/VibeSec.git
cd VibeSec

# Copy environment files
cp backend/.env.example backend/.env
# Update backend/.env with your credentials
```

### 2. Start Infrastructure

```bash
docker-compose up -d
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Open Application

Visit [http://localhost:3000](http://localhost:3000)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/verify` | Verify Firebase token |
| GET | `/api/v1/projects` | List user projects |
| POST | `/api/v1/projects/github` | Import from GitHub |
| POST | `/api/v1/projects/zip` | Upload ZIP project |
| POST | `/api/v1/projects/{id}/scans` | Trigger analysis |
| GET | `/api/v1/projects/{id}/scans` | Get scan history |

## License

MIT
