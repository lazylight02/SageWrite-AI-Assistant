# SageWrite — AI Professional Email & LinkedIn Message Writer

A production-ready, elegant Streamlit communication assistant powered by the official **Google GenAI SDK** (`google-genai`) and **Supabase PostgreSQL**. SageWrite crafts tailored emails and concise LinkedIn messages for students, job seekers, and professionals.

---

## Features

- **Professional Email Generation**: Structured with high-impact subject lines, formal salutations, concise value-driven bodies, and professional sign-offs.
- **Strictly Bounded LinkedIn Messages**: Tailored to stay under 300 characters for LinkedIn connection requests and InMail.
- **5 High-Impact Purposes**:
  1. Job application
  2. Referral request
  3. Interview follow-up
  4. Internship request
  5. Thank-you after interview
- **Regenerate & Download**: One-click regeneration and `.txt` draft downloads with custom filenames.
- **Supabase Cloud History**: Save drafts securely to Supabase PostgreSQL and review past messages anytime.
- **Aesthetic Visual Design**: Custom Warm Ivory (`#F7F6F0`), Deep Forest (`#183D32`), Soft Sage (`#A8BDA5`), and Muted Sand (`#E9E7DE`) styling.

---

## Technology Stack

- **Language**: Python 3.12+
- **Frontend / Framework**: Streamlit
- **AI Engine**: Google Gemini API via official `google-genai` SDK (`gemini-2.5-flash` with fallbacks)
- **Database**: Supabase PostgreSQL with Row Level Security (RLS)
- **Configuration**: `python-dotenv`

---

## Quick Start (VS Code Terminal)

### 1. Open Terminal & Activate Virtual Environment

**Windows PowerShell:**
```powershell
# Set execution policy if activating scripts is restricted:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Activate virtual environment:
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

*(If you don't have a `.venv` yet, create it with `python -m venv .venv`)*

---

### 2. Install Dependencies

```powershell
pip install -r requirements.txt
```

---

### 3. Configure API Keys

1. Copy `.env.example` to `.env`:
   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env
   ```
2. Open `.env` and fill in your keys:
   ```env
   # Google Gemini API Key (Get free key from https://aistudio.google.com/app/apikey)
   GEMINI_API_KEY=your_gemini_api_key_here

   # Optional: Preferred model (defaults to gemini-2.5-flash)
   GEMINI_MODEL=gemini-2.5-flash

   # Supabase Credentials (from Supabase Dashboard > Project Settings > API)
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your_supabase_anon_public_key_here
   ```

> ⚠️ **Security Warning**: Always use the public/anon key for `SUPABASE_KEY`. Never use a `service_role` or secret key in client applications.

---

### 4. Supabase Database Setup (One-time)

1. Open your Supabase project dashboard at [supabase.com](https://supabase.com).
2. Go to **SQL Editor** from the left navigation bar.
3. Open `supabase_schema.sql` from this project, paste its contents into the SQL Editor, and click **Run**.
4. This creates the `generated_messages` table and configures Row-Level Security (RLS) policies.

---

### 5. Launch the Application

Run from either the root folder or the `ai_communication_assistant` directory:

```powershell
streamlit run app.py
```

Streamlit will launch and automatically open `http://localhost:8501` in your browser.

---

## Project Structure

```text
SageWrite_AI_Communication_Assistant/
├── .venv/                         # Python virtual environment
├── ai_communication_assistant/
│   ├── app.py                    # Main Streamlit application
│   ├── requirements.txt          # Python dependencies
│   ├── .env                      # Local secret credentials (git-ignored)
│   ├── .env.example              # Configuration template
│   ├── .gitignore                # Git ignore rules
│   ├── supabase_schema.sql       # Supabase PostgreSQL DDL & RLS policies
│   └── README.md                 # Project documentation
├── app.py                         # Root entrypoint redirector
├── requirements.txt               # Root dependencies
├── .env.example                   # Root configuration template
├── .gitignore                     # Root git-ignore rules
└── README.md                      # Root documentation
```

---

## Error Handling & Troubleshooting

- **Gemini Key Error (400/403):** Verify that your `GEMINI_API_KEY` in `.env` is valid and active in Google AI Studio.
- **Model Not Found (404):** SageWrite automatically uses `gemini-2.5-flash` with fallbacks to `gemini-2.0-flash` and `gemini-1.5-flash`.
- **Supabase Table Not Found (42P01):** Run `supabase_schema.sql` in your Supabase SQL Editor.
- **Supabase RLS Error (42501):** Ensure the `anon` policies in `supabase_schema.sql` are active.
- **PowerShell Script Error:** Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` before activating `.venv`.

---

## License

Created for academic and professional career development.
