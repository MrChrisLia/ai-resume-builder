from .core import *


def _jobposting_to_job(payload: dict, source: str, base_url: str, keyword: str, default_location: str, country_label: str) -> dict | None:
    if not isinstance(payload, dict):
        return None
    title = _clean_job_text(payload.get('title') or payload.get('name'))
    if not title:
        return None
    org = payload.get('hiringOrganization') or payload.get('organization') or {}
    company = _clean_job_text(org.get('name') if isinstance(org, dict) else org) or source
    job_location = payload.get('jobLocation') or payload.get('applicantLocationRequirements')
    if isinstance(job_location, list):
        location = ', '.join(
            _clean_job_text(((loc.get('address') or {}).get('addressLocality') if isinstance(loc.get('address'), dict) else loc.get('name')) if isinstance(loc, dict) else loc)
            for loc in job_location
        )
    elif isinstance(job_location, dict):
        address = job_location.get('address') or {}
        location = _clean_job_text(
            address.get('addressLocality') or address.get('addressRegion') or job_location.get('name') or default_location
        )
    else:
        location = _clean_job_text(default_location or country_label)
    employment = payload.get('employmentType')
    if isinstance(employment, list):
        employment_text = ' '.join(str(item) for item in employment)
    else:
        employment_text = str(employment or '')
    href = str(payload.get('url') or payload.get('@id') or '').strip()
    url = _absolute_url(base_url, href) if href else base_url
    job_id = uuid.uuid5(uuid.NAMESPACE_URL, f'{source}:{url}:{title}').hex[:16]
    return {
        'id': f'{re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")}-{job_id}',
        'title': title,
        'company': company,
        'location': location or default_location or country_label,
        'job_type': _map_job_type(employment_text),
        'category': _clean_job_text(employment_text),
        'salary': _clean_job_text(payload.get('baseSalary') or ''),
        'posted_at': _iso_to_date(payload.get('datePosted')),
        'description': _clean_job_description(payload.get('description') or ''),
        'url': url,
        'source': source,
        'source_method': 'json-ld',
        'search_terms': keyword,
        'search_location': default_location or country_label,
        'strict_title_match': False,
    }


def _json_ld_jobs(raw: str, source: str, base_url: str, keyword: str, default_location: str, country_label: str) -> list[dict]:
    jobs = []
    for payload in _extract_json_ld(raw):
        records = []
        if payload.get('@type') == 'JobPosting':
            records.append(payload)
        elif payload.get('@graph'):
            records.extend(item for item in payload.get('@graph') or [] if isinstance(item, dict) and item.get('@type') == 'JobPosting')
        elif payload.get('@type') == 'ItemList':
            for item in payload.get('itemListElement') or []:
                if isinstance(item, dict):
                    candidate = item.get('item') or item
                    if isinstance(candidate, dict) and candidate.get('@type') == 'JobPosting':
                        records.append(candidate)
        for record in records:
            job = _jobposting_to_job(record, source, base_url, keyword, default_location, country_label)
            if job:
                jobs.append(job)
    return jobs


def _anchor_jobs(raw: str, source: str, base_url: str, keyword: str, default_location: str, country_label: str, limit: int) -> list[dict]:
    jobs = []
    seen = set()
    keyword_lower = keyword.lower()
    keyword_tokens = [token for token in re.findall(r'[a-zA-Z0-9+#.-]{3,}', keyword_lower) if token not in {'job', 'jobs', 'the', 'and'}]
    generic_titles = {
        'jobs', 'find jobs', 'search jobs', 'job search', 'careers', 'career',
        'login', 'log in', 'sign in', 'sign up', 'register', 'manage', 'candidates',
        'employers', 'companies', 'internship', 'get the newsletter', 'career explorer quiz',
    }
    for href, text in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', raw or '', flags=re.I | re.S):
        title = _clean_job_text(text)
        if not title or len(title) < 4 or len(title) > 140:
            continue
        title_lower = title.lower()
        if title_lower in generic_titles:
            continue
        url = _absolute_url(base_url, href)
        parsed_path = urllib.parse.urlparse(url).path.lower()
        looks_like_job = any(marker in parsed_path for marker in ('job', 'jobs', 'career', 'position', 'recruit', 'opening', 'offer'))
        if keyword_tokens and not any(token in title_lower for token in keyword_tokens):
            continue
        if not looks_like_job and not keyword_lower:
            continue
        key = url.lower()
        if key in seen:
            continue
        seen.add(key)
        job_id = uuid.uuid5(uuid.NAMESPACE_URL, f'{source}:{url}:{title}').hex[:16]
        jobs.append({
            'id': f'{re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")}-{job_id}',
            'title': title,
            'company': source,
            'location': default_location or country_label,
            'job_type': '',
            'category': '',
            'salary': '',
            'posted_at': '',
            'description': _clean_job_description(f'{title}\nSearch result from {source}'),
            'url': url,
            'source': source,
            'source_method': 'public-html',
            'search_terms': keyword,
            'search_location': default_location or country_label,
            'strict_title_match': False,
        })
        if len(jobs) >= limit:
            break
    return jobs


def _extract_generic_board_jobs(raw: str, source: str, base_url: str, keyword: str, default_location: str, country_label: str, limit: int = 30) -> list[dict]:
    jobs = _json_ld_jobs(raw, source, base_url, keyword, default_location, country_label)
    if len(jobs) < limit:
        existing = {job.get('url') for job in jobs}
        for job in _anchor_jobs(raw, source, base_url, keyword, default_location, country_label, limit - len(jobs)):
            if job.get('url') not in existing:
                jobs.append(job)
                existing.add(job.get('url'))
    return jobs[:limit]


def _fetch_generic_board(
    source: str,
    base_url: str,
    params: dict,
    keyword: str,
    default_location: str,
    country_label: str,
    limit: int = 30,
    headers: dict | None = None,
) -> tuple[list[dict], bool, str | None]:
    cache_key = f"generic:{source.lower()}:{keyword.lower() or '_latest'}:{default_location.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    jobs = []
    error = None
    try:
        url = base_url if not params else f'{base_url}?{urllib.parse.urlencode(params)}'
        raw = _fetch_text_url(url, timeout=8, headers=headers or _job_source_headers(source))
        jobs = _extract_generic_board_jobs(raw, source, base_url, keyword, default_location, country_label, limit)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('%s search unavailable: %s', source, exc)
        error = str(exc)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error
