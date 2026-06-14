from .core import *

def _linkedin_country_locations(country: str, location: str) -> list[str]:
    location = re.sub(r'\s+', ' ', location or '').strip()
    if location:
        return [location]
    return {
        'united_states': ['United States'],
        'japan': ['Japan'],
        'taiwan': ['Taiwan'],
        'any': ['United States', 'Japan', 'Taiwan'],
    }.get(country, ['United States', 'Japan', 'Taiwan'])


def _canonical_linkedin_url(href: str, job_id: str = '') -> str:
    href = _html.unescape(href or '').strip()
    if not href and job_id:
        return f'https://www.linkedin.com/jobs/view/{job_id}'
    parsed = urllib.parse.urlparse(href)
    if not parsed.scheme:
        parsed = urllib.parse.urlparse(_absolute_url('https://www.linkedin.com', href))
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))


def _extract_linkedin_card(card: str, search_location: str, keyword: str) -> dict | None:
    job_id = _regex_first(r'data-entity-urn="urn:li:jobPosting:(\d+)"', card)
    href = _regex_first(r'class="[^"]*base-card__full-link[^"]*"[^>]+href="([^"]+)"', card)
    link = _canonical_linkedin_url(href, job_id)
    title = _regex_first(r'class="[^"]*base-search-card__title[^"]*"[^>]*>\s*(.*?)\s*</h3>', card)
    company = _regex_first(r'class="[^"]*base-search-card__subtitle[^"]*"[^>]*>\s*(.*?)\s*</h4>', card)
    job_location = _regex_first(r'class="[^"]*job-search-card__location[^"]*"[^>]*>\s*(.*?)\s*</span>', card)
    posted_at = _regex_first(r'<time[^>]+datetime="([^"]+)"', card)
    salary = _regex_first(r'class="[^"]*job-search-card__salary-info[^"]*"[^>]*>\s*(.*?)\s*</span>', card)
    if not title or not link:
        return None
    job_id = job_id or link.rstrip('/').split('/')[-1] or uuid.uuid4().hex[:10]
    description = '\n'.join(part for part in (
        f'Company: {company}' if company else '',
        f'Location: {job_location}' if job_location else '',
        f'Posted: {posted_at}' if posted_at else '',
    ) if part)
    return {
        'id': f'linkedin-{job_id}',
        'title': title,
        'company': company or 'LinkedIn employer',
        'location': job_location or search_location,
        'job_type': '',
        'category': '',
        'salary': salary,
        'posted_at': posted_at,
        'description': _clean_job_description(description),
        'url': link,
        'source': 'LinkedIn',
        'source_method': 'guest-public',
        'search_terms': keyword,
        'search_location': search_location,
    }


def _fetch_linkedin_jobs(search: str, country: str = 'any', location: str = '', limit: int = 36, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    locations = _linkedin_country_locations(country, location)
    cache_key = f"linkedin:{keyword.lower() or '_latest'}:{country}:{'|'.join(locations).lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    errors = []
    per_location_limit = max(1, limit // max(1, len(locations)))
    try:
        for search_location in locations:
            fetched_for_location = 0
            for page in range(pages):
                params = {
                    'keywords': keyword,
                    'location': search_location,
                    'start': str(page * 25),
                }
                url = f'{LINKEDIN_SEARCH_URL}?{urllib.parse.urlencode(params)}'
                try:
                    raw = _fetch_text_url(url, timeout=12, headers=_job_source_headers('LinkedIn'))
                except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
                    errors.append(f'{search_location}: {exc}')
                    break
                cards = re.split(r'(?=<div class="base-card[^"]*base-search-card[^"]*job-search-card")', raw)
                parsed_any = False
                for card in cards:
                    if 'job-search-card' not in card:
                        continue
                    job = _extract_linkedin_card(card, search_location, keyword)
                    if not job:
                        continue
                    jobs.append(job)
                    fetched_for_location += 1
                    parsed_any = True
                    if fetched_for_location >= per_location_limit or len(jobs) >= limit:
                        break
                if not parsed_any:
                    break
                if fetched_for_location >= per_location_limit or len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except Exception as exc:
        logger.warning('LinkedIn search failed unexpectedly: %s', exc)
        errors.append(str(exc))

    jobs = _enrich_job_descriptions(jobs, limit=min(10, len(jobs)))
    error = '; '.join(errors)[:500] if errors and not jobs else None
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _indeed_country_targets(country: str, location: str) -> list[tuple[str, str, str, str]]:
    requested_location = re.sub(r'\s+', ' ', location or '').strip()
    country_keys = ('united_states', 'japan', 'taiwan') if country == 'any' else (country,)
    targets = []
    for country_key in country_keys:
        host_label = INDEED_HOSTS_BY_COUNTRY.get(country_key)
        if not host_label:
            continue
        host, country_label = host_label
        query_location = requested_location or country_label
        indexed_location = query_location
        if country_label.lower() not in query_location.lower():
            indexed_location = f'{query_location}, {country_label}'
        targets.append((country_key, host, query_location, indexed_location))
    return targets


def _indeed_salary_text(result: dict) -> str:
    snippet = result.get('salarySnippet')
    if isinstance(snippet, dict) and snippet.get('text'):
        return _clean_job_text(snippet.get('text'))
    salary = result.get('extractedSalary')
    if not isinstance(salary, dict):
        return ''
    minimum = salary.get('min')
    maximum = salary.get('max')
    salary_type = _clean_job_text(salary.get('type')).lower()
    if not minimum or minimum == -1:
        return ''
    if maximum and maximum != -1 and maximum != minimum:
        value = f'{minimum} - {maximum}'
    else:
        value = str(minimum)
    return f'{value} {salary_type}'.strip()


def _extract_indeed_provider_results(raw: str) -> list[dict]:
    data = _extract_js_assignment_json(raw, 'window.mosaic.providerData["mosaic-provider-jobcards"]=')
    model = data.get('metaData', {}).get('mosaicProviderJobCardsModel', {})
    results = model.get('results') or data.get('results') or []
    return results if isinstance(results, list) else []


def _extract_indeed_card(result: dict, host: str, country_key: str, indexed_location: str, keyword: str) -> dict | None:
    if not isinstance(result, dict):
        return None
    job_key = _clean_job_text(result.get('jobkey') or result.get('jobKey'))
    title = _clean_job_text(result.get('displayTitle') or result.get('title'))
    if not job_key or not title:
        return None
    company = _clean_job_text(result.get('company') or result.get('companyName')) or 'Indeed employer'
    job_location = _clean_job_text(
        result.get('formattedLocation') or result.get('location') or result.get('remoteLocation') or indexed_location
    )
    salary = _indeed_salary_text(result)
    job_types = [str(item) for item in (result.get('jobTypes') or []) if item]
    category = ', '.join(_clean_job_text(item) for item in job_types if _clean_job_text(item))
    posted_at = _epoch_to_date(result.get('pubDate')) or _clean_job_text(result.get('formattedRelativeTime'))
    snippet = _clean_job_description(result.get('snippet') or '')
    benefits = []
    for benefit in result.get('rankedBenefits') or []:
        if isinstance(benefit, dict):
            label = _clean_job_text(benefit.get('name') or benefit.get('label'))
        else:
            label = _clean_job_text(benefit)
        if label:
            benefits.append(label)
    description = '\n'.join(part for part in (
        snippet,
        f"Job type: {category}" if category else '',
        f"Benefits: {', '.join(benefits[:6])}" if benefits else '',
        f'Posted: {posted_at}' if posted_at else '',
    ) if part)
    return {
        'id': f'indeed-{country_key}-{job_key}',
        'title': title,
        'company': company,
        'location': job_location or indexed_location,
        'job_type': _map_job_type(category),
        'category': category,
        'salary': salary,
        'posted_at': posted_at,
        'description': _clean_job_description(description),
        'url': f'https://{host}/viewjob?{urllib.parse.urlencode({"jk": job_key})}',
        'source': 'Indeed',
        'source_method': 'public-search',
        'search_terms': keyword,
        'search_location': indexed_location,
    }


def _fetch_indeed_jobs(search: str, country: str = 'any', location: str = '', limit: int = 45, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    targets = _indeed_country_targets(country, location)
    target_key = '|'.join(f'{country_key}:{host}:{query_location}' for country_key, host, query_location, _ in targets)
    cache_key = f"indeed:{keyword.lower() or '_latest'}:{target_key.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    errors = []
    per_target_limit = max(1, limit // max(1, len(targets)))

    def fetch_target(target: tuple[str, str, str, str]) -> tuple[list[dict], str | None]:
        country_key, host, query_location, indexed_location = target
        target_jobs = []
        try:
            for page in range(pages):
                params = {'q': keyword, 'l': query_location, 'start': str(page * 10)}
                url = f'https://{host}/jobs?{urllib.parse.urlencode(params)}'
                raw = _fetch_text_url(url, timeout=12, headers=_indeed_headers(host))
                try:
                    results = _extract_indeed_provider_results(raw)
                except json.JSONDecodeError as exc:
                    if 'captcha' in raw.lower() or 'blocked' in raw.lower():
                        return target_jobs, f'{host}: blocked or captcha'
                    return target_jobs, f'{host}: {exc}'
                if not results:
                    if 'captcha' in raw.lower() or 'blocked' in raw.lower():
                        return target_jobs, f'{host}: blocked or captcha'
                    break
                for result in results:
                    job = _extract_indeed_card(result, host, country_key, indexed_location, keyword)
                    if not job:
                        continue
                    target_jobs.append(job)
                    if len(target_jobs) >= per_target_limit:
                        break
                if len(target_jobs) >= per_target_limit:
                    break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            return target_jobs, f'{host}: {exc}'
        return target_jobs, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(3, max(1, len(targets)))) as executor:
        futures = {executor.submit(fetch_target, target): target for target in targets}
        for future in concurrent.futures.as_completed(futures):
            target_jobs, error = future.result()
            jobs.extend(target_jobs)
            if error:
                errors.append(error)

    jobs = _enrich_job_descriptions(jobs, limit=min(8, len(jobs)))
    error = '; '.join(errors)[:500] if errors and not jobs else None
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


