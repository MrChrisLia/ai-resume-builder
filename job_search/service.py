import urllib.parse

from .core import (
    VALID_JOB_TYPES,
    VALID_JOB_COUNTRIES,
    JOB_DESCRIPTION_MAX_LENGTH,
    JAPAN_SOURCE_DIRECTORY,
    ALLOWED_JOB_DETAIL_HOSTS,
    _filter_jobs,
    _dedupe_jobs,
    _fallback_jobs,
    _annotate_job_metadata,
    _fetch_detail_page_description,
)
from .providers_taiwan import _fetch_104_browser_jobs, _fetch_104_jobs
from .providers_japan import _fetch_japan_jobs
from .providers_us import _fetch_us_jobs, _fetch_remotive_jobs
from .providers_global import _fetch_linkedin_jobs, _fetch_indeed_jobs
from .providers_google import _fetch_google_jobs


def search_jobs(title: str, country: str, location: str, job_type: str) -> dict:
    source_errors = {}
    cached = False
    jobs = []

    if country in ('taiwan', 'any'):
        jobs_104, cached_104, error_104 = _fetch_104_browser_jobs(title, location, limit=72, pages=3, detail_limit=18)
        cached = cached or cached_104
        jobs.extend(jobs_104)
        if error_104:
            source_errors['104-browser'] = error_104
            jobs_104_api, cached_104_api, error_104_api = _fetch_104_jobs(title or location)
            cached = cached or cached_104_api
            jobs.extend(jobs_104_api)
            if error_104_api:
                source_errors['104'] = error_104_api

    if country in ('japan', 'any'):
        japan_jobs, cached_japan, japan_errors = _fetch_japan_jobs(title, location)
        cached = cached or cached_japan
        jobs.extend(japan_jobs)
        source_errors.update(japan_errors)

    if country in ('united_states', 'any'):
        us_jobs, cached_us, us_errors = _fetch_us_jobs(title, location)
        cached = cached or cached_us
        jobs.extend(us_jobs)
        source_errors.update(us_errors)

    if country in ('united_states', 'japan', 'taiwan', 'any'):
        linkedin_jobs, cached_linkedin, error_linkedin = _fetch_linkedin_jobs(title, country, location, limit=45, pages=1)
        cached = cached or cached_linkedin
        jobs.extend(linkedin_jobs)
        if error_linkedin:
            source_errors['linkedin'] = error_linkedin

        indeed_jobs, cached_indeed, error_indeed = _fetch_indeed_jobs(title, country, location, limit=45, pages=1)
        cached = cached or cached_indeed
        jobs.extend(indeed_jobs)
        if error_indeed:
            source_errors['indeed'] = error_indeed

        google_jobs, cached_google, error_google = _fetch_google_jobs(title, country, location, limit=24)
        cached = cached or cached_google
        jobs.extend(google_jobs)
        if error_google:
            source_errors['google'] = error_google

    remotive_jobs, cached_remotive = _fetch_remotive_jobs(title)
    cached = cached or cached_remotive
    jobs.extend(remotive_jobs)
    jobs = _dedupe_jobs(jobs)
    jobs = [_annotate_job_metadata(job) for job in jobs]

    filtered = _filter_jobs(jobs, title, country, location, job_type)
    if not filtered:
        filtered = _filter_jobs(_fallback_jobs(title), title, country, location, job_type)
    source_names = sorted({job.get('source') for job in filtered if job.get('source')})
    source_methods = sorted({job.get('source_method') for job in filtered if job.get('source_method')})
    return {
        'success': True,
        'jobs': filtered,
        'count': len(filtered),
        'cached': cached,
        'source': ', '.join(source_names) if source_names else 'Sample',
        'source_methods': source_methods,
        'source_errors': source_errors,
        'japan_sources': JAPAN_SOURCE_DIRECTORY if country in ('japan', 'any') else {},
    }


def job_detail_description(data: dict) -> tuple[dict, int]:
    job = {
        'id': str(data.get('id') or '')[:160],
        'title': str(data.get('title') or '')[:300],
        'company': str(data.get('company') or '')[:300],
        'location': str(data.get('location') or '')[:300],
        'category': str(data.get('category') or '')[:300],
        'job_type': str(data.get('job_type') or '')[:80],
        'description': str(data.get('description') or '')[:JOB_DESCRIPTION_MAX_LENGTH],
        'url': str(data.get('url') or '')[:1200],
        'source': str(data.get('source') or '')[:120],
        'search_terms': str(data.get('search_terms') or '')[:300],
        'search_location': str(data.get('search_location') or '')[:300],
    }

    parsed = urllib.parse.urlparse(job['url'])
    if parsed.scheme != 'https' or parsed.netloc.lower() not in ALLOWED_JOB_DETAIL_HOSTS:
        return {'success': False, 'error': 'Unsupported job detail host'}, 400

    description = _fetch_detail_page_description(job)
    if not description:
        return {'success': False, 'error': 'No fuller description available'}, 404

    enriched = _annotate_job_metadata({**job, 'description': description, 'description_source': 'detail-page'})
    return {
        'success': True,
        'description': enriched['description'],
        'description_source': enriched.get('description_source'),
        'japanese_requirement': enriched.get('japanese_requirement', ''),
        'security_clearance': enriched.get('security_clearance', ''),
        'public_safety_score': enriched.get('public_safety_score'),
        'public_safety_label': enriched.get('public_safety_label', ''),
        'public_safety_city': enriched.get('public_safety_city', ''),
    }, 200
