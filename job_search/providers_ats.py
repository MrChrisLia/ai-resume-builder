from .core import *


ATS_GREENHOUSE_BOARDS = (
    'airbnb', 'andurilindustries', 'databricks', 'discord', 'figma',
    'robinhood', 'stripe', 'warnerbrosdiscovery', 'zapier',
)
ATS_LEVER_BOARDS = (
    'anduril', 'cloudflare', 'datadog', 'figma', 'scaleai',
)
ATS_ASHBY_BOARDS = (
    'openai', 'cursor', 'linear', 'notion', 'perplexity', 'sierra', 'watershed',
)
ATS_WORKABLE_BOARDS = (
    'canonical', 'kraken', 'remote', 'safetyculture',
)

ATS_COMPANY_NAMES = {
    'mercari': 'Mercari',
    'smartnews': 'SmartNews',
    'woven-by-toyota': 'Woven by Toyota',
}


def _ats_text(value) -> str:
    return _clean_job_text(value)


def _ats_company(slug: str, fallback: str = '') -> str:
    return _ats_text(fallback or ATS_COMPANY_NAMES.get(slug) or slug.replace('-', ' ').title())


def _ats_location(value, default='Remote') -> str:
    if isinstance(value, dict):
        parts = [
            value.get('name'),
            value.get('city'),
            value.get('region') or value.get('state'),
            value.get('country'),
        ]
        return _ats_text(value.get('location') or ', '.join(str(part) for part in parts if part) or default)
    if isinstance(value, list):
        parts = []
        for item in value:
            if isinstance(item, dict):
                parts.append(_ats_location(item, ''))
            elif item:
                parts.append(str(item))
        return _ats_text(', '.join(part for part in parts if part) or default)
    return _ats_text(value or default)


def _fetch_greenhouse_board(slug: str, search: str, limit: int) -> tuple[list[dict], str | None]:
    url = GREENHOUSE_BOARD_API_URL.format(slug=urllib.parse.quote(slug))
    jobs = []
    try:
        raw = _fetch_text_url(url, timeout=10, headers={'User-Agent': 'Job Search and Resume Creator local dev', 'Accept': 'application/json'})
        payload = json.loads(raw)
        for item in (payload.get('jobs') or [])[:limit]:
            title = _ats_text(item.get('title'))
            absolute_url = str(item.get('absolute_url') or '').strip()
            offices = item.get('offices') or []
            departments = item.get('departments') or []
            company = _ats_company(slug, payload.get('company_name'))
            job = {
                'id': f"greenhouse-{slug}-{item.get('id') or uuid.uuid4().hex[:10]}",
                'title': title,
                'company': company,
                'location': _ats_location(offices, 'Remote'),
                'job_type': '',
                'category': _ats_location(departments, ''),
                'salary': '',
                'posted_at': _iso_to_date(item.get('updated_at') or item.get('first_published')),
                'description': _clean_job_description(item.get('content') or ''),
                'url': absolute_url,
                'source': 'Greenhouse',
                'source_method': 'ats-api',
                'search_terms': search,
                'strict_title_match': False,
            }
            if job['title'] and job['url']:
                jobs.append(job)
        return jobs, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return jobs, f'{slug}: {exc}'


def _fetch_lever_board(slug: str, search: str, limit: int) -> tuple[list[dict], str | None]:
    url = LEVER_POSTINGS_API_URL.format(slug=urllib.parse.quote(slug))
    jobs = []
    try:
        raw = _fetch_text_url(url, timeout=10, headers={'User-Agent': 'Job Search and Resume Creator local dev', 'Accept': 'application/json'})
        payload = json.loads(raw)
        if not isinstance(payload, list):
            return jobs, None
        for item in payload[:limit]:
            categories = item.get('categories') or {}
            lists = item.get('lists') or []
            description = '\n'.join(part for part in (
                item.get('descriptionPlain') or item.get('description') or '',
                '\n'.join(_strip_html(section.get('content') or '') for section in lists if isinstance(section, dict)),
            ) if part)
            job = {
                'id': f"lever-{slug}-{item.get('id') or uuid.uuid4().hex[:10]}",
                'title': _ats_text(item.get('text')),
                'company': _ats_company(slug),
                'location': _ats_location(categories.get('location'), 'Remote'),
                'job_type': _map_job_type(categories.get('commitment') or ''),
                'category': _ats_text(categories.get('team') or categories.get('department')),
                'salary': '',
                'posted_at': _epoch_to_date((item.get('createdAt') or 0) / 1000 if item.get('createdAt') else None),
                'description': _clean_job_description(description),
                'url': str(item.get('hostedUrl') or item.get('applyUrl') or '').strip(),
                'source': 'Lever',
                'source_method': 'ats-api',
                'search_terms': search,
                'strict_title_match': False,
            }
            if job['title'] and job['url']:
                jobs.append(job)
        return jobs, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return jobs, f'{slug}: {exc}'


def _fetch_ashby_board(slug: str, search: str, limit: int) -> tuple[list[dict], str | None]:
    url = ASHBY_BOARD_API_URL.format(slug=urllib.parse.quote(slug))
    jobs = []
    try:
        raw = _fetch_text_url(url, timeout=10, headers={'User-Agent': 'Job Search and Resume Creator local dev', 'Accept': 'application/json'})
        payload = json.loads(raw)
        for item in (payload.get('jobs') or [])[:limit]:
            comp = item.get('compensation') or {}
            salary = _ats_text(comp.get('compensationTierSummary') or comp.get('summary') or '')
            location = item.get('location') or {}
            job = {
                'id': f"ashby-{slug}-{item.get('id') or uuid.uuid4().hex[:10]}",
                'title': _ats_text(item.get('title')),
                'company': _ats_company(slug),
                'location': _ats_location(location, 'Remote'),
                'job_type': _map_job_type(item.get('employmentType') or ''),
                'category': _ats_text(item.get('department') or item.get('team')),
                'salary': salary,
                'posted_at': _iso_to_date(item.get('publishedAt') or item.get('createdAt')),
                'description': _clean_job_description(item.get('descriptionHtml') or item.get('description') or ''),
                'url': str(item.get('jobUrl') or item.get('applyUrl') or '').strip(),
                'source': 'Ashby',
                'source_method': 'ats-api',
                'search_terms': search,
                'strict_title_match': False,
            }
            if job['title'] and job['url']:
                jobs.append(job)
        return jobs, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return jobs, f'{slug}: {exc}'


def _workable_job_url(slug: str, item: dict) -> str:
    url = str(item.get('url') or item.get('shortlink') or item.get('application_url') or '').strip()
    if url:
        return url
    shortcode = str(item.get('shortcode') or item.get('id') or '').strip()
    return f'https://apply.workable.com/{slug}/j/{shortcode}' if shortcode else ''


def _workable_records(slug: str) -> tuple[list[dict], str]:
    headers = {'User-Agent': 'Job Search and Resume Creator local dev', 'Accept': 'application/json'}
    try:
        url = WORKABLE_JOBS_API_URL.format(slug=urllib.parse.quote(slug))
        raw = _fetch_text_url(url, timeout=10, headers=headers)
        payload = json.loads(raw)
        return payload.get('results') or payload.get('jobs') or [], _ats_company(slug, payload.get('name'))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        url = WORKABLE_WIDGET_API_URL.format(slug=urllib.parse.quote(slug))
        raw = _fetch_text_url(url, timeout=10, headers=headers)
        payload = json.loads(raw)
        return payload.get('jobs') or payload.get('results') or [], _ats_company(slug, payload.get('name'))


def _fetch_workable_board(slug: str, search: str, limit: int) -> tuple[list[dict], str | None]:
    jobs = []
    try:
        records, company = _workable_records(slug)
        for item in records[:limit]:
            description = '\n'.join(part for part in (
                item.get('description') or '',
                f"Experience: {item.get('experience')}" if item.get('experience') else '',
                f"Function: {item.get('function')}" if item.get('function') else '',
                f"Industry: {item.get('industry')}" if item.get('industry') else '',
            ) if part)
            job = {
                'id': f"workable-{slug}-{item.get('shortcode') or item.get('id') or uuid.uuid4().hex[:10]}",
                'title': _ats_text(item.get('title')),
                'company': company,
                'location': _ats_location(item.get('location') or item.get('locations'), 'Remote'),
                'job_type': _map_job_type(item.get('employment_type') or ''),
                'category': _ats_text(item.get('department') or item.get('function')),
                'salary': '',
                'posted_at': _iso_to_date(item.get('published') or item.get('published_on') or item.get('created_at')),
                'description': _clean_job_description(description),
                'url': _workable_job_url(slug, item),
                'source': 'Workable',
                'source_method': 'ats-api',
                'search_terms': search,
                'strict_title_match': False,
            }
            if job['title'] and job['url']:
                jobs.append(job)
        return jobs, None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return jobs, f'{slug}: {exc}'


def _fetch_ats_jobs(search: str, limit: int = 80) -> tuple[list[dict], bool, dict[str, str]]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    cache_key = f"ats:{keyword.lower() or '_latest'}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('errors', {})

    tasks = []
    per_board_limit = 12
    for slug in ATS_GREENHOUSE_BOARDS:
        if not _source_disabled(f'ats:greenhouse:{slug}'):
            tasks.append(('greenhouse', slug, lambda s=slug: _fetch_greenhouse_board(s, keyword, per_board_limit)))
    for slug in ATS_LEVER_BOARDS:
        if not _source_disabled(f'ats:lever:{slug}'):
            tasks.append(('lever', slug, lambda s=slug: _fetch_lever_board(s, keyword, per_board_limit)))
    for slug in ATS_ASHBY_BOARDS:
        if not _source_disabled(f'ats:ashby:{slug}'):
            tasks.append(('ashby', slug, lambda s=slug: _fetch_ashby_board(s, keyword, per_board_limit)))
    for slug in ATS_WORKABLE_BOARDS:
        if not _source_disabled(f'ats:workable:{slug}'):
            tasks.append(('workable', slug, lambda s=slug: _fetch_workable_board(s, keyword, per_board_limit)))

    jobs = []
    errors_by_source = {}
    jobs_by_source = {}
    if not tasks:
        return jobs, False, errors_by_source
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(12, len(tasks))) as executor:
        futures = {executor.submit(fetcher): (source, slug) for source, slug, fetcher in tasks}
        for future in concurrent.futures.as_completed(futures):
            source, slug = futures[future]
            source_key = f'ats:{source}:{slug}'
            try:
                source_jobs, error = future.result()
                jobs.extend(source_jobs)
                if source_jobs:
                    jobs_by_source[source] = jobs_by_source.get(source, 0) + len(source_jobs)
                if error:
                    errors_by_source.setdefault(source, []).append(error)
                    _record_source_failure(source_key, error)
                else:
                    _record_source_success(source_key)
            except Exception as exc:
                errors_by_source.setdefault(source, []).append(f'{slug}: {exc}')
                _record_source_failure(source_key, exc)

    errors = {
        source: '; '.join(items)[:500]
        for source, items in errors_by_source.items()
        if items and not jobs_by_source.get(source) and source not in {'lever', 'workable'}
    }
    jobs = jobs[:limit]
    _cache_set(cache_key, jobs=jobs, errors=errors)
    return jobs, False, errors
