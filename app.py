import os
import io
import re
import uuid
import json
import time as _time
import logging
import threading
import queue
import pypdf
from docx import Document as DocxDocument
from flask import Flask, render_template, request, jsonify, send_file, abort
from dotenv import load_dotenv
from google.genai import errors as genai_errors
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from resume_generator import (generate_resume, analyze_fit, parse_resume_text,
                               generate_cover_letter, generate_interview_prep)
from job_search import (
    VALID_JOB_TYPES, VALID_JOB_COUNTRIES, JOB_DESCRIPTION_MAX_LENGTH,
    safe_screenshot_path, search_jobs as run_job_search,
    job_detail_description as run_job_detail_description,
)
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
JOB_SEARCH_TTL = 30 * 60
JOB_SEARCH_QUEUE_MAX = 20
JOB_SEARCH_WORKERS = 2
_job_search_queue = queue.Queue(maxsize=JOB_SEARCH_QUEUE_MAX)
_job_search_jobs = {}
_job_search_lock = threading.Lock()

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


def _cleanup_job_search_jobs():
    cutoff = _time.time() - JOB_SEARCH_TTL
    with _job_search_lock:
        expired = [
            job_id for job_id, job in _job_search_jobs.items()
            if job.get('updated_at', job.get('created_at', 0)) < cutoff
        ]
        for job_id in expired:
            _job_search_jobs.pop(job_id, None)


def _job_search_snapshot(job_id: str) -> dict | None:
    with _job_search_lock:
        job = _job_search_jobs.get(job_id)
        return dict(job) if job else None


def _set_job_search_state(job_id: str, **updates):
    with _job_search_lock:
        job = _job_search_jobs.get(job_id)
        if not job:
            return
        job.update(updates)
        job['updated_at'] = _time.time()


def _job_search_worker():
    while True:
        job_id = _job_search_queue.get()
        try:
            job = _job_search_snapshot(job_id)
            if not job or job.get('cancel_requested'):
                _set_job_search_state(job_id, status='cancelled', progress='Cancelled')
                continue
            params = job.get('params') or {}
            _set_job_search_state(job_id, status='running', progress='Searching job sources')
            result = run_job_search(
                params.get('title', ''),
                params.get('country', 'any'),
                params.get('location', ''),
                params.get('job_type', 'any'),
                deep_search=bool(params.get('deep_search')),
            )
            latest = _job_search_snapshot(job_id)
            if latest and latest.get('cancel_requested'):
                _set_job_search_state(job_id, status='cancelled', progress='Cancelled')
            else:
                _set_job_search_state(
                    job_id,
                    status='completed',
                    progress='Complete',
                    result=result,
                )
        except Exception as exc:
            logger.exception('Background job search failed')
            _set_job_search_state(
                job_id,
                status='failed',
                progress='Failed',
                error=str(exc)[:500] or 'Search failed.',
            )
        finally:
            _job_search_queue.task_done()


def _cleanup_worker():
    while True:
        _time.sleep(3600)
        _cleanup_output_dir()
        _cleanup_job_search_jobs()


_cleanup_output_dir()
threading.Thread(target=_cleanup_worker, daemon=True).start()
for _ in range(JOB_SEARCH_WORKERS):
    threading.Thread(target=_job_search_worker, daemon=True).start()


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


@app.route('/favicon.ico')
def favicon():
    return ('', 204)


@app.route('/job-screenshot/<filename>')
def job_screenshot(filename):
    try:
        path = safe_screenshot_path(filename)
    except ValueError:
        abort(400)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, mimetype='image/png')


# ── Job search ─────────────────────────────────────────────────────────────────

@app.route('/search-jobs')
@limiter.limit('20 per hour')
def search_jobs():
    title = str(request.args.get('title', '')).strip()[:120]
    country = _v(str(request.args.get('country', 'any')).strip(), VALID_JOB_COUNTRIES, 'any')
    location = str(request.args.get('location', '')).strip()[:120]
    job_type = _v(str(request.args.get('job_type', 'any')).strip(), VALID_JOB_TYPES, 'any')
    deep_search = str(request.args.get('deep_search', '')).lower() in ('1', 'true', 'yes', 'on')
    job_id = uuid.uuid4().hex
    payload = {
        'id': job_id,
        'status': 'queued',
        'progress': 'Queued',
        'params': {
            'title': title,
            'country': country,
            'location': location,
            'job_type': job_type,
            'deep_search': deep_search,
        },
        'created_at': _time.time(),
        'updated_at': _time.time(),
        'cancel_requested': False,
    }
    try:
        with _job_search_lock:
            _job_search_jobs[job_id] = payload
        _job_search_queue.put_nowait(job_id)
    except queue.Full:
        with _job_search_lock:
            _job_search_jobs.pop(job_id, None)
        return jsonify({'success': False, 'error': 'Job search queue is full. Try again in a minute.'}), 429
    return jsonify({'success': True, 'queued': True, 'job_id': job_id, 'status': 'queued', 'progress': 'Queued'}), 202


@app.route('/search-jobs/<job_id>')
@limiter.limit('120 per hour')
def search_jobs_status(job_id):
    if not re.fullmatch(r'[a-f0-9]{32}', job_id or ''):
        return jsonify({'success': False, 'error': 'Invalid job id'}), 400
    job = _job_search_snapshot(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Search job not found or expired'}), 404
    response = {
        'success': True,
        'job_id': job_id,
        'status': job.get('status', 'queued'),
        'progress': job.get('progress', ''),
    }
    if job.get('status') == 'completed':
        response.update(job.get('result') or {})
        response['job_id'] = job_id
        response['status'] = 'completed'
    elif job.get('status') == 'failed':
        response['success'] = False
        response['error'] = job.get('error') or 'Search failed.'
    return jsonify(response)


@app.route('/search-jobs/<job_id>/cancel', methods=['POST'])
@limiter.limit('60 per hour')
def cancel_search_jobs(job_id):
    if not re.fullmatch(r'[a-f0-9]{32}', job_id or ''):
        return jsonify({'success': False, 'error': 'Invalid job id'}), 400
    with _job_search_lock:
        job = _job_search_jobs.get(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Search job not found or expired'}), 404
        job['cancel_requested'] = True
        job['status'] = 'cancelled'
        job['progress'] = 'Cancelled'
        job['updated_at'] = _time.time()
        status = job.get('status')
    return jsonify({'success': True, 'job_id': job_id, 'status': status})


@app.route('/job-detail-description', methods=['POST'])
@limiter.limit('80 per hour')
def job_detail_description():
    payload, status = run_job_detail_description(request.get_json(silent=True) or {})
    return jsonify(payload), status


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
os.makedirs(PROFILES_DIR, exist_ok=True)

_SAFE_PROFILE_NAME = re.compile(r'^[a-zA-Z0-9_-]+\.json$')


@app.route('/save-profile', methods=['POST'])
def save_profile():
    data     = request.get_json() or {}
    name     = str(data.get('name', '')).strip()[:200]
    filename = str(data.get('filename', '')).strip()
    profile  = data.get('data', {})

    if not isinstance(profile, dict):
        return jsonify({'error': 'invalid profile data'}), 400

    # Derive a safe filename from the profile name when none is provided
    if not filename:
        safe_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', name or 'profile')[:60].strip('_') or 'profile'
        filename = f'{safe_stem}.json'

    if not _SAFE_PROFILE_NAME.match(filename):
        return jsonify({'error': 'invalid filename'}), 400

    path = os.path.realpath(os.path.join(PROFILES_DIR, filename))
    if not path.startswith(os.path.realpath(PROFILES_DIR) + os.sep):
        return jsonify({'error': 'invalid filename'}), 400
    try:
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump({'name': name, 'data': profile}, fh, ensure_ascii=False, indent=2)
    except Exception:
        logger.exception('Error writing profile file: %s', filename)
        return jsonify({'error': 'could not save profile'}), 500

    return jsonify({'ok': True, 'filename': filename})


@app.route('/auto-load-profile')
def auto_load_profile():
    try:
        files = sorted(
            (f for f in os.listdir(PROFILES_DIR) if f.endswith('.json')),
            key=lambda f: os.path.getmtime(os.path.join(PROFILES_DIR, f)),
            reverse=True,  # most recently modified first
        )
        if not files:
            return jsonify({'found': False, 'profiles': []})
        profiles = []
        for fname in files:
            path = os.path.join(PROFILES_DIR, fname)
            try:
                with open(path, encoding='utf-8') as fh:
                    raw = json.load(fh)
                profile_data = raw.get('data', raw)
                # Use name from profile data, fall back to filename
                name = (profile_data.get('name') or
                        fname.removesuffix('.json').replace('_', ' ').replace('-', ' ').title())
                profiles.append({'filename': fname, 'name': name, 'profile': profile_data})
            except Exception:
                logger.warning('Could not parse profile file: %s', fname)
        return jsonify({'found': bool(profiles), 'profiles': profiles})
    except Exception:
        logger.exception('Error in auto_load_profile')
        return jsonify({'found': False, 'profiles': []})


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
