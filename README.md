# AI Interview Preparation Assistant

A comprehensive, production-quality AI-powered web application built using **Streamlit** (Multipage Architecture) and **Supabase** (PostgreSQL/Auth/Storage). This platform helps students and job seekers prepare for Technical, HR, Coding, and Company-Specific interviews using Generative AI (Gemini 2.5 Flash / Groq Llama), Resume Analysis, Speech-to-Text Voice Analysis, RAG knowledge assistance, Personalized roadmaps, and Gamification.

---

## ⚡ Main Features

1. **Authentication System (Supabase Auth)**: Secure Signup, Login, Password Reset, Google OAuth (Google Sign-In) with server-side PKCE verifier fallback logic to bypass iframe cookie/sandbox restrictions, and session persistence.
2. **Dashboard Performance Tracker**: Beautiful Plotly metrics showing averages, trend lines, skill radar competency, and a weekly activity calendar.
3. **Resume Analyzer (ATS Checker)**: PDF/DOCX resume scanner that computes ATS scores, identifies strengths/gaps, extracts skills, generates matching questions, and exports professional PDF reports.
4. **Technical Interview Engine**: Practice domain questions (OOP, DBMS, OS, DSA, ML, Cloud, Cybersecurity, DevOps) with strict AI grading metrics.
5. **HR STAR Coaching**: Behavioral questions matched to candidate profiles with detailed STAR structure checking (Situation, Task, Action, Result).
6. **LeetCode Coding Editor**: Python, Java, C++, and JS editor. Submit code for AI assessment of correctness, time/space complexity, and best practices.
7. **Flagship Mock Interview Simulator**: Full multi-persona mock interview session (Friendly/Strict Recruiter, FAANG Interviewer, Startup Founder) with follow-ups, final reports, and PDF downloads.
8. **Voice Speech-to-Text Mode**: Speaks questions aloud and listens through the browser microphone to analyze speaking speed (WPM), confidence, filler word frequency, and communication clarity.
9. **Company-Specific Prep**: Target Google, Amazon, Microsoft, Meta, Netflix, TCS, Infosys, etc. tailored to culture, core values, and question styles.
10. **RAG Knowledge Assistant (LangChain + FAISS)**: Index placement notes, PDFs, or slides to get context-grounded Q&A assistance with verified source citations.
11. **Personalized Roadmaps**: AI coach study schedules targeting Weak Areas over custom durations.
12. **Gamification & Daily Challenges**: Streak tracker, Weekly Leaderboard, XP points, and achievements.
13. **Admin Dashboard**: Moderation dashboard for managing system configs, monitoring event audit logs, and checking users or uploads.

---

## 📂 Project Folder Structure

```
ai-interview-prep/
├── .streamlit/
│   └── config.toml             # Streamlit Dark theme & runner configs
├── src/
│   ├── __init__.py
│   ├── auth/
│   │   ├── __init__.py
│   │   └── supabase_auth.py    # Supabase authentication handlers
│   ├── database/
│   │   ├── __init__.py
│   │   ├── supabase_client.py  # Supabase client CRUD operations
│   │   └── schema.sql          # PostgreSQL database schema script
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── prompts.py          # Reusable prompts & prompt templates
│   │   ├── gemini_client.py    # Primary Gemini 2.5 Flash client
│   │   ├── groq_client.py      # Alternative Groq Llama client
│   │   └── rag_engine.py       # LangChain + FAISS + sentence-transformers pipeline
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── pdf_processor.py    # PyPDF2/pdfplumber text extraction
│   │   ├── report_generator.py # PDF report creation with FPDF2
│   │   └── helpers.py          # Formatter, XP, dates, and common tools
│   └── components/
│       ├── __init__.py
│       ├── ui_components.py    # Reusable Glassmorphism UI components & custom CSS
│       └── charts.py           # Plotly radar, trends, gauge, and activity charts
├── pages/                      # Streamlit Multipage screens
│   ├── 01_Dashboard.py
│   ├── 02_Resume_Analyzer.py
│   ├── 03_Technical_Interview.py
│   ├── 04_HR_Interview.py
│   ├── 05_Coding_Interview.py
│   ├── 06_Mock_Interview.py
│   ├── 07_Voice_Interview.py
│   ├── 08_Company_Prep.py
│   ├── 09_RAG_Assistant.py
│   ├── 10_Personalized_Roadmap.py
│   ├── 11_Performance_Analytics.py
│   ├── 12_Leaderboard.py
│   ├── 13_Admin_Dashboard.py
│   ├── 14_Career_Coach.py
│   └── 15_Settings.py
├── tests/                      # PyTest unit testing
│   ├── test_auth.py
│   ├── test_ai_clients.py
│   ├── test_rag.py
│   └── test_pdf.py
├── .env.example                # Template for configurations
├── conftest.py                 # Auto-configures sys.path for pytest
├── run.ps1                     # PowerShell dev scripts
├── requirements.txt            # Package dependencies
└── app.py                      # Main authentication landing page
```

---

## 🛠️ Local Installation & Setup

### 1. Clone & Set Up Directory
Create a project folder and navigate to it:
```bash
mkdir ai-prep && cd ai-prep
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
GROQ_API_KEY=your-groq-api-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

> [!NOTE]
> A detailed step-by-step walkthrough for Google Cloud Console and Supabase OAuth dashboard setup can be found in the [Google OAuth Setup Guide](google_oauth_guide.md).


### 3. Setup Database Schema
1. Log in to your **Supabase Console**.
2. Open the **SQL Editor**.
3. Copy the entire contents of [schema.sql](src/database/schema.sql) and click **Run**.
4. Create two storage buckets in the Supabase Storage tab:
   - `resumes` (public: yes)
   - `documents` (public: yes)

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Launch the Web Application
```bash
streamlit run app.py
```

Or use the bundled PowerShell script:
```powershell
.\run.ps1 run        # start server
.\run.ps1 test       # run all tests
.\run.ps1 seed       # seed demo data for a user
.\run.ps1 lint       # run flake8
```

---

## 🧪 Running Automated Tests
The `conftest.py` at the project root automatically adds `src` to the Python path, so no manual `PYTHONPATH` is required:
```bash
pytest -v
```
