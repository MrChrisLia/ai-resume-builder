# AI Resume Builder

An AI-powered resume builder that generates tailored, ATS-optimized resumes, cover letters, and interview prep from your profile and a job description — powered by Google Gemini.

## Features

- **Resume generation** — Rewrites bullets with strong action verbs, weaves in job keywords, writes a targeted summary
- **Job fit analysis** — Scores candidate match (1–10) with strengths and gaps, including language requirement checks
- **Cover letter** — Professional 3–4 paragraph letter or formal Japanese business letter format
- **Interview prep** — 10 targeted questions (behavioral, technical, situational, motivation, growth) with talking points
- **4 resume templates** — Modern, Classic, Minimal, Japanese (職務経歴書)
- **Photo support** — Optional headshot included in PDF and DOCX output
- **Multi-format export** — Download as PDF, DOCX, or Markdown
- **Resume history** — Saves past generations with re-download support
- **Profile import** — Upload an existing resume (PDF, DOCX, TXT, JSON) to auto-fill your profile
- **Light / dark mode**
- **Shareable via ngrok** — Share a live session with anyone over the internet

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, Flask |
| AI | Google Gemini (`gemini-2.0-flash-lite`) via `google-genai` SDK |
| Document generation | `python-docx`, WeasyPrint (HTML → PDF) |
| PDF parsing | pypdf |
| Frontend | Vanilla JS, CSS custom properties |

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/MrChrisLia/ai-resume-builder.git
cd ai-resume-builder
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **WeasyPrint** requires system libraries. On macOS: `brew install pango`. On Ubuntu: `apt install libpango-1.0-0`.

### 3. Add your Gemini API key

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

Get a free API key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

### 4. Run the app

```bash
venv/bin/python app.py
```

Open [http://localhost:5001](http://localhost:5001) in your browser.

### 5. Share with ngrok (optional)

```bash
ngrok http 5001
```

## Usage

1. Fill in your profile (or import an existing resume)
2. Paste a job description
3. Choose a template
4. Click **Analyze Fit** to check your match score, then **Generate Resume**
5. Download as PDF or DOCX, generate a cover letter, or run interview prep

## Project Structure

```
ai-resume-builder/
├── app.py                 # Flask routes
├── resume_generator.py    # Gemini AI prompts and parsing
├── document_builder.py    # PDF, DOCX, Markdown builders
├── requirements.txt
├── static/
│   ├── app.js
│   └── style.css
└── templates/
    └── index.html
```

## License

MIT
