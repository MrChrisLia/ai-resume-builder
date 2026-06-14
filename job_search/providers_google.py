from .core import *


def _google_country_targets(country: str, location: str) -> list[tuple[str, str, str]]:
    requested_location = re.sub(r'\s+', ' ', location or '').strip()
    country_labels = {
        'united_states': 'United States',
        'japan': 'Japan',
        'taiwan': 'Taiwan',
    }
    country_keys = ('united_states', 'japan', 'taiwan') if country == 'any' else (country,)
    targets = []
    for country_key in country_keys:
        country_label = country_labels.get(country_key)
        if not country_label:
            continue
        search_location = requested_location or country_label
        indexed_location = search_location
        if country_label.lower() not in search_location.lower():
            indexed_location = f'{search_location}, {country_label}'
        targets.append((country_key, search_location, indexed_location))
    return targets


def _google_job_query(keyword: str, search_location: str, country_key: str) -> str:
    terms = [keyword or 'jobs', 'jobs', 'careers', 'apply', search_location]
    if country_key == 'taiwan':
        terms.extend(('Taiwan', '104 OR LinkedIn OR Indeed'))
    elif country_key == 'japan':
        terms.extend(('Japan', 'CareerCross OR Daijob OR LinkedIn OR Indeed'))
    elif country_key == 'united_states':
        terms.extend(('United States', 'Dice OR LinkedIn OR Indeed OR careers'))
    return ' '.join(term for term in terms if term).strip()


def _extract_google_company(title: str, display_link: str) -> str:
    title = _clean_job_text(title)
    for separator in (' - ', ' | ', ' at '):
        if separator in title:
            candidate = title.rsplit(separator, 1)[-1].strip()
            if candidate and len(candidate) <= 80:
                return candidate
    host = (display_link or '').replace('www.', '').strip()
    return host or 'Google result'


def _normalize_google_item(item: dict, country_key: str, search_location: str, keyword: str) -> dict | None:
    link = str(item.get('link') or '').strip()
    title = _clean_job_text(item.get('title'))
    snippet = _clean_job_description(item.get('snippet') or '')
    if not link or not title:
        return None
    parsed = urllib.parse.urlparse(link)
    if parsed.scheme not in ('http', 'https') or not parsed.netloc:
        return None
    display_link = _clean_job_text(item.get('displayLink') or parsed.netloc)
    description = '\n'.join(part for part in (
        snippet,
        f'Search result from {display_link}' if display_link else '',
    ) if part)
    return {
        'id': f'google-{uuid.uuid5(uuid.NAMESPACE_URL, link).hex[:16]}',
        'title': title,
        'company': _extract_google_company(title, display_link),
        'location': search_location,
        'job_type': '',
        'category': 'Google job lead',
        'salary': '',
        'posted_at': '',
        'description': _clean_job_description(description),
        'url': link,
        'source': 'Google Search',
        'source_method': 'custom-search-api',
        'search_terms': keyword,
        'search_location': search_location,
        'strict_title_match': False,
    }


def _fetch_google_jobs(search: str, country: str = 'any', location: str = '', limit: int = 24) -> tuple[list[dict], bool, str | None]:
    api_key = os.environ.get('GOOGLE_CSE_API_KEY') or os.environ.get('GOOGLE_CUSTOM_SEARCH_API_KEY')
    search_engine_id = os.environ.get('GOOGLE_CSE_ID') or os.environ.get('GOOGLE_CUSTOM_SEARCH_ENGINE_ID')
    if not api_key or not search_engine_id:
        return [], False, None

    keyword = re.sub(r'\s+', ' ', search or '').strip()
    targets = _google_country_targets(country, location)
    target_key = '|'.join(f'{country_key}:{search_location}' for country_key, search_location, _ in targets)
    cache_key = f"google:{keyword.lower() or '_latest'}:{target_key.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    errors = []
    per_target_limit = max(1, limit // max(1, len(targets)))
    for country_key, query_location, indexed_location in targets:
        fetched_for_target = 0
        for start in (1, 11):
            if fetched_for_target >= per_target_limit or len(jobs) >= limit:
                break
            params = {
                'key': api_key,
                'cx': search_engine_id,
                'q': _google_job_query(keyword, query_location, country_key),
                'num': str(min(10, per_target_limit - fetched_for_target)),
                'start': str(start),
                'safe': 'active',
            }
            url = f'{GOOGLE_CSE_URL}?{urllib.parse.urlencode(params)}'
            try:
                raw = _fetch_text_url(url, timeout=12, headers={
                    'User-Agent': 'Job Search and Resume Creator local dev',
                    'Accept': 'application/json',
                })
                payload = json.loads(raw)
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                errors.append(f'{indexed_location}: {exc}')
                break
            if payload.get('error'):
                message = payload.get('error', {}).get('message') or 'Google Custom Search error'
                errors.append(f'{indexed_location}: {message}')
                break
            items = payload.get('items') or []
            if not items:
                break
            for item in items:
                job = _normalize_google_item(item, country_key, indexed_location, keyword)
                if not job:
                    continue
                jobs.append(job)
                fetched_for_target += 1
                if fetched_for_target >= per_target_limit or len(jobs) >= limit:
                    break

    error = '; '.join(errors)[:500] if errors and not jobs else None
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error
