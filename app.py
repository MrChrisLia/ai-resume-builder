import os
import io
import re
import uuid
import json
import time as _time
import logging
import threading
import pypdf
from docx import Document as DocxDocument
from flask import Flask, render_template, request, jsonify, send_file, abort
from dotenv import load_dotenv
from google.genai import errors as genai_errors
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from resume_generator import (generate_resume, analyze_fit, parse_resume_text,
                               generate_cover_letter, generate_interview_prep)
from document_builder import (build_docx, build_pdf, build_markdown, build_preview_html,
                               build_cover_letter_docx, build_cover_letter_pdf,
                               build_cover_letter_md)

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
_secret = os.environ.get('FLASK_SECRET_KEY')
if not _secret:
    _secret = os.urandom(32)
    # Note: sessions won't persist across restarts without FLASK_SECRET_KEY set
app.secret_key = _secret
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB upload limit

limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri='memory://',
    default_limits=['300 per day', '60 per hour'],
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

VALID_TEMPLATES = frozenset({'modern', 'classic', 'minimal', 'japanese', 'taiwanese'})
VALID_LANGUAGES  = frozenset({'english', 'japanese', 'taiwanese'})

_SAFE_NAME = re.compile(r'^(cl_)?[a-f0-9]+\.(docx|pdf|md|html)$')


def _v(val, allowed, default):
    """Return val if it's in the allowed set, else default."""
    return val if val in allowed else default


def _cleanup_output_dir():
    cutoff = _time.time() - 3600  # 1-hour TTL
    for fname in os.listdir(OUTPUT_DIR):
        fpath = os.path.join(OUTPUT_DIR, fname)
        try:
            if os.path.isfile(fpath) and os.path.getmtime(fpath) < cutoff:
                os.unlink(fpath)
        except Exception:
            pass


def _cleanup_worker():
    while True:
        _time.sleep(3600)
        _cleanup_output_dir()


_cleanup_output_dir()
threading.Thread(target=_cleanup_worker, daemon=True).start()


@app.after_request
def _security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "script-src 'self' 'unsafe-inline'; "
        "frame-src 'self';"
    )
    return response


def _safe_path(filename):
    if not _SAFE_NAME.match(filename):
        abort(400)
    return os.path.join(OUTPUT_DIR, filename)


def _file_id():
    return uuid.uuid4().hex[:10]


def _ai_error(e: Exception) -> tuple[str, int, int | None]:
    """Translate a Gemini API exception into a (message, http_status, retry_after_seconds) tuple."""
    if isinstance(e, genai_errors.ClientError):
        code = e.status_code if hasattr(e, 'status_code') else 0
        msg  = str(e)
        if code == 429 or 'RESOURCE_EXHAUSTED' in msg:
            import re as _re
            delay = _re.search(r'retry[^\d]*(\d+)', msg, _re.I)
            secs  = int(delay.group(1)) if delay else None
            wait  = f' Please wait {secs} seconds and try again.' if secs else ' Please wait a moment and try again.'
            return (f'Gemini quota limit reached — you exceeded the free-tier rate limit.{wait}', 429, secs)
        if code == 400 or 'INVALID_ARGUMENT' in msg:
            return ('Gemini rejected the request (invalid input). Try shortening the job description.', 400, None)
        if code == 401 or 'UNAUTHENTICATED' in msg:
            return ('Gemini API key is invalid or missing. Check your .env file.', 401, None)
        if code == 403 or 'PERMISSION_DENIED' in msg:
            return ('Gemini API key does not have permission to use this model.', 403, None)
        if code == 404 or 'NOT_FOUND' in msg:
            return (f'Gemini model not found. Check the model name in resume_generator.py.', 404, None)
        if code == 503 or 'UNAVAILABLE' in msg:
            return ('Gemini API is temporarily unavailable. Please try again in a few seconds.', 503, None)
        return (f'Gemini API error ({code}): {msg[:200]}', 500, None)
    logger.exception('Unexpected non-Gemini error in AI call')
    return ('An unexpected error occurred. Please try again.', 500, None)


# ── Pages ──────────────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ── Import ─────────────────────────────────────────────────────────────────────

@app.route('/import-profile', methods=['POST'])
@limiter.limit('30 per minute')
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
    except Exception:
        logger.exception('Unexpected error in import_profile')
        return jsonify({'error': 'An unexpected error occurred. Please try again.'}), 500


# ── Auto-load profile from profiles/ directory ─────────────────────────────────

PROFILES_DIR = os.path.join(os.path.dirname(__file__), 'profiles')

@app.route('/auto-load-profile')
def auto_load_profile():
    try:
        files = sorted(
            (f for f in os.listdir(PROFILES_DIR) if f.endswith('.json')),
            key=lambda f: os.path.getmtime(os.path.join(PROFILES_DIR, f)),
            reverse=True,  # most recently modified first
        )
        if not files:
            return jsonify({'found': False})
        path = os.path.join(PROFILES_DIR, files[0])
        with open(path, encoding='utf-8') as fh:
            profile = json.load(fh)
        profile_data = profile.get('data', profile)  # handle both export formats
        return jsonify({'found': True, 'profile': profile_data, 'filename': files[0]})
    except Exception:
        logger.exception('Error in auto_load_profile')
        return jsonify({'found': False})


# ── Fit analysis ───────────────────────────────────────────────────────────────

@app.route('/analyze-fit', methods=['POST'])
@limiter.limit('15 per minute')
def fit():
    data = request.get_json() or {}
    candidate          = data.get('candidate', {})
    job_description    = data.get('job_description', '')[:8000].strip()
    additional_notes   = data.get('additional_notes', '')[:2000].strip()
    language           = _v(data.get('language', 'english').strip(), VALID_LANGUAGES, 'english')
    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400
    try:
        return jsonify({'success': True, 'fit': analyze_fit(candidate, job_description, additional_notes, language)})
    except Exception as e:
        msg, status, retry = _ai_error(e)
        resp = {'error': msg}
        if retry: resp['retry_after'] = retry
        return jsonify(resp), status


# ── Resume generation ──────────────────────────────────────────────────────────

@app.route('/generate', methods=['POST'])
@limiter.limit('10 per minute')
def generate():
    data = request.get_json() or {}
    candidate        = data.get('candidate', {})
    job_description  = data.get('job_description', '')[:8000].strip()
    formats          = [f for f in data.get('formats', ['docx', 'pdf']) if f in ('docx', 'pdf', 'md')]
    template         = _v(data.get('template', 'modern'), VALID_TEMPLATES, 'modern')
    language         = _v(data.get('language', 'english').strip(), VALID_LANGUAGES, 'english')
    additional_notes = data.get('additional_notes', '')[:2000].strip()

    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400

    try:
        resume_data = generate_resume(candidate, job_description, template, language, additional_notes)
    except Exception as e:
        msg, status, retry = _ai_error(e)
        resp = {'error': msg}
        if retry: resp['retry_after'] = retry
        return jsonify(resp), status

    if not isinstance(resume_data, dict):
        return jsonify({'error': 'AI returned an unexpected response. Please try again.'}), 500

    # Re-attach photo for document builders (stripped before Gemini call to save tokens)
    if candidate.get('photo'):
        resume_data['photo'] = candidate['photo']

    fid = _file_id()
    downloads = {}

    try:
        if 'docx' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.docx')
            build_docx(resume_data, p, template, language)
            downloads['docx'] = f'/download/{fid}.docx'

        if 'pdf' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.pdf')
            build_pdf(resume_data, p, template, language)
            downloads['pdf'] = f'/download/{fid}.pdf'

        if 'md' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.md')
            build_markdown(resume_data, p)
            downloads['md'] = f'/download/{fid}.md'

        html_path = os.path.join(OUTPUT_DIR, f'{fid}.html')
        build_preview_html(resume_data, html_path, template, language)
        downloads['preview'] = f'/preview/{fid}.html'
    except Exception:
        logger.exception('Error building resume documents')
        return jsonify({'error': 'Failed to build documents. Please try again.'}), 500

    # Strip photo before sending to client — documents already built, no need to store base64 in localStorage
    resume_for_client = {k: v for k, v in resume_data.items() if k != 'photo'}

    return jsonify({'success': True, 'downloads': downloads,
                    'resume': resume_for_client, 'file_id': fid})


# ── Regenerate files from stored resume JSON ───────────────────────────────────

@app.route('/regenerate', methods=['POST'])
@limiter.limit('15 per minute')
def regenerate():
    data        = request.get_json() or {}
    resume_data = data.get('resume_data', {})
    formats     = [f for f in data.get('formats', ['docx', 'pdf']) if f in ('docx', 'pdf', 'md')]
    template    = _v(data.get('template', 'modern'), VALID_TEMPLATES, 'modern')
    language    = _v(data.get('language', 'english').strip(), VALID_LANGUAGES, 'english')
    if not isinstance(resume_data, dict) or not resume_data:
        return jsonify({'error': 'No resume data provided'}), 400

    fid = _file_id()
    downloads = {}
    try:
        if 'docx' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.docx')
            build_docx(resume_data, p, template, language)
            downloads['docx'] = f'/download/{fid}.docx'
        if 'pdf' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.pdf')
            build_pdf(resume_data, p, template, language)
            downloads['pdf'] = f'/download/{fid}.pdf'
        if 'md' in formats:
            p = os.path.join(OUTPUT_DIR, f'{fid}.md')
            build_markdown(resume_data, p)
            downloads['md'] = f'/download/{fid}.md'
        html_path = os.path.join(OUTPUT_DIR, f'{fid}.html')
        build_preview_html(resume_data, html_path, template, language)
        downloads['preview'] = f'/preview/{fid}.html'
    except Exception:
        logger.exception('Error building documents in regenerate')
        return jsonify({'error': 'Failed to build documents. Please try again.'}), 500
    return jsonify({'success': True, 'downloads': downloads})


# ── Cover letter ───────────────────────────────────────────────────────────────

@app.route('/generate-cover-letter', methods=['POST'])
@limiter.limit('10 per minute')
def cover_letter():
    data = request.get_json() or {}
    candidate        = data.get('candidate', {})
    job_description  = data.get('job_description', '')[:8000].strip()
    resume_data      = data.get('resume_data', {})
    formats          = [f for f in data.get('formats', ['docx', 'pdf']) if f in ('docx', 'pdf', 'md')]
    template         = _v(data.get('template', 'modern'), VALID_TEMPLATES, 'modern')
    additional_notes = data.get('additional_notes', '')[:2000].strip()
    language         = _v(data.get('language', 'english').strip(), VALID_LANGUAGES, 'english')

    if not job_description:        return jsonify({'error': 'Job description required'}), 400
    if not candidate.get('name'): return jsonify({'error': 'Name required'}), 400

    try:
        letter = generate_cover_letter(candidate, job_description, resume_data, template, language, additional_notes)
    except Exception as e:
        msg, status, retry = _ai_error(e)
        resp = {'error': msg}
        if retry: resp['retry_after'] = retry
        return jsonify(resp), status

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
@limiter.limit('10 per minute')
def interview_prep():
    data = request.get_json() or {}
    candidate        = data.get('candidate', {})
    job_description  = data.get('job_description', '')[:8000].strip()
    template         = _v(data.get('template', 'modern'), VALID_TEMPLATES, 'modern')
    additional_notes = data.get('additional_notes', '')[:2000].strip()
    language         = _v(data.get('language', 'english').strip(), VALID_LANGUAGES, 'english')

    if not job_description: return jsonify({'error': 'Job description required'}), 400
    try:
        questions = generate_interview_prep(candidate, job_description, template, language, additional_notes)
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        msg, status, retry = _ai_error(e)
        resp = {'error': msg}
        if retry: resp['retry_after'] = retry
        return jsonify(resp), status


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
    app.run(debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true', port=5001)
