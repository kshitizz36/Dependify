<div align="center">

# 🔧 Dependify

### AI-Powered Code Modernization & Technical Debt Elimination

**Ship features faster by automating tech debt — not wrestling with it.**

[![Built with Modal](https://img.shields.io/badge/Compute-Modal-6366f1?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjQiIGhlaWdodD0iMjQiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPjxjaXJjbGUgY3g9IjEyIiBjeT0iMTIiIHI9IjEwIi8+PC9zdmc+)](https://modal.com)
[![Powered by Claude](https://img.shields.io/badge/AI-Claude%20(Anthropic)-cc785c?style=for-the-badge)](https://anthropic.com)
[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-000000?style=for-the-badge&logo=next.js)](https://nextjs.org)
[![Supabase](https://img.shields.io/badge/Realtime-Supabase-3ecf8e?style=for-the-badge&logo=supabase)](https://supabase.com)

---

*Dependify scans your GitHub repository, identifies outdated code, refactors it using AI agents running in parallel serverless containers, verifies correctness through a self-healing loop, and opens a pull request — all in minutes.*

</div>

---

## 🔥 The Problem

- **41%** of developers spend most of their time dealing with technical debt
- Developers dedicate **16.4 hours/week** to maintenance tasks — debugging, refactoring, updating dependencies
- Manual code modernization is tedious, error-prone, and blocks feature development

## 💡 The Solution

Dependify automates the entire code modernization workflow using a **3-agent AI pipeline** that reads, writes, and verifies code changes — then opens a GitHub PR for your review.

---

## 🧠 Architecture — The 3-Agent Pipeline

Dependify uses a multi-agent architecture where each agent is specialized for its role, running in isolated serverless containers on [Modal](https://modal.com):

```
┌─────────────┐     ┌──────────────┐     ┌───────────────────────┐     ┌────────────┐
│   GitHub     │────▶│  📖 Reader   │────▶│  ✍️ Writer            │────▶│  🔍 Verify │
│   Repo URL   │     │  (Sonnet)    │     │  (Haiku × 100)       │     │  + Self-Heal│
└─────────────┘     └──────────────┘     └──────────────────────┘     └─────┬──────┘
                                                                            │
                                                                     ┌──────▼──────┐
                                                                     │  🚀 Git     │
                                                                     │  Push + PR  │
                                                                     └─────────────┘
```

### Agent 1 — 📖 Reader (Claude Sonnet)
> *"What needs to change?"*

- Clones the repo inside a **Modal container**
- Recursively scans all source files
- Uses **Claude Sonnet** (smartest model) to analyze each file for outdated syntax, deprecated APIs, and modernization opportunities
- Outputs a structured list of `CodeChange` objects
- Streams real-time `READING` status updates to the dashboard via Supabase

### Agent 2 — ✍️ Writer (Claude Haiku × 100 parallel)
> *"Rewrite it."*

- Takes each flagged file and refactors it using **Claude Haiku** (fast and cost-efficient)
- Runs in **up to 100 parallel Modal containers** — processes entire codebases in minutes, not hours
- Generates complete refactored files with detailed inline comments
- Streams `WRITING` progress to the dashboard in real-time

### Agent 3 — 🔍 Verifier (Self-Healing Loop)
> *"Is this correct? If not, fix it."*

- **Haiku** performs a fast verification pass — checks functionality preservation, syntax validity, and completeness
- If verification **fails**: **Sonnet** analyzes the root cause deeply, then **Haiku** applies targeted fixes
- Retries up to 2 times in a **self-healing loop** before accepting the best result
- Streams `VERIFYING` → `FIXING` → `VERIFIED` status updates live

### Finally — 🚀 Git Driver
- Creates a fork (or branch on your own repo)
- Stages all refactored files, commits with descriptive messages
- Opens a **Pull Request** back to your repository for review

---

## 🖥️ Dashboard — Real-Time Live Coding

The **Next.js** dashboard provides a live, immersive experience as Dependify processes your repository:

- **Live Code Card** — watch refactored code appear character-by-character with a typewriter animation and progress bar
- **Multi-File View** — see all files being processed simultaneously  
- **Status Timeline** — track each file through Reading → Writing → Verifying → Pushing
- **Real-time updates** powered by **Supabase Realtime** subscriptions — no polling

### Design
- Dark theme with glassmorphism cards and green accent palette
- Canvas gradient background with animated elements
- Built with **Tailwind CSS** + **shadcn/ui** components

---

## 🛠️ Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **AI Models** | Claude Sonnet + Haiku (Anthropic) | Code analysis, refactoring, and verification |
| **Compute** | Modal | Serverless containers for parallel processing (up to 100 concurrent) |
| **Backend** | FastAPI + Uvicorn | REST API + WebSocket server |
| **Frontend** | Next.js 15 + TypeScript | Dashboard with live updates |
| **Database & Realtime** | Supabase | PostgreSQL + real-time subscriptions |
| **Auth** | GitHub OAuth + JWT | Secure API authentication |
| **Styling** | Tailwind CSS + shadcn/ui | Component library and design system |
| **Version Control** | GitPython + GitHub API | Automated branching, committing, and PR creation |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 20+ / pnpm
- [Modal](https://modal.com) account
- [Supabase](https://supabase.com) project
- [Anthropic](https://console.anthropic.com) API key
- GitHub personal access token

### 1. Clone the Repository

```bash
git clone https://github.com/kshitizz36/Dependify.git
cd Dependify
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create your `.env` file:
```bash
cp .env.example .env
```

Fill in your credentials:
```env
ANTHROPIC_API_KEY=your_anthropic_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
GITHUB_TOKEN=your_github_pat
GITHUB_CLIENT_ID=your_oauth_client_id
GITHUB_CLIENT_SECRET=your_oauth_client_secret
API_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
FRONTEND_URL=http://localhost:3000
```

Configure Modal secrets:
```bash
modal token new
modal secret create ANTHROPIC_API_KEY ANTHROPIC_API_KEY=your_key
modal secret create SUPABASE_URL SUPABASE_URL=your_url
modal secret create SUPABASE_KEY SUPABASE_KEY=your_key
```

Set up the database — run the SQL files in your Supabase SQL editor:
```bash
# In order:
backend/COMPLETE_SCHEMA.sql
backend/ADD_COLUMNS_TO_SUPABASE.sql
```

Start the server:
```bash
python server.py
# API running at http://localhost:5001
# Docs at http://localhost:5001/docs
```

### 3. Frontend Setup

```bash
cd frontend
pnpm install
```

Create `.env.local`:
```env
NEXT_PUBLIC_API_URL=http://localhost:5001
NEXT_PUBLIC_WS_URL=ws://localhost:5001
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_oauth_client_id
```

Start the dev server:
```bash
pnpm dev
# Dashboard at http://localhost:3000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns version and status |
| `POST` | `/auth/github` | Exchange GitHub OAuth code for JWT token |
| `GET` | `/auth/me` | Get authenticated user info |
| `POST` | `/update` | Process a repository (rate limited) |
| `WS` | `/ws` | WebSocket for real-time processing updates |

Full interactive docs available at `/docs` (Swagger) and `/redoc` when the server is running.

---

## 🔐 Security

- **No hardcoded credentials** — all secrets via environment variables and Modal Secrets
- **JWT authentication** for API endpoints
- **GitHub OAuth** for user login
- **Rate limiting** (configurable per-minute and per-hour limits)
- **CORS restriction** to your frontend domain only
- **Input validation** on all endpoints with Pydantic models

---

## 📂 Project Structure

```
Dependify/
├── backend/
│   ├── server.py           # FastAPI server — REST + WebSocket
│   ├── checker.py          # Reader Agent — Sonnet code analysis
│   ├── modal_write.py      # Writer Agent — Haiku parallel refactoring
│   ├── modal_verify.py     # Verifier Agent — self-healing validation loop
│   ├── containers.py       # Modal container definitions for sandboxed execution
│   ├── git_driver.py       # Git operations — fork, branch, commit, PR
│   ├── config.py           # Centralized environment config
│   ├── auth.py             # JWT + GitHub OAuth authentication
│   ├── socket_manager.py   # WebSocket connection manager
│   ├── requirements.txt    # Python dependencies
│   └── .env.example        # Environment variable template
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx            # Main dashboard
│   │   │   ├── login/page.tsx      # Login page (GitHub OAuth + Email)
│   │   │   └── auth/callback/      # OAuth callback handler
│   │   ├── components/
│   │   │   ├── MainDash.tsx        # Dashboard with repo processing UI
│   │   │   ├── LiveCodeCard.tsx    # Typewriter code animation
│   │   │   ├── MultiFileCodeCard.tsx # Multi-file view
│   │   │   ├── GradientCanvas.tsx  # Animated background
│   │   │   └── ui/                 # shadcn/ui primitives
│   │   └── lib/
│   │       └── supabaseClient.ts   # Supabase real-time client
│   ├── package.json
│   └── tailwind.config.ts
│
└── README.md
```

---

## 🧗 Challenges We Faced

- **Debugging Modal containers** — running AI agents inside serverless containers meant we couldn't just `print()` and see output. We had to figure out logging, secrets management, and handling cold starts across 100 parallel containers
- **Self-healing verification loop** — getting the Verifier agent to actually fix broken refactors was tricky. We designed a multi-model pipeline where Haiku checks, Sonnet diagnoses, and Haiku fixes — getting them to communicate properly took multiple iterations
- **Real-time Supabase sync** — making the dashboard update live as files are processed across dozens of containers simultaneously. Handling race conditions and ordering of status updates (Reading → Writing → Verifying → Verified) was a real challenge
- **Git automation at scale** — programmatically forking repos, creating branches, staging hundreds of files, and opening PRs through the GitHub API without hitting rate limits or auth issues
- **LLM output parsing** — AI models don't always return clean JSON. We built robust parsing with fallbacks for markdown-wrapped responses, partial outputs, and malformed JSON

---

## 🏆 Accomplishments We're Proud Of

- Built a **3-agent AI pipeline** (Reader → Writer → Verifier) that works end-to-end autonomously
- **100 parallel Modal containers** processing files simultaneously — entire repos modernized in minutes
- **Self-healing code** — the Verifier agent doesn't just flag problems, it actually fixes them with a retry loop using two different AI models
- Fully automated **GitHub PR creation** — from fork to branch to commit to pull request, zero manual steps
- **Live dashboard** with typewriter code animation — you can literally watch AI rewrite your code character by character in real-time
- Scalable architecture that works the same for a 10-file repo or a 10,000-file repo

---

## 📚 What We Learned

- How to orchestrate **multi-agent AI systems** where different models collaborate (Sonnet for deep thinking, Haiku for speed)
- Efficient **parallel processing** with Modal's serverless containers and managing state across them
- Building **real-time data pipelines** with Supabase subscriptions for instant UI updates
- Best practices for **automating GitHub workflows** — forking, branching, and PR creation via API
- How to make AI output **production-reliable** — structured parsing, validation, and self-correction loops

---

## � What's Next for Dependify

- **AI-powered unit test generation** — automatically generate tests for refactored code before opening the PR
- **Multi-language support** — expand beyond JavaScript/TypeScript to Python, Go, Rust, and Java
- **VS Code extension** — trigger Dependify directly from your editor
- **CI/CD integration** — run Dependify as a GitHub Action on every push
- **Custom style enforcement** — let teams define their own coding standards and have AI follow them
- **Security vulnerability patching** — not just modernize syntax, but automatically fix known CVEs in dependencies

---

<div align="center">

**Dependify** — *Where AI meets code maintenance. Code smarter, not harder.*

Built by [@kshitizz36](https://github.com/kshitizz36)

</div>
