from .core import *
from .providers_generic import _fetch_generic_board

def _normalize_remotive_job(job: dict) -> dict:
    description = _strip_html(job.get('description', ''))
    posted_at = str(job.get('publication_date', '')).split('T')[0]
    job_id = str(job.get('id') or uuid.uuid4().hex[:10])
    return {
        'id': f'remotive-{job_id}',
        'title': str(job.get('title') or '').strip(),
        'company': str(job.get('company_name') or '').strip(),
        'location': str(job.get('candidate_required_location') or 'Remote').strip(),
        'job_type': _pretty_job_type(job.get('job_type')),
        'category': str(job.get('category') or '').strip(),
        'salary': str(job.get('salary') or '').strip(),
        'posted_at': posted_at,
        'description': description[:5000],
        'url': str(job.get('url') or '').strip(),
        'source': 'Remotive',
    }


def _fetch_remotive_jobs(search: str) -> tuple[list[dict], bool]:
    cache_key = re.sub(r'\s+', ' ', search or '').strip().lower() or '_latest'
    now = _time.time()
    with _job_search_lock:
        cached = _job_search_cache.get(cache_key)
        if cached and now - cached['time'] < JOB_SEARCH_CACHE_TTL:
            return cached['jobs'], True

    params = {'limit': '80'}
    if search:
        params['search'] = search
    url = f'{REMOTIVE_API_URL}?{urllib.parse.urlencode(params)}'

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'AIResumeBuilder/1.0 local job search',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode('utf-8'))
        jobs = [_normalize_remotive_job(job) for job in payload.get('jobs', [])]
        jobs = [job for job in jobs if job.get('title') and job.get('company') and job.get('url')]
        with _job_search_lock:
            _job_search_cache[cache_key] = {'time': now, 'jobs': jobs}
        return jobs, False
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        logger.warning('Remotive job search failed; using fallback jobs', exc_info=True)
        return _fallback_jobs(search), False


def _normalize_remoteok_job(job: dict) -> dict:
    job_id = str(job.get('id') or job.get('slug') or uuid.uuid4().hex[:10])
    salary_min = job.get('salary_min')
    salary_max = job.get('salary_max')
    salary = ''
    if salary_min or salary_max:
        salary = f"${salary_min or ''} - ${salary_max or ''}".replace('$ - ', '').strip()
    tags = [str(tag) for tag in (job.get('tags') or []) if tag]
    return {
        'id': f'remoteok-{job_id}',
        'title': _clean_job_text(job.get('position')),
        'company': _clean_job_text(job.get('company')),
        'location': _clean_job_text(job.get('location') or 'Remote, Worldwide'),
        'job_type': '',
        'category': ', '.join(tags[:4]),
        'salary': salary,
        'posted_at': _iso_to_date(job.get('date')),
        'description': _clean_job_description(job.get('description'))[:JOB_DESCRIPTION_MAX_LENGTH],
        'url': str(job.get('url') or job.get('apply_url') or '').strip(),
        'source': 'RemoteOK',
        'source_method': 'public-api',
        'search_terms': ', '.join(tags),
        'strict_title_match': True,
    }


def _fetch_remoteok_jobs(search: str, limit: int = 40) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    cache_key = f"remoteok:{keyword.lower() or '_latest'}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    jobs = []
    error = None
    try:
        raw = _fetch_text_url(REMOTEOK_API_URL, timeout=12, headers={
            'User-Agent': 'Job Search and Resume Creator local dev',
            'Accept': 'application/json',
        })
        payload = json.loads(raw)
        for record in payload:
            if not isinstance(record, dict) or 'legal' in record:
                continue
            normalized = _normalize_remoteok_job(record)
            if normalized['title'] and normalized['company'] and normalized['url']:
                jobs.append(normalized)
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning('RemoteOK job search unavailable: %s', exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _normalize_jobicy_job(job: dict) -> dict:
    job_id = str(job.get('id') or job.get('jobSlug') or uuid.uuid4().hex[:10])
    job_types = job.get('jobType') or []
    industries = job.get('jobIndustry') or []
    salary_min = job.get('salaryMin')
    salary_max = job.get('salaryMax')
    currency = job.get('salaryCurrency') or ''
    period = job.get('salaryPeriod') or ''
    salary = ''
    if salary_min or salary_max:
        salary = f"{currency} {salary_min or ''} - {salary_max or ''} {period}".strip()
    return {
        'id': f'jobicy-{job_id}',
        'title': _clean_job_text(job.get('jobTitle')),
        'company': _clean_job_text(job.get('companyName')),
        'location': _clean_job_text(job.get('jobGeo') or 'Remote, USA'),
        'job_type': _map_job_type(' '.join(str(item) for item in job_types)),
        'category': _clean_job_text(', '.join(str(item) for item in industries)),
        'salary': salary,
        'posted_at': _iso_to_date(job.get('pubDate')),
        'description': _clean_job_description(job.get('jobDescription') or job.get('jobExcerpt'))[:JOB_DESCRIPTION_MAX_LENGTH],
        'url': str(job.get('url') or '').strip(),
        'source': 'Jobicy',
        'source_method': 'public-api',
        'search_terms': ' '.join(str(item) for item in industries + job_types if item),
        'search_location': 'United States',
        'strict_title_match': True,
    }


def _fetch_jobicy_jobs(search: str, limit: int = 40) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    cache_key = f"jobicy:{keyword.lower() or '_latest'}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    params = {'count': str(limit), 'geo': 'usa'}
    url = f'{JOBICY_API_URL}?{urllib.parse.urlencode(params)}'
    jobs = []
    error = None
    try:
        raw = _fetch_text_url(url, timeout=12, headers={
            'User-Agent': 'Job Search and Resume Creator local dev',
            'Accept': 'application/json',
        })
        payload = json.loads(raw)
        for record in payload.get('jobs') or []:
            normalized = _normalize_jobicy_job(record)
            if normalized['title'] and normalized['company'] and normalized['url']:
                jobs.append(normalized)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning('Jobicy job search unavailable: %s', exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _normalize_arbeitnow_job(job: dict) -> dict:
    tags = [str(tag) for tag in (job.get('tags') or []) if tag]
    job_types = [str(item) for item in (job.get('job_types') or []) if item]
    location = _clean_job_text(job.get('location') or '')
    if job.get('remote') and not location:
        location = 'Remote, Worldwide'
    return {
        'id': f"arbeitnow-{job.get('slug') or uuid.uuid4().hex[:10]}",
        'title': _clean_job_text(job.get('title')),
        'company': _clean_job_text(job.get('company_name')),
        'location': location or 'Remote',
        'job_type': _map_job_type(' '.join(job_types)),
        'category': ', '.join(tags[:4]),
        'salary': '',
        'posted_at': _epoch_to_date(job.get('created_at')),
        'description': _clean_job_description(job.get('description'))[:JOB_DESCRIPTION_MAX_LENGTH],
        'url': str(job.get('url') or '').strip(),
        'source': 'Arbeitnow',
        'source_method': 'public-api',
        'search_terms': ' '.join(tags + job_types),
        'strict_title_match': True,
    }


def _fetch_arbeitnow_jobs(search: str, limit: int = 40) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    cache_key = f"arbeitnow:{keyword.lower() or '_latest'}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    jobs = []
    error = None
    try:
        raw = _fetch_text_url(ARBEITNOW_API_URL, timeout=12, headers={
            'User-Agent': 'Job Search and Resume Creator local dev',
            'Accept': 'application/json',
        })
        payload = json.loads(raw)
        for record in payload.get('data') or []:
            normalized = _normalize_arbeitnow_job(record)
            if normalized['title'] and normalized['company'] and normalized['url']:
                jobs.append(normalized)
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        logger.warning('Arbeitnow job search unavailable: %s', exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_dice_card(card: str, keyword: str, search_location: str) -> dict | None:
    guid = _regex_first(r'data-job-guid="([^"]+)"', card)
    link = _regex_first(r'data-testid="job-search-job-detail-link"[^>]+href="([^"]+)"', card)
    title = _regex_first(r'data-testid="job-search-job-detail-link"[^>]*>\s*(.*?)\s*</a>', card)
    company = _regex_first(r'company-profile/[^"]+?companyname=[^"]+"[^>]*>.*?<p[^>]*>\s*(.*?)\s*</p>\s*</a>', card)
    description = _regex_first(r'<p class="[^"]*line-clamp-2[^"]*"[^>]*>\s*(.*?)\s*</p>', card)
    pills = [
        _clean_job_text(item)
        for item in re.findall(r'<p[^>]+class="[^"]*text-sm font-normal text-zinc-600[^"]*"[^>]*>\s*(.*?)\s*</p>', card, re.I | re.S)
    ]
    pills = [pill for pill in pills if pill and pill != '•']
    job_location = pills[0] if pills else search_location
    posted_at = pills[1] if len(pills) > 1 else ''
    job_type_text = _regex_first(r'employmentType-label"[^>]*class="[^"]*"[^>]*>\s*(.*?)\s*</p>', card)
    if not title or not link:
        return None
    return {
        'id': f'dice-{guid or link.rstrip("/").split("/")[-1]}',
        'title': title,
        'company': company or 'Dice employer',
        'location': job_location or search_location,
        'job_type': _map_job_type(job_type_text),
        'category': job_type_text,
        'salary': '',
        'posted_at': posted_at,
        'description': _clean_job_description(description),
        'url': link,
        'source': 'Dice',
        'source_method': 'public-html',
        'search_terms': keyword,
        'search_location': search_location or 'United States',
    }


def _fetch_dice_jobs(search: str, location: str = '', limit: int = 40, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    search_location = re.sub(r'\s+', ' ', location or '').strip() or 'United States'
    cache_key = f"dice:{keyword.lower() or '_latest'}:{search_location.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    jobs = []
    error = None
    try:
        for page in range(1, pages + 1):
            params = {'q': keyword, 'location': search_location, 'page': str(page)}
            url = f'{DICE_SEARCH_URL}?{urllib.parse.urlencode(params)}'
            raw = _fetch_text_url(url, timeout=12, headers=_job_source_headers('Dice'))
            cards = re.split(r'(?=<div[^>]+data-id="[^"]+"[^>]+data-job-guid="[^"]+"[^>]+data-testid="job-card")', raw)
            parsed = 0
            for card in cards:
                if 'data-testid="job-card"' not in card:
                    continue
                job = _extract_dice_card(card, keyword, search_location)
                if not job:
                    continue
                jobs.append(job)
                parsed += 1
                if len(jobs) >= limit:
                    break
            if not parsed or len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Dice job search unavailable: %s', exc)
        error = str(exc)
    jobs = _enrich_job_descriptions(jobs, limit=min(12, len(jobs)))
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_clearancejobs_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    params = {'keywords': keyword}
    if city:
        params['location'] = city
    return _fetch_generic_board('ClearanceJobs', CLEARANCEJOBS_SEARCH_URL, params, keyword, city or 'United States', 'United States', limit)


def _fetch_usajobs_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    params = {'k': keyword}
    if city:
        params['l'] = city
    return _fetch_generic_board('USAJobs', USAJOBS_SEARCH_URL, params, keyword, city or 'United States', 'United States', limit)


def _fetch_builtin_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    base = f'{BUILTIN_SEARCH_URL}/remote/{urllib.parse.quote(keyword)}' if keyword else BUILTIN_SEARCH_URL
    return _fetch_generic_board('Built In', base, {}, keyword, city or 'Remote, United States', 'United States', limit)


def _fetch_wellfound_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Wellfound', WELLFOUND_SEARCH_URL, {'q': keyword}, keyword, location or 'United States', 'United States', limit)


def _fetch_weworkremotely_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('We Work Remotely', WEWORKREMOTELY_SEARCH_URL, {'term': keyword}, keyword, 'Remote, United States', 'United States', limit)


def _fetch_ziprecruiter_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    return _fetch_generic_board('ZipRecruiter', ZIPRECRUITER_SEARCH_URL, {'search': keyword, 'location': city}, keyword, city or 'United States', 'United States', limit)


def _fetch_glassdoor_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    return _fetch_generic_board('Glassdoor', GLASSDOOR_SEARCH_URL, {'sc.keyword': keyword, 'locT': 'N', 'locId': city}, keyword, city or 'United States', 'United States', limit)


def _fetch_us_jobs(search: str, location: str = '') -> tuple[list[dict], bool, dict[str, str]]:
    providers = {
        'dice': lambda: _fetch_dice_jobs(search, location, limit=45, pages=1),
        'remoteok': lambda: _fetch_remoteok_jobs(search, limit=45),
        'jobicy': lambda: _fetch_jobicy_jobs(search, limit=45),
        'arbeitnow': lambda: _fetch_arbeitnow_jobs(search, limit=45),
        'clearancejobs': lambda: _fetch_clearancejobs_jobs(search, location),
        'usajobs': lambda: _fetch_usajobs_jobs(search, location),
        'builtin': lambda: _fetch_builtin_jobs(search, location),
        'wellfound': lambda: _fetch_wellfound_jobs(search, location),
        'weworkremotely': lambda: _fetch_weworkremotely_jobs(search, location),
        'ziprecruiter': lambda: _fetch_ziprecruiter_jobs(search, location),
        'glassdoor': lambda: _fetch_glassdoor_jobs(search, location),
    }
    jobs = []
    cached = False
    source_errors = {}
    active_providers = {name: fetcher for name, fetcher in providers.items() if not _source_disabled(f'us:{name}')}
    if not active_providers:
        return jobs, cached, source_errors
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(active_providers)) as executor:
        futures = {executor.submit(fetcher): name for name, fetcher in active_providers.items()}
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            try:
                source_jobs, source_cached, error = future.result()
                jobs.extend(source_jobs)
                cached = cached or source_cached
                if error:
                    source_errors[name] = error
                    _record_source_failure(f'us:{name}', error)
                else:
                    _record_source_success(f'us:{name}')
            except Exception as exc:
                logger.warning('%s US provider failed unexpectedly: %s', name, exc)
                source_errors[name] = str(exc)
                _record_source_failure(f'us:{name}', exc)
    return jobs, cached, source_errors
