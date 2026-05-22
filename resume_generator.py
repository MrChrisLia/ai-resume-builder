import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
_client = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
_MODEL  = 'gemini-3.1-flash-lite'


# ── Schemas ────────────────────────────────────────────────────────────────────

RESUME_SCHEMA = """
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "linkedin": "string",
  "github": "string",
  "summary": "2-3 sentence professional summary targeting this specific role",
  "experience": [
    {
      "company": "string",
      "title": "string",
      "start_date": "string",
      "end_date": "string (or 'Present')",
      "bullets": ["string — strong action verb, quantified where possible"]
    }
  ],
  "education": [
    {
      "school": "string",
      "degree": "string",
      "field": "string",
      "graduation": "string",
      "gpa": "string or empty string"
    }
  ],
  "skills": [
    {"category": "string", "items": ["string"]}
  ],
  "languages": [
    {"language": "string", "proficiency": "string", "certificate": "string or empty string"}
  ],
  "projects": [
    {"name": "string", "description": "string", "technologies": "string"}
  ],
  "certifications": ["string"]
}
"""

FIT_SCHEMA = """
{
  "score": <integer 1-10>,
  "verdict": "<one of: Excellent Fit | Strong Fit | Good Fit | Partial Fit | Weak Fit>",
  "summary": "<2-3 sentence overall assessment>",
  "strengths": ["<specific strength that matches the job>"],
  "gaps": ["<specific gap or missing requirement>"]
}
"""

PROFILE_SCHEMA = """
{
  "name": "string",
  "email": "string",
  "phone": "string",
  "location": "string",
  "linkedin": "string",
  "github": "string",
  "experience": [
    {"company": "string", "title": "string", "start_date": "string",
     "end_date": "string", "description": "string"}
  ],
  "education": [
    {"school": "string", "degree": "string", "field": "string",
     "graduation": "string", "gpa": "string"}
  ],
  "skills": [{"category": "string", "items": ["string"]}],
  "languages": [{"language": "string", "proficiency": "string", "certificate": "string or empty string"}],
  "projects": [{"name": "string", "technologies": "string", "description": "string"}],
  "certifications": ["string"],
  "extra_info": "string"
}
"""

INTERVIEW_SCHEMA = """
[
  {
    "question": "string",
    "category": "Behavioral | Technical | Situational | Motivation | Growth",
    "why_asked": "string — what the interviewer is looking for",
    "talking_points": ["string", "string", "string"]
  }
]
"""


# ── Internal helpers ───────────────────────────────────────────────────────────

def _strip_photo(candidate: dict) -> dict:
    """Remove the base64 photo before sending to Gemini — it's huge and the AI doesn't need it."""
    return {k: v for k, v in candidate.items() if k != 'photo'}

def _call_json(prompt: str, temperature: float = 0.3) -> str:
    response = _client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type='application/json',
        ),
    )
    text = (response.text or '').strip()
    if not text:
        raise ValueError('Gemini returned an empty response. Please try again.')
    if text.startswith('```'):
        lines = text.splitlines()
        text = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
    return text.strip()


def _parse_json(text: str):
    """Parse JSON from model output, discarding any extra text the model appends after the value."""
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        if 'Extra data' in str(e) and e.pos > 0:
            return json.loads(text[:e.pos])
        raise


def _call_text(prompt: str, temperature: float = 0.5) -> str:
    response = _client.models.generate_content(
        model=_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(temperature=temperature),
    )
    return response.text.strip()


# ── Public API ─────────────────────────────────────────────────────────────────

def analyze_fit(candidate_data: dict, job_description: str) -> dict:
    candidate_data = _strip_photo(candidate_data)
    prompt = f"""You are a senior recruiter. Evaluate how well this candidate matches the job.

=== CANDIDATE PROFILE ===
{json.dumps(candidate_data, indent=2)}

=== JOB DESCRIPTION ===
{job_description}

Score honestly (1-10) on: skills match, experience relevance, education fit, language requirements, overall alignment.
List 3-5 strengths and 2-4 gaps — name actual skills and requirements.

MANDATORY LANGUAGE CHECK: Scan the job description for ANY human language requirements (e.g. "Japanese required", "must be bilingual", "English fluency", "Mandarin speaker", "native Korean", etc.). Compare each required language against the candidate's languages list. If a required language is missing from the candidate's profile OR their proficiency is insufficient, it MUST appear in the gaps list prefixed with ⚠️ (e.g. "⚠️ Japanese fluency required but not listed in candidate profile"). Do this check even if you have already found enough other gaps.

Return ONLY valid JSON (no markdown):
{FIT_SCHEMA}
"""
    return _parse_json(_call_json(prompt))


def generate_resume(candidate_data: dict, job_description: str, template: str = 'modern') -> dict:
    candidate_data = _strip_photo(candidate_data)
    is_japanese = template == 'japanese'
    lang_note = (
        "\nWrite ALL content in formal Japanese (ですます調). "
        "Format dates as YYYY年MM月. Use Japanese professional terminology."
    ) if is_japanese else ''

    prompt = f"""You are an expert resume writer and ATS optimization specialist.
Create a perfectly tailored, ATS-optimized resume.{lang_note}

=== CANDIDATE INFORMATION ===
{json.dumps(candidate_data, indent=2)}

=== JOB DESCRIPTION ===
{job_description}

Instructions:
1. Rewrite experience bullets with strong action verbs aligned with the role.
2. Quantify achievements wherever data exists; otherwise write impactful qualitative bullets.
3. Weave job description keywords naturally into bullets and summary.
4. Write a 2-3 sentence summary targeting this specific role.
5. Group and order skills by job relevance.
6. Include languages if relevant to the role.
7. Incorporate extra_info items (awards, publications, etc.) where relevant.
8. ONLY use provided information — never fabricate.
9. Bullets: one line each, max ~100 characters.

Return ONLY valid JSON (no markdown fences):
{RESUME_SCHEMA}

Return empty arrays [] for sections with no data.
"""
    return _parse_json(_call_json(prompt, temperature=0.4))


def generate_cover_letter(candidate_data: dict, job_description: str,
                           resume_data: dict, template: str = 'modern') -> dict:
    candidate_data = _strip_photo(candidate_data)
    is_japanese = template == 'japanese'

    if is_japanese:
        style = (
            "Write a formal Japanese business cover letter (拝啓〜敬具 format). "
            "Use 敬語 throughout. Address the company as 貴社."
        )
        schema = '{"text": "letter body in Japanese", "job_title": "役職名", "company": "会社名"}'
    else:
        style = (
            "Write a professional 3-4 paragraph cover letter. "
            "Open with enthusiasm for the role, highlight 2 key achievements, close with a call to action. "
            "Tone: confident, warm, specific — avoid clichés."
        )
        schema = '{"text": "letter body paragraphs only", "job_title": "extracted job title", "company": "extracted company name or \'the company\'"}'

    top_bullets = [
        b for exp in resume_data.get('experience', [])[:2]
        for b in exp.get('bullets', [])[:3]
    ]

    prompt = f"""You are an expert cover letter writer. {style}

=== CANDIDATE ===
{json.dumps(candidate_data, indent=2)}

=== JOB DESCRIPTION ===
{job_description}

=== RESUME SUMMARY ===
{resume_data.get('summary', '')}

=== TOP ACHIEVEMENT BULLETS ===
{json.dumps(top_bullets, indent=2)}

Return ONLY valid JSON:
{schema}

The "text" field: complete letter body only — no date, no address, no salutation, no sign-off.
Use paragraph breaks (double newline) between paragraphs.
"""
    return _parse_json(_call_json(prompt, temperature=0.6))


def generate_interview_prep(candidate_data: dict, job_description: str,
                             template: str = 'modern') -> list:
    candidate_data = _strip_photo(candidate_data)
    is_japanese = template == 'japanese'
    lang_note = "Write all questions and answers in Japanese (ですます調)." if is_japanese else ''

    prompt = f"""You are an expert interview coach. Generate targeted interview preparation.
{lang_note}

=== CANDIDATE ===
{json.dumps(candidate_data, indent=2)}

=== JOB DESCRIPTION ===
{job_description}

Generate exactly 10 questions:
- 3 behavioral (STAR method, past experience)
- 3 role-specific technical
- 2 situational ("what would you do if...")
- 1 motivation / culture fit
- 1 weakness or growth

For each question: WHY interviewers ask it, and 3-4 specific talking points the candidate should cover,
referencing their ACTUAL experience listed above.

Return ONLY valid JSON array (no markdown):
{INTERVIEW_SCHEMA}
"""
    return _parse_json(_call_json(prompt, temperature=0.5))


def parse_resume_text(text: str) -> dict:
    prompt = f"""You are a resume parser. Extract all information from the resume text below.

=== RESUME TEXT ===
{text}

Instructions:
- Group skills into logical categories (Languages, Frameworks, Tools, Cloud, etc.)
- Copy experience descriptions verbatim — do not rewrite
- Detect spoken languages (e.g., "Fluent in Spanish", "Native: Mandarin")
- Put awards, publications, volunteering, etc. in extra_info
- Use "" for missing text fields, [] for missing arrays

Return ONLY valid JSON (no markdown):
{PROFILE_SCHEMA}
"""
    return _parse_json(_call_json(prompt))
