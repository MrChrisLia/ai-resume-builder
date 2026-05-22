import os
import io
import re
import uuid
import json
import pypdf
from docx import Document as DocxDocument
from flask import Flask, render_template, request, jsonify, send_file, abort
from dotenv import load_dotenv
from google.genai import errors as genai_errors
from resume_generator import (generate_resume, analyze_fit, parse_resume_text,
                               generate_cover_letter, generate_interview_prep)
from document_builder import (build_docx, build_pdf, build_markdown, build_preview_html,
                               build_cover_letter_docx, build_cover_letter_pdf,
                               build_cover_letter_md)

load_dotenv()

app = Flask(__name__)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

_SAFE_NAME = re.compile(r'^[a-f0-9_]+\.(docx|pdf|md|html)$')


def _safe_path(filename):
    if not _SAFE_NAME.match(filename):
        abort(400)
    return os.path.join(OUTPUT_DIR, filename)


def _file_id():
    return uuid.uuid4().hex[:10]


def _ai_error(e: Exception) -> tuple[str, int]:
    """Translate a Gemini API exception into a user-friendly (message, http_status) tuple."""
    if isinstance(e, genai_errors.ClientError):
        code = e.status_code if hasattr(e, 'status_code') else 0
        msg  = str(e)
        if code == 429 or 'RESOURCE_EXHAUSTED' in msg:
            # Try to extract the retry delay from the error body
            import re as _re
            delay = _re.search(r'retry[^\d]*(\d+)', msg, _re.I)
            wait  = f' Please wait {delay.group(1)} seconds and try again.' if delay else ' Please wait a moment and try again.'
            return (f'Gemini API rate limit reached — you exceeded the free-tier quota.{wait}', 429)
        if code == 400 or 'INVALID_ARGUMENT' in msg:
            return ('Gemini rejected the request (invalid input). Try shortening the job description.', 400)
        if code == 401 or 'UNAUTHENTICATED' in msg:
            return ('Gemini API key is invalid or missing. Check your .env file.', 401)
        if code == 403 or 'PERMISSION_DENIED' in msg:
            return ('Gemini API key does not have permission to use this model.', 403)
        if code == 404 or 'NOT_FOUND' in msg:
            return (f'Gemini model not found. Check the model name in resume_generator.py.', 404)
        if code == 503 or 'UNAVAILABLE' in msg:
            return ('Gemini API is temporarily unavailable. Please try again in a few seconds.', 503)
        return (f'Gemini API error ({code}): {msg[:200]}', 500)
    return (str(e)[:300], 500)


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Import ─────────────────────────────────────────────────────────────────────

@app.route('/import-profile', methods=['POST'])
def import_profile():
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        fname = file.filename.lower()
        text  = ''
        if fname.endswith('.pdf'):
            raw = file.read()
            try:
                reader = pypdf.PdfReader(io.BytesIO(raw))
                if reader.is_encrypted:
                    return jsonify({'error': 'PDF is password-protected. Remove the password and try again.'}), 400
                pages = []
                for page in reader.pages:
                    try:
                        pages.append(page.extract_text() or '')
                    except Exception:
                        pages.append('')
                text = '\n'.join(pages)
            except pypdf.errors.PdfReadError as e:
                return jsonify({'error': f'Could not read PDF ({e}). Try saving as DOCX or TXT instead.'}), 400
        elif fname.endswith('.docx'):
            doc = DocxDocument(io.BytesIO(file.read()))
            text = '\n'.join(p.text for p in doc.paragraphs)
        elif fname.endswith(('.txt', '.md')):
            text = file.read().decode('utf-8', errors='ignore')
        elif fname.endswith('.json'):
            try:
                profile = json.loads(file.read().decode('utf-8'))
                return jsonify({'success': True, 'profile': profile})
            except Exception:
                return jsonify({'error': 'Invalid JSON file'}), 400
        else:
            return jsonify({'error': 'Unsupported file type. Use PDF, DOCX, TXT, MD, or JSON.'}), 400

        text = text.strip()
        if not text:
            hint = ' Try opening in Word and saving as DOCX, then importing that.' if fname.endswith('.pdf') else ''
            return jsonify({'error': f'Could not extract text from the file.{hint}'}), 400

        profile = parse_resume_text(text)
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── Fit analysis ───────────────────────────────────────────────────────────────

@app.route('/analyze-fit', methods=['POST'])
def fit():
    data = request.get_json() or {}
    candidate       = data.get('candidate', {})
    job_description = data.get('job_description', '').strip()
    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400
    try:
        return jsonify({'success': True, 'fit': analyze_fit(candidate, job_description)})
    except Exception as e:
        msg, status = _ai_error(e)
        return jsonify({'error': msg}), status


# ── Resume generation ──────────────────────────────────────────────────────────

@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json() or {}
    candidate      = data.get('candidate', {})
    job_description = data.get('job_description', '').strip()
    formats         = data.get('formats', ['docx', 'pdf'])
    template        = data.get('template', 'modern')

    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400

    try:
        resume_data = generate_resume(candidate, job_description, template)
    except Exception as e:
        msg, status = _ai_error(e)
        return jsonify({'error': msg}), status

    # Re-attach photo for document builders (stripped before Gemini call to save tokens)
    if candidate.get('photo'):
        resume_data['photo'] = candidate['photo']

    fid = _file_id()
    downloads = {}

    if 'docx' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.docx')
        build_docx(resume_data, p, template)
        downloads['docx'] = f'/download/{fid}.docx'

    if 'pdf' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.pdf')
        build_pdf(resume_data, p, template)
        downloads['pdf'] = f'/download/{fid}.pdf'

    if 'md' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.md')
        build_markdown(resume_data, p)
        downloads['md'] = f'/download/{fid}.md'

    html_path = os.path.join(OUTPUT_DIR, f'{fid}.html')
    build_preview_html(resume_data, html_path, template)
    downloads['preview'] = f'/preview/{fid}.html'

    # Strip photo before sending to client — documents already built, no need to store base64 in localStorage
    resume_for_client = {k: v for k, v in resume_data.items() if k != 'photo'}

    return jsonify({'success': True, 'downloads': downloads,
                    'resume': resume_for_client, 'file_id': fid})


# ── Regenerate files from stored resume JSON ───────────────────────────────────

@app.route('/regenerate', methods=['POST'])
def regenerate():
    data        = request.get_json() or {}
    resume_data = data.get('resume_data', {})
    formats     = data.get('formats', ['docx', 'pdf'])
    template    = data.get('template', 'modern')
    if not resume_data: return jsonify({'error': 'No resume data provided'}), 400

    fid = _file_id()
    downloads = {}
    if 'docx' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.docx')
        build_docx(resume_data, p, template)
        downloads['docx'] = f'/download/{fid}.docx'
    if 'pdf' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.pdf')
        build_pdf(resume_data, p, template)
        downloads['pdf'] = f'/download/{fid}.pdf'
    if 'md' in formats:
        p = os.path.join(OUTPUT_DIR, f'{fid}.md')
        build_markdown(resume_data, p)
        downloads['md'] = f'/download/{fid}.md'
    html_path = os.path.join(OUTPUT_DIR, f'{fid}.html')
    build_preview_html(resume_data, html_path, template)
    downloads['preview'] = f'/preview/{fid}.html'
    return jsonify({'success': True, 'downloads': downloads})


# ── Cover letter ───────────────────────────────────────────────────────────────

@app.route('/generate-cover-letter', methods=['POST'])
def cover_letter():
    data = request.get_json() or {}
    candidate      = data.get('candidate', {})
    job_description = data.get('job_description', '').strip()
    resume_data    = data.get('resume_data', {})
    formats        = data.get('formats', ['docx', 'pdf'])
    template       = data.get('template', 'modern')

    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400

    try:
        letter = generate_cover_letter(candidate, job_description, resume_data, template)
    except Exception as e:
        msg, status = _ai_error(e)
        return jsonify({'error': msg}), status

    fid = _file_id()
    downloads = {}

    if 'docx' in formats:
        p = os.path.join(OUTPUT_DIR, f'cl_{fid}.docx')
        build_cover_letter_docx(letter, candidate, p)
        downloads['docx'] = f'/download/cl_{fid}.docx'
    if 'pdf' in formats:
        p = os.path.join(OUTPUT_DIR, f'cl_{fid}.pdf')
        build_cover_letter_pdf(letter, candidate, p)
        downloads['pdf'] = f'/download/cl_{fid}.pdf'
    if 'md' in formats:
        p = os.path.join(OUTPUT_DIR, f'cl_{fid}.md')
        build_cover_letter_md(letter, candidate, p)
        downloads['md'] = f'/download/cl_{fid}.md'

    return jsonify({'success': True, 'downloads': downloads, 'letter': letter})


# ── Interview prep ─────────────────────────────────────────────────────────────

@app.route('/interview-prep', methods=['POST'])
def interview_prep():
    data = request.get_json() or {}
    candidate      = data.get('candidate', {})
    job_description = data.get('job_description', '').strip()
    template       = data.get('template', 'modern')

    if not job_description: return jsonify({'error': 'Job description required'}), 400
    try:
        questions = generate_interview_prep(candidate, job_description, template)
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        msg, status = _ai_error(e)
        return jsonify({'error': msg}), status


# ── File serving ───────────────────────────────────────────────────────────────

@app.route('/download/<filename>')
def download(filename):
    path = _safe_path(filename)
    if not os.path.isfile(path): abort(404)
    return send_file(path, as_attachment=True)


@app.route('/preview/<filename>')
def preview(filename):
    path = _safe_path(filename)
    if not os.path.isfile(path): abort(404)
    return send_file(path, mimetype='text/html')


if __name__ == '__main__':
    app.run(debug=True, port=5001)
