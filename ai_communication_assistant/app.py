import os
from datetime import datetime
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from supabase import create_client, Client

# ---------- Environment Configuration ----------
def load_app_env():
    """Locate and load .env from script directory, current directory, or parent directory."""
    script_dir = Path(__file__).resolve().parent
    potential_paths = [
        script_dir / ".env",
        Path.cwd() / ".env",
        script_dir.parent / ".env",
    ]
    for env_path in potential_paths:
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path, override=False)
            return env_path
    load_dotenv()
    return None

load_app_env()

def get_config():
    """Retrieve environment variables with fallback to st.secrets if configured."""
    def _read_val(key: str, default: str = "") -> str:
        val = os.getenv(key, "")
        if not val and hasattr(st, "secrets") and key in st.secrets:
            try:
                val = str(st.secrets[key])
            except Exception:
                pass
        return val.strip()

    gemini_key = _read_val("GEMINI_API_KEY")
    gemini_model = _read_val("GEMINI_MODEL", "gemini-3.8-flash")
    supabase_url = _read_val("SUPABASE_URL")
    supabase_key = _read_val("SUPABASE_KEY")
    return gemini_key, gemini_model, supabase_url, supabase_key

GEMINI_API_KEY, GEMINI_MODEL, SUPABASE_URL, SUPABASE_KEY = get_config()

# ---------- Streamlit Page Config & Aesthetic Theme ----------
st.set_page_config(
    page_title="SageWrite | AI Professional Communication",
    page_icon="✦",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --ivory: #F7F6F0;
    --forest: #183D32;
    --sage: #A8BDA5;
    --sand: #E9E7DE;
    --ink: #252923;
}

.stApp {
    background: var(--ivory);
    color: var(--ink);
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    max-width: 1180px;
    padding-top: 2.2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: var(--forest) !important;
}

.hero {
    padding: 1.5rem 0 1rem;
}

.eyebrow {
    color: #718574;
    letter-spacing: .16em;
    text-transform: uppercase;
    font-size: .72rem;
    font-weight: 700;
}

.hero h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    margin: .35rem 0;
}

.hero p {
    color: #687168;
    font-size: 1.02rem;
}

.panel {
    background: #fffefa;
    border: 1px solid var(--sand);
    border-radius: 18px;
    padding: 1.35rem;
}

div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: var(--sand) !important;
    border-radius: 16px !important;
}

.stButton>button, .stFormSubmitButton>button {
    background: var(--forest);
    color: white;
    border: 0;
    border-radius: 10px;
    padding: .62rem 1.15rem;
    font-weight: 600;
}

.stButton>button:hover, .stFormSubmitButton>button:hover {
    background: #285747;
    color: white;
    border: 0;
}

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
    border-radius: 10px;
}

[data-testid="stSidebar"] {
    background: #EFEEE6;
}

[data-testid="stSidebar"] h1 {
    font-family: 'Playfair Display', serif;
}

.small-note {
    color: #788078;
    font-size: .85rem;
}

.result-box {
    background: #fffefa;
    border: 1px solid var(--sand);
    border-radius: 16px;
    padding: 1.35rem;
    white-space: pre-wrap;
    line-height: 1.68;
    font-size: .98rem;
    color: var(--ink);
}

.status-pill {
    display: inline-block;
    padding: 3px 9px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.status-pill.ok {
    background: #E3EDE4;
    color: #183D32;
    border: 1px solid #C4D6C6;
}
.status-pill.warn {
    background: #FFF3CD;
    color: #856404;
    border: 1px solid #FFEEBA;
}

hr {
    border-color: var(--sand);
}
</style>
""", unsafe_allow_html=True)

# ---------- Supabase Client Initialization ----------
@st.cache_resource(show_spinner=False)
def get_supabase(url: str, key: str):
    """Instantiate a Supabase client using anon/publishable credentials."""
    if not url or not key:
        return None
    # Security check: never accept secret/service-role keys in a client app
    if "service_role" in key.lower() or key.startswith("sb_secret_"):
        return "SERVICE_KEY_ERROR"
    try:
        return create_client(url, key)
    except Exception:
        return None

# ---------- Gemini Text Generation ----------
PURPOSE_GUIDELINES = {
    "Job application": "Express interest in the specific position, highlight key technical and interpersonal strengths, and request consideration for an interview.",
    "Referral request": "Respectfully ask for a referral or informational chat, highlighting genuine alignment with the company culture and role.",
    "Interview follow-up": "Politely check on the status of the interview process, reaffirm enthusiasm for the role, and offer any additional information if needed.",
    "Internship request": "Reach out as an enthusiastic, motivated student seeking an internship opportunity, emphasizing rapid learning ability and foundational skills.",
    "Thank-you after interview": "Express genuine appreciation for the interviewer's time, mention key conversational takeaways, and reiterate excitement for next steps."
}

def generate_message(data: dict, message_type: str) -> str:
    """Generate professional communication drafts using Google GenAI SDK."""
    gemini_key, preferred_model, _, _ = get_config()

    if not gemini_key or gemini_key == "your_gemini_api_key_here":
        raise RuntimeError("Google Gemini API key is missing. Please add your GEMINI_API_KEY to the .env file.")

    client = genai.Client(api_key=gemini_key)

    profile_text = f"""CANDIDATE / SENDER PROFILE:
- Full Name: {data.get('name', '').strip()}
- Degree / Academic Background: {data.get('degree', '').strip() or 'Not specified'}
- Technical & Soft Skills: {data.get('skills', '').strip() or 'Not specified'}
- Relevant Projects / Experience: {data.get('experience', '').strip() or 'Not specified'}

OPPORTUNITY DETAILS:
- Target Company / Recipient: {data.get('company', '').strip()}
- Target Role / Subject: {data.get('role', '').strip()}
- Goal / Purpose: {data.get('purpose', '').strip()}
- Additional Context / Job Description: {data.get('context', '').strip() or 'None provided'}
"""

    purpose = data.get("purpose", "Professional communication")
    purpose_advice = PURPOSE_GUIDELINES.get(purpose, "Maintain a courteous, clear, and professional tone.")

    if message_type == "Email":
        prompt = f"""You are an expert executive career communication specialist.
Write a polished, personalized, and effective professional email based STRICTLY on the details provided below.

PURPOSE: {purpose}
GUIDANCE: {purpose_advice}

EMAIL STRUCTURE:
1. First line MUST start with 'Subject: ' followed by a compelling, concise subject line.
2. A blank line.
3. Formal professional salutation (e.g. 'Dear [Recipient Name / Hiring Manager],').
4. A clear, engaging opening statement establishing the purpose.
5. 1-2 focused body paragraphs connecting the candidate's skills and experience to the opportunity.
6. A polite, clear call-to-action.
7. Professional sign-off and the sender's full name.

STRICT CONSTRAINTS:
- Do NOT invent experiences, degrees, or metrics not present in the profile.
- Return ONLY the complete email (Subject line + body).

{profile_text}"""
    else:
        prompt = f"""You are an expert career networking advisor.
Write a high-impact, professional LinkedIn connection request / direct message.

PURPOSE: {purpose}
GUIDANCE: {purpose_advice}

CRITICAL REQUIREMENT:
- The total length MUST be STRICTLY under 300 characters (including all spaces, letters, and punctuation).
- Target length: 220 to 260 characters so it fits comfortably.
- Return ONLY the plain message text.
- Do NOT include subject lines, quotation marks, greeting labels, or hashtags.
- Ensure every statement is derived solely from the provided profile.

{profile_text}"""

    # Modern Gemini models with automatic multi-tier fallback
    candidate_models = [
        preferred_model if preferred_model else "gemini-3.8-flash",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-2.5-flash-lite",
        "gemini-2.5-pro"
    ]
    # Remove duplicates preserving order
    models_to_try = []
    for m in candidate_models:
        if m and m not in models_to_try:
            models_to_try.append(m)

    last_error = None
    response = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            if response and response.text:
                break
        except APIError as api_err:
            last_error = api_err
            status_code = getattr(api_err, "code", None)
            err_msg = str(api_err)
            
            # Quota exceeded
            if status_code == 429 or "RESOURCE_EXHAUSTED" in err_msg:
                raise RuntimeError("Gemini API quota or rate limit exceeded. Please wait a minute and retry.")
            
            # Explicit key rejection
            if status_code == 403 or "API_KEY_INVALID" in err_msg or "API key not valid" in err_msg:
                raise RuntimeError("Invalid Gemini API key. Please check your GEMINI_API_KEY in the .env file.")
            
            # Model not found or high demand: try next model in fallback list
            if status_code in (404, 503) or "NOT_FOUND" in err_msg or "UNAVAILABLE" in err_msg or "no longer available" in err_msg:
                continue

            # For other API errors, try next model before giving up
            continue

        except Exception as general_err:
            last_error = general_err
            err_type = type(general_err).__name__
            err_msg = str(general_err)
            if "ConnectError" in err_type or "getaddrinfo" in err_msg or "timeout" in err_msg.lower():
                raise RuntimeError("Network error: Unable to connect to the Gemini API. Please check your internet connection.")
            continue

    if not response or not response.text:
        if last_error:
            raise RuntimeError(f"Gemini API request failed: {last_error}")
        raise RuntimeError("Gemini returned an empty response. Please review your input and try again.")

    output_text = response.text.strip()

    # Clean up formatting artifacts if present
    if output_text.startswith('"""') and output_text.endswith('"""'):
        output_text = output_text[3:-3].strip()
    if output_text.startswith('"') and output_text.endswith('"'):
        output_text = output_text[1:-1].strip()

    # Safety constraint: enforce <= 300 characters for LinkedIn
    if message_type == "LinkedIn" and len(output_text) > 300:
        truncated = output_text[:300]
        last_punct = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
        if last_punct > 180:
            output_text = truncated[:last_punct + 1].strip()
        else:
            output_text = truncated.rstrip()

    return output_text

# ---------- Supabase Database Functions ----------
def save_message(sb, row: dict):
    """Save generated draft to Supabase with comprehensive error handling."""
    if sb == "SERVICE_KEY_ERROR":
        return False, "Security warning: A secret/service-role key was detected. Please use the public/anon key instead."
    if sb is None:
        return False, "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to your .env file."

    try:
        sb.table("generated_messages").insert(row).execute()
        return True, "Draft successfully saved to your Supabase history."
    except Exception as exc:
        err_msg = str(exc)
        err_type = type(exc).__name__
        if "42P01" in err_msg or "does not exist" in err_msg:
            return False, "Table 'generated_messages' was not found. Please execute the SQL in 'supabase_schema.sql' in your Supabase SQL Editor."
        elif "42501" in err_msg or "row-level security" in err_msg.lower():
            return False, "Access denied by Row-Level Security. Please apply the RLS policies from 'supabase_schema.sql'."
        elif "ConnectError" in err_type or "getaddrinfo" in err_msg or "timeout" in err_msg.lower():
            return False, "Network error: Unable to reach Supabase. Please verify your connection."
        elif "401" in err_msg or "Invalid API key" in err_msg or "JWT" in err_msg:
            return False, "Supabase authentication failed. Please check your SUPABASE_KEY."
        return False, f"Could not save draft: {err_msg}"

def load_history(sb):
    """Load message history from Supabase, returning (rows, error_message)."""
    if sb == "SERVICE_KEY_ERROR":
        return [], "Security warning: Supabase secret/service-role key detected. Please configure the anon/public key."
    if sb is None:
        return [], "Supabase is not configured. Add SUPABASE_URL and SUPABASE_KEY to your .env file to view history."

    try:
        result = sb.table("generated_messages").select("*").order("created_at", desc=True).limit(50).execute()
        return (result.data or []), None
    except Exception as exc:
        err_msg = str(exc)
        err_type = type(exc).__name__
        if "42P01" in err_msg or "does not exist" in err_msg:
            return [], "Table 'generated_messages' does not exist in Supabase yet. Please run 'supabase_schema.sql' in your Supabase SQL Editor to set it up."
        elif "42501" in err_msg or "row-level security" in err_msg.lower():
            return [], "Access denied by Row-Level Security. Please run 'supabase_schema.sql' to allow read access."
        elif "ConnectError" in err_type or "getaddrinfo" in err_msg or "timeout" in err_msg.lower():
            return [], "Network error: Unable to reach Supabase. Please check your internet connection."
        elif "401" in err_msg or "Invalid API key" in err_msg or "JWT" in err_msg:
            return [], "Supabase authentication failed. Please check your SUPABASE_URL and SUPABASE_KEY."
        return [], f"Could not load history: {err_msg}"

# ---------- Session State Initialization ----------
if "generated" not in st.session_state:
    st.session_state.generated = None
if "last_data" not in st.session_state:
    st.session_state.last_data = None
if "last_type" not in st.session_state:
    st.session_state.last_type = "Email"
if "save_feedback" not in st.session_state:
    st.session_state.save_feedback = None

# Track form field state to prevent input reset on rerun
for field in ["name", "degree", "skills", "experience", "company", "role", "context"]:
    if f"form_{field}" not in st.session_state:
        st.session_state[f"form_{field}"] = ""

# Connect to Supabase
sb_client = get_supabase(SUPABASE_URL, SUPABASE_KEY)

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("# ✦ SageWrite")
    st.caption("Thoughtful words. Better connections.")
    st.divider()

    page = st.radio("WORKSPACE", ["Create message", "Message history"], label_visibility="visible")

    st.divider()
    st.markdown("**System Status**")

    # Status chips
    if GEMINI_API_KEY and GEMINI_API_KEY != "your_gemini_api_key_here":
        st.markdown('<span class="status-pill ok">● Gemini Configured</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill warn">▲ Gemini Key Missing</span>', unsafe_allow_html=True)

    if sb_client and sb_client != "SERVICE_KEY_ERROR":
        st.markdown('<span class="status-pill ok">● Supabase Connected</span>', unsafe_allow_html=True)
    elif sb_client == "SERVICE_KEY_ERROR":
        st.markdown('<span class="status-pill warn">▲ Supabase Key Insecure</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-pill warn">○ Supabase Not Configured</span>', unsafe_allow_html=True)

    st.divider()
    st.markdown("**About SageWrite**")
    st.markdown('<span class="small-note">Minimal, focused career writing assistant powered by Gemini AI and Supabase.</span>', unsafe_allow_html=True)
    st.caption("Your credentials stay securely on your machine.")

# ---------- Main View: Create Message ----------
if page == "Create message":
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">AI PROFESSIONAL COMMUNICATION</div>
      <h1>Make your next message matter.</h1>
      <p>Craft tailored emails and concise LinkedIn messages for internships, jobs, referrals, and interviews.</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([1.02, .98], gap="large")

    with left:
        st.markdown("### Your details")
        with st.form("message_form"):
            name = st.text_input(
                "Full name *",
                value=st.session_state.form_name,
                placeholder="e.g. Prakash Reddy"
            )
            degree = st.text_input(
                "Degree / course",
                value=st.session_state.form_degree,
                placeholder="e.g. B.Tech in Computer Science & AI"
            )
            skills = st.text_area(
                "Key skills",
                value=st.session_state.form_skills,
                placeholder="Python, Streamlit, SQL, machine learning, communication...",
                height=75
            )
            experience = st.text_area(
                "Relevant projects / experience",
                value=st.session_state.form_experience,
                placeholder="Briefly describe 1-2 relevant projects, achievements, or coursework.",
                height=90
            )

            st.markdown("### Opportunity details")
            company = st.text_input(
                "Company / recipient *",
                value=st.session_state.form_company,
                placeholder="e.g. Google, Microsoft, or hiring manager name"
            )
            role = st.text_input(
                "Job role / subject *",
                value=st.session_state.form_role,
                placeholder="e.g. AI Intern / Software Engineer"
            )
            context = st.text_area(
                "Job description or context (optional)",
                value=st.session_state.form_context,
                placeholder="Paste key requirements from the job posting or details about your goal.",
                height=100
            )

            purpose = st.selectbox(
                "Purpose",
                [
                    "Job application",
                    "Referral request",
                    "Interview follow-up",
                    "Internship request",
                    "Thank-you after interview"
                ]
            )

            # Segmented control with backward compatibility for earlier Streamlit versions
            if hasattr(st, "segmented_control"):
                fmt = st.segmented_control("Message format", ["Email", "LinkedIn"], default="Email")
                message_type = fmt if fmt else "Email"
            else:
                message_type = st.radio("Message format", ["Email", "LinkedIn"], horizontal=True)

            submitted = st.form_submit_button("✦ Generate message", use_container_width=True)

        if submitted:
            # Sync session state with current form values
            st.session_state.form_name = name
            st.session_state.form_degree = degree
            st.session_state.form_skills = skills
            st.session_state.form_experience = experience
            st.session_state.form_company = company
            st.session_state.form_role = role
            st.session_state.form_context = context

            # Validation: Empty form submission check
            if not any([name.strip(), company.strip(), role.strip(), skills.strip(), experience.strip()]):
                st.warning("Please fill in your details before generating a message.")
            else:
                missing = [label for label, val in [("Full name", name), ("Company / recipient", company), ("Job role / subject", role)] if not val.strip()]
                if missing:
                    st.warning(f"Please provide required fields: {', '.join(missing)}")
                else:
                    data = {
                        "name": name.strip(),
                        "degree": degree.strip(),
                        "skills": skills.strip(),
                        "experience": experience.strip(),
                        "company": company.strip(),
                        "role": role.strip(),
                        "context": context.strip(),
                        "purpose": purpose
                    }
                    with st.spinner("Crafting your professional draft..."):
                        try:
                            generated_text = generate_message(data, message_type)
                            st.session_state.generated = generated_text
                            st.session_state.last_data = data
                            st.session_state.last_type = message_type
                            st.session_state.save_feedback = None
                            st.success("Your draft is ready!")
                        except Exception as exc:
                            st.error(str(exc))

    with right:
        st.markdown("### Your draft")

        if st.session_state.generated:
            st.markdown(f'<div class="result-box">{st.session_state.generated}</div>', unsafe_allow_html=True)

            if st.session_state.last_type == "LinkedIn":
                char_count = len(st.session_state.generated)
                if char_count <= 300:
                    st.markdown(f'<span class="status-pill ok" style="margin-top:10px;">✓ {char_count}/300 characters</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span class="status-pill warn" style="margin-top:10px;">▲ {char_count}/300 characters (exceeds limit)</span>', unsafe_allow_html=True)

            st.write("")
            c1, c2 = st.columns(2)

            with c1:
                company_slug = (st.session_state.last_data.get("company", "draft") if st.session_state.last_data else "draft").replace(" ", "_").lower()
                type_slug = st.session_state.last_type.lower()
                st.download_button(
                    "↓ Download .txt",
                    st.session_state.generated,
                    file_name=f"sagewrite_{company_slug}_{type_slug}.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with c2:
                if st.button("↻ Regenerate", use_container_width=True):
                    if st.session_state.last_data:
                        with st.spinner("Creating an updated draft..."):
                            try:
                                regenerated = generate_message(st.session_state.last_data, st.session_state.last_type)
                                st.session_state.generated = regenerated
                                st.session_state.save_feedback = None
                                st.rerun()
                            except Exception as exc:
                                st.error(str(exc))
                    else:
                        st.warning("No previous prompt data found to regenerate. Please fill the form and submit.")

            # Save to history button
            if st.button("Save to history", use_container_width=True):
                if st.session_state.last_data and st.session_state.generated:
                    row_data = {
                        "name": st.session_state.last_data.get("name", "Anonymous"),
                        "message_type": st.session_state.last_type,
                        "purpose": st.session_state.last_data.get("purpose", "General"),
                        "company": st.session_state.last_data.get("company", "Unspecified"),
                        "generated_content": st.session_state.generated,
                    }
                    ok, msg = save_message(sb_client, row_data)
                    st.session_state.save_feedback = (ok, msg)

            if st.session_state.save_feedback:
                ok, msg = st.session_state.save_feedback
                if ok:
                    st.success(msg)
                else:
                    st.warning(msg)

        else:
            st.markdown("""
            <div class="panel">
              <div class="eyebrow">YOUR MESSAGE WILL APPEAR HERE</div>
              <h3 style="margin-top:1rem">A clear message opens doors.</h3>
              <p style="color:#687168">Fill in your details on the left, select a message format, and click Generate. You can review, regenerate, download, and store your drafts in Supabase.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<p class="small-note" style="margin-top:1.2rem;">AI drafts should always be reviewed and personalized before sending.</p>', unsafe_allow_html=True)

# ---------- Message History View ----------
else:
    st.markdown("""
    <div class="hero">
      <div class="eyebrow">YOUR WORKSPACE</div>
      <h1>Message history.</h1>
      <p>Revisit drafts you have previously saved to your Supabase PostgreSQL database.</p>
    </div>
    """, unsafe_allow_html=True)

    if sb_client is None:
        st.info("💡 Connect Supabase to save and browse your message history. Add SUPABASE_URL and SUPABASE_KEY to your .env file.")
    elif sb_client == "SERVICE_KEY_ERROR":
        st.error("⚠️ Security alert: A service-role or secret key was detected in SUPABASE_KEY. Please replace it with the public 'anon' key from your Supabase API settings.")
    else:
        history, error_msg = load_history(sb_client)

        if error_msg:
            st.warning(f"⚠️ {error_msg}")
        elif not history:
            st.info("No saved drafts found yet. Generate a message in the workspace and click 'Save to history'.")
        else:
            st.caption(f"Showing {len(history)} saved draft{'s' if len(history) != 1 else ''}:")
            for item in history:
                m_type = item.get("message_type", "Message")
                purpose = item.get("purpose", "Draft")
                comp = item.get("company", "General")
                raw_created = item.get("created_at", "")

                formatted_time = ""
                if raw_created:
                    try:
                        clean_ts = raw_created.replace("Z", "+00:00")
                        dt = datetime.fromisoformat(clean_ts)
                        formatted_time = dt.strftime("%b %d, %Y · %I:%M %p")
                    except Exception:
                        formatted_time = str(raw_created)[:16]

                title = f"{m_type} · {purpose} · {comp}"
                with st.expander(title):
                    st.caption(f"👤 {item.get('name', 'Anonymous')}   |   📅 {formatted_time}")
                    content = item.get("generated_content", "")
                    st.markdown(f'<div class="result-box">{content}</div>', unsafe_allow_html=True)
                    st.write("")
                    item_id = item.get("id", "draft")
                    st.download_button(
                        f"↓ Download this draft",
                        content,
                        file_name=f"sagewrite_{comp.lower().replace(' ', '_')}_{item_id}.txt",
                        key=f"download_{item_id}"
                    )
