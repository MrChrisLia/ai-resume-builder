'use strict';

// ── Storage keys ──────────────────────────────────────────────────────────────
const PROFILES_KEY = 'resumeProfiles';
const ACTIVE_KEY   = 'activeProfileId';
const HISTORY_KEY  = 'resumeHistory';

let saveTimer       = null;
let currentTemplate = 'modern';
let currentLanguage = 'english';
let _lastResumeData = null; // cached for cover letter & interview prep

// ── Theme ─────────────────────────────────────────────────────────────────────

function toggleTheme() {
  const next = document.documentElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
  applyTheme(next);
  localStorage.setItem('theme', next);
}

function applyTheme(theme) {
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
    document.getElementById('theme-btn').textContent = '🌙 Dark';
  } else {
    document.documentElement.removeAttribute('data-theme');
    document.getElementById('theme-btn').textContent = '☀ Light';
  }
}

// ── Template selector ─────────────────────────────────────────────────────────

function selectTemplate(name, el) {
  currentTemplate = name;
  document.querySelectorAll('.template-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
}

// ── Language selector ─────────────────────────────────────────────────────────

function selectLanguage(lang, el) {
  currentLanguage = lang;
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
}

// ── Profile storage helpers ───────────────────────────────────────────────────

function genId() {
  return Math.random().toString(36).slice(2, 10);
}

function getProfiles() {
  try { return JSON.parse(localStorage.getItem(PROFILES_KEY)) || {}; }
  catch { return {}; }
}

function saveProfiles(p) {
  localStorage.setItem(PROFILES_KEY, JSON.stringify(p));
}

function getActiveId() {
  return localStorage.getItem(ACTIVE_KEY) || '';
}

function setActiveId(id) {
  localStorage.setItem(ACTIVE_KEY, id);
}

function migrateIfNeeded() {
  const old = localStorage.getItem('resumeProfile');
  if (!old) return;
  const profiles = getProfiles();
  if (Object.keys(profiles).length === 0) {
    let data = {};
    try { data = JSON.parse(old); } catch {}
    const id = genId();
    profiles[id] = { name: data.name || 'My Profile', data };
    saveProfiles(profiles);
    setActiveId(id);
  }
  localStorage.removeItem('resumeProfile');
}

// ── Profile selector UI ───────────────────────────────────────────────────────

function renderProfileSelect() {
  const select   = document.getElementById('profile-select');
  const profiles = getProfiles();
  const activeId = getActiveId();
  select.innerHTML = '';
  Object.entries(profiles).forEach(([id, profile]) => {
    const opt = document.createElement('option');
    opt.value = id;
    opt.textContent = profile.name;
    opt.selected = id === activeId;
    select.appendChild(opt);
  });
}

function initProfileSelector() {
  let profiles = getProfiles();
  let activeId = getActiveId();

  if (Object.keys(profiles).length === 0) {
    const id = genId();
    profiles[id] = { name: 'My Profile', data: {} };
    saveProfiles(profiles);
    activeId = id;
    setActiveId(id);
  } else if (!profiles[activeId]) {
    activeId = Object.keys(profiles)[0];
    setActiveId(activeId);
  }

  renderProfileSelect();
  return activeId;
}

// ── Profile actions ───────────────────────────────────────────────────────────

function switchProfile(newId) {
  _saveToStorage(getActiveId());
  setActiveId(newId);
  const profiles = getProfiles();
  _populateForm(profiles[newId]?.data || {});
  _resetRightPanel();
}

function createProfile() {
  const name = prompt('Name for the new profile:', 'New Profile');
  if (!name?.trim()) return;
  _saveToStorage(getActiveId());
  const profiles = getProfiles();
  const id = genId();
  profiles[id] = { name: name.trim(), data: {} };
  saveProfiles(profiles);
  setActiveId(id);
  renderProfileSelect();
  _populateForm({});
}

function renameProfile() {
  const activeId = getActiveId();
  const profiles = getProfiles();
  const current  = profiles[activeId]?.name || '';
  const newName  = prompt('Rename profile:', current);
  if (!newName?.trim() || newName.trim() === current) return;
  profiles[activeId].name = newName.trim();
  saveProfiles(profiles);
  renderProfileSelect();
}

function deleteProfile() {
  const profiles = getProfiles();
  const activeId = getActiveId();
  if (Object.keys(profiles).length <= 1) {
    alert('You must keep at least one profile.');
    return;
  }
  const profileName = profiles[activeId]?.name || 'this profile';
  if (!confirm(`Delete "${profileName}"? This cannot be undone.`)) return;
  delete profiles[activeId];
  saveProfiles(profiles);
  const newId = Object.keys(profiles)[0];
  setActiveId(newId);
  renderProfileSelect();
  _populateForm(profiles[newId]?.data || {});
}

// ── Profile JSON export / import ──────────────────────────────────────────────

function exportProfileJSON() {
  _saveToStorage(getActiveId());
  const profiles = getProfiles();
  const activeId = getActiveId();
  const profile  = profiles[activeId];
  if (!profile) return;
  const blob = new Blob([JSON.stringify({ name: profile.name, data: profile.data }, null, 2)],
    { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${profile.name.replace(/\s+/g, '_')}_profile.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function triggerProfileImport() {
  document.getElementById('profile-json-input').click();
}

async function handleProfileImport(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';
  try {
    const text = await file.text();
    const parsed = JSON.parse(text);
    const profileData = parsed.data || parsed; // handle both formats
    _populateForm(profileData);
    scheduleSave();
  } catch {
    showError('Could not parse JSON file.');
  }
}

// ── Auto-save ─────────────────────────────────────────────────────────────────

function scheduleSave() {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(() => _saveToStorage(getActiveId()), 700);
}

function _saveToStorage(id) {
  if (!id) return;
  const profiles = getProfiles();
  if (!profiles[id]) return;
  profiles[id].data = collectCandidate();
  saveProfiles(profiles);
  const indicator = document.getElementById('save-indicator');
  indicator.classList.add('visible');
  clearTimeout(indicator._hideTimer);
  indicator._hideTimer = setTimeout(() => indicator.classList.remove('visible'), 2200);
}

// ── Photo upload ──────────────────────────────────────────────────────────────

function triggerPhotoUpload() {
  document.getElementById('photo-input').click();
}

function handlePhotoUpload(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';
  const reader = new FileReader();
  reader.onload = e => {
    const dataUrl = e.target.result;
    document.getElementById('photo-preview').src = dataUrl;
    document.getElementById('photo-preview').classList.remove('hidden');
    document.getElementById('photo-placeholder').classList.add('hidden');
    document.getElementById('btn-remove-photo').classList.remove('hidden');
    scheduleSave();
  };
  reader.readAsDataURL(file);
}

function removePhoto(event) {
  if (event) event.stopPropagation();
  document.getElementById('photo-preview').src = '';
  document.getElementById('photo-preview').classList.add('hidden');
  document.getElementById('photo-placeholder').classList.remove('hidden');
  document.getElementById('btn-remove-photo').classList.add('hidden');
  scheduleSave();
}

function _restorePhoto(photoDataUrl) {
  const preview     = document.getElementById('photo-preview');
  const placeholder = document.getElementById('photo-placeholder');
  const removeBtn   = document.getElementById('btn-remove-photo');
  if (photoDataUrl) {
    preview.src = photoDataUrl;
    preview.classList.remove('hidden');
    placeholder.classList.add('hidden');
    removeBtn.classList.remove('hidden');
  } else {
    preview.src = '';
    preview.classList.add('hidden');
    placeholder.classList.remove('hidden');
    removeBtn.classList.add('hidden');
  }
}

// ── Form population ───────────────────────────────────────────────────────────

function _populateForm(data) {
  ['name', 'email', 'phone', 'location', 'linkedin', 'github'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = data[id] || '';
  });

  const extraEl = document.getElementById('extra-info');
  if (extraEl) extraEl.value = data.extra_info || '';

  _restorePhoto(data.photo || '');

  function fillBlock(container, templateId, fields, values) {
    container.appendChild(cloneTemplate(templateId));
    const block = container.lastElementChild;
    fields.forEach(name => {
      const el = block.querySelector(`[name="${name}"]`);
      if (!el) return;
      el.value = Array.isArray(values[name])
        ? values[name].join(', ')
        : (values[name] || '');
    });
  }

  // Experience
  const expList = document.getElementById('experience-list');
  expList.innerHTML = '';
  (data.experience?.length ? data.experience : [{}]).forEach(exp => {
    fillBlock(expList, 'tpl-experience',
      ['company', 'title', 'start_date', 'end_date', 'description'], exp);
  });

  // Education
  const eduList = document.getElementById('education-list');
  eduList.innerHTML = '';
  (data.education?.length ? data.education : [{}]).forEach(edu => {
    fillBlock(eduList, 'tpl-education',
      ['school', 'degree', 'field', 'graduation'], edu);
  });

  // Skills
  const skillList = document.getElementById('skills-list');
  skillList.innerHTML = '';
  (data.skills?.length ? data.skills : [{}]).forEach(s => {
    fillBlock(skillList, 'tpl-skill-category', ['category', 'items'], s);
  });

  // Languages
  const langList = document.getElementById('languages-list');
  langList.innerHTML = '';
  (data.languages || []).forEach(l => {
    langList.appendChild(cloneTemplate('tpl-language'));
    const block     = langList.lastElementChild;
    const langInput  = block.querySelector('[name="language"]');
    const profSelect = block.querySelector('[name="proficiency"]');
    const certInput  = block.querySelector('[name="certificate"]');
    if (langInput)  langInput.value  = l.language    || '';
    if (profSelect) profSelect.value = l.proficiency || 'Fluent';
    if (certInput)  certInput.value  = l.certificate || '';
  });

  // Projects
  const projList = document.getElementById('projects-list');
  projList.innerHTML = '';
  (data.projects || []).forEach(p => {
    fillBlock(projList, 'tpl-project', ['name', 'technologies', 'description'], p);
  });

  // Certifications
  const certList = document.getElementById('certs-list');
  certList.innerHTML = '';
  (data.certifications || []).forEach(c => {
    certList.appendChild(cloneTemplate('tpl-cert'));
    const input = certList.lastElementChild.querySelector('[name="cert"]');
    if (input) input.value = c;
  });
}

// ── Collect form data ─────────────────────────────────────────────────────────

function _getBlocks(containerId, fieldNames) {
  return Array.from(
    document.getElementById(containerId).querySelectorAll('.entry-block')
  ).map(block => {
    const obj = {};
    fieldNames.forEach(name => {
      const el = block.querySelector(`[name="${name}"]`);
      obj[name] = el ? el.value.trim() : '';
    });
    return obj;
  }).filter(obj => Object.values(obj).some(v => v));
}

function collectCandidate() {
  const rawSkills = _getBlocks('skills-list', ['category', 'items']);
  const skills = rawSkills.map(s => ({
    category: s.category,
    items: s.items.split(',').map(i => i.trim()).filter(Boolean),
  }));

  const rawLangs = _getBlocks('languages-list', ['language', 'proficiency', 'certificate']);
  const languages = rawLangs.filter(l => l.language);

  const certs = Array.from(
    document.querySelectorAll('#certs-list .entry-block')
  ).map(b => b.querySelector('[name="cert"]')?.value.trim()).filter(Boolean);

  const photoEl = document.getElementById('photo-preview');
  const photo = (!photoEl.classList.contains('hidden') && photoEl.src.startsWith('data:'))
    ? photoEl.src : '';

  return {
    name:        document.getElementById('name').value.trim(),
    email:       document.getElementById('email').value.trim(),
    phone:       document.getElementById('phone').value.trim(),
    location:    document.getElementById('location').value.trim(),
    linkedin:    document.getElementById('linkedin').value.trim(),
    github:      document.getElementById('github').value.trim(),
    extra_info:  document.getElementById('extra-info').value.trim(),
    photo,
    experience:  _getBlocks('experience-list', ['company', 'title', 'start_date', 'end_date', 'description']),
    education:   _getBlocks('education-list',  ['school', 'degree', 'field', 'graduation']),
    skills,
    languages,
    projects:    _getBlocks('projects-list',   ['name', 'technologies', 'description']),
    certifications: certs,
  };
}

// ── Dynamic block helpers ─────────────────────────────────────────────────────

function cloneTemplate(id) {
  return document.getElementById(id).content.cloneNode(true);
}

function removeBlock(btn) {
  btn.closest('.entry-block').remove();
  scheduleSave();
}

function addExperience()    { document.getElementById('experience-list').appendChild(cloneTemplate('tpl-experience')); }
function addEducation()     { document.getElementById('education-list').appendChild(cloneTemplate('tpl-education')); }
function addSkillCategory() { document.getElementById('skills-list').appendChild(cloneTemplate('tpl-skill-category')); }
function addLanguage()      { document.getElementById('languages-list').appendChild(cloneTemplate('tpl-language')); }
function addProject()       { document.getElementById('projects-list').appendChild(cloneTemplate('tpl-project')); }
function addCert()          { document.getElementById('certs-list').appendChild(cloneTemplate('tpl-cert')); }

// ── Collapsible cards ─────────────────────────────────────────────────────────

function toggleCard(titleEl) {
  const body    = titleEl.closest('.card').querySelector('.card-body');
  const chevron = titleEl.querySelector('.chevron');
  const isOpen  = !body.classList.contains('collapsed');
  body.classList.toggle('collapsed', isOpen);
  chevron.style.transform = isOpen ? 'rotate(-90deg)' : '';
}

// ── File import ───────────────────────────────────────────────────────────────

function triggerImport() {
  document.getElementById('import-file-input').click();
}

async function handleImport(input) {
  const file = input.files[0];
  if (!file) return;
  input.value = '';

  const btn = document.getElementById('btn-import');
  btn.disabled = true;
  btn.textContent = 'Importing...';

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/import-profile', { method: 'POST', body: formData });
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error(`Server error (HTTP ${res.status}) — check the terminal for details`);
    }
    if (!res.ok || !data.success) throw new Error(data.error || 'Import failed.');
    _populateForm(data.profile);
    scheduleSave();
    hideError();
  } catch (err) {
    showError(`Import failed: ${err.message}`);
  } finally {
    btn.disabled = false;
    btn.textContent = 'Resume File';
  }
}

// ── Analyze Job Fit ───────────────────────────────────────────────────────────

async function analyzeFit() {
  const candidate     = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();

  if (!candidate.name) return showError('Please enter your full name.');
  if (!jobDescription)  return showError('Please paste the job description.');

  setFitLoading(true);
  hideError();
  document.getElementById('fit-card').classList.add('hidden');
  document.getElementById('generate-section').classList.add('hidden');
  document.getElementById('results').classList.add('hidden');
  document.getElementById('cl-results').classList.add('hidden');
  document.getElementById('interview-section').classList.add('hidden');

  try {
    const res  = await fetch('/analyze-fit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, job_description: jobDescription, additional_notes: document.getElementById('additional-notes').value.trim(), language: currentLanguage }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) throw new Error(data.error || 'Analysis failed.');
    showFitCard(data.fit);
    document.getElementById('generate-section').classList.remove('hidden');
    document.getElementById('generate-section').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    showError(err.message);
  } finally {
    setFitLoading(false);
  }
}

function setFitLoading(on) {
  const btn = document.getElementById('btn-fit');
  btn.disabled = on;
  document.getElementById('btn-fit-text').textContent = on ? 'Analyzing…' : 'Check Job Fit';
  document.getElementById('btn-fit-spinner').classList.toggle('hidden', !on);
}

function showFitCard(fit) {
  const score     = fit.score ?? 0;
  const circleEl  = document.getElementById('fit-circle');
  const verdictEl = document.getElementById('fit-verdict');
  const summaryEl = document.getElementById('fit-summary');
  const sectionsEl = document.getElementById('fit-sections');

  document.getElementById('fit-score-num').textContent = score;

  const tier = score >= 8 ? 'high' : score >= 6 ? 'mid' : score >= 4 ? 'low' : 'poor';
  circleEl.className  = `fit-score-circle score-${tier}`;
  verdictEl.className = `fit-verdict verdict-${tier}`;
  verdictEl.textContent = fit.verdict || '';
  summaryEl.textContent = fit.summary || '';

  sectionsEl.innerHTML = '';
  if (fit.strengths?.length) {
    const div = document.createElement('div');
    div.className = 'fit-list fit-strengths';
    div.innerHTML = `<h4>Strengths</h4><ul>${fit.strengths.map(s => `<li>${s}</li>`).join('')}</ul>`;
    sectionsEl.appendChild(div);
  }
  if (fit.gaps?.length) {
    const div = document.createElement('div');
    div.className = 'fit-list fit-gaps';
    div.innerHTML = `<h4>Gaps / Areas to Address</h4><ul>${fit.gaps.map(g => `<li>${g}</li>`).join('')}</ul>`;
    sectionsEl.appendChild(div);
  }

  document.getElementById('fit-card').classList.remove('hidden');
  document.getElementById('fit-card').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Generate Resume ───────────────────────────────────────────────────────────

async function generateResume() {
  const candidate      = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();
  const formats = [];
  if (document.getElementById('fmt-docx').checked) formats.push('docx');
  if (document.getElementById('fmt-pdf').checked)  formats.push('pdf');
  if (document.getElementById('fmt-md').checked)   formats.push('md');

  if (!formats.length) return showError('Select at least one output format.');

  setGenLoading(true);
  hideError();
  document.getElementById('results').classList.add('hidden');

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, job_description: jobDescription, formats, template: currentTemplate, language: currentLanguage, additional_notes: document.getElementById('additional-notes').value.trim() }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) throw new Error(data.error || 'Generation failed.');

    _lastResumeData = data.resume;
    showResults(data.downloads, data.resume);
    addToHistory(candidate, jobDescription, data.resume, data.downloads, data.file_id);

    // Reveal cover letter & interview prep buttons
    document.getElementById('btn-cover-letter').classList.remove('hidden');
    document.getElementById('btn-interview').classList.remove('hidden');
  } catch (err) {
    showError(err.message);
  } finally {
    setGenLoading(false);
  }
}

function setGenLoading(on) {
  const btn = document.getElementById('btn-generate');
  btn.disabled = on;
  document.getElementById('btn-text').textContent = on ? 'Generating…' : 'Generate Tailored Resume';
  document.getElementById('btn-spinner').classList.toggle('hidden', !on);
}

// ── Generate Cover Letter ─────────────────────────────────────────────────────

async function generateCoverLetter() {
  const candidate      = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();
  const formats = [];
  if (document.getElementById('fmt-docx').checked) formats.push('docx');
  if (document.getElementById('fmt-pdf').checked)  formats.push('pdf');
  if (document.getElementById('fmt-md').checked)   formats.push('md');

  document.getElementById('btn-cl-text').textContent = 'Generating…';
  document.getElementById('btn-cl-spinner').classList.remove('hidden');
  document.getElementById('btn-cover-letter').disabled = true;
  document.getElementById('cl-results').classList.add('hidden');
  hideError();

  try {
    const res  = await fetch('/generate-cover-letter', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        candidate,
        job_description: jobDescription,
        resume_data: _lastResumeData || {},
        formats,
        template: currentTemplate,
        language: currentLanguage,
        additional_notes: document.getElementById('additional-notes').value.trim(),
      }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) throw new Error(data.error || 'Cover letter generation failed.');

    const letter = data.letter;
    document.getElementById('cl-meta').textContent =
      `${letter.job_title || 'Position'} at ${letter.company || 'Company'}`;
    document.getElementById('cl-text').textContent = letter.text || '';

    const dlEl = document.getElementById('cl-downloads');
    dlEl.innerHTML = '';
    const labels = { docx: '📄 .docx', pdf: '📋 .pdf', md: '📝 .md' };
    Object.entries(data.downloads || {}).forEach(([fmt, url]) => {
      const a = document.createElement('a');
      a.href = url; a.className = 'download-btn'; a.download = '';
      a.textContent = labels[fmt] || fmt;
      dlEl.appendChild(a);
    });

    document.getElementById('cl-results').classList.remove('hidden');
    document.getElementById('cl-results').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    showError(err.message);
  } finally {
    document.getElementById('btn-cl-text').textContent = 'Generate Cover Letter';
    document.getElementById('btn-cl-spinner').classList.add('hidden');
    document.getElementById('btn-cover-letter').disabled = false;
  }
}

// ── Generate Interview Prep ───────────────────────────────────────────────────

async function generateInterviewPrep() {
  const candidate      = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();

  document.getElementById('btn-ip-text').textContent = 'Generating…';
  document.getElementById('btn-ip-spinner').classList.remove('hidden');
  document.getElementById('btn-interview').disabled = true;
  document.getElementById('interview-section').classList.add('hidden');
  hideError();

  try {
    const res  = await fetch('/interview-prep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, job_description: jobDescription, template: currentTemplate, language: currentLanguage, additional_notes: document.getElementById('additional-notes').value.trim() }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) throw new Error(data.error || 'Failed to generate interview prep.');

    renderInterviewPrep(data.questions);
    document.getElementById('interview-section').classList.remove('hidden');
    document.getElementById('interview-section').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    showError(err.message);
  } finally {
    document.getElementById('btn-ip-text').textContent = 'Generate Interview Prep';
    document.getElementById('btn-ip-spinner').classList.add('hidden');
    document.getElementById('btn-interview').disabled = false;
  }
}

function renderInterviewPrep(questions) {
  const grid = document.getElementById('interview-grid');
  grid.innerHTML = '';

  const catClass = {
    'Behavioral':  'cat-behavioral',
    'Technical':   'cat-technical',
    'Situational': 'cat-situational',
    'Motivation':  'cat-motivation',
    'Growth':      'cat-growth',
  };

  questions.forEach((q, i) => {
    const cls = catClass[q.category] || 'cat-behavioral';
    const item = document.createElement('div');
    item.className = 'interview-item';
    item.innerHTML = `
      <div class="interview-header" onclick="toggleInterviewItem(this.parentElement)">
        <span class="interview-category ${cls}">${q.category}</span>
        <span class="interview-question">${q.question}</span>
        <span class="interview-chevron">▾</span>
      </div>
      <div class="interview-body">
        <p class="interview-why"><strong>Why asked:</strong> ${q.why_asked}</p>
        <ul class="interview-points">
          ${(q.talking_points || []).map(pt => `<li>${pt}</li>`).join('')}
        </ul>
      </div>`;
    grid.appendChild(item);
  });
}

function toggleInterviewItem(el) {
  el.classList.toggle('open');
}

// ── Preview Modal ─────────────────────────────────────────────────────────────

function showPreviewModal(url) {
  document.getElementById('preview-iframe').src = url;
  document.getElementById('preview-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closePreviewModal(event) {
  if (event && event.target !== document.getElementById('preview-modal')) return;
  document.getElementById('preview-modal').classList.add('hidden');
  document.getElementById('preview-iframe').src = 'about:blank';
  document.body.style.overflow = '';
}

// ── History ───────────────────────────────────────────────────────────────────

function getHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY)) || []; }
  catch { return []; }
}

function saveHistory(list) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(list));
}

function addToHistory(candidate, jobDescription, resumeData, downloads, fileId) {
  const history = getHistory();
  const jdLines = jobDescription.split('\n').map(l => l.trim()).filter(Boolean);
  const entry = {
    id:          genId(),
    file_id:     fileId,
    profile:     candidate.name || 'Unknown',
    job_snippet: jdLines[0]?.slice(0, 70) || 'Job',
    template:    currentTemplate,
    timestamp:   Date.now(),
    resume_data: resumeData,
    photo:       candidate.photo || '',  // stored separately to re-attach on re-download
    summary:     resumeData.summary || '',
    downloads,
  };
  history.unshift(entry);
  if (history.length > 20) history.length = 20; // keep last 20
  saveHistory(history);
  renderHistory();
}

function renderHistory() {
  const history = getHistory();
  const card    = document.getElementById('history-card');
  const grid    = document.getElementById('history-grid');

  if (!history.length) {
    card.style.display = 'none';
    return;
  }
  card.style.display = '';
  grid.innerHTML = '';

  history.forEach(entry => {
    const time = new Date(entry.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
    const div = document.createElement('div');
    div.className = 'history-card';

    const dlButtons = Object.entries(entry.downloads || {})
      .filter(([fmt]) => fmt !== 'preview')
      .map(([fmt, url]) => `<a class="btn-history" href="${url}" download>↓ .${fmt}</a>`)
      .join('');

    const previewBtn = entry.downloads?.preview
      ? `<button class="btn-history" onclick="showPreviewModal('${entry.downloads.preview}')">👁 Preview</button>`
      : '';

    div.innerHTML = `
      <div class="history-card-title">${entry.profile}</div>
      <div class="history-card-meta">${entry.job_snippet}<br>Template: ${entry.template}</div>
      <div class="history-card-time">${time}</div>
      <div class="history-card-actions">
        <button class="btn-history" onclick="redownloadEntry('${entry.id}')">↻ Re-download</button>
        ${previewBtn}
        ${dlButtons}
        <button class="btn-history danger" onclick="deleteHistoryEntry('${entry.id}')">✕</button>
      </div>`;
    grid.appendChild(div);
  });
}

async function redownloadEntry(id) {
  const history = getHistory();
  const entry   = history.find(e => e.id === id);
  if (!entry) return;

  const formats = [];
  if (document.getElementById('fmt-docx').checked) formats.push('docx');
  if (document.getElementById('fmt-pdf').checked)  formats.push('pdf');
  if (document.getElementById('fmt-md').checked)   formats.push('md');
  if (!formats.length) formats.push('pdf');

  try {
    const resumeWithPhoto = entry.photo
      ? { ...entry.resume_data, photo: entry.photo }
      : entry.resume_data;

    const res  = await fetch('/regenerate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_data: resumeWithPhoto, formats, template: entry.template }),
    });
    const data = await res.json();
    if (!res.ok || !data.success) throw new Error(data.error || 'Re-download failed.');
    showResults(data.downloads, entry.resume_data);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  } catch (err) {
    showError(err.message);
  }
}

function deleteHistoryEntry(id) {
  const history = getHistory().filter(e => e.id !== id);
  saveHistory(history);
  renderHistory();
}

function clearHistory() {
  if (!confirm('Clear all resume history?')) return;
  saveHistory([]);
  renderHistory();
}

// ── Shared UI helpers ─────────────────────────────────────────────────────────

function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.toggle('hidden', !msg);
  if (msg) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function hideError() {
  document.getElementById('error-msg').classList.add('hidden');
}

function _resetRightPanel() {
  document.getElementById('fit-card').classList.add('hidden');
  document.getElementById('generate-section').classList.add('hidden');
  document.getElementById('results').classList.add('hidden');
  document.getElementById('cl-results').classList.add('hidden');
  document.getElementById('interview-section').classList.add('hidden');
  document.getElementById('error-msg').classList.add('hidden');
  document.getElementById('job-description').value = '';
}

function showResults(downloads, resume) {
  const linksEl = document.getElementById('download-links');
  linksEl.innerHTML = '';

  const labels = { docx: '📄 Download .docx', pdf: '📋 Download .pdf', md: '📝 Download .md' };

  Object.entries(downloads).forEach(([fmt, url]) => {
    if (fmt === 'preview') {
      const btn = document.createElement('button');
      btn.className = 'download-btn';
      btn.textContent = '👁 Preview';
      btn.onclick = () => showPreviewModal(url);
      linksEl.appendChild(btn);
    } else {
      const a = document.createElement('a');
      a.href = url; a.className = 'download-btn'; a.download = '';
      a.textContent = labels[fmt] || `Download .${fmt}`;
      linksEl.appendChild(a);
    }
  });

  const previewBox = document.getElementById('preview-box');
  if (resume?.summary) {
    document.getElementById('preview-summary').textContent = resume.summary;
    previewBox.style.display = '';
  } else {
    previewBox.style.display = 'none';
  }

  const resultsEl = document.getElementById('results');
  resultsEl.classList.remove('hidden');
  resultsEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Init ──────────────────────────────────────────────────────────────────────

window.addEventListener('DOMContentLoaded', () => {
  // Restore theme
  const savedTheme = localStorage.getItem('theme') || 'dark';
  applyTheme(savedTheme);

  migrateIfNeeded();
  const activeId = initProfileSelector();
  const profiles  = getProfiles();
  _populateForm(profiles[activeId]?.data || {});

  renderHistory();

  // Auto-save on any change in profile panel
  document.getElementById('panel-info').addEventListener('input',  scheduleSave);
  document.getElementById('panel-info').addEventListener('change', scheduleSave);
});
