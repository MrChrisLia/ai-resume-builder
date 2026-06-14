from .core import *

def _first_present(data: dict, *keys, default='') -> str:
    for key in keys:
        val = data.get(key)
        if val not in (None, ''):
            return str(val).strip()
    return default


def _clean_104_text(value) -> str:
    if isinstance(value, list):
        value = ' '.join(str(v) for v in value)
    return _strip_html(str(value or '')).strip()


def _clean_104_description(value) -> str:
    if isinstance(value, list):
        value = '\n'.join(str(v) for v in value)
    return _strip_html_preserve_lines(str(value or '')).strip()


def _normalize_104_job(job: dict) -> dict:
    job_id = _first_present(job, 'jobNo', 'jobno', 'jobId', 'job_id', 'linkJob')
    link = _first_present(job, 'link', 'jobLink', 'url')
    if link.startswith('//'):
        link = f'https:{link}'
    elif link.startswith('/'):
        link = f'https://www.104.com.tw{link}'
    elif not link and job_id:
        link = f'https://www.104.com.tw/job/{job_id}'

    location = _first_present(job, 'jobAddrNoDesc', 'jobAddress', 'address', 'location')
    if job.get('jobAddress') and job.get('jobAddrNoDesc') and job['jobAddress'] not in location:
        location = f"{location} {job['jobAddress']}".strip()

    description = _clean_104_description(_first_present(job, 'description', 'jobDescription', 'desc'))
    salary = _first_present(job, 'salaryDesc', 'salary', 'salaryLow', 'salaryHigh')
    category = _first_present(job, 'jobCatDesc', 'coIndustryDesc', 'industryDesc')
    posted_at = _first_present(job, 'appearDate', 'appear_date', 'date')

    return {
        'id': f'104-{job_id or uuid.uuid4().hex[:10]}',
        'title': _clean_104_text(_first_present(job, 'jobName', 'job_name', 'title')),
        'company': _clean_104_text(_first_present(job, 'custName', 'company', 'companyName')),
        'location': _clean_104_text(location or 'Taiwan'),
        'job_type': '',
        'category': _clean_104_text(category),
        'salary': _clean_104_text(salary),
        'posted_at': posted_at,
        'description': description[:5000],
        'url': link,
        'source': '104',
    }


def _fetch_104_detail(job: dict) -> dict:
    raw_id = job.get('id', '').removeprefix('104-')
    if not raw_id or raw_id.startswith('sample'):
        return job

    cache_key = f'104-detail:{raw_id}'
    now = _time.time()
    with _job_search_lock:
        cached = _job_search_cache.get(cache_key)
        if cached and now - cached['time'] < JOB_SEARCH_CACHE_TTL:
            return {**job, **cached['job']}

    url = TAIWAN_104_DETAIL_URL.format(job_id=urllib.parse.quote(raw_id))
    try:
        req = urllib.request.Request(url, headers=_headers_104(job.get('url') or 'https://www.104.com.tw/jobs/search/'))
        with urllib.request.urlopen(req, timeout=6) as resp:
            content_type = resp.headers.get('content-type', '')
            raw = resp.read().decode('utf-8', errors='ignore')
        if 'json' not in content_type.lower() and raw.lstrip().startswith('<'):
            return job
        payload = json.loads(raw)
        data = payload.get('data') or {}
        detail = data.get('jobDetail') or data.get('condition') or data
        header = data.get('header') or {}
        merged = {
            'title': _clean_104_text(_first_present(header, 'jobName', default=job.get('title', ''))),
            'company': _clean_104_text(_first_present(header, 'custName', default=job.get('company', ''))),
            'description': _clean_104_description(_first_present(detail, 'jobDescription', 'description', default=job.get('description', '')))[:8000],
            'salary': _clean_104_text(_first_present(detail, 'salary', 'salaryDesc', default=job.get('salary', ''))),
            'location': _clean_104_text(_first_present(detail, 'addressRegion', 'addressDetail', default=job.get('location', 'Taiwan'))),
        }
        merged = {k: v for k, v in merged.items() if v}
        with _job_search_lock:
            _job_search_cache[cache_key] = {'time': now, 'job': merged}
        return {**job, **merged}
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return job


def _headers_104(referer='https://www.104.com.tw/jobs/search/') -> dict:
    return {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36'
        ),
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': referer,
        'Connection': 'close',
    }


def _fetch_104_jobs(search: str, limit: int = 24) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    cache_key = f"104-search:{keyword.lower() or '_latest'}"
    now = _time.time()
    with _job_search_lock:
        cached = _job_search_cache.get(cache_key)
        if cached and now - cached['time'] < JOB_SEARCH_CACHE_TTL:
            return cached['jobs'], True, cached.get('error')

    params = {
        'ro': '0',
        'kwop': '7',
        'keyword': keyword,
        'expansionType': 'area,spec,com,job,wf,wktm',
        'order': '15',
        'asc': '0',
        'page': '1',
        'mode': 's',
        'jobsource': 'job_search',
    }
    url = f'{TAIWAN_104_SEARCH_URL}?{urllib.parse.urlencode(params)}'

    jobs = []
    error = None
    try:
        req = urllib.request.Request(url, headers=_headers_104('https://www.104.com.tw/jobs/search/'))
        with urllib.request.urlopen(req, timeout=8) as resp:
            content_type = resp.headers.get('content-type', '')
            raw = resp.read().decode('utf-8', errors='ignore')
        if 'json' not in content_type.lower() and raw.lstrip().startswith('<'):
            raise ValueError('104 returned an HTML challenge instead of JSON')
        payload = json.loads(raw)
        records = (payload.get('data') or {}).get('list') or payload.get('list') or []
        for record in records[:limit]:
            normalized = _normalize_104_job(record)
            if normalized.get('title') and normalized.get('company'):
                jobs.append(_fetch_104_detail(normalized))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError, ValueError) as exc:
        logger.warning('104 job search unavailable; falling back to other sources: %s', exc)
        error = str(exc)

    with _job_search_lock:
        _job_search_cache[cache_key] = {'time': now, 'jobs': jobs, 'error': error}
    return jobs, False, error


def _fetch_104_browser_jobs(search: str, location: str = '', limit: int = 72, pages: int = 3, detail_limit: int = 18) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"104-browser:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}:{detail_limit}"
    now = _time.time()
    with _job_search_lock:
        cached = _job_search_cache.get(cache_key)
        if cached and now - cached['time'] < JOB_SEARCH_CACHE_TTL:
            return cached['jobs'], True, cached.get('error')

    if not os.path.isfile(TAIWAN_104_BROWSER_SCRIPT):
        return [], False, '104 browser scraper script not found'

    cmd = [
        'node',
        TAIWAN_104_BROWSER_SCRIPT,
        '--keyword', keyword,
        '--location', city,
        '--limit', str(limit),
        '--pages', str(pages),
        '--detailLimit', str(detail_limit),
        '--fast',
        '--screenshotDir', OUTPUT_DIR,
    ]
    jobs = []
    error = None
    try:
        proc = subprocess.run(
            cmd,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=240,
            check=False,
        )
        if proc.returncode != 0 and not proc.stdout.strip():
            raise RuntimeError((proc.stderr or '104 browser scraper failed').strip()[:300])
        payload = json.loads(proc.stdout.strip() or '{}')
        if not payload.get('ok'):
            raise RuntimeError(payload.get('error') or '104 browser scraper failed')
        if payload.get('blocked'):
            raise RuntimeError(payload.get('reason') or '104 displayed a browser challenge')

        screenshot = payload.get('screenshot') or ''
        screenshot_url = f'/job-screenshot/{screenshot}' if _SAFE_SCREENSHOT_NAME.match(screenshot) else ''
        for raw_job in payload.get('jobs') or []:
            normalized = {
                'id': f"104-{raw_job.get('id') or uuid.uuid4().hex[:10]}",
                'title': _clean_104_text(raw_job.get('title')),
                'company': _clean_104_text(raw_job.get('company')),
                'location': _clean_104_text(raw_job.get('location') or 'Taiwan'),
                'job_type': _pretty_job_type(raw_job.get('job_type')),
                'category': _clean_104_text(raw_job.get('category')),
                'salary': _clean_104_text(raw_job.get('salary')),
                'posted_at': _clean_104_text(raw_job.get('posted_at')),
                'description': _clean_104_description(raw_job.get('description'))[:8000],
                'url': str(raw_job.get('url') or '').strip(),
                'source': '104',
                'source_method': _clean_104_text(raw_job.get('method')),
                'screenshot_url': screenshot_url,
                'result_page': raw_job.get('result_page'),
                'search_terms': keyword,
                'search_location': city,
            }
            if normalized['title'] and normalized['url']:
                if not normalized['description']:
                    normalized['description'] = normalized['title']
                jobs.append(normalized)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, RuntimeError) as exc:
        logger.warning('104 browser POC unavailable; falling back to other sources: %s', exc)
        error = str(exc)

    with _job_search_lock:
        _job_search_cache[cache_key] = {'time': now, 'jobs': jobs, 'error': error}
    return jobs, False, error


