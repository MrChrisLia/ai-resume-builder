#!/usr/bin/env node
'use strict';

const fs = require('fs');
const http = require('http');
const net = require('net');
const os = require('os');
const path = require('path');
const { spawn } = require('child_process');

const chromePath = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const args = parseArgs(process.argv.slice(2));
const keyword = String(args.keyword || '').trim();
const location = String(args.location || '').trim();
const limit = Math.max(1, Math.min(Number(args.limit || 72), 120));
const maxPages = Math.max(1, Math.min(Number(args.pages || 3), 8));
const detailLimit = Math.max(0, Math.min(Number(args.detailLimit || args.detail_limit || 18), limit));
const fastMode = args.fast === true || args.fast === 'true' || args.fast === '1';
const screenshotDir = args.screenshotDir || path.join(process.cwd(), 'output');

main().then(() => {
  process.exit(0);
}).catch(err => {
  writeJson({ ok: false, jobs: [], error: err.message || String(err) });
  process.exit(0);
});

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i++) {
    const item = argv[i];
    if (!item.startsWith('--')) continue;
    const key = item.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      out[key] = true;
    } else {
      out[key] = next;
      i++;
    }
  }
  return out;
}

async function main() {
  const timings = {};
  const startedAt = Date.now();
  if (!fs.existsSync(chromePath)) {
    throw new Error(`Chrome executable not found at ${chromePath}`);
  }
  fs.mkdirSync(screenshotDir, { recursive: true });

  const port = await getFreePort();
  const userDataDir = fs.mkdtempSync(path.join(os.tmpdir(), '104-browser-poc-'));
  const chrome = spawn(chromePath, [
    '--headless=new',
    '--disable-gpu',
    '--disable-dev-shm-usage',
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-background-networking',
    '--window-size=1365,900',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    'about:blank',
  ], { stdio: 'ignore' });
  chrome.unref();

  let cdp;
  try {
    const target = await createTarget(port);
    cdp = await Cdp.connect(target.webSocketDebuggerUrl);
    await cdp.send('Page.enable');
    await cdp.send('Runtime.enable');
    await cdp.send('Network.enable');
    await cdp.send('Network.setUserAgentOverride', {
      userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36',
      acceptLanguage: 'zh-TW,zh;q=0.9,en;q=0.8',
      platform: 'macOS',
    });
    await cdp.send('Network.setExtraHTTPHeaders', {
      headers: {
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
      },
    });
    timings.browser_ms = Date.now() - startedAt;

    const url = buildSearchUrl(keyword, location, 1);
    await cdp.send('Page.navigate', { url });
    await waitForPage(cdp);
    await sleep(2500);
    await cdp.send('Runtime.evaluate', {
      expression: `(${loadMoreResults.toString()})(${JSON.stringify(Math.min(limit, 36))})`,
      returnByValue: true,
      awaitPromise: true,
    });

    const screenshotName = `104_${Date.now()}_${Math.random().toString(36).slice(2, 8)}.png`;
    const screenshotPath = path.join(screenshotDir, screenshotName);
    const shot = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    fs.writeFileSync(screenshotPath, Buffer.from(shot.data, 'base64'));
    timings.initial_page_ms = Date.now() - startedAt - timings.browser_ms;

    let cookieError = 'Skipped in fast mode';
    let browserFetchError = 'Skipped in fast mode';
    if (!fastMode) {
      const allCookies = await cdp.send('Network.getAllCookies');
      const cookieHeader = buildCookieHeader(allCookies.cookies || []);
      const cookieJobs = cookieHeader
        ? await fetchJobsWithCookies(keyword, location, limit, cookieHeader, url).catch(err => ({ jobs: [], error: err.message }))
        : { jobs: [], error: 'No 104 cookies found in browser session' };
      cookieError = cookieJobs.error || '';
      if (cookieJobs.jobs?.length) {
        writeJson({
          ok: true,
          url,
          screenshot: screenshotName,
          jobs: cookieJobs.jobs,
          pageTitle: '',
          blocked: false,
          reason: '',
          method: 'browser-cookies-http',
        });
        return;
      }

      const browserFetched = await cdp.send('Runtime.evaluate', {
        expression: `(${fetchJobsInBrowser.toString()})(${JSON.stringify(keyword)}, ${JSON.stringify(location)}, ${JSON.stringify(limit)})`,
        returnByValue: true,
        awaitPromise: true,
      });
      const browserFetchResult = browserFetched.result?.value || {};
      browserFetchError = browserFetchResult.error || '';
      if (browserFetchResult.jobs?.length) {
        writeJson({
          ok: true,
          url,
          screenshot: screenshotName,
          jobs: browserFetchResult.jobs,
          pageTitle: '',
          blocked: false,
          reason: '',
          method: 'browser-context-fetch',
          cookieError,
        });
        return;
      }
    }

    const collectStartedAt = Date.now();
    const result = await collectPagedJobs(cdp, keyword, location, limit, maxPages, true);
    timings.collect_ms = Date.now() - collectStartedAt;
    const jobsForDetail = (result.jobs || []).slice(0, detailLimit);
    const enrichStartedAt = Date.now();
    const enriched = jobsForDetail.length
      ? await cdp.send('Runtime.evaluate', {
        expression: `(${enrichJobsFromDetailAjax.toString()})(${JSON.stringify(jobsForDetail)})`,
        returnByValue: true,
        awaitPromise: true,
      }).then(value => value.result?.value || { jobs: jobsForDetail }).catch(() => ({ jobs: jobsForDetail }))
      : { jobs: [] };
    timings.enrich_ms = Date.now() - enrichStartedAt;
    timings.total_ms = Date.now() - startedAt;
    const returnedJobs = [
      ...(Array.isArray(enriched.jobs) ? enriched.jobs : jobsForDetail),
      ...(Array.isArray(result.jobs) ? result.jobs.slice(jobsForDetail.length) : []),
    ];
    writeJson({
      ok: true,
      url,
      screenshot: screenshotName,
      jobs: returnedJobs,
      pageTitle: result.title || '',
      blocked: Boolean(result.blocked),
      reason: result.reason || '',
      method: enriched.method || 'browser-dom',
      pagesScanned: result.pagesScanned || 1,
      detailLimit,
      timings,
      cookieError,
      browserFetchError,
    });
  } finally {
    try { if (cdp) cdp.close(); } catch {}
    try { chrome.kill('SIGKILL'); } catch {}
    try { fs.rmSync(userDataDir, { recursive: true, force: true }); } catch {}
  }
}

async function enrichJobsFromDetailAjax(jobs) {
  const enriched = [];
  let enrichedCount = 0;
  const batchSize = 12;
  for (let i = 0; i < jobs.length; i += batchSize) {
    const batch = jobs.slice(i, i + batchSize);
    const results = await Promise.all(batch.map(enrichOne));
    for (const result of results) {
      enriched.push(result.job);
      if (result.enriched) enrichedCount += 1;
    }
  }
  return { jobs: enriched, method: enrichedCount ? 'browser-detail-ajax' : 'browser-dom' };

  async function enrichOne(job) {
    try {
      const rawId = String(job.id || '').match(/([^/?#]+)$/)?.[1] || '';
      if (!rawId) {
        return { job, enriched: false };
      }
      const controller = new AbortController();
      const response = await withTimeout(
        fetch(`/job/ajax/content/${encodeURIComponent(rawId)}`, {
          signal: controller.signal,
          credentials: 'include',
          referrer: job.url || location.href,
          headers: {
            'Accept': 'application/json, text/plain, */*',
            'X-Requested-With': 'XMLHttpRequest',
          },
        }),
        5000,
        controller
      );
      const raw = await withTimeout(response.text(), 5000, controller);
      if (!response.ok || raw.trim().startsWith('<')) {
        return { job, enriched: false };
      }
      const payload = JSON.parse(raw);
      const data = payload?.data || {};
      const header = data.header || {};
      const detail = data.jobDetail || data.job || data;
      const condition = data.condition || {};
      const locationText = [
        firstPresent(detail, 'addressRegion', 'jobAddrNoDesc'),
        firstPresent(detail, 'addressDetail', 'jobAddress'),
      ].filter(Boolean).join(' ');
      const description = format104Description(data, job);
      return {
        job: {
          ...job,
          title: cleanText(firstPresent(header, 'jobName') || job.title),
          company: cleanText(firstPresent(header, 'custName') || job.company),
          category: cleanText(valueText(firstPresent(detail, 'jobCategory', 'jobCat') || job.category)),
          location: cleanText(locationText || job.location),
          job_type: map104JobType(firstPresent(detail, 'jobType', 'workType')),
          salary: cleanText(firstPresent(detail, 'salary', 'salaryDesc') || job.salary),
          description,
          method: 'browser-detail-ajax',
        },
        enriched: true,
      };
    } catch {
      return { job, enriched: false };
    }
  }

  function withTimeout(promise, timeoutMs, controller) {
    let timer;
    const timeout = new Promise((_, reject) => {
      timer = setTimeout(() => {
        try { controller?.abort(); } catch {}
        reject(new Error('104 detail timeout'));
      }, timeoutMs);
    });
    return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
  }

  function firstPresent(data, ...keys) {
    for (const key of keys) {
      const value = data?.[key];
      if (value !== undefined && value !== null && value !== '') return value;
    }
    return '';
  }

  function cleanHtml(value) {
    return cleanText(value)
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/p>/gi, '\n')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/\n\s+/g, '\n')
      .replace(/[ \t]+/g, ' ')
      .trim();
  }

  function cleanText(value) {
    return String(value || '').replace(/\s+/g, ' ').trim();
  }

  function map104JobType(value) {
    const text = jobTypeText(value).toLowerCase();
    if (!text) return '';
    if (/全職|full.?time/.test(text)) return 'full_time';
    if (/兼職|part.?time/.test(text)) return 'part_time';
    if (/約聘|contract|派遣/.test(text)) return 'contract';
    if (/實習|intern/.test(text)) return 'internship';
    return '';
  }

  function jobTypeText(value) {
    const normalized = cleanText(valueText(value));
    return ({
      '1': '全職',
      '2': '兼職',
      '3': '高階',
      '4': '派遣',
      '5': '接案',
      '6': '家教',
      '7': '實習',
    })[normalized] || normalized;
  }

  function format104Description(data, job) {
    const detail = data.jobDetail || data.job || data;
    const condition = data.condition || {};
    const lines = [];

    addBlock('工作內容', firstPresent(detail, 'jobDescription', 'description') || job.description);
    addPair('職務類別', firstPresent(detail, 'jobCategory', 'jobCat') || firstPresent(data, 'jobCategory'));
    addPair('工作待遇', firstPresent(detail, 'salary', 'salaryDesc') || job.salary);
    addPair('工作性質', jobTypeText(firstPresent(detail, 'jobType', 'workType')));
    addPair('上班地點', [
      firstPresent(detail, 'addressRegion', 'jobAddrNoDesc'),
      firstPresent(detail, 'addressDetail', 'jobAddress'),
    ].filter(Boolean).join(' '));
    addPair('管理責任', firstPresent(detail, 'manageResp', 'manageResponsibility'));
    addPair('出差外派', firstPresent(detail, 'businessTrip', 'travel'));
    addPair('上班時段', firstPresent(detail, 'workPeriod', 'workTime'));
    addPair('休假制度', firstPresent(detail, 'vacationPolicy', 'holidayPolicy'));
    addPair('可上班日', firstPresent(detail, 'startWorkingDay', 'startWorkingDate'));
    addPair('需求人數', firstPresent(detail, 'needEmp', 'needEmployee'));

    const conditionLines = [];
    addCondition(conditionLines, '工作經歷', firstPresent(condition, 'workExp', 'workExperience'));
    addCondition(conditionLines, '學歷要求', firstPresent(condition, 'edu', 'education'));
    addCondition(conditionLines, '科系要求', firstPresent(condition, 'major', 'majorCategory'));
    addCondition(conditionLines, '語文條件', firstPresent(condition, 'language', 'languages'));
    addCondition(conditionLines, '擅長工具', firstPresent(condition, 'specialty', 'tools'));
    addCondition(conditionLines, '工作技能', firstPresent(condition, 'skill', 'skills'));
    addCondition(conditionLines, '具備證照', firstPresent(condition, 'certificate', 'certificates'));
    addCondition(conditionLines, '其他條件', firstPresent(condition, 'other', 'otherCondition'));
    if (conditionLines.length) {
      lines.push('條件要求');
      lines.push(...conditionLines);
    }

    const welfare = firstPresent(data.welfare || {}, 'welfare', 'legalTag', 'tag') || firstPresent(data, 'welfare');
    addBlock('福利制度', welfare);

    const formatted = lines
      .map(line => String(line || '').trim())
      .filter(Boolean)
      .join('\n');
    return formatted || cleanHtml(job.description || '');

    function addPair(label, value) {
      const text = valueText(value);
      if (!text || text === '不拘') {
        if (label === '科系要求' || label === '工作技能') {
          lines.push(label);
          lines.push(text || '不拘');
        }
        return;
      }
      lines.push(label);
      lines.push(text);
    }

    function addBlock(label, value) {
      const text = cleanHtml(valueText(value));
      if (!text) return;
      lines.push(label);
      lines.push(text);
    }

    function addCondition(target, label, value) {
      const text = cleanHtml(valueText(value));
      if (!text) return;
      target.push(label);
      target.push(text);
    }
  }

  function valueText(value) {
    if (value === undefined || value === null || value === '') return '';
    if (Array.isArray(value)) {
      return value.map(item => valueText(item)).filter(Boolean).join('、');
    }
    if (typeof value === 'object') {
      const preferred = [
        'description', 'desc', 'name', 'value', 'text', 'title', 'jobName',
        'jobCategory', 'jobCat', 'language', 'ability', 'skill', 'certificate',
      ];
      for (const key of preferred) {
        if (value[key] !== undefined && value[key] !== null && value[key] !== '') {
          const text = valueText(value[key]);
          if (text) return text;
        }
      }
      return Object.entries(value)
        .filter(([key]) => !/url|link|id|code|no|sort|percent/i.test(key))
        .map(([, item]) => valueText(item))
        .filter(Boolean)
        .join('、');
    }
    return cleanHtml(String(value));
  }
}

async function fetchJobsInBrowser(keywordValue, locationValue, maxJobs) {
  try {
    const searchKeyword = `${keywordValue || ''} ${locationValue || ''}`.trim();
    const params = new URLSearchParams({
      ro: '0',
      kwop: '7',
      keyword: searchKeyword,
      expansionType: 'area,spec,com,job,wf,wktm',
      order: '15',
      asc: '0',
      page: '1',
      mode: 's',
      jobsource: 'job_search',
    });
    const listPayload = await fetchJson(`/jobs/search/list?${params.toString()}`);
    const records = listPayload?.data?.list || listPayload?.list || [];
    const jobs = [];
    for (const record of records.slice(0, maxJobs)) {
      const job = normalize104Record(record);
      if (!job.rawId || !job.title) continue;
      const detail = await fetchDetail(job).catch(() => job);
      jobs.push(detail);
    }
    return { jobs };
  } catch (err) {
    return { jobs: [], error: err.message || String(err) };
  }

  async function fetchDetail(job) {
    const detailPayload = await fetchJson(`/job/ajax/content/${encodeURIComponent(job.rawId)}`);
    const data = detailPayload?.data || {};
    const detail = data.jobDetail || data.condition || data;
    const header = data.header || {};
    return {
      ...job,
      title: cleanText(firstPresent(header, 'jobName') || job.title),
      company: cleanText(firstPresent(header, 'custName') || job.company),
      location: cleanText(firstPresent(detail, 'addressRegion', 'addressDetail') || job.location),
      salary: cleanText(firstPresent(detail, 'salary', 'salaryDesc') || job.salary),
      description: cleanText(firstPresent(detail, 'jobDescription', 'description') || job.description),
      method: 'browser-context-fetch',
    };
  }

  async function fetchJson(url) {
    const response = await fetch(url, {
      credentials: 'include',
      headers: {
        'Accept': 'application/json, text/plain, */*',
        'X-Requested-With': 'XMLHttpRequest',
      },
    });
    const raw = await response.text();
    if (!response.ok) throw new Error(`browser fetch HTTP ${response.status}`);
    if (raw.trim().startsWith('<')) throw new Error('browser fetch returned HTML instead of JSON');
    return JSON.parse(raw);
  }

  function normalize104Record(record) {
    const urlId = String(firstPresent(record, 'link', 'jobLink', 'url')).match(/\/job\/([^/?#]+)/)?.[1] || '';
    const rawId = firstPresent(record, 'jobNo', 'jobno', 'jobId', 'job_id', 'linkJob') || urlId;
    let url = firstPresent(record, 'link', 'jobLink', 'url');
    if (url.startsWith('//')) url = `https:${url}`;
    else if (url.startsWith('/')) url = `https://www.104.com.tw${url}`;
    else if (!url && rawId) url = `https://www.104.com.tw/job/${rawId}`;
    return {
      id: rawId || url,
      rawId,
      title: cleanText(firstPresent(record, 'jobName', 'job_name', 'title')),
      company: cleanText(firstPresent(record, 'custName', 'company', 'companyName')),
      location: cleanText(firstPresent(record, 'jobAddrNoDesc', 'jobAddress', 'address', 'location') || 'Taiwan'),
      salary: cleanText(firstPresent(record, 'salaryDesc', 'salary', 'salaryLow', 'salaryHigh')),
      posted_at: cleanText(firstPresent(record, 'appearDate', 'appear_date', 'date')),
      category: cleanText(firstPresent(record, 'jobCatDesc', 'coIndustryDesc', 'industryDesc')),
      description: cleanText(firstPresent(record, 'description', 'jobDescription', 'desc')),
      url,
      source: '104',
      method: 'browser-context-fetch',
    };
  }

  function firstPresent(data, ...keys) {
    for (const key of keys) {
      const value = data?.[key];
      if (value !== undefined && value !== null && value !== '') return String(value);
    }
    return '';
  }

  function cleanText(value) {
    return String(Array.isArray(value) ? value.join(' ') : value || '')
      .replace(/<script[\s\S]*?<\/script>/gi, ' ')
      .replace(/<style[\s\S]*?<\/style>/gi, ' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ')
      .replace(/&amp;/g, '&')
      .replace(/\s+/g, ' ')
      .trim();
  }
}

function buildListApiUrl(keywordValue, locationValue) {
  const params = new URLSearchParams({
    ro: '0',
    kwop: '7',
    keyword: `${keywordValue || ''} ${locationValue || ''}`.trim(),
    expansionType: 'area,spec,com,job,wf,wktm',
    order: '15',
    asc: '0',
    page: '1',
    mode: 's',
    jobsource: 'job_search',
  });
  return `https://www.104.com.tw/jobs/search/list?${params.toString()}`;
}

function buildCookieHeader(cookies) {
  return cookies
    .filter(cookie => /(^|\.)104\.com\.tw$/.test(cookie.domain || ''))
    .map(cookie => `${cookie.name}=${cookie.value}`)
    .join('; ');
}

async function fetchJobsWithCookies(keywordValue, locationValue, maxJobs, cookieHeader, referer) {
  const listUrl = buildListApiUrl(keywordValue, locationValue);
  const payload = await fetchJson(listUrl, cookieHeader, referer);
  const records = payload?.data?.list || payload?.list || [];
  const jobs = [];
  for (const record of records.slice(0, maxJobs)) {
    const normalized = normalize104Record(record);
    if (!normalized.id || !normalized.title) continue;
    const detailed = await fetchDetailWithCookies(normalized, cookieHeader).catch(() => normalized);
    jobs.push(detailed);
  }
  return { jobs };
}

async function fetchDetailWithCookies(job, cookieHeader) {
  const detailUrl = `https://www.104.com.tw/job/ajax/content/${encodeURIComponent(job.rawId)}`;
  const payload = await fetchJson(detailUrl, cookieHeader, job.url || 'https://www.104.com.tw/jobs/search/');
  const data = payload?.data || {};
  const detail = data.jobDetail || data.condition || data;
  const header = data.header || {};
  return {
    ...job,
    title: cleanText(firstPresent(header, 'jobName') || job.title),
    company: cleanText(firstPresent(header, 'custName') || job.company),
    location: cleanText(firstPresent(detail, 'addressRegion', 'addressDetail') || job.location),
    salary: cleanText(firstPresent(detail, 'salary', 'salaryDesc') || job.salary),
    description: cleanText(firstPresent(detail, 'jobDescription', 'description') || job.description),
  };
}

async function fetchJson(url, cookieHeader, referer) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 12000);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
        'Referer': referer,
        'Cookie': cookieHeader,
      },
    });
    const raw = await response.text();
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    if (raw.trim().startsWith('<')) throw new Error('104 returned HTML instead of JSON with browser cookies');
    return JSON.parse(raw);
  } finally {
    clearTimeout(timer);
  }
}

function normalize104Record(record) {
  const urlId = String(firstPresent(record, 'link', 'jobLink', 'url')).match(/\/job\/([^/?#]+)/)?.[1] || '';
  const rawId = firstPresent(record, 'jobNo', 'jobno', 'jobId', 'job_id', 'linkJob') || urlId;
  let url = firstPresent(record, 'link', 'jobLink', 'url');
  if (url.startsWith('//')) url = `https:${url}`;
  else if (url.startsWith('/')) url = `https://www.104.com.tw${url}`;
  else if (!url && rawId) url = `https://www.104.com.tw/job/${rawId}`;

  const area = firstPresent(record, 'jobAddrNoDesc', 'jobAddress', 'address', 'location') || 'Taiwan';
  return {
    id: rawId || url,
    rawId,
    title: cleanText(firstPresent(record, 'jobName', 'job_name', 'title')),
    company: cleanText(firstPresent(record, 'custName', 'company', 'companyName')),
    location: cleanText(area),
    salary: cleanText(firstPresent(record, 'salaryDesc', 'salary', 'salaryLow', 'salaryHigh')),
    posted_at: cleanText(firstPresent(record, 'appearDate', 'appear_date', 'date')),
    category: cleanText(firstPresent(record, 'jobCatDesc', 'coIndustryDesc', 'industryDesc')),
    description: cleanText(firstPresent(record, 'description', 'jobDescription', 'desc')),
    url,
    source: '104',
    method: 'browser-cookies-http',
  };
}

function firstPresent(data, ...keys) {
  for (const key of keys) {
    const value = data?.[key];
    if (value !== undefined && value !== null && value !== '') return String(value);
  }
  return '';
}

function cleanText(value) {
  return String(Array.isArray(value) ? value.join(' ') : value || '')
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/\s+/g, ' ')
    .trim();
}

function buildSearchUrl(keywordValue, locationValue, page = 1) {
  const params = new URLSearchParams();
  if (keywordValue) params.set('keyword', keywordValue);
  const area = areaCodeForLocation(locationValue);
  if (area) {
    params.set('area', area);
  } else if (locationValue) {
    params.set('keyword', `${keywordValue} ${locationValue}`.trim());
  }
  params.set('order', '15');
  params.set('page', String(Math.max(1, Number(page) || 1)));
  return `https://www.104.com.tw/jobs/search/?${params.toString()}`;
}

function areaCodeForLocation(value) {
  const text = String(value || '').trim().toLowerCase();
  if (!text || /remote|anywhere|worldwide|global/.test(text)) return '';
  const areas = [
    [/台北|臺北|taipei/, '6001001000'],
    [/新北|new taipei/, '6001002000'],
    [/桃園|taoyuan/, '6001005000'],
    [/新竹|hsinchu/, '6001006000,6001007000'],
    [/台中|臺中|taichung/, '6001008000'],
    [/台南|臺南|tainan/, '6001014000'],
    [/高雄|kaohsiung/, '6001016000'],
  ];
  return areas.find(([pattern]) => pattern.test(text))?.[1] || '';
}

async function loadMoreResults(targetCount) {
  const maxScrolls = Math.max(8, Math.ceil(targetCount / 6));
  let previousCount = 0;
  let stableRounds = 0;
  for (let i = 0; i < maxScrolls; i++) {
    const count = new Set(
      Array.from(document.querySelectorAll('a[href*="/job/"]'))
        .map(anchor => (anchor.href || '').match(/\/job\/([^/?#]+)/)?.[1] || anchor.href)
        .filter(Boolean)
    ).size;
    if (count >= targetCount) break;
    if (count === previousCount) stableRounds += 1;
    else stableRounds = 0;
    if (stableRounds >= 3) break;
    previousCount = count;
    window.scrollTo(0, document.body.scrollHeight);
    await new Promise(resolve => setTimeout(resolve, 500));
  }
  window.scrollTo(0, Math.min(document.body.scrollHeight, 1400));
  await new Promise(resolve => setTimeout(resolve, 250));
}

async function collectPagedJobs(cdp, keywordValue, locationValue, targetCount, pageCount, firstPageLoaded = false) {
  const jobs = [];
  const seen = new Set();
  let title = '';
  let pagesScanned = 0;

  for (let page = 1; page <= pageCount && jobs.length < targetCount; page++) {
    const pageUrl = buildSearchUrl(keywordValue, locationValue, page);
    if (page !== 1 || !firstPageLoaded) {
      await cdp.send('Page.navigate', { url: pageUrl });
      await waitForPage(cdp);
      await sleep(page === 1 ? 2200 : 1600);
      await cdp.send('Runtime.evaluate', {
        expression: `(${loadMoreResults.toString()})(${JSON.stringify(Math.min(targetCount - jobs.length, 36))})`,
        returnByValue: true,
        awaitPromise: true,
      });
    }

    const extracted = await cdp.send('Runtime.evaluate', {
      expression: `(${extractJobs.toString()})(${JSON.stringify(Math.min(targetCount - jobs.length, 60))})`,
      returnByValue: true,
      awaitPromise: true,
    });
    const result = extracted.result?.value || {};
    title = result.title || title;
    pagesScanned = page;
    if (result.blocked) {
      return {
        title,
        blocked: true,
        reason: result.reason || '104 displayed a browser challenge',
        jobs,
        pagesScanned,
      };
    }

    let added = 0;
    for (const job of result.jobs || []) {
      const key = String(job.id || job.url || '').toLowerCase();
      if (!key || seen.has(key)) continue;
      seen.add(key);
      jobs.push({ ...job, result_page: page });
      added++;
      if (jobs.length >= targetCount) break;
    }

    if (!result.jobs?.length || added === 0) break;
  }

  return { title, blocked: false, reason: '', jobs, pagesScanned };
}

function extractJobs(maxJobs) {
  const text = document.body?.innerText || '';
  const title = document.title || '';
  const blocked = /cloudflare|確認您是真人|verify you are human|just a moment|請稍候/i.test(text + ' ' + title);
  if (blocked) {
    return { title, blocked: true, reason: '104 displayed a browser challenge', jobs: [] };
  }

  const anchors = Array.from(document.querySelectorAll('a[href*="/job/"]'));
  const seen = new Set();
  const jobs = [];
  for (const anchor of anchors) {
    const href = anchor.href || '';
    const jobId = href.match(/\/job\/([^/?#]+)/)?.[1] || href;
    const titleText = clean(anchor.innerText || anchor.textContent || '');
    if (!titleText || titleText.length < 2 || seen.has(jobId)) continue;

    const card = findCard(anchor, titleText);
    const rawCardText = card?.innerText || '';
    const cardText = clean(rawCardText);
    if (!cardText || cardText.length < titleText.length) continue;

    const lines = rawCardText.split('\n').map(clean).filter(Boolean);
    const titleLineIndex = lines.findIndex(line => line.includes(titleText));
    const company = findCompany(lines, titleLineIndex);
    const location = findFirst(lines, /(台北|臺北|新北|桃園|新竹|台中|臺中|台南|臺南|高雄|基隆|宜蘭|苗栗|彰化|南投|雲林|嘉義|屏東|台東|臺東|花蓮|澎湖|金門|Taiwan|Taipei|Hsinchu|Taichung|Kaohsiung)/i) || 'Taiwan';
    const salary = findFirst(lines, /(月薪|年薪|時薪|待遇面議|面議|NT\$|TWD|元)/i);
    const posted = findFirst(lines, /^\d{1,2}\/\d{1,2}$|^\d+ 天內|^今日|^昨天/);

    seen.add(jobId);
    jobs.push({
      id: jobId,
      title: titleText,
      company,
      location,
      salary,
      posted_at: posted,
      description: cardText,
      url: href,
      source: '104',
    });
    if (jobs.length >= maxJobs) break;
  }
  return { title, blocked: false, jobs };

  function clean(value) {
    return String(value || '').replace(/\s+/g, ' ').trim();
  }
  function findFirst(lines, regex) {
    return lines.find(line => regex.test(line)) || '';
  }
  function findCompany(lines, titleIndex) {
    if (titleIndex >= 0) {
      for (let i = titleIndex + 1; i < Math.min(lines.length, titleIndex + 5); i++) {
        const line = lines[i];
        if (line && !/儲存|應徵|待遇|月薪|年薪|工作|職缺/.test(line)) return line;
      }
    }
    return '';
  }
  function findCard(anchor, titleText) {
    let node = anchor;
    let best = anchor;
    for (let depth = 0; node && depth < 9; depth++, node = node.parentElement) {
      const rawNodeText = node.innerText || '';
      const nodeText = clean(rawNodeText);
      const lines = rawNodeText.split('\n').map(clean).filter(Boolean);
      if (nodeText.includes(titleText) && lines.length >= 3 && nodeText.length > titleText.length + 25) {
        best = node;
        break;
      }
    }
    return best;
  }
}

async function waitForPage(cdp) {
  await Promise.race([
    cdp.waitFor('Page.loadEventFired', 15000).catch(() => null),
    sleep(8000),
  ]);
}

function getFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

function createTarget(port) {
  return requestJson({
    method: 'PUT',
    hostname: '127.0.0.1',
    port,
    path: '/json/new?about:blank',
  }, 15000);
}

function requestJson(options, timeoutMs) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.request(options, res => {
        let raw = '';
        res.setEncoding('utf8');
        res.on('data', chunk => raw += chunk);
        res.on('end', () => {
          try {
            resolve(JSON.parse(raw));
          } catch (err) {
            reject(err);
          }
        });
      });
      req.on('error', err => {
        if (Date.now() - started < timeoutMs) {
          setTimeout(attempt, 250);
        } else {
          reject(err);
        }
      });
      req.end();
    };
    attempt();
  });
}

class Cdp {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 1;
    this.pending = new Map();
    this.waiters = new Map();
    ws.onmessage = event => this.onMessage(event);
  }

  static connect(url) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(url);
      ws.onopen = () => resolve(new Cdp(ws));
      ws.onerror = () => reject(new Error('Could not connect to Chrome DevTools'));
    });
  }

  send(method, params = {}) {
    const id = this.nextId++;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => {
        if (!this.pending.has(id)) return;
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, 120000);
    });
  }

  waitFor(method, timeoutMs = 10000) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        const list = this.waiters.get(method) || [];
        this.waiters.set(method, list.filter(item => item.resolve !== resolve));
        reject(new Error(`CDP event timeout: ${method}`));
      }, timeoutMs);
      const list = this.waiters.get(method) || [];
      list.push({ resolve, timer });
      this.waiters.set(method, list);
    });
  }

  onMessage(event) {
    const msg = JSON.parse(event.data);
    if (msg.id && this.pending.has(msg.id)) {
      const pending = this.pending.get(msg.id);
      this.pending.delete(msg.id);
      if (msg.error) pending.reject(new Error(msg.error.message));
      else pending.resolve(msg.result || {});
      return;
    }
    if (msg.method && this.waiters.has(msg.method)) {
      const list = this.waiters.get(msg.method);
      const waiter = list.shift();
      if (!list.length) this.waiters.delete(msg.method);
      if (waiter) {
        clearTimeout(waiter.timer);
        waiter.resolve(msg.params || {});
      }
    }
  }

  close() {
    this.ws.close();
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function writeJson(value) {
  fs.writeSync(1, JSON.stringify(value));
}
