import ssl

from .core import *
from .providers_generic import _extract_generic_board_jobs, _fetch_generic_board

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


def _fetch_taiwan_generic_with_ssl_fallback(
    source: str,
    base_url: str,
    params: dict,
    search: str,
    location: str = '',
    limit: int = 30,
) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip() or 'Taiwan'
    cache_key = f"taiwan-generic:{source.lower()}:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    url = base_url if not params else f'{base_url}?{urllib.parse.urlencode(params)}'
    jobs = []
    error = None
    try:
        req = urllib.request.Request(url, headers=_job_source_headers(source))
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw = resp.read().decode('utf-8', errors='ignore')
        except urllib.error.URLError as exc:
            if not isinstance(exc.reason, ssl.SSLError):
                raise
            context = ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=8, context=context) as resp:
                raw = resp.read().decode('utf-8', errors='ignore')
        jobs = _extract_generic_board_jobs(raw, source, base_url, keyword, city, 'Taiwan', limit)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('%s search unavailable: %s', source, exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_1111_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_taiwan_generic_with_ssl_fallback('1111', TAIWAN_1111_SEARCH_URL, {'ks': keyword}, keyword, location, limit)


def _fetch_cake_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Cake', TAIWAN_CAKE_SEARCH_URL, {'query': keyword}, keyword, location or 'Taiwan', 'Taiwan', limit)


def _fetch_yourator_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Yourator', TAIWAN_YOURATOR_SEARCH_URL, {'term': keyword}, keyword, location or 'Taiwan', 'Taiwan', limit)


def _fetch_yes123_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_taiwan_generic_with_ssl_fallback('yes123', TAIWAN_YES123_SEARCH_URL, {'find_key1': keyword}, keyword, location, limit)


def _fetch_518_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_taiwan_generic_with_ssl_fallback('518', TAIWAN_518_SEARCH_URL, {'kw': keyword}, keyword, location, limit)


def _fetch_meet_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Meet.jobs', TAIWAN_MEET_JOBS_SEARCH_URL, {'keywords': keyword}, keyword, location or 'Taiwan', 'Taiwan', limit)


def _tw_field(record: dict, prefix: str) -> str:
    for key, value in record.items():
        if str(key).startswith(prefix):
            return _clean_104_text(value)
    return ''


def _fetch_taiwanjobs_open_data(search: str, location: str = '', limit: int = 80) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"taiwanjobs-open-data:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        raw = _fetch_text_url(TAIWAN_JOBS_OPEN_DATA_URL, timeout=12, headers={'User-Agent': 'Job Search and Resume Creator local dev', 'Accept': 'application/json'})
        payload = json.loads(raw)
        records = ((payload.get('result') or {}).get('records') if isinstance(payload, dict) else payload) or []
        keyword_tokens = [token for token in re.split(r'[^a-z0-9+#.]+', keyword.lower()) if token]
        keyword_tokens.extend(re.findall(r'[\u3400-\u9fff]+', keyword))
        for record in records:
            if not isinstance(record, dict):
                continue
            title = _tw_field(record, 'OCCU_DESC') or _tw_field(record, 'CJOB_NAME2') or _tw_field(record, 'CJOB_NAME1')
            company = _tw_field(record, 'COMPNAME') or 'TaiwanJobs employer'
            job_location = _tw_field(record, 'CITYNAME') or 'Taiwan'
            description = _tw_field(record, 'JOB_DETAIL')
            category = _tw_field(record, 'CJOB_NAME2') or _tw_field(record, 'CJOB_NAME1')
            haystack = ' '.join((title, company, job_location, description, category)).lower()
            if keyword_tokens and not all(token.lower() in haystack for token in keyword_tokens):
                continue
            salary_low = _tw_field(record, 'NT_L')
            salary_high = _tw_field(record, 'NT_U')
            salary_type = _tw_field(record, 'SALARYCD')
            salary = ''
            if salary_low or salary_high:
                salary = f"{salary_type} {salary_low or ''} - {salary_high or ''}".strip().replace(' - ', ' - ')
            url = _tw_field(record, 'URL_QUERY')
            job_id = urllib.parse.parse_qs(urllib.parse.urlparse(url).query).get('HIRE_ID', [''])[0] or uuid.uuid5(uuid.NAMESPACE_URL, f'{company}:{title}:{url}').hex[:10]
            normalized = {
                'id': f'taiwanjobs-{job_id}',
                'title': title,
                'company': company,
                'location': job_location,
                'job_type': _map_job_type(_tw_field(record, 'WK_TYPE')),
                'category': category,
                'salary': salary,
                'posted_at': _tw_field(record, 'TRANDATE'),
                'description': _clean_104_description('\n'.join(part for part in (
                    description,
                    f"Experience: {_tw_field(record, 'EXPERIENCE')}" if _tw_field(record, 'EXPERIENCE') else '',
                    f"Work time: {_tw_field(record, 'WKTIME')}" if _tw_field(record, 'WKTIME') else '',
                    f"Education: {_tw_field(record, 'EDGRDESC')}" if _tw_field(record, 'EDGRDESC') else '',
                ) if part))[:8000],
                'url': url,
                'source': 'TaiwanJobs',
                'source_method': 'government-open-data',
                'search_terms': keyword,
                'search_location': city or 'Taiwan',
                'strict_title_match': False,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('TaiwanJobs open data unavailable: %s', exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_taiwan_jobs(search: str, location: str = '', deep_search: bool = False) -> tuple[list[dict], bool, dict[str, str]]:
    fetchers = {
        'taiwanjobs': lambda: _fetch_taiwanjobs_open_data(search, location),
        'cake': lambda: _fetch_cake_jobs(search, location),
        'yes123': lambda: _fetch_yes123_jobs(search, location),
        'meet-jobs': lambda: _fetch_meet_jobs(search, location),
    }
    if deep_search:
        fetchers.update({
            '1111': lambda: _fetch_1111_jobs(search, location),
            'yourator': lambda: _fetch_yourator_jobs(search, location),
            '518': lambda: _fetch_518_jobs(search, location),
        })
    jobs = []
    cached = False
    source_errors = {}
    active_fetchers = {name: fetcher for name, fetcher in fetchers.items() if not _source_disabled(f'taiwan:{name}')}
    if not active_fetchers:
        return jobs, cached, source_errors
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_fetchers)) as executor:
        futures = {executor.submit(fetcher): name for name, fetcher in active_fetchers.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                source_jobs, source_cached, error = future.result()
                jobs.extend(source_jobs)
                cached = cached or source_cached
                if error:
                    source_errors[name] = error
                    _record_source_failure(f'taiwan:{name}', error)
                else:
                    _record_source_success(f'taiwan:{name}')
            except Exception as exc:
                logger.warning('%s Taiwan provider failed unexpectedly: %s', name, exc)
                source_errors[name] = str(exc)
                _record_source_failure(f'taiwan:{name}', exc)
    return jobs, cached, source_errors
