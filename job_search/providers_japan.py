from .core import *
from .providers_ats import _fetch_lever_board, _fetch_workable_board
from .providers_generic import _fetch_generic_board

def _parse_gaijinpot_summary(summary: str) -> tuple[str, str, str]:
    summary = _clean_job_text(summary)
    category = ''
    location = 'Japan'
    company = ''

    match = re.match(r'(.+?)\s+position in\s+(.+?)\s+at\s+(.+)$', summary, flags=re.I)
    if match:
        category = match.group(1).strip()
        location = match.group(2).strip()
        company = match.group(3).strip()
    else:
        at_match = re.search(r'\s+at\s+(.+)$', summary, flags=re.I)
        if at_match:
            company = at_match.group(1).strip()
        in_match = re.search(r'\s+in\s+(.+?)(?:\s+at\s+|$)', summary, flags=re.I)
        if in_match:
            location = in_match.group(1).strip()

    return company, location, category


def _fetch_gaijinpot_jobs(search: str, location: str = '', limit: int = 40) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"gaijinpot:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    params = {}
    if keyword:
        params['keywords'] = keyword
    url = GAIJINPOT_FEED_URL if not params else f'{GAIJINPOT_FEED_URL}?{urllib.parse.urlencode(params)}'

    jobs = []
    error = None
    try:
        raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('GaijinPot'))
        root = ET.fromstring(raw)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.findall('atom:entry', ns)[:limit]:
            title = _clean_job_text(entry.findtext('atom:title', default='', namespaces=ns))
            summary = entry.findtext('atom:summary', default='', namespaces=ns) or ''
            company, job_location, category = _parse_gaijinpot_summary(summary)
            link_el = entry.find('atom:link', ns)
            link = (link_el.attrib.get('href') if link_el is not None else '') or entry.findtext('atom:id', default='', namespaces=ns)
            content_el = entry.find('atom:content', ns)
            description = ''.join(content_el.itertext()) if content_el is not None else summary
            posted_at = (entry.findtext('atom:published', default='', namespaces=ns) or '').split('T')[0]
            job_id = link.rstrip('/').split('/')[-1] if link else uuid.uuid4().hex[:10]

            normalized = {
                'id': f'gaijinpot-{job_id}',
                'title': title,
                'company': company,
                'location': job_location or 'Japan',
                'job_type': '',
                'category': category,
                'salary': '',
                'posted_at': posted_at,
                'description': _clean_job_description(description),
                'url': link,
                'source': 'GaijinPot',
                'search_terms': keyword,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ET.ParseError, OSError) as exc:
        logger.warning('GaijinPot job search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_japan_dev_tag(block: str, icon_name: str) -> str:
    return _regex_first(
        rf'{re.escape(icon_name)}[^>]*>.*?<div class="job__tag-desc">\s*(.*?)\s*</div>',
        block,
    )


def _fetch_japan_dev_jobs(search: str, location: str = '', limit: int = 60) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"japan-dev:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    params = {'keywords': keyword} if keyword else {}
    url = JAPAN_DEV_JOBS_URL if not params else f'{JAPAN_DEV_JOBS_URL}?{urllib.parse.urlencode(params)}'
    jobs = []
    error = None
    try:
        raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('JapanDev'))
        cards = re.split(r'<li class="job-item"', raw)[1:]
        for idx, card in enumerate(cards[:limit]):
            block = f'<li class="job-item"{card}'
            title_match = re.search(r'<a href="([^"]+)"[^>]*class="job-item__title"[^>]*>(.*?)</a>', block, flags=re.I | re.S)
            if not title_match:
                continue
            href, raw_title = title_match.groups()
            title = _clean_job_text(raw_title)
            link = _absolute_url('https://japan-dev.com', href)
            contract = _regex_first(r'class="job-item__contract-type"[^>]*>(.*?)</div>', block)
            logo_company = _regex_first(r'class="company-logo__inner"[^>]*alt="([^"]+)"', block)
            company = logo_company or contract.split('・')[0].strip()
            category = contract.split('・', 1)[1].strip() if '・' in contract else ''
            job_location = _extract_japan_dev_tag(block, 'location-icon') or 'Japan'
            salary = _extract_japan_dev_tag(block, 'salary-gray.svg') or _extract_japan_dev_tag(block, 'yen-icon-simple')
            tags = [_clean_job_text(tag) for tag in re.findall(r'class="job-top-tag-list__job-top-tag"[^>]*>.*?<span[^>]*>(.*?)</span>', block, flags=re.I | re.S)]
            technologies = [_clean_job_text(tag) for tag in re.findall(r'class="technology-list__technology"[^>]*>.*?<a[^>]*>(.*?)</a>', block, flags=re.I | re.S)]
            tags = [tag for tag in tags + technologies if tag]
            posted_at = 'NEW' if 'new-indicator' in block and 'NEW!' in block else ''
            description_parts = [contract, f"Tags: {', '.join(tags)}" if tags else '', f"Salary: {salary}" if salary else '']

            normalized = {
                'id': f'japan-dev-{link.rstrip("/").split("/")[-1] or idx}',
                'title': title,
                'company': company,
                'location': job_location,
                'job_type': 'full_time',
                'category': category or ', '.join(tags[:3]),
                'salary': salary,
                'posted_at': posted_at,
                'description': _clean_job_description('\n'.join(part for part in description_parts if part)),
                'url': link,
                'source': 'Japan Dev',
                'search_terms': keyword,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Japan Dev job search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_daijob_detail(card: str, label: str) -> str:
    pattern = rf'<dt>\s*<span>\s*{re.escape(label)}\s*</span>\s*</dt>\s*<dd>\s*(.*?)\s*</dd>'
    return _regex_first(pattern, card)


def _fetch_daijob_jobs(search: str, location: str = '', limit: int = 40, pages: int = 2) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"daijob:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        for page in range(1, pages + 1):
            params = {'job_search_form_hidden': '1', 'page': str(page)}
            if keyword:
                params['keywords'] = keyword
            url = f'{DAIJOB_SEARCH_URL}?{urllib.parse.urlencode(params)}'
            raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('Daijob'))
            cards = re.split(r'<div class="job-card-wrap">', raw)[1:]
            if not cards:
                break
            for card in cards:
                title_match = re.search(r'class="job-card__title[^"]*"[^>]*>\s*<a href="([^"]+)"[^>]*>(.*?)</a>', card, flags=re.I | re.S)
                if not title_match:
                    continue
                href, raw_title = title_match.groups()
                link = _absolute_url('https://www.daijob.com', href)
                job_id = link.rstrip('/').split('/')[-1] if link else uuid.uuid4().hex[:10]
                company = _extract_daijob_detail(card, 'Company') or _extract_daijob_detail(card, 'Recruiter')
                if not company or 'publicly visible' in company.lower():
                    company = _regex_first(r'<img[^>]*alt="([^"]+)"', card) or company
                location_text = _extract_daijob_detail(card, 'Location') or 'Japan'
                salary = _extract_daijob_detail(card, 'Salary')
                japanese_level = _extract_daijob_detail(card, 'Japanese Level')
                description = _extract_daijob_detail(card, 'Job Description')
                posted_at = 'NEW' if 'badge--new' in card else ''

                normalized = {
                    'id': f'daijob-{job_id}',
                    'title': _clean_job_text(raw_title),
                    'company': company or 'Daijob employer',
                    'location': location_text,
                    'job_type': '',
                    'category': japanese_level,
                    'salary': salary,
                    'posted_at': posted_at,
                    'description': _clean_job_description(description),
                    'url': link,
                    'source': 'Daijob',
                    'search_terms': keyword,
                }
                if normalized['title'] and normalized['url']:
                    jobs.append(normalized)
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Daijob search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_careercross_label(card: str, label: str) -> str:
    pattern = (
        rf'<td[^>]*class="[^"]*job-box-flex[^"]*"[^>]*>\s*{re.escape(label)}\s*</td>\s*'
        rf'<td[^>]*class="[^"]*(?:job-box-text|no-border)[^"]*"[^>]*>\s*(.*?)\s*</td>'
    )
    return _regex_first(pattern, card)


def _fetch_careercross_jobs(search: str, location: str = '', limit: int = 40, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"careercross:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        for page in range(1, pages + 1):
            params = {'page': str(page)}
            if keyword:
                params['keyword'] = keyword
            url = f'{CAREERCROSS_SEARCH_URL}?{urllib.parse.urlencode(params)}'
            raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('CareerCross'))
            cards = re.split(r'<div class="result-job-box"', raw)[1:]
            if not cards:
                break
            for card in cards:
                block = f'<div class="result-job-box"{card}'
                title_match = re.search(r'<a[^>]+href="([^"]+)"[^>]+class="job-details-url"[^>]*title="([^"]+)"', block, re.I | re.S)
                if not title_match:
                    continue
                href, raw_title = title_match.groups()
                link = _absolute_url('https://www.careercross.com', href)
                job_id = _regex_first(r'id="job_(\d+)"', block) or link.rstrip('/').split('-')[-1] or uuid.uuid4().hex[:10]
                company = _extract_careercross_label(block, 'Hiring Company') or _extract_careercross_label(block, 'Recruiter')
                job_location = _extract_careercross_label(block, 'Location') or 'Japan'
                job_type_text = _extract_careercross_label(block, 'Job Type')
                salary = _extract_careercross_label(block, 'Salary')
                posted_at = _extract_careercross_label(block, 'Updated')

                description = '\n'.join(part for part in (
                    job_type_text,
                    f'Salary: {salary}' if salary else '',
                    f'Updated: {posted_at}' if posted_at else '',
                ) if part)
                normalized = {
                    'id': f'careercross-{job_id}',
                    'title': _clean_job_text(raw_title),
                    'company': company or 'CareerCross employer',
                    'location': _japan_location(job_location),
                    'job_type': _map_job_type(job_type_text),
                    'category': job_type_text,
                    'salary': salary,
                    'posted_at': posted_at,
                    'description': _clean_job_description(description),
                    'url': link,
                    'source': 'CareerCross',
                    'search_terms': keyword,
                }
                if normalized['title'] and normalized['url']:
                    jobs.append(normalized)
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('CareerCross search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_green_jobs(search: str, location: str = '', limit: int = 40) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"green:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        params = {'keyword': keyword} if keyword else {}
        url = GREEN_SEARCH_URL if not params else f'{GREEN_SEARCH_URL}?{urllib.parse.urlencode(params)}'
        data = _extract_next_data(_fetch_text_url(url, timeout=10, headers=_job_source_headers('Green')))
        offers = _find_first_key(data, 'jobOffers') or []
        for offer in offers[:limit]:
            if not isinstance(offer, dict):
                continue
            company = offer.get('company') or {}
            client_business = offer.get('clientBusiness') or {}
            skills = offer.get('skillNames') or []
            tags = offer.get('tagNames') or []
            description = '\n'.join(part for part in (
                offer.get('name') or '',
                client_business.get('introduction') or '',
                f"Skills: {', '.join(skills)}" if skills else '',
                f"Tags: {', '.join(tags)}" if tags else '',
            ) if part)
            normalized = {
                'id': f"green-{offer.get('id') or uuid.uuid4().hex[:10]}",
                'title': _clean_job_text(offer.get('title') or offer.get('name')),
                'company': _clean_job_text(company.get('name') or 'Green employer'),
                'location': _japan_location(offer.get('areaName') or 'Japan'),
                'job_type': '',
                'category': _clean_job_text(offer.get('name') or ', '.join(skills[:3])),
                'salary': _clean_job_text(offer.get('salary')),
                'posted_at': _epoch_to_date(offer.get('jobOfferUpdatedAtTimestamp')),
                'description': _clean_job_description(description),
                'url': _absolute_url('https://www.green-japan.com', offer.get('jobOfferUrl') or ''),
                'source': 'Green',
                'search_terms': keyword,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('Green search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_mynavi_condition(card: str, label: str) -> str:
    pattern = rf'<th[^>]*class="tableCondition__head"[^>]*>\s*{re.escape(label)}\s*</th>\s*<td[^>]*class="tableCondition__body"[^>]*>(.*?)</td>'
    return _regex_first(pattern, card)


def _fetch_mynavi_jobs(search: str, location: str = '', limit: int = 40, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"mynavi:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')
    if not keyword:
        return [], False, None

    jobs = []
    error = None
    try:
        safe_keyword = urllib.parse.quote(keyword.replace(' ', ''), safe='')
        for page in range(1, pages + 1):
            suffix = f'/kw{safe_keyword}/' if page == 1 else f'/kw{safe_keyword}/pg{page}/'
            raw = _fetch_text_url(f'{MYNAVI_SEARCH_BASE_URL}{suffix}', timeout=10, headers=_job_source_headers('Mynavi'))
            cards = re.split(r'<div class="cassetteRecruit">', raw)[1:]
            if not cards:
                break
            for card in cards:
                block = f'<div class="cassetteRecruit">{card}'
                title_match = re.search(r'class="js__ga--setCookieOccName"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.I | re.S)
                if not title_match:
                    continue
                href, raw_title = title_match.groups()
                link = _absolute_url('https://tenshoku.mynavi.jp', href)
                company = _regex_first(r'class="cassetteRecruit__name"[^>]*>(.*?)</h3>', block)
                employment = _regex_first(r'class="labelEmploymentStatus"[^>]*>(.*?)</span>', block)
                description = _extract_mynavi_condition(block, '仕事内容')
                audience = _extract_mynavi_condition(block, '対象となる方')
                job_location = _extract_mynavi_condition(block, '勤務地')
                salary = _extract_mynavi_condition(block, '給与') or _extract_mynavi_condition(block, '初年度年収')
                posted_at = _regex_first(r'class="cassetteRecruit__updateDate"[^>]*>(.*?)</p>', block)
                tags = [_clean_job_text(tag) for tag in re.findall(r'class="label[^"]*"[^>]*>(.*?)</span>', block, re.I | re.S)]
                description_full = '\n'.join(part for part in (
                    description,
                    f'Candidate: {audience}' if audience else '',
                    f"Tags: {', '.join(tag for tag in tags if tag)}" if tags else '',
                ) if part)

                normalized = {
                    'id': f'mynavi-{link.rstrip("/").split("/")[-1] or uuid.uuid4().hex[:10]}',
                    'title': _clean_job_text(raw_title),
                    'company': company or 'Mynavi employer',
                    'location': _japan_location(job_location),
                    'job_type': _map_job_type(employment),
                    'category': employment,
                    'salary': salary,
                    'posted_at': posted_at,
                    'description': _clean_job_description(description_full),
                    'url': link,
                    'source': 'Mynavi Tenshoku',
                    'search_terms': keyword,
                }
                if normalized['title'] and normalized['url']:
                    jobs.append(normalized)
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Mynavi search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_wantedly_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"wantedly:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        params = {'keywords': keyword} if keyword else {}
        url = WANTEDLY_SEARCH_URL if not params else f'{WANTEDLY_SEARCH_URL}?{urllib.parse.urlencode(params)}'
        raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('Wantedly'))
        postings = []
        for payload in _extract_json_ld(raw):
            if payload.get('@type') == 'ItemList':
                postings.extend((item.get('item') if isinstance(item, dict) else None) for item in payload.get('itemListElement', []))
        for posting in [p for p in postings if isinstance(p, dict)][:limit]:
            org = posting.get('hiringOrganization') or {}
            employment = posting.get('employmentType')
            normalized = {
                'id': f"wantedly-{((posting.get('identifier') or {}).get('value') if isinstance(posting.get('identifier'), dict) else '') or posting.get('@id', '').rstrip('/').split('/')[-1] or uuid.uuid4().hex[:10]}",
                'title': _clean_job_text(posting.get('title')),
                'company': _clean_job_text(org.get('name') or 'Wantedly employer'),
                'location': 'Japan',
                'job_type': _map_job_type(str(employment or '')),
                'category': str(employment or '').replace('_', ' ').title(),
                'salary': '',
                'posted_at': _iso_to_date(posting.get('datePosted')),
                'description': _clean_job_description(posting.get('description') or ''),
                'url': posting.get('url') or posting.get('@id') or '',
                'source': 'Wantedly',
                'search_terms': keyword,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('Wantedly search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _find_findy_job_descriptions(data) -> list[dict]:
    candidates = []

    def walk(value):
        if isinstance(value, dict):
            if value.get('__typename') == 'JobDescription' and value.get('id') and value.get('title'):
                candidates.append(value)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(data)
    deduped = []
    seen = set()
    for item in candidates:
        if item.get('id') in seen:
            continue
        seen.add(item.get('id'))
        deduped.append(item)
    return deduped


def _fetch_findy_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"findy:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        slug = re.sub(r'[^a-z0-9+#.]+', '-', keyword.lower()).strip('-') if keyword else ''
        slug = slug.replace('#', 'sharp').replace('+', 'plus').replace('.', '')
        url = FINDY_RECOMMENDS_URL if not slug else f'{FINDY_RECOMMENDS_URL}/{urllib.parse.quote(slug)}'
        data = _extract_next_data(_fetch_text_url(url, timeout=10, headers=_job_source_headers('Findy')))
        for item in _find_findy_job_descriptions(data)[:limit]:
            company = item.get('company') or {}
            skills = [skill.get('name') for skill in item.get('skills') or [] if isinstance(skill, dict) and skill.get('name')]
            tags = [tag.get('name') for tag in item.get('tags') or [] if isinstance(tag, dict) and tag.get('name')]
            salary_min = item.get('numericSalaryMin')
            salary_max = item.get('numericSalaryMax')
            salary = ''
            if salary_min or salary_max:
                salary = f"JPY {salary_min or ''} - {salary_max or ''}".strip()
            job_type = (item.get('jobType') or {}).get('name') if isinstance(item.get('jobType'), dict) else ''
            normalized = {
                'id': f"findy-{item.get('id') or uuid.uuid4().hex[:10]}",
                'title': _clean_job_text(item.get('title')),
                'company': _clean_job_text(company.get('name') or 'Findy employer'),
                'location': 'Japan',
                'job_type': '',
                'category': _clean_job_text(job_type or ', '.join(skills[:3])),
                'salary': salary,
                'posted_at': _iso_to_date(item.get('publishedAt') or item.get('createdAt')),
                'description': _clean_job_description('\n'.join(part for part in (
                    item.get('description') or '',
                    f"Skills: {', '.join(skills)}" if skills else '',
                    f"Tags: {', '.join(tags[:8])}" if tags else '',
                ) if part)),
                'url': f"https://findy-code.io/companies/{company.get('id', '')}/jobs/{item.get('id')}" if company.get('id') else url,
                'source': 'Findy',
                'search_terms': keyword,
            }
            if normalized['title']:
                jobs.append(normalized)
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            logger.warning('Findy search unavailable: %s', exc)
            error = str(exc)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        logger.warning('Findy search unavailable: %s', exc)
        error = str(exc)

    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_michael_page_field(card: str, class_name: str) -> str:
    pattern = rf'class="{re.escape(class_name)}"[^>]*>\s*(?:<i[^>]*>.*?</i>)?\s*(.*?)\s*</div>'
    return _regex_first(pattern, card)


def _fetch_michael_page_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"michael-page:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        params = {'keywords': keyword} if keyword else {}
        url = MICHAEL_PAGE_SEARCH_URL if not params else f'{MICHAEL_PAGE_SEARCH_URL}?{urllib.parse.urlencode(params)}'
        raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('MichaelPage'))
        cards = re.split(r'<li class="views-row">', raw)[1:]
        for card in cards:
            block = f'<li class="views-row">{card}'
            title_match = re.search(r'class="job-title[^"]*"[^>]*>.*?<a href="([^"]+)"[^>]*>(.*?)</a>', block, re.I | re.S)
            if not title_match:
                continue
            href, raw_title = title_match.groups()
            link = _absolute_url('https://www.michaelpage.co.jp', href)
            job_id = _regex_first(r'class="job-title[^"]*"[^>]+id="([^"]+)"', block) or link.rstrip('/').split('/')[-1] or uuid.uuid4().hex[:10]
            job_location = _extract_michael_page_field(block, 'job-location') or 'Japan'
            contract_type = _extract_michael_page_field(block, 'job-contract-type')
            salary = _extract_michael_page_field(block, 'job-salary')
            company_type = _extract_michael_page_field(block, 'job-company-type')
            work_style = _extract_michael_page_field(block, 'job-nature')
            summary = _regex_first(r'class="job_advert__job-summary-text"[^>]*>(.*?)</div>', block)
            bullets = _regex_first(r'class="job_advert__job-desc-bullet-points"[^>]*>(.*?)</div>', block)
            description = '\n'.join(part for part in (
                summary,
                bullets,
                f'Client type: {company_type}' if company_type else '',
                f'Work style: {work_style}' if work_style else '',
            ) if part)

            normalized = {
                'id': f'michael-page-{job_id}',
                'title': _clean_job_text(raw_title),
                'company': 'Michael Page',
                'location': _japan_location(job_location),
                'job_type': _map_job_type(contract_type),
                'category': company_type or contract_type,
                'salary': salary,
                'posted_at': '',
                'description': _clean_job_description(description),
                'url': link,
                'source': 'Michael Page',
                'source_method': 'recruiter',
                'search_terms': keyword,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Michael Page search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_rgf_label(card: str, label: str) -> str:
    return _regex_first(rf'<span[^>]*>\s*{re.escape(label)}\s*</span>.*?<dd[^>]*>\s*(.*?)\s*</dd>', card)


def _fetch_rgf_jobs(search: str, location: str = '', limit: int = 30, pages: int = 1) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"rgf:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        for page in range(1, pages + 1):
            params = {'keyword': keyword} if keyword else {}
            if page == 1:
                base_url = RGF_SEARCH_URL
            else:
                base_url = _absolute_url(RGF_SEARCH_URL, f'page/{page}/')
            url = base_url if not params else f'{base_url}?{urllib.parse.urlencode(params)}'
            raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('RGFProfessional'))
            cards = re.split(r'<article class="h-full">', raw)[1:]
            if not cards:
                break
            for card in cards:
                block = f'<article class="h-full">{card}'
                href = _regex_first(r'<a[^>]+href="([^"]+)"', block)
                raw_title = _regex_first(r'class="card-title-underline"[^>]*>(.*?)</span>', block)
                if not href or not raw_title:
                    continue
                link = _absolute_url('https://www.rgf-professional.jp', href)
                tags = [_clean_job_text(tag) for tag in re.findall(r'<li[^>]*>\s*(.*?)\s*</li>', block, re.I | re.S)]
                tags = [tag for tag in tags if tag]
                salary = _extract_rgf_label(block, 'Salary')
                job_location = _extract_rgf_label(block, 'Location') or 'Japan'
                posted_at = _regex_first(r'Posted:\s*([0-9.]+)', block)
                description = '\n'.join(part for part in (
                    f"Tags: {', '.join(tags[:8])}" if tags else '',
                    f'Salary: {salary}' if salary else '',
                    f'Posted: {posted_at}' if posted_at else '',
                ) if part)
                job_id = link.rstrip('/').split('/')[-1] or uuid.uuid4().hex[:10]

                normalized = {
                    'id': f'rgf-{job_id}',
                    'title': _clean_job_text(raw_title),
                    'company': 'RGF Professional',
                    'location': _japan_location(job_location),
                    'job_type': '',
                    'category': ', '.join(tags[:3]),
                    'salary': salary,
                    'posted_at': posted_at,
                    'description': _clean_job_description(description),
                    'url': link,
                    'source': 'RGF Professional',
                    'source_method': 'recruiter',
                    'search_terms': keyword,
                }
                if normalized['title'] and normalized['url']:
                    jobs.append(normalized)
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('RGF Professional search unavailable: %s', exc)
        error = str(exc)

    jobs = _enrich_job_descriptions(jobs)
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_tokyodev_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('TokyoDev', TOKYODEV_JOBS_URL, {'search': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _rakuten_location(raw_location: str, href: str) -> str:
    job_location = re.sub(r'^\s*Location:\s*', '', _clean_job_text(raw_location), flags=re.I).strip()
    if job_location and job_location.lower() != 'japan':
        return _japan_location(job_location)
    city = _regex_first(r'/job/([^/]+)/', href).replace('-', ' ').title()
    return _japan_location(f'{city}, Japan' if city else 'Japan')


def _fetch_rakuten_jobs(search: str, location: str = '', limit: int = 45, pages: int = 2) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"rakuten:{keyword.lower() or '_latest'}:{city.lower()}:{limit}:{pages}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    try:
        for page in range(1, pages + 1):
            params = {}
            if keyword:
                params['keywords'] = keyword
            if page > 1:
                params['p'] = str(page)
            url = RAKUTEN_JAPAN_SEARCH_URL if not params else f'{RAKUTEN_JAPAN_SEARCH_URL}?{urllib.parse.urlencode(params)}'
            raw = _fetch_text_url(url, timeout=10, headers=_job_source_headers('Rakuten'))
            cards = re.findall(
                r'<li>\s*<a href="([^"]+)"\s+data-job-id="([^"]+)">(.*?)</a>',
                raw or '',
                flags=re.I | re.S,
            )
            if not cards:
                break
            for href, job_id, block in cards:
                title = _regex_first(r'<h2>\s*(.*?)\s*</h2>', block)
                if not title:
                    continue
                category = re.sub(
                    r'^\s*Category:\s*',
                    '',
                    _regex_first(r'class="job-category"[^>]*>\s*(.*?)\s*</span>', block),
                    flags=re.I,
                ).strip()
                raw_location = _regex_first(r'class="job-location"[^>]*>\s*(.*?)\s*</span>', block)
                link = _absolute_url('https://japan-job-en.rakuten.careers', href)
                normalized = {
                    'id': f'rakuten-{job_id or uuid.uuid5(uuid.NAMESPACE_URL, link).hex[:10]}',
                    'title': title,
                    'company': 'Rakuten',
                    'location': _rakuten_location(raw_location, href),
                    'job_type': '',
                    'category': category,
                    'salary': '',
                    'posted_at': '',
                    'description': _clean_job_description('\n'.join(part for part in (
                        category,
                        raw_location,
                        'Direct Rakuten careers posting',
                    ) if part)),
                    'url': link,
                    'source': 'Rakuten',
                    'source_method': 'public-html',
                    'search_terms': keyword,
                    'strict_title_match': False,
                }
                if normalized['title'] and normalized['url']:
                    jobs.append(normalized)
                if len(jobs) >= limit:
                    break
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Rakuten search unavailable: %s', exc)
        error = str(exc)

    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_japan_ats_company_jobs(source_key: str, source_label: str, fetcher, search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"japan-company:{source_key}:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs, error = fetcher(keyword, limit)
    jobs = [
        {
            **job,
            'source': source_label,
            'source_platform': job.get('source'),
            'source_method': job.get('source_method') or 'ats-api',
        }
        for job in jobs
    ]
    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _extract_mercari_default_jobs(raw: str) -> list[dict]:
    start = raw.find('\\"defaultJobs\\":')
    if start < 0:
        return []
    array_start = raw.find('[', start)
    if array_start < 0:
        return []
    depth = 0
    end = None
    for index, char in enumerate(raw[array_start:], array_start):
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if not end:
        return []
    try:
        return json.loads(raw[array_start:end].replace('\\"', '"'))
    except json.JSONDecodeError:
        return []


def _fetch_mercari_direct_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    city = re.sub(r'\s+', ' ', location or '').strip()
    cache_key = f"mercari-direct:{keyword.lower() or '_latest'}:{city.lower()}:{limit}"
    cached = _cache_get(cache_key)
    if cached:
        return cached['jobs'], True, cached.get('error')

    jobs = []
    error = None
    location_names = {
        'roppongi': 'Tokyo - Roppongi Office, Japan',
        'namba': 'Osaka - Namba Office, Japan',
        'hakata': 'Fukuoka - Hakata Office, Japan',
    }
    try:
        raw = _fetch_text_url('https://careers.mercari.com/en/jobs/', timeout=10, headers=_job_source_headers('Mercari'))
        for item in _extract_mercari_default_jobs(raw):
            title = _clean_job_text(item.get('title'))
            if not title:
                continue
            shortcode = re.sub(r'-\d+$', '', str(item.get('slug') or '').strip())
            locations = [
                location_names.get(str(slug), str(slug).replace('-', ' ').title())
                for slug in item.get('locations') or []
            ]
            categories = [str(value).replace('-', ' ').title() for value in item.get('jobCategories') or []]
            departments = [str(value).replace('-', ' ').title() for value in item.get('departments') or []]
            employment_types = [str(value).replace('-', ' ').title() for value in item.get('employmentTypes') or []]
            url = f'https://apply.workable.com/j/{shortcode}' if shortcode else str(item.get('guid') or '')
            normalized = {
                'id': f"mercari-{shortcode or uuid.uuid5(uuid.NAMESPACE_URL, str(item.get('guid') or title)).hex[:10]}",
                'title': title,
                'company': 'Mercari',
                'location': ', '.join(locations) or 'Tokyo, Japan',
                'job_type': _map_job_type(' '.join(employment_types)),
                'category': ', '.join(categories + departments),
                'salary': '',
                'posted_at': '',
                'description': _clean_job_description('\n'.join(part for part in (
                    f"Categories: {', '.join(categories)}" if categories else '',
                    f"Departments: {', '.join(departments)}" if departments else '',
                    f"Employment: {', '.join(employment_types)}" if employment_types else '',
                    'Direct Mercari careers posting',
                ) if part)),
                'url': url,
                'source': 'Mercari',
                'source_method': 'public-next-data',
                'source_platform': 'Mercari Careers',
                'search_terms': keyword,
                'strict_title_match': False,
            }
            if normalized['title'] and normalized['url']:
                jobs.append(normalized)
            if len(jobs) >= limit:
                break
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        logger.warning('Mercari careers search unavailable: %s', exc)
        error = str(exc)

    _cache_set(cache_key, jobs=jobs, error=error)
    return jobs, False, error


def _fetch_mercari_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    jobs, cached, error = _fetch_mercari_direct_jobs(search, location, limit)
    if jobs:
        return jobs, cached, error
    fallback_jobs, fallback_cached, fallback_error = _fetch_japan_ats_company_jobs(
        'mercari',
        'Mercari',
        lambda keyword, board_limit: _fetch_workable_board('mercari', keyword, board_limit),
        search,
        location,
        limit,
    )
    return fallback_jobs, cached or fallback_cached, error or fallback_error


def _fetch_smartnews_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    return _fetch_japan_ats_company_jobs(
        'smartnews',
        'SmartNews',
        lambda keyword, board_limit: _fetch_workable_board('smartnews', keyword, board_limit),
        search,
        location,
        limit,
    )


def _fetch_woven_toyota_jobs(search: str, location: str = '', limit: int = 35) -> tuple[list[dict], bool, str | None]:
    return _fetch_japan_ats_company_jobs(
        'woven-toyota',
        'Woven by Toyota',
        lambda keyword, board_limit: _fetch_lever_board('woven-by-toyota', keyword, board_limit),
        search,
        location,
        limit,
    )


def _fetch_bizreach_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('BizReach', BIZREACH_SEARCH_URL, {'keyword': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_doda_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('doda', DODA_SEARCH_URL, {'k': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_wexpats_jobs(search: str, location: str = '', limit: int = 30) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('WeXpats', WEXPATS_SEARCH_URL, {'keyword': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_openwork_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('OpenWork', OPENWORK_SEARCH_URL, {'keyword': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_forkwell_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Forkwell', FORKWELL_SEARCH_URL, {'q': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_paiza_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('Paiza', PAIZA_SEARCH_URL, {'keyword': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_lapras_jobs(search: str, location: str = '', limit: int = 25) -> tuple[list[dict], bool, str | None]:
    keyword = re.sub(r'\s+', ' ', search or '').strip()
    return _fetch_generic_board('LAPRAS', LAPRAS_SEARCH_URL, {'q': keyword}, keyword, location or 'Japan', 'Japan', limit)


def _fetch_japan_jobs(search: str, location: str = '', deep_search: bool = False) -> tuple[list[dict], bool, dict[str, str]]:
    jobs = []
    cached = False
    source_errors = {}
    fetchers = {
        'japan-dev': lambda: _fetch_japan_dev_jobs(search, location),
        'gaijinpot': lambda: _fetch_gaijinpot_jobs(search, location),
        'daijob': lambda: _fetch_daijob_jobs(search, location),
        'careercross': lambda: _fetch_careercross_jobs(search, location),
        'green': lambda: _fetch_green_jobs(search, location),
        'mynavi': lambda: _fetch_mynavi_jobs(search, location),
        'wantedly': lambda: _fetch_wantedly_jobs(search, location),
        'findy': lambda: _fetch_findy_jobs(search, location),
        'michael-page': lambda: _fetch_michael_page_jobs(search, location),
        'rgf': lambda: _fetch_rgf_jobs(search, location),
        'tokyodev': lambda: _fetch_tokyodev_jobs(search, location),
        'rakuten': lambda: _fetch_rakuten_jobs(search, location),
        'mercari': lambda: _fetch_mercari_jobs(search, location),
        'smartnews': lambda: _fetch_smartnews_jobs(search, location),
        'woven-toyota': lambda: _fetch_woven_toyota_jobs(search, location),
    }
    if deep_search:
        fetchers.update({
            'bizreach': lambda: _fetch_bizreach_jobs(search, location),
            'doda': lambda: _fetch_doda_jobs(search, location),
            'wexpats': lambda: _fetch_wexpats_jobs(search, location),
            'openwork': lambda: _fetch_openwork_jobs(search, location),
            'forkwell': lambda: _fetch_forkwell_jobs(search, location),
            'paiza': lambda: _fetch_paiza_jobs(search, location),
            'lapras': lambda: _fetch_lapras_jobs(search, location),
        })
    active_fetchers = {name: fetcher for name, fetcher in fetchers.items() if not _source_disabled(f'japan:{name}')}
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
                    _record_source_failure(f'japan:{name}', error)
                else:
                    _record_source_success(f'japan:{name}')
            except Exception as exc:
                logger.warning('%s Japan provider failed unexpectedly: %s', name, exc)
                source_errors[name] = str(exc)
                _record_source_failure(f'japan:{name}', exc)
    return jobs, cached, source_errors
