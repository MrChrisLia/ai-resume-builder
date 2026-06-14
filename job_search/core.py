import os
import re
import uuid
import json
import time as _time
import logging
import threading
import html as _html
import subprocess
import concurrent.futures
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import urllib.error
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)
logger = logging.getLogger(__name__)


VALID_TEMPLATES = frozenset({'modern', 'classic', 'minimal', 'japanese', 'taiwanese'})
VALID_LANGUAGES  = frozenset({'english', 'japanese', 'taiwanese'})
VALID_JOB_TYPES  = frozenset({'any', 'full_time', 'contract', 'part_time', 'freelance', 'internship'})
VALID_JOB_COUNTRIES = frozenset({'any', 'united_states', 'japan', 'taiwan'})

_SAFE_NAME = re.compile(r'^(cl_)?[a-f0-9]+\.(docx|pdf|md|html)$')
_SAFE_SCREENSHOT_NAME = re.compile(r'^104_[a-zA-Z0-9_-]+\.png$')
_TAG_RE = re.compile(r'<[^>]+>')
_SCRIPT_STYLE_RE = re.compile(r'<(script|style).*?>.*?</\1>', re.I | re.S)

REMOTIVE_API_URL = 'https://remotive.com/api/remote-jobs'
REMOTEOK_API_URL = 'https://remoteok.com/api'
ARBEITNOW_API_URL = 'https://www.arbeitnow.com/api/job-board-api'
JOBICY_API_URL = 'https://jobicy.com/api/v2/remote-jobs'
DICE_SEARCH_URL = 'https://www.dice.com/jobs'
GOOGLE_CSE_URL = 'https://www.googleapis.com/customsearch/v1'
TAIWAN_104_SEARCH_URL = 'https://www.104.com.tw/jobs/search/list'
TAIWAN_104_DETAIL_URL = 'https://www.104.com.tw/job/ajax/content/{job_id}'
TAIWAN_104_BROWSER_SCRIPT = os.path.join(BASE_DIR, 'scripts', 'scrape_104_browser.js')
GAIJINPOT_FEED_URL = 'https://jobs.gaijinpot.com/en/job/feed/atom'
JAPAN_DEV_JOBS_URL = 'https://japan-dev.com/jobs'
DAIJOB_SEARCH_URL = 'https://www.daijob.com/en/jobs/search_result'
CAREERCROSS_SEARCH_URL = 'https://www.careercross.com/en/job-search/result'
GREEN_SEARCH_URL = 'https://www.green-japan.com/search_key/01'
MYNAVI_SEARCH_BASE_URL = 'https://tenshoku.mynavi.jp/list'
WANTEDLY_SEARCH_URL = 'https://www.wantedly.com/projects'
FINDY_RECOMMENDS_URL = 'https://findy-code.io/recommends'
MICHAEL_PAGE_SEARCH_URL = 'https://www.michaelpage.co.jp/en/jobs'
RGF_SEARCH_URL = 'https://www.rgf-professional.jp/en/jobs/'
LINKEDIN_SEARCH_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
LINKEDIN_DETAIL_URL = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}'
INDEED_HOSTS_BY_COUNTRY = {
    'united_states': ('www.indeed.com', 'United States'),
    'japan': ('jp.indeed.com', 'Japan'),
    'taiwan': ('tw.indeed.com', 'Taiwan'),
}
US_PUBLIC_SAFETY_CITY_SCORES = {
    'ann arbor': 5,
    'arlington': 5,
    'bellevue': 5,
    'boulder': 5,
    'cambridge': 5,
    'cary': 5,
    'cupertino': 5,
    'frisco': 5,
    'irvine': 5,
    'madison': 5,
    'mountain view': 5,
    'naperville': 5,
    'plano': 5,
    'provo': 5,
    'redmond': 5,
    'san mateo': 5,
    'santa clara': 5,
    'scottsdale': 5,
    'sunnyvale': 5,
    'virginia beach': 5,
    'alexandria': 4,
    'annapolis junction': 4,
    'austin': 4,
    'bethesda': 4,
    'boise': 4,
    'boston': 4,
    'buffalo': 4,
    'canby': 4,
    'charlotte': 4,
    'colorado springs': 4,
    'denver': 4,
    'fairfield': 4,
    'greenwood village': 4,
    'harrisburg': 4,
    'honolulu': 4,
    'hudson': 4,
    'huntsville': 4,
    'king of prussia': 4,
    'lincoln': 4,
    'minneapolis': 4,
    'nashville': 4,
    'palo alto': 4,
    'pittsburgh': 4,
    'portland': 4,
    'portsmouth': 4,
    'raleigh': 4,
    'reston': 4,
    'salt lake city': 4,
    'san diego': 4,
    'san jose': 4,
    'sandy': 4,
    'santa monica': 4,
    'seattle': 4,
    'sparks': 4,
    'tampa': 4,
    'wenatchee': 4,
    'whippany': 4,
    'washington': 4,
    'atlanta': 3,
    'chicago': 3,
    'columbus': 3,
    'dallas': 3,
    'fort worth': 3,
    'houston': 3,
    'indianapolis': 3,
    'jacksonville': 3,
    'kansas city': 3,
    'las vegas': 3,
    'los angeles': 3,
    'miami': 3,
    'new york': 3,
    'orlando': 3,
    'philadelphia': 3,
    'phoenix': 3,
    'richmond': 3,
    'sacramento': 3,
    'san antonio': 3,
    'san francisco': 3,
    'st louis': 3,
    'tucson': 3,
    'baltimore': 2,
    'baton rouge': 2,
    'cleveland': 2,
    'little rock': 2,
    'new orleans': 2,
    'oakland': 2,
    'stockton': 2,
    'albuquerque': 1,
    'detroit': 1,
    'memphis': 1,
}
US_STATE_ABBREVIATIONS = frozenset({
    'al', 'ak', 'az', 'ar', 'ca', 'co', 'ct', 'de', 'dc', 'fl', 'ga', 'hi', 'ia', 'id',
    'il', 'in', 'ks', 'ky', 'la', 'ma', 'md', 'me', 'mi', 'mn', 'mo', 'ms', 'mt', 'nc',
    'nd', 'ne', 'nh', 'nj', 'nm', 'nv', 'ny', 'oh', 'ok', 'or', 'pa', 'ri', 'sc', 'sd',
    'tn', 'tx', 'ut', 'va', 'vt', 'wa', 'wi', 'wv', 'wy'
})
US_STATE_NAMES = frozenset({
    'alabama', 'alaska', 'arizona', 'arkansas', 'california', 'colorado', 'connecticut',
    'delaware', 'district of columbia', 'florida', 'georgia', 'hawaii', 'idaho',
    'illinois', 'indiana', 'iowa', 'kansas', 'kentucky', 'louisiana', 'maine',
    'maryland', 'massachusetts', 'michigan', 'minnesota', 'mississippi', 'missouri',
    'montana', 'nebraska', 'nevada', 'new hampshire', 'new jersey', 'new mexico',
    'new york', 'north carolina', 'north dakota', 'ohio', 'oklahoma', 'oregon',
    'pennsylvania', 'rhode island', 'south carolina', 'south dakota', 'tennessee',
    'texas', 'utah', 'vermont', 'virginia', 'washington', 'west virginia',
    'wisconsin', 'wyoming'
})
JOB_SEARCH_CACHE_TTL = 15 * 60
JOB_DESCRIPTION_MAX_LENGTH = 24_000
JOB_DETAIL_ENRICH_LIMIT = 12
_job_search_cache = {}
_job_search_lock = threading.Lock()
ALLOWED_JOB_DETAIL_HOSTS = frozenset({
    'japan-dev.com',
    'www.japan-dev.com',
    'www.daijob.com',
    'www.careercross.com',
    'www.green-japan.com',
    'www.michaelpage.co.jp',
    'www.rgf-professional.jp',
    'tenshoku.mynavi.jp',
    'www.wantedly.com',
    'www.linkedin.com',
    'linkedin.com',
    'us.linkedin.com',
    'jp.linkedin.com',
    'tw.linkedin.com',
    'indeed.com',
    'www.indeed.com',
    'jp.indeed.com',
    'tw.indeed.com',
    'dice.com',
    'www.dice.com',
})

JAPAN_SOURCE_DIRECTORY = {
    'direct': (
        'Japan Dev', 'GaijinPot', 'Daijob', 'CareerCross', 'Green',
        'Mynavi Tenshoku', 'Wantedly', 'Findy', 'Michael Page',
        'RGF Professional', 'LinkedIn Jobs', 'Indeed Japan'
    ),
    'session_or_blocked': (
        'TokyoDev', 'Jobs in Japan', 'YOLO Japan', 'WeXpats Jobs',
        'BizReach', 'Doda', 'Rikunabi NEXT',
        'Kyujinbox', 'Paiza', 'Forkwell', 'LAPRAS', 'type', 'en-gage',
        'TownWork', 'Baitoru', 'Hello Work Internet Service', 'Robert Walters',
        'Hays Japan', 'JAC Recruitment', 'Morgan McKinley', 'en world',
        'Pasona Global', 'Adecco Japan'
    ),
}

FALLBACK_JOBS = [
    {
        'id': 'sample-product-manager',
        'title': 'Product Manager',
        'company': 'Northstar Labs',
        'location': 'Remote, United States',
        'job_type': 'full_time',
        'category': 'Product',
        'salary': '$120,000 - $155,000',
        'posted_at': '',
        'description': (
            'Own the roadmap for an AI workflow product, interview users, write clear requirements, '
            'partner with design and engineering, and measure adoption across customer segments.'
        ),
        'url': 'https://remotive.com/remote-jobs',
        'source': 'Sample',
    },
    {
        'id': 'sample-frontend-engineer',
        'title': 'Frontend Engineer',
        'company': 'SignalWorks',
        'location': 'Remote, Worldwide',
        'job_type': 'contract',
        'category': 'Software Development',
        'salary': '',
        'posted_at': '',
        'description': (
            'Build responsive application screens with JavaScript, CSS, and accessibility-minded UI patterns. '
            'Collaborate with backend engineers on APIs and ship product improvements weekly.'
        ),
        'url': 'https://remotive.com/remote-jobs',
        'source': 'Sample',
    },
    {
        'id': 'sample-data-analyst',
        'title': 'Data Analyst',
        'company': 'Civic Metrics',
        'location': 'Remote, Europe',
        'job_type': 'full_time',
        'category': 'Data',
        'salary': '',
        'posted_at': '',
        'description': (
            'Analyze product and operations data, build dashboards, define reporting metrics, '
            'and translate findings into recommendations for leadership and cross-functional teams.'
        ),
        'url': 'https://remotive.com/remote-jobs',
        'source': 'Sample',
    },
    {
        'id': 'sample-growth-marketer-taiwan',
        'title': 'Growth Marketing Manager',
        'company': 'HarborLoop',
        'location': 'Remote, Taiwan',
        'job_type': 'full_time',
        'category': 'Marketing',
        'salary': '',
        'posted_at': '',
        'description': (
            'Lead Taiwan market campaigns, localize messaging, manage paid acquisition, '
            'and partner with sales to convert qualified leads into customers.'
        ),
        'url': 'https://remotive.com/remote-jobs',
        'source': 'Sample',
    },
]



def _strip_html(value: str) -> str:
    value = _SCRIPT_STYLE_RE.sub(' ', value or '')
    value = _TAG_RE.sub(' ', value)
    value = _html.unescape(value)
    return re.sub(r'\s+', ' ', value).strip()


def _strip_html_preserve_lines(value: str) -> str:
    value = _SCRIPT_STYLE_RE.sub('\n', value or '')
    value = re.sub(r'<\s*br\s*/?\s*>', '\n', value, flags=re.I)
    value = re.sub(r'</\s*(p|div|li|tr|h[1-6])\s*>', '\n', value, flags=re.I)
    value = _TAG_RE.sub(' ', value)
    value = _html.unescape(value)
    lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in value.splitlines()]
    return '\n'.join(line for line in lines if line).strip()


def _pretty_job_type(value: str) -> str:
    value = (value or '').strip().lower()
    return value if value in VALID_JOB_TYPES else ''


def _job_source_headers(host_label='AIResumeBuilder/1.0 local job search') -> dict:
    return {
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36 '
            f'{host_label}'
        ),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8',
        'Connection': 'close',
    }


def _indeed_headers(host: str) -> dict:
    headers = _job_source_headers('Indeed')
    headers.update({
        'Accept-Language': 'en-US,en;q=0.9,ja;q=0.8,zh-TW;q=0.7',
        'Referer': f'https://{host}/',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    })
    return headers


def _fetch_text_url(url: str, timeout: int = 10, headers: dict | None = None) -> str:
    req = urllib.request.Request(url, headers=headers or _job_source_headers())
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='ignore')


def _cache_get(cache_key: str):
    now = _time.time()
    with _job_search_lock:
        cached = _job_search_cache.get(cache_key)
        if cached and now - cached['time'] < JOB_SEARCH_CACHE_TTL:
            return cached
    return None


def _cache_set(cache_key: str, **payload):
    with _job_search_lock:
        _job_search_cache[cache_key] = {'time': _time.time(), **payload}


def _absolute_url(base: str, href: str) -> str:
    return urllib.parse.urljoin(base, _html.unescape(href or '').strip())


def _clean_job_text(value) -> str:
    if isinstance(value, list):
        value = ' '.join(str(v) for v in value)
    return _strip_html(str(value or '')).strip()


def _clean_job_description(value, max_length: int = JOB_DESCRIPTION_MAX_LENGTH) -> str:
    return _strip_html_preserve_lines(value or '')[:max_length]


def _regex_first(pattern: str, text: str, default: str = '', flags=re.I | re.S) -> str:
    match = re.search(pattern, text or '', flags)
    return _clean_job_text(match.group(1)) if match else default


def _find_first_key(data, target_key: str):
    if isinstance(data, dict):
        if target_key in data:
            return data[target_key]
        for value in data.values():
            found = _find_first_key(value, target_key)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_first_key(value, target_key)
            if found is not None:
                return found
    return None


def _extract_next_data(raw: str) -> dict:
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">\s*(.*?)\s*</script>', raw or '', re.S)
    if not match:
        return {}
    return json.loads(_html.unescape(match.group(1)))


def _extract_js_assignment_json(raw: str, marker: str) -> dict:
    idx = (raw or '').find(marker)
    if idx < 0:
        return {}
    decoder = json.JSONDecoder()
    payload, _ = decoder.raw_decode(raw[idx + len(marker):].lstrip())
    return payload if isinstance(payload, dict) else {}


def _extract_json_ld(raw: str) -> list[dict]:
    payloads = []
    for match in re.finditer(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>\s*(.*?)\s*</script>', raw or '', re.I | re.S):
        raw_payload = match.group(1)
        try:
            payload = json.loads(raw_payload)
        except json.JSONDecodeError:
            try:
                payload = json.loads(_html.unescape(raw_payload))
            except json.JSONDecodeError:
                continue
        if isinstance(payload, list):
            payloads.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            payloads.append(payload)
    return payloads


def _walk_json_dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json_dicts(child)


def _json_ld_jobposting_description(raw: str) -> str:
    jobposting = _json_ld_jobposting(raw)
    if jobposting and jobposting.get('description'):
        return _clean_job_description(jobposting.get('description'))
    return ''


def _json_ld_jobposting(raw: str) -> dict:
    for payload in _extract_json_ld(raw):
        for item in _walk_json_dicts(payload):
            item_type = item.get('@type')
            if item_type == 'JobPosting' or (isinstance(item_type, list) and 'JobPosting' in item_type):
                return item
    return {}


def _json_value_text(value) -> str:
    if isinstance(value, str):
        return _clean_job_description(value)
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return '\n'.join(part for part in (_json_value_text(item) for item in value) if part)
    if isinstance(value, dict):
        if value.get('@type') == 'MonetaryAmount':
            currency = value.get('currency') or ''
            amount = value.get('value')
            return f'{currency} {_json_value_text(amount)}'.strip()
        if value.get('@type') == 'QuantitativeValue':
            minimum = value.get('minValue')
            maximum = value.get('maxValue')
            unit = value.get('unitText') or ''
            if minimum and maximum:
                return f'{minimum} - {maximum} {unit}'.strip()
            return f"{minimum or maximum or ''} {unit}".strip()
        if value.get('@type') == 'Place':
            return _json_value_text(value.get('address'))
        if value.get('@type') == 'PostalAddress':
            return ' '.join(str(value.get(key) or '') for key in ('addressCountry', 'addressRegion', 'addressLocality', 'streetAddress')).strip()
        return '\n'.join(part for part in (_json_value_text(item) for item in value.values()) if part)
    return ''


def _extract_jobposting_sections(raw: str, fields: tuple[tuple[str, str], ...]) -> str:
    jobposting = _json_ld_jobposting(raw)
    if not jobposting:
        return ''
    parts = []
    for label, key in fields:
        value = _json_value_text(jobposting.get(key))
        if value and value.lower() != 'null～null':
            parts.append(f'{label}\n{value}')
    return '\n\n'.join(parts)


def _extract_meta_content(raw: str, name: str) -> str:
    patterns = (
        rf'<meta[^>]+property=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']',
        rf'<meta[^>]+name=["\']{re.escape(name)}["\'][^>]+content=["\'](.*?)["\']',
    )
    for pattern in patterns:
        value = _regex_first(pattern, raw)
        if value:
            return value
    return ''


def _extract_daijob_detail_description(raw: str) -> str:
    parts = []
    for match in re.finditer(
        r'<section class="job-section">.*?'
        r'<span class="job-section__label">\s*(.*?)\s*</span>.*?'
        r'<div class="job-section__body">\s*(.*?)\s*</div>\s*</section>',
        raw or '',
        re.I | re.S,
    ):
        label, body = match.groups()
        label = _clean_job_text(label)
        body = _clean_job_description(body)
        if label and body:
            parts.append(f'{label}\n{body}')
    return '\n\n'.join(parts)


def _extract_careercross_detail_description(raw: str) -> str:
    parts = []
    description = _regex_first(r'<span id="jsonld-description">\s*(.*?)\s*</span>', raw)
    if description:
        parts.append(f'Job Description\n{description}')

    def table_rows_after_heading(heading: str) -> list[str]:
        rows = []
        table = re.search(rf'<h2>\s*{re.escape(heading)}\s*</h2>\s*<table[^>]*>(.*?)</table>', raw or '', re.I | re.S)
        if not table:
            return rows
        for row in re.finditer(r'<tr[^>]*>(.*?)</tr>', table.group(1), re.I | re.S):
            cells = re.findall(r'<td[^>]*>(.*?)</td>', row.group(1), re.I | re.S)
            if len(cells) >= 2:
                label = _clean_job_text(cells[0])
                value = _clean_job_text(cells[1])
                if label and value:
                    rows.append(f'{label}: {value}')
        return rows

    requirements = table_rows_after_heading('General Requirements')
    if requirements:
        parts.append('General Requirements\n' + '\n'.join(requirements))

    required_skills = _regex_first(r'<h2>\s*Required Skills\s*</h2>\s*<span[^>]*id="qualifications-required-skills"[^>]*>\s*(.*?)\s*</span>', raw)
    if required_skills:
        parts.append(f'Required Skills\n{required_skills}')

    location_block = re.search(r'<h2>\s*Job Location\s*</h2>\s*(.*?)\s*<h2>', raw or '', re.I | re.S)
    if location_block:
        location = _clean_job_text(location_block.group(1))
        if location:
            parts.append(f'Job Location\n{location}')

    work_conditions = table_rows_after_heading('Work Conditions')
    if work_conditions:
        parts.append('Work Conditions\n' + '\n'.join(work_conditions))

    category_block = re.search(r'<h2>\s*Job Category\s*</h2>\s*(.*?)(?:</div>\s*</div>|<h2>)', raw or '', re.I | re.S)
    if category_block:
        categories = _clean_job_text(category_block.group(1))
        if categories:
            parts.append(f'Job Category\n{categories}')

    other_sections = []
    for heading, element_id in (
        ('Other Salary Description', 'benefits-other-salary-description'),
    ):
        value = _regex_first(rf'id="{re.escape(element_id)}"[^>]*>\s*(.*?)\s*</span>', raw)
        if value:
            other_sections.append(f'{heading}: {value}')
    if other_sections:
        parts.append('Additional Conditions\n' + '\n'.join(other_sections))

    return '\n\n'.join(parts)

def _extract_michael_page_detail_description(raw: str) -> str:
    block_match = re.search(r'<div id="job-description">(.*?)<div id="summary"', raw or '', re.I | re.S)
    if block_match:
        return _clean_job_description(block_match.group(1))
    return _json_ld_jobposting_description(raw)


def _extract_green_detail_description(raw: str) -> str:
    return _extract_jobposting_sections(raw, (
        ('Job Description', 'description'),
        ('Requirements', 'experienceRequirements'),
        ('Benefits', 'jobBenefits'),
        ('Work Hours', 'workHours'),
        ('Salary', 'baseSalary'),
        ('Location', 'jobLocation'),
        ('Appeal', 'incentiveCompensation'),
    ))


def _extract_mynavi_detail_description(raw: str) -> str:
    return _extract_jobposting_sections(raw, (
        ('Job Description', 'description'),
        ('Requirements', 'experienceRequirements'),
        ('Work Hours', 'workHours'),
        ('Benefits', 'jobBenefits'),
        ('Salary', 'baseSalary'),
        ('Location', 'jobLocation'),
    ))


def _extract_wantedly_detail_description(raw: str) -> str:
    try:
        data = _extract_next_data(raw)
    except json.JSONDecodeError:
        data = {}

    candidates = []
    for item in _walk_json_dicts(data):
        if item.get('__typename') == 'JobPost' and item.get('id'):
            score = sum(1 for key in ('whatDescription', 'whyDescription', 'howDescription', 'detailDescription') if item.get(key))
            if score:
                candidates.append((score, item))
    if not candidates:
        return _json_ld_jobposting_description(raw)

    jobpost = sorted(candidates, key=lambda pair: pair[0], reverse=True)[0][1]
    parts = []
    section_map = (
        ('What We Do', 'whatDescription'),
        ('Why We Do It', 'whyDescription'),
        ('How We Work', 'howDescription'),
        ('Role Details', 'detailDescription'),
    )
    for label, key in section_map:
        section = jobpost.get(key) or {}
        body = section.get('body') if isinstance(section, dict) else ''
        body = _clean_job_description(body)
        if body:
            parts.append(f'{label}\n{body}')

    extras = []
    occupation = _clean_job_text(jobpost.get('occupationName'))
    if occupation:
        extras.append(f'Occupation: {occupation}')
    location = jobpost.get('location') or {}
    if isinstance(location, dict):
        location_text = _clean_job_text(' '.join(str(location.get(key) or '') for key in ('prefecture', 'line1', 'line2')))
        if location_text:
            extras.append(f'Location: {location_text}')
    labels = [item.get('label') for item in jobpost.get('hiringTypes') or [] if isinstance(item, dict) and item.get('label')]
    labels.extend(item.get('label') for item in jobpost.get('featureTags') or [] if isinstance(item, dict) and item.get('label'))
    if labels:
        extras.append(f"Tags: {', '.join(labels)}")
    if extras:
        parts.append('Posting Details\n' + '\n'.join(extras))

    return '\n\n'.join(parts)


def _extract_linkedin_detail_description(raw: str) -> str:
    parts = []
    description = _regex_first(
        r'<div[^>]+class="[^"]*show-more-less-html__markup[^"]*"[^>]*>\s*(.*?)\s*</div>',
        raw,
    )
    if description:
        parts.append(f'Job Description\n{description}')

    criteria = []
    for item in re.finditer(r'<li[^>]+class="[^"]*description__job-criteria-item[^"]*"[^>]*>(.*?)</li>', raw or '', re.I | re.S):
        block = item.group(1)
        label = _regex_first(r'<h3[^>]*>\s*(.*?)\s*</h3>', block)
        value = _regex_first(r'<span[^>]+class="[^"]*description__job-criteria-text[^"]*"[^>]*>\s*(.*?)\s*</span>', block)
        if label and value:
            criteria.append(f'{label}: {value}')
    if criteria:
        parts.append('Job Criteria\n' + '\n'.join(criteria))

    posted = _regex_first(r'class="[^"]*posted-time-ago__text[^"]*"[^>]*>\s*(.*?)\s*</span>', raw)
    if posted:
        parts.append(f'Posted\n{posted}')
    return '\n\n'.join(parts)


def _extract_indeed_detail_description(raw: str) -> str:
    try:
        data = _extract_js_assignment_json(raw, 'window._initialData=')
    except json.JSONDecodeError:
        data = {}

    for item in _walk_json_dicts(data):
        description = item.get('description') if isinstance(item, dict) else None
        if isinstance(description, dict):
            html_description = description.get('html') or description.get('text')
            if html_description:
                return _clean_job_description(html_description)

    sanitized = _find_first_key(data, 'sanitizedJobDescription') if data else ''
    if sanitized:
        return _clean_job_description(sanitized)

    description = _regex_first(
        r'<div[^>]+id=["\']jobDescriptionText["\'][^>]*>\s*(.*?)\s*</div>',
        raw,
    )
    if description:
        return _clean_job_description(description)
    return ''


def _extract_dice_detail_description(raw: str) -> str:
    description = _json_ld_jobposting_description(raw)
    if description:
        return description
    block_match = re.search(
        r'<div[^>]+class="[^"]*job-detail-description[^"]*"[^>]*>\s*(.*?)(?:</div>\s*</div>\s*<div|<h3|<section|</main>)',
        raw or '',
        re.I | re.S,
    )
    if block_match:
        return _clean_job_description(block_match.group(1))
    return ''


def _extract_rgf_detail_description(raw: str) -> str:
    block_match = re.search(
        r'<div class="lg:mt-25 mt-20 custom-cms">(.*?)(?:<section|<aside|<footer|</main>)',
        raw or '',
        re.I | re.S,
    )
    if block_match:
        return _clean_job_description(block_match.group(1))
    return _extract_meta_content(raw, 'og:description')[:JOB_DESCRIPTION_MAX_LENGTH]


def _extract_detail_page_description(job: dict, raw: str) -> str:
    source = str(job.get('source') or '').strip().lower()
    if source == 'daijob':
        description = _extract_daijob_detail_description(raw)
    elif source == 'careercross':
        description = _extract_careercross_detail_description(raw)
    elif source == 'michael page':
        description = _extract_michael_page_detail_description(raw)
    elif source == 'green':
        description = _extract_green_detail_description(raw)
    elif source == 'mynavi tenshoku':
        description = _extract_mynavi_detail_description(raw)
    elif source == 'wantedly':
        description = _extract_wantedly_detail_description(raw)
    elif source == 'linkedin':
        description = _extract_linkedin_detail_description(raw)
    elif source == 'indeed':
        description = _extract_indeed_detail_description(raw)
    elif source == 'dice':
        description = _extract_dice_detail_description(raw)
    elif source == 'rgf professional':
        description = _extract_rgf_detail_description(raw)
    else:
        description = _json_ld_jobposting_description(raw)

    if not description:
        description = _json_ld_jobposting_description(raw)
    if not description:
        description = _extract_meta_content(raw, 'description')
    return _clean_job_description(description)


def _fetch_detail_page_description(job: dict) -> str:
    url = str(job.get('url') or '').strip()
    if not url:
        return ''
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != 'https' or parsed.netloc.lower() not in ALLOWED_JOB_DETAIL_HOSTS:
        return ''
    cache_key = f"job-detail-description:{url}"
    cached = _cache_get(cache_key)
    if cached:
        return cached.get('description', '')
    description = ''
    try:
        detail_url = url
        if str(job.get('source') or '').strip().lower() == 'linkedin':
            raw_id = str(job.get('id') or '').removeprefix('linkedin-')
            if raw_id.isdigit():
                detail_url = LINKEDIN_DETAIL_URL.format(job_id=urllib.parse.quote(raw_id))
        if str(job.get('source') or '').strip().lower() == 'indeed':
            headers = _indeed_headers(urllib.parse.urlparse(detail_url).netloc)
        else:
            headers = _job_source_headers(str(job.get('source') or 'JobDetail'))
        raw = _fetch_text_url(detail_url, timeout=10, headers=headers)
        description = _extract_detail_page_description(job, raw)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.info('Job detail description unavailable for %s: %s', url, exc)
    _cache_set(cache_key, description=description)
    return description


def _enrich_job_descriptions(jobs: list[dict], limit: int = JOB_DETAIL_ENRICH_LIMIT) -> list[dict]:
    candidates = [
        job for job in jobs[:limit]
        if job.get('url') and job.get('source') in {
            'Japan Dev', 'Daijob', 'CareerCross', 'Green', 'Mynavi Tenshoku',
            'Wantedly', 'Michael Page', 'RGF Professional', 'LinkedIn', 'Indeed', 'Dice'
        }
    ]
    if not candidates:
        return jobs

    enriched_by_id = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(candidates))) as executor:
        futures = {executor.submit(_fetch_detail_page_description, job): job for job in candidates}
        for future in concurrent.futures.as_completed(futures):
            job = futures[future]
            try:
                description = future.result()
            except Exception as exc:
                logger.info('Job detail enrichment failed for %s: %s', job.get('url'), exc)
                continue
            if len(description) > len(job.get('description') or '') + 40:
                enriched = dict(job)
                enriched['description'] = description[:JOB_DESCRIPTION_MAX_LENGTH]
                enriched['description_source'] = 'detail-page'
                enriched_by_id[enriched.get('id')] = enriched

    return [enriched_by_id.get(job.get('id'), job) for job in jobs]


def _epoch_to_date(value) -> str:
    try:
        timestamp = int(value)
    except (TypeError, ValueError):
        return ''
    if timestamp > 10_000_000_000:
        timestamp = timestamp // 1000
    try:
        return datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()
    except (OSError, OverflowError, ValueError):
        return ''


def _iso_to_date(value: str) -> str:
    value = str(value or '').strip()
    if not value:
        return ''
    return value.split('T')[0].split(' ')[0]


def _map_job_type(value: str) -> str:
    normalized = re.sub(r'[\s_-]+', ' ', (value or '').strip().lower())
    if not normalized:
        return ''
    if any(term in normalized for term in ('full time', 'full-time', '正社員', 'permanent', 'mid career')):
        return 'full_time'
    if any(term in normalized for term in ('contract', 'contractor', '契約', '業務委託')):
        return 'contract'
    if any(term in normalized for term in ('part time', 'part-time', 'アルバイト', 'パート')):
        return 'part_time'
    if any(term in normalized for term in ('freelance', 'フリーランス', 'side job', '副業')):
        return 'freelance'
    if any(term in normalized for term in ('intern', 'インターン', '学生')):
        return 'internship'
    return ''


def _japan_location(value: str) -> str:
    value = _clean_job_text(value)
    return f'Japan - {value}' if value and 'japan' not in value.lower() and '日本' not in value else (value or 'Japan')


def _infer_japanese_requirement(job: dict) -> str:
    text = ' '.join(str(job.get(k, '')) for k in (
        'title', 'company', 'location', 'category', 'job_type', 'description', 'search_terms'
    ))
    text = re.sub(r'\s+', ' ', text or '').strip()
    lower = text.lower()
    source = str(job.get('source') or '').strip().lower()
    category = str(job.get('category') or '').strip().lower()

    if source == 'daijob':
        if 'native level' in category or 'jlpt level 1' in category or re.search(r'\bn1\b', category):
            return 'Fluent Japanese required'
        if 'business level' in category or 'jlpt level 2' in category or re.search(r'\bn2\b', category):
            return 'Business Japanese required'
        if 'daily conversation' in category or 'conversation level' in category:
            return 'Japanese required'

    no_japanese_patterns = (
        r'\bno japanese (?:language )?(?:required|needed)\b',
        r'\bjapanese (?:language )?(?:not required|not needed|unnecessary)\b',
        r'日本語(?:不要|不問|必要なし)',
    )
    if any(re.search(pattern, lower if '\\b' in pattern else text, re.I) for pattern in no_japanese_patterns):
        return 'No Japanese required'

    fluent_patterns = (
        r'\b(?:native|fluent)\s+japanese\b',
        r'\bjapanese\s+(?:native|fluent|fluency)\b',
        r'\b(?:jlpt\s*)?n1\b',
        r'日本語[^。,\n]*(?:ネイティブ|流暢|上級|N1)',
        r'(?:ネイティブ|流暢|上級|N1)[^。,\n]*日本語',
    )
    if any(re.search(pattern, text, re.I) for pattern in fluent_patterns):
        return 'Fluent Japanese required'

    business_patterns = (
        r'\bbusiness (?:level )?japanese\b',
        r'\bjapanese\s+business (?:level)?\b',
        r'\b(?:jlpt\s*)?n2\b',
        r'日本語[^。,\n]*(?:ビジネス|N2)',
        r'(?:ビジネス|N2)[^。,\n]*日本語',
    )
    if any(re.search(pattern, text, re.I) for pattern in business_patterns):
        return 'Business Japanese required'

    required_patterns = (
        r'\bjapanese (?:language )?(?:required|needed|mandatory)\b',
        r'\brequires japanese\b',
        r'日本語[^。,\n]*(?:必須|必要)',
        r'(?:必須|必要)[^。,\n]*日本語',
    )
    if any(re.search(pattern, text, re.I) for pattern in required_patterns):
        return 'Japanese required'

    return ''


def _infer_security_clearance(job: dict) -> str:
    text = ' '.join(str(job.get(k, '')) for k in (
        'title', 'company', 'location', 'category', 'job_type', 'description', 'search_terms', 'search_location'
    ))
    text = re.sub(r'\s+', ' ', text or '').strip()
    if not text:
        return ''
    lower = text.lower()

    no_clearance_patterns = (
        r'\bno (?:security )?clearance (?:required|needed)\b',
        r'\b(?:security )?clearance (?:is )?(?:not required|not needed)\b',
    )
    if any(re.search(pattern, lower, re.I) for pattern in no_clearance_patterns):
        return ''

    location_text = ' '.join(str(job.get(k, '')) for k in ('location', 'search_location')).lower()
    us_context = (
        any(term in location_text for term in _country_aliases('united_states')) or
        any(term in lower for term in ('u.s. citizen', 'us citizen', 'dod', 'department of defense', 'federal government'))
    )
    if not us_context:
        return ''

    hard_required_context = (
        r'(?:required|must|eligible|ability to obtain|ability to maintain|obtain and maintain)',
        r'(?:requires|requirement|eligibility)',
    )
    required_context = hard_required_context + (
        r'(?:active|current|existing)',
    )
    hard_required_near_clearance = any(
        re.search(rf'{ctx}.{{0,80}}(?:clearance|public trust|ts/sci|sci|polygraph|secret)', lower, re.I) or
        re.search(rf'(?:clearance|public trust|ts/sci|sci|polygraph|secret).{{0,80}}{ctx}', lower, re.I)
        for ctx in hard_required_context
    )
    required_near_clearance = any(
        re.search(rf'{ctx}.{{0,80}}(?:clearance|public trust|ts/sci|sci|polygraph|secret)', lower, re.I) or
        re.search(rf'(?:clearance|public trust|ts/sci|sci|polygraph|secret).{{0,80}}{ctx}', lower, re.I)
        for ctx in required_context
    )
    preferred_only = (
        not hard_required_near_clearance and
        (
            re.search(r'\b(?:preferred|desired|nice to have|plus)\b.{0,80}(?:clearance|public trust|ts/sci|sci|polygraph|secret)', lower, re.I) or
            re.search(r'(?:clearance|public trust|ts/sci|sci|polygraph|secret).{0,80}\b(?:preferred|desired|nice to have|plus)\b', lower, re.I)
        )
    )
    if preferred_only:
        return ''

    if re.search(r'\bts\s*/\s*sci\b|\btop secret\s*/\s*sci\b', lower):
        return 'TS/SCI clearance required'
    if re.search(r'\btop secret\b', lower):
        return 'Top Secret clearance required'
    if re.search(r'\bpublic trust\b', lower):
        return 'Public Trust required'
    if re.search(r'\b(?:active|current|existing)\s+secret\b|\bsecret\s+(?:clearance|level)\b', lower):
        return 'Secret clearance required'
    if re.search(r'\b(?:security )?clearance\b|\bpolygraph\b', lower):
        if re.search(r'\b(?:ability to obtain|ability to maintain|obtain and maintain|eligible for)\b', lower):
            return 'Clearance eligibility required'
        return 'Security clearance required'
    return ''


def _normalize_us_city(value: str) -> str:
    value = re.sub(r'\([^)]*\)', ' ', value or '')
    value = re.sub(r'\b(?:remote|hybrid|onsite|on-site|greater|metro area|area)\b', ' ', value, flags=re.I)
    value = re.sub(r'\b\d{5}(?:-\d{4})?\b', ' ', value)
    value = re.sub(r'[^a-zA-Z .-]+', ' ', value)
    value = re.sub(r'\s+', ' ', value).strip().lower()
    return value.replace('.', '').replace('-', ' ')


def _extract_us_city(location: str) -> str:
    location = re.sub(r'\s+', ' ', location or '').strip()
    if not location or re.fullmatch(r'(?i)(?:remote|united states|usa|u\.s\.|us|north america|americas)', location):
        return ''
    first_location = re.split(r'\s*(?:;|\||/|\bor\b)\s*', location, maxsplit=1, flags=re.I)[0].strip()
    parts = [part.strip() for part in first_location.split(',') if part.strip()]
    if len(parts) >= 2:
        state_part = _normalize_us_city(parts[1])
        state = re.sub(r'[^A-Za-z]', '', parts[1].split()[0] if parts[1].split() else '').lower()
        if state in US_STATE_ABBREVIATIONS or state_part in US_STATE_NAMES or any(term in parts[1].lower() for term in ('united states', 'usa', 'u.s.')):
            candidate = _normalize_us_city(parts[0])
            if candidate in US_PUBLIC_SAFETY_CITY_SCORES:
                return candidate
            for city in sorted(US_PUBLIC_SAFETY_CITY_SCORES, key=len, reverse=True):
                if re.search(rf'\b{re.escape(city)}\b', candidate, re.I):
                    return city
            return candidate
    for city in sorted(US_PUBLIC_SAFETY_CITY_SCORES, key=len, reverse=True):
        if re.search(rf'\b{re.escape(city)}\b', first_location, re.I):
            return city
    return ''


def _infer_us_public_safety(job: dict) -> dict:
    location_text = ' '.join(str(job.get(k, '')) for k in ('location', 'search_location')).strip()
    location_lower = location_text.lower()
    us_context = any(term in location_lower for term in _country_aliases('united_states'))
    if not us_context:
        parts = [part.strip() for part in re.split(r'[, ]+', location_text) if part.strip()]
        normalized_location = _normalize_us_city(location_text)
        us_context = (
            any(part.lower().rstrip('.') in US_STATE_ABBREVIATIONS for part in parts) or
            any(re.search(rf'\b{re.escape(state)}\b', normalized_location) for state in US_STATE_NAMES)
        )
    if not us_context:
        return {}

    city = _extract_us_city(str(job.get('location') or '')) or _extract_us_city(str(job.get('search_location') or ''))
    if not city:
        return {}
    score = US_PUBLIC_SAFETY_CITY_SCORES.get(city, 3)
    labels = {
        5: 'Great public safety',
        4: 'Good public safety',
        3: 'Moderate public safety',
        2: 'Elevated safety risk',
        1: 'Higher safety risk',
    }
    return {
        'public_safety_city': city.title(),
        'public_safety_score': score,
        'public_safety_label': labels[score],
    }


def _annotate_job_metadata(job: dict) -> dict:
    normalized = dict(job)
    if not normalized.get('japanese_requirement'):
        normalized['japanese_requirement'] = _infer_japanese_requirement(normalized)
    if not normalized.get('security_clearance'):
        normalized['security_clearance'] = _infer_security_clearance(normalized)
    if not normalized.get('public_safety_score'):
        normalized.update(_infer_us_public_safety(normalized))
    return normalized



def _job_text(job: dict) -> str:
    return ' '.join(str(job.get(k, '')) for k in (
        'title', 'company', 'location', 'category', 'job_type', 'description',
        'japanese_requirement', 'security_clearance', 'search_terms'
    )).lower()


def _job_title_matches(job: dict, title: str) -> bool:
    title = re.sub(r'\s+', ' ', title or '').strip().lower()
    if not title:
        return True
    tokens = [t for t in re.split(r'[^a-z0-9+#.]+', title) if t]
    tokens.extend(re.findall(r'[\u3400-\u9fff]+', title))
    if not tokens:
        return title in _job_text(job)
    if job.get('strict_title_match'):
        haystack = ' '.join(str(job.get(k, '')) for k in (
            'title', 'company', 'category', 'job_type', 'location', 'search_terms'
        )).lower()
    else:
        haystack = _job_text(job)
    return all(token in haystack for token in tokens)


def _country_aliases(country: str) -> tuple[str, ...]:
    return {
        'united_states': ('united states', 'usa', 'u.s.', 'us only', 'america', 'americas', 'north america'),
        'japan': (
            'japan', 'tokyo', 'osaka', 'kyoto', 'yokohama', 'nagoya', 'fukuoka',
            'sapporo', 'kobe', '日本', '東京', '大阪', '京都', '横浜', '名古屋', '福岡',
            '札幌', '神戸', 'asia', 'apac'
        ),
        'taiwan': (
            'taiwan', 'taipei', 'taichung', 'kaohsiung', 'tainan', 'hsinchu',
            '台灣', '臺灣', '台北', '臺北', '新北', '桃園', '台中', '臺中', '台南', '臺南',
            '高雄', '新竹', 'asia', 'apac'
        ),
    }.get(country, ())


def _job_location_matches(job: dict, country: str, location: str) -> bool:
    query = re.sub(r'\s+', ' ', location or '').strip().lower()
    job_location = ' '.join(str(job.get(k, '')) for k in ('location', 'search_location')).lower()
    remote_terms = {'remote', 'anywhere', 'worldwide', 'global'}
    if query in remote_terms:
        return True

    if country == 'any' and not query:
        target_terms = set()
        for target_country in ('united_states', 'japan', 'taiwan'):
            target_terms.update(_country_aliases(target_country))
        return (
            any(term in job_location for term in target_terms) or
            any(term in job_location for term in ('worldwide', 'global', 'anywhere'))
        )

    if country != 'any':
        country_terms = _country_aliases(country)
        country_match = any(term in job_location for term in country_terms)
        global_match = any(term in job_location for term in ('worldwide', 'global', 'anywhere'))
        if not country_match and not global_match:
            return False
        if not query:
            return True
        city_aliases = {
            'taipei': ('taipei', '台北', '臺北', 'new taipei', '新北'),
            'taichung': ('taichung', '台中', '臺中'),
            'kaohsiung': ('kaohsiung', '高雄'),
            'tainan': ('tainan', '台南', '臺南'),
            'hsinchu': ('hsinchu', '新竹'),
            'tokyo': ('tokyo', '東京'),
            'osaka': ('osaka', '大阪'),
            'kyoto': ('kyoto', '京都'),
            'yokohama': ('yokohama', '横浜'),
            'nagoya': ('nagoya', '名古屋'),
            'fukuoka': ('fukuoka', '福岡'),
            'sapporo': ('sapporo', '札幌'),
            'kobe': ('kobe', '神戸'),
            'irvine': ('irvine',),
            'new york': ('new york',),
            'san francisco': ('san francisco',),
            'los angeles': ('los angeles',),
        }.get(query, (query,))
        return global_match or any(term in job_location for term in city_aliases)

    aliases = {
        'us': ('united states', 'usa', 'u.s.', 'us only', 'america', 'americas', 'north america'),
        'usa': ('united states', 'usa', 'u.s.', 'us only', 'america', 'americas', 'north america'),
        'united states': ('united states', 'usa', 'u.s.', 'us only', 'america', 'americas', 'north america'),
        'uk': ('united kingdom', 'uk', 'great britain', 'england'),
        'united kingdom': ('united kingdom', 'uk', 'great britain', 'england'),
        'eu': ('europe', 'european union', 'eu'),
        'japan': ('japan', 'tokyo', 'osaka', 'kyoto', 'yokohama', 'nagoya', 'fukuoka', '日本', '東京', '大阪', '京都', '横浜', '名古屋', '福岡', 'asia', 'apac'),
        'tokyo': ('tokyo', 'japan', 'asia', 'apac'),
        'osaka': ('osaka', 'japan', 'asia', 'apac'),
        'kyoto': ('kyoto', 'japan', 'asia', 'apac'),
        'yokohama': ('yokohama', 'japan', 'asia', 'apac'),
        'nagoya': ('nagoya', 'japan', 'asia', 'apac'),
        'fukuoka': ('fukuoka', 'japan', 'asia', 'apac'),
        'sapporo': ('sapporo', 'japan', 'asia', 'apac'),
        'kobe': ('kobe', 'japan', 'asia', 'apac'),
        'taiwan': ('taiwan', 'taipei', 'kaohsiung', 'asia', 'apac'),
        'taipei': ('taipei', 'taiwan', 'asia', 'apac'),
        'kaohsiung': ('kaohsiung', 'taiwan', 'asia', 'apac'),
        'taichung': ('taichung', 'taiwan', 'asia', 'apac'),
        'tainan': ('tainan', 'taiwan', 'asia', 'apac'),
        'hsinchu': ('hsinchu', 'taiwan', 'asia', 'apac'),
        'canada': ('canada', 'americas', 'north america'),
        'mexico': ('mexico', 'americas', 'north america', 'latin america'),
        'australia': ('australia', 'oceania', 'apac'),
        'new zealand': ('new zealand', 'oceania', 'apac'),
    }
    candidates = aliases.get(query, (query,))
    if any(candidate in job_location for candidate in candidates):
        return True

    # Worldwide listings are valid when the user gives a specific location.
    if any(term in job_location for term in ('worldwide', 'global', 'anywhere')):
        return True

    tokens = [t for t in re.split(r'[^a-z0-9]+', query) if len(t) > 1]
    return bool(tokens) and all(token in job_location for token in tokens)


def _filter_jobs(jobs: list[dict], title: str, country: str, location: str, job_type: str, limit: int = 180) -> list[dict]:
    matched = []
    for job in jobs:
        if not _job_title_matches(job, title):
            continue
        if not _job_location_matches(job, country, location):
            continue
        if job_type != 'any' and job.get('job_type') != job_type:
            continue
        matched.append(job)
    if len(matched) <= limit:
        return matched

    buckets = {}
    for job in matched:
        source = job.get('source') or 'Unknown'
        buckets.setdefault(source, []).append(job)

    filtered = []
    source_order = list(buckets.keys())
    while len(filtered) < limit and source_order:
        next_order = []
        for source in source_order:
            bucket = buckets[source]
            if bucket:
                filtered.append(bucket.pop(0))
                if len(filtered) >= limit:
                    break
            if bucket:
                next_order.append(source)
        source_order = next_order
    return filtered


def _fallback_jobs(search: str = '') -> list[dict]:
    jobs = [dict(job) for job in FALLBACK_JOBS]
    return [job for job in jobs if _job_title_matches(job, search)]


def _dedupe_jobs(jobs: list[dict]) -> list[dict]:
    seen = set()
    deduped = []
    for job in jobs:
        key = (job.get('url') or job.get('id') or '').strip().lower()
        if not key:
            key = f"{job.get('source', '')}:{job.get('company', '')}:{job.get('title', '')}".lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(job)
    return deduped




def safe_screenshot_path(filename: str) -> str:
    if not _SAFE_SCREENSHOT_NAME.match(filename):
        raise ValueError('Invalid screenshot filename')
    return os.path.join(OUTPUT_DIR, filename)

__all__ = [name for name in globals() if not name.startswith('__')]
