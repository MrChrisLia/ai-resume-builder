'use strict';

// ── Storage keys ──────────────────────────────────────────────────────────────
const PROFILES_KEY = 'resumeProfiles';
const ACTIVE_KEY   = 'activeProfileId';
const HISTORY_KEY  = 'resumeHistory';

// ── UI Translations ───────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    'powered-by': 'Powered by Gemini',
    'step1-title': ' Your Profile', 'step2-title': ' Job & Generate',
    'profile-label': 'Profile', 'save-indicator': '✓ Saved',
    'import-label': 'Import:', 'btn-import': 'Resume File',
    'btn-profile-json': 'Profile JSON',
    'import-hint': 'PDF, DOCX, TXT, MD — AI fills your profile',
    'personal-details': 'Personal Details', 'photo-add': 'Add Photo',
    'photo-label': 'Profile Photo',
    'photo-hint-text': 'Optional. Included in PDF and Japanese resume. Passport-style photo recommended.',
    'remove-photo': 'Remove Photo',
    'name-label': 'Full Name', 'email-label': 'Email', 'phone-label': 'Phone',
    'location-label': 'Location', 'linkedin-label': 'LinkedIn URL',
    'github-label': 'GitHub / Portfolio',
    'work-exp': 'Work Experience', 'btn-add-exp': '+ Add Position',
    'education-title': 'Education', 'btn-add-edu': '+ Add Education',
    'skills-title': 'Skills',
    'skills-hint': 'Group skills by category (e.g. "Languages", "Frameworks", "Tools"). Gemini reorders by job relevance.',
    'btn-add-skill': '+ Add Category',
    'languages-title': 'Languages',
    'languages-hint': 'Human languages you speak. Gemini includes these when relevant to the role.',
    'btn-add-lang': '+ Add Language',
    'projects-title': 'Projects', 'btn-add-proj': '+ Add Project',
    'optional': '(optional)',
    'certs-title': 'Certifications / Professional Licenses',
    'btn-add-cert': '+ Add Certification',
    'extra-info-title': 'Additional Information',
    'extra-info-hint': "Awards, publications, volunteer work, hobbies, etc. Gemini decides what's relevant.",
    'extra-info-placeholder': 'e.g. Eagle Scout, published paper on X, volunteered at Y, open source contributor to Z...',
    'job-posting-title': 'Paste the Job Posting',
    'job-posting-hint': 'Include the full job description. Gemini reads it to tailor your resume — and rates how well you match.',
    'jd-placeholder': 'Paste the full job description here...',
    'additional-notes-label': 'Anything else we should know before generating?',
    'notes-placeholder': "e.g. I'm open to relocation, targeting a senior role, prefer not to mention my gap year, emphasize leadership over technical skills…",
    'btn-fit-text': 'Check Job Fit', 'fit-card-title': 'Job Fit Analysis',
    'strengths-title': 'Strengths', 'gaps-title': 'Gaps / Areas to Address',
    'output-formats-title': 'Output Formats', 'template-title': 'Resume Template',
    'lang-selector-title': 'Content Language',
    'lang-selector-hint': 'The language Gemini writes the resume in — independent of the visual template.',
    'tmpl-modern-name': 'Modern', 'tmpl-modern-desc': 'Clean, ATS-friendly',
    'tmpl-classic-name': 'Classic', 'tmpl-classic-desc': 'Traditional serif',
    'tmpl-minimal-name': 'Minimal', 'tmpl-minimal-desc': 'Ultra-clean',
    'btn-generate-text': 'Generate Tailored Resume',
    'btn-cl-text': 'Generate Cover Letter', 'btn-ip-text': 'Generate Interview Prep',
    'results-title': 'Your resume is ready!', 'cl-results-title': 'Cover letter ready!',
    'interview-title': '🎯 Interview Preparation', 'interview-close': '✕ Close',
    'history-title': '📁 Resume History', 'btn-clear-all': 'Clear All',
    'btn-rename': 'Rename', 'btn-new-profile': '+ New',
    'btn-export': 'Export', 'btn-delete': 'Delete',
    'preview-modal-title': 'Resume Preview',
    'analyzing': 'Analyzing…', 'generating': 'Generating…', 'importing': 'Importing…',
    'history-redownload': '↻ Re-download', 'history-preview': '👁 Preview',
    'history-template': 'Template:',
    'clear-history-confirm': 'Clear all resume history?',
    'delete-profile-confirm': 'Delete "{name}"? This cannot be undone.',
    'err-no-name': 'Please enter your full name.',
    'err-no-job': 'Please paste the job description.',
    'err-no-format': 'Select at least one output format.',
    'err-import-json': 'Could not parse JSON file.',
    'err-import-prefix': 'Import failed: ',
    // Entry-block template labels
    'tpl-company': 'Company', 'tpl-job-title': 'Job Title',
    'tpl-start-date': 'Start Date', 'tpl-end-date': 'End Date',
    'tpl-responsibilities': 'Responsibilities & Achievements',
    'tpl-school': 'School / University / Platform',
    'tpl-graduation': 'Graduation / Completion Year',
    'tpl-degree': 'Degree / Course', 'tpl-field': 'Field of Study',
    'tpl-category': 'Category', 'tpl-skills-csv': 'Skills (comma-separated)',
    'tpl-lang-name': 'Language', 'tpl-proficiency': 'Proficiency',
    'tpl-certificate': 'Certificate',
    'opt-native': 'Native', 'opt-fluent': 'Fluent',
    'opt-professional': 'Professional Working',
    'opt-conversational': 'Conversational', 'opt-basic': 'Basic',
    'tpl-project-name': 'Project Name', 'tpl-technologies': 'Technologies',
    'tpl-description': 'Description', 'tpl-cert-label': 'Certification',
  },
  ja: {
    'powered-by': 'Gemini搭載',
    'step1-title': ' プロフィール', 'step2-title': ' 求人・生成',
    'profile-label': 'プロフィール', 'save-indicator': '✓ 保存済み',
    'import-label': 'インポート:', 'btn-import': '履歴書ファイル',
    'btn-profile-json': 'プロフィールJSON',
    'import-hint': 'PDF・DOCX・TXT・MD — AIがプロフィールを入力',
    'personal-details': '個人情報', 'photo-add': '写真追加',
    'photo-label': 'プロフィール写真',
    'photo-hint-text': '任意。PDFと履歴書に含まれます。証明写真推奨。',
    'remove-photo': '写真を削除',
    'name-label': '氏名', 'email-label': 'メールアドレス', 'phone-label': '電話番号',
    'location-label': '住所', 'linkedin-label': 'LinkedIn URL',
    'github-label': 'GitHub / ポートフォリオ',
    'work-exp': '職務経歴', 'btn-add-exp': '＋職歴を追加',
    'education-title': '学歴', 'btn-add-edu': '＋学歴を追加',
    'skills-title': 'スキル',
    'skills-hint': 'カテゴリ別にグループ化（例：言語、フレームワーク、ツール）。Geminiが関連度順に並び替えます。',
    'btn-add-skill': '＋カテゴリを追加',
    'languages-title': '語学',
    'languages-hint': '話せる言語を入力してください。Geminiが役割に応じて含めます。',
    'btn-add-lang': '＋言語を追加',
    'projects-title': 'プロジェクト', 'btn-add-proj': '＋プロジェクトを追加',
    'optional': '（任意）',
    'certs-title': '資格・免許', 'btn-add-cert': '＋資格を追加',
    'extra-info-title': 'その他',
    'extra-info-hint': '受賞歴、出版物、ボランティア、趣味など。Geminiが関連性を判断します。',
    'extra-info-placeholder': '例：受賞歴、論文発表、ボランティア活動、オープンソース貢献...',
    'job-posting-title': '求人票を貼り付け',
    'job-posting-hint': '求人票の全文を貼り付けてください。Geminiが履歴書をカスタマイズし、マッチ度を評価します。',
    'jd-placeholder': '求人票の全文をここに貼り付けてください...',
    'additional-notes-label': '生成前に伝えておきたいことはありますか？',
    'notes-placeholder': '例：転勤可、シニアポジション希望、ギャップイヤーは触れないで、リーダーシップを強調して...',
    'btn-fit-text': '適性チェック', 'fit-card-title': '適性分析',
    'strengths-title': '強み', 'gaps-title': 'ギャップ・改善点',
    'output-formats-title': '出力形式', 'template-title': '履歴書テンプレート',
    'lang-selector-title': '生成言語',
    'lang-selector-hint': 'Geminiが履歴書を生成する言語です（テンプレートに依存しません）。',
    'tmpl-modern-name': 'モダン', 'tmpl-modern-desc': 'クリーン・ATS対応',
    'tmpl-classic-name': 'クラシック', 'tmpl-classic-desc': '伝統的セリフ体',
    'tmpl-minimal-name': 'ミニマル', 'tmpl-minimal-desc': '超シンプル',
    'btn-generate-text': '履歴書を生成',
    'btn-cl-text': '送付状を生成', 'btn-ip-text': '面接対策を生成',
    'results-title': '履歴書が完成しました！', 'cl-results-title': '送付状が完成しました！',
    'interview-title': '🎯 面接準備', 'interview-close': '✕ 閉じる',
    'history-title': '📁 履歴書履歴', 'btn-clear-all': 'すべて削除',
    'btn-rename': '名前変更', 'btn-new-profile': '＋新規',
    'btn-export': 'エクスポート', 'btn-delete': '削除',
    'preview-modal-title': 'プレビュー',
    'analyzing': '分析中…', 'generating': '生成中…', 'importing': 'インポート中…',
    'history-redownload': '↻ 再ダウンロード', 'history-preview': '👁 プレビュー',
    'history-template': 'テンプレート:',
    'clear-history-confirm': '履歴書の履歴をすべて削除しますか？',
    'delete-profile-confirm': '「{name}」を削除しますか？この操作は元に戻せません。',
    'err-no-name': '氏名を入力してください。',
    'err-no-job': '求人票を貼り付けてください。',
    'err-no-format': '出力形式を1つ以上選択してください。',
    'err-import-json': 'JSONファイルを解析できませんでした。',
    'err-import-prefix': 'インポート失敗: ',
    // Entry-block template labels
    'tpl-company': '会社名', 'tpl-job-title': '役職名',
    'tpl-start-date': '開始年月', 'tpl-end-date': '終了年月',
    'tpl-responsibilities': '職務内容・実績',
    'tpl-school': '学校 / 大学 / プラットフォーム',
    'tpl-graduation': '卒業・修了年', 'tpl-degree': '学位 / コース',
    'tpl-field': '専攻・学科', 'tpl-category': 'カテゴリ',
    'tpl-skills-csv': 'スキル（カンマ区切り）',
    'tpl-lang-name': '言語', 'tpl-proficiency': '習熟度',
    'tpl-certificate': '資格・検定',
    'opt-native': 'ネイティブ', 'opt-fluent': '流暢',
    'opt-professional': 'ビジネスレベル',
    'opt-conversational': '日常会話レベル', 'opt-basic': '基礎レベル',
    'tpl-project-name': 'プロジェクト名', 'tpl-technologies': '使用技術',
    'tpl-description': '概要', 'tpl-cert-label': '資格・免許',
  },
  tw: {
    'powered-by': '由 Gemini 驅動',
    'step1-title': ' 個人資料', 'step2-title': ' 職缺與生成',
    'profile-label': '資料', 'save-indicator': '✓ 已儲存',
    'import-label': '匯入：', 'btn-import': '履歷檔案',
    'btn-profile-json': '資料JSON',
    'import-hint': 'PDF、DOCX、TXT、MD — AI 自動填寫資料',
    'personal-details': '個人資料', 'photo-add': '新增照片',
    'photo-label': '大頭照',
    'photo-hint-text': '選填。包含於PDF與日式履歷中。建議使用證件照。',
    'remove-photo': '移除照片',
    'name-label': '姓名', 'email-label': '電子郵件', 'phone-label': '電話',
    'location-label': '地址', 'linkedin-label': 'LinkedIn 網址',
    'github-label': 'GitHub / 作品集',
    'work-exp': '工作經歷', 'btn-add-exp': '＋新增職位',
    'education-title': '學歷', 'btn-add-edu': '＋新增學歷',
    'skills-title': '技能',
    'skills-hint': '依類別分組（如程式語言、框架、工具）。Gemini 會依職缺相關度排序。',
    'btn-add-skill': '＋新增類別',
    'languages-title': '語言',
    'languages-hint': '您所會的語言。Gemini 會在相關職位中加入這些資訊。',
    'btn-add-lang': '＋新增語言',
    'projects-title': '專案', 'btn-add-proj': '＋新增專案',
    'optional': '（選填）',
    'certs-title': '證照與專業執照', 'btn-add-cert': '＋新增證照',
    'extra-info-title': '其他資訊',
    'extra-info-hint': '獎項、出版物、志工經歷、興趣等。Gemini 會判斷相關性。',
    'extra-info-placeholder': '例：獲獎紀錄、論文發表、志工服務、開源專案貢獻...',
    'job-posting-title': '貼上職缺說明',
    'job-posting-hint': '貼上完整職缺說明。Gemini 將據此客製化您的履歷，並評估符合度。',
    'jd-placeholder': '在此貼上完整的職缺說明...',
    'additional-notes-label': '生成前還有什麼需要告訴我們的嗎？',
    'notes-placeholder': '例：可接受外派、應徵資深職位、不提空窗期、強調領導力而非技術...',
    'btn-fit-text': '檢查職缺適合度', 'fit-card-title': '職缺適合度分析',
    'strengths-title': '優勢', 'gaps-title': '落差 / 待加強項目',
    'output-formats-title': '輸出格式', 'template-title': '履歷範本',
    'lang-selector-title': '生成語言',
    'lang-selector-hint': 'Gemini 生成履歷的語言，與版面範本無關。',
    'tmpl-modern-name': '現代風', 'tmpl-modern-desc': '簡潔，ATS 友善',
    'tmpl-classic-name': '經典', 'tmpl-classic-desc': '傳統襯線字體',
    'tmpl-minimal-name': '極簡', 'tmpl-minimal-desc': '超簡約',
    'btn-generate-text': '生成客製化履歷',
    'btn-cl-text': '生成求職信', 'btn-ip-text': '生成面試準備資料',
    'results-title': '您的履歷已完成！', 'cl-results-title': '求職信已完成！',
    'interview-title': '🎯 面試準備', 'interview-close': '✕ 關閉',
    'history-title': '📁 履歷紀錄', 'btn-clear-all': '清除全部',
    'btn-rename': '重新命名', 'btn-new-profile': '＋新增',
    'btn-export': '匯出', 'btn-delete': '刪除',
    'preview-modal-title': '履歷預覽',
    'analyzing': '分析中…', 'generating': '生成中…', 'importing': '匯入中…',
    'history-redownload': '↻ 重新下載', 'history-preview': '👁 預覽',
    'history-template': '範本:',
    'clear-history-confirm': '清除所有履歷紀錄？',
    'delete-profile-confirm': '刪除「{name}」？此操作無法復原。',
    'err-no-name': '請輸入您的姓名。',
    'err-no-job': '請貼上職缺說明。',
    'err-no-format': '請選擇至少一種輸出格式。',
    'err-import-json': '無法解析 JSON 檔案。',
    'err-import-prefix': '匯入失敗：',
    // Entry-block template labels
    'tpl-company': '公司名稱', 'tpl-job-title': '職稱',
    'tpl-start-date': '開始日期', 'tpl-end-date': '結束日期',
    'tpl-responsibilities': '職責與成就',
    'tpl-school': '學校 / 大學 / 平台',
    'tpl-graduation': '畢業 / 結業年份', 'tpl-degree': '學位 / 課程',
    'tpl-field': '主修科系', 'tpl-category': '類別',
    'tpl-skills-csv': '技能（逗號分隔）',
    'tpl-lang-name': '語言', 'tpl-proficiency': '熟練程度',
    'tpl-certificate': '語言證照',
    'opt-native': '母語', 'opt-fluent': '流利',
    'opt-professional': '商務用',
    'opt-conversational': '日常對話', 'opt-basic': '基礎',
    'tpl-project-name': '專案名稱', 'tpl-technologies': '使用技術',
    'tpl-description': '專案描述', 'tpl-cert-label': '證照',
  },
};

let saveTimer       = null;
let currentTemplate = 'modern';
let currentLanguage = 'english';
let currentUILang   = 'en';
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

// ── UI language (i18n) ────────────────────────────────────────────────────────

function t(key) {
  return (TRANSLATIONS[currentUILang] || TRANSLATIONS.en)[key] ?? TRANSLATIONS.en[key] ?? key;
}

function _applyTranslations(root) {
  root.querySelectorAll('[data-i18n]').forEach(node => {
    const val = t(node.getAttribute('data-i18n'));
    if (val) node.textContent = val;
  });
  root.querySelectorAll('[data-i18n-placeholder]').forEach(node => {
    const val = t(node.getAttribute('data-i18n-placeholder'));
    if (val) node.placeholder = val;
  });
}

function setUILang(lang, el) {
  currentUILang = lang;
  localStorage.setItem('uiLang', lang);
  document.documentElement.lang = lang === 'ja' ? 'ja' : lang === 'tw' ? 'zh-TW' : 'en';
  document.querySelectorAll('.ui-lang-btn').forEach(b => b.classList.remove('selected'));
  if (el) el.classList.add('selected');
  _applyTranslations(document);
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
  if (!confirm(t('delete-profile-confirm').replace('{name}', profileName))) return;
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
    showError(t('err-import-json'));
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
  const frag = document.getElementById(id).content.cloneNode(true);
  _applyTranslations(frag);
  return frag;
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
  btn.textContent = t('importing');

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
    showError(t('err-import-prefix') + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = t('btn-import');
  }
}

// ── Analyze Job Fit ───────────────────────────────────────────────────────────

async function analyzeFit() {
  const candidate     = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();

  if (!candidate.name) return showError(t('err-no-name'));
  if (!jobDescription)  return showError(t('err-no-job'));

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
    if (!res.ok || !data.success) {
      if (data.retry_after) startCountdown(data.retry_after, 'error-msg');
      throw new Error(data.error || 'Analysis failed.');
    }
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
  document.getElementById('btn-fit-text').textContent = on ? t('analyzing') : t('btn-fit-text');
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

  function _makeList(className, title, items) {
    const div = document.createElement('div');
    div.className = className;
    const h4 = document.createElement('h4');
    h4.textContent = title;
    const ul = document.createElement('ul');
    items.forEach(item => {
      const li = document.createElement('li');
      li.textContent = item;
      ul.appendChild(li);
    });
    div.appendChild(h4);
    div.appendChild(ul);
    return div;
  }

  if (fit.strengths?.length)
    sectionsEl.appendChild(_makeList('fit-list fit-strengths', t('strengths-title'), fit.strengths));
  if (fit.gaps?.length)
    sectionsEl.appendChild(_makeList('fit-list fit-gaps', t('gaps-title'), fit.gaps));

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

  if (!formats.length) return showError(t('err-no-format'), 'error-msg-generate');

  setGenLoading(true);
  hideError('error-msg-generate');
  document.getElementById('results').classList.add('hidden');

  try {
    const res  = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, job_description: jobDescription, formats, template: currentTemplate, language: currentLanguage, additional_notes: document.getElementById('additional-notes').value.trim() }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) {
      if (data.retry_after) startCountdown(data.retry_after, 'error-msg-generate');
      throw new Error(data.error || 'Generation failed.');
    }

    _lastResumeData = data.resume;
    showResults(data.downloads, data.resume);
    addToHistory(candidate, jobDescription, data.resume, data.downloads, data.file_id);

    // Reveal cover letter & interview prep buttons
    document.getElementById('btn-cover-letter').classList.remove('hidden');
    document.getElementById('btn-interview').classList.remove('hidden');
  } catch (err) {
    showError(err.message, 'error-msg-generate');
  } finally {
    setGenLoading(false);
  }
}

function setGenLoading(on) {
  const btn = document.getElementById('btn-generate');
  btn.disabled = on;
  document.getElementById('btn-text').textContent = on ? t('generating') : t('btn-generate-text');
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

  document.getElementById('btn-cl-text').textContent = t('generating');
  document.getElementById('btn-cl-spinner').classList.remove('hidden');
  document.getElementById('btn-cover-letter').disabled = true;
  document.getElementById('cl-results').classList.add('hidden');
  hideError('error-msg-generate');

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
    if (!res.ok || !data.success) {
      if (data.retry_after) startCountdown(data.retry_after, 'error-msg-generate');
      throw new Error(data.error || 'Cover letter generation failed.');
    }

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
    showError(err.message, 'error-msg-generate');
  } finally {
    document.getElementById('btn-cl-text').textContent = t('btn-cl-text');
    document.getElementById('btn-cl-spinner').classList.add('hidden');
    document.getElementById('btn-cover-letter').disabled = false;
  }
}

// ── Generate Interview Prep ───────────────────────────────────────────────────

async function generateInterviewPrep() {
  const candidate      = collectCandidate();
  const jobDescription = document.getElementById('job-description').value.trim();

  document.getElementById('btn-ip-text').textContent = t('generating');
  document.getElementById('btn-ip-spinner').classList.remove('hidden');
  document.getElementById('btn-interview').disabled = true;
  document.getElementById('interview-section').classList.add('hidden');
  hideError('error-msg-generate');

  try {
    const res  = await fetch('/interview-prep', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ candidate, job_description: jobDescription, template: currentTemplate, language: currentLanguage, additional_notes: document.getElementById('additional-notes').value.trim() }),
    });
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (!res.ok || !data.success) {
      if (data.retry_after) startCountdown(data.retry_after, 'error-msg-generate');
      throw new Error(data.error || 'Failed to generate interview prep.');
    }

    renderInterviewPrep(data.questions);
    document.getElementById('interview-section').classList.remove('hidden');
    document.getElementById('interview-section').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  } catch (err) {
    showError(err.message, 'error-msg-generate');
  } finally {
    document.getElementById('btn-ip-text').textContent = t('btn-ip-text');
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

  questions.forEach((q) => {
    const cls  = catClass[q.category] || 'cat-behavioral';
    const item = document.createElement('div');
    item.className = 'interview-item';

    const header = document.createElement('div');
    header.className = 'interview-header';
    header.onclick = function() { toggleInterviewItem(this.parentElement); };

    const catSpan = document.createElement('span');
    catSpan.className = `interview-category ${cls}`;
    catSpan.textContent = q.category || '';

    const qSpan = document.createElement('span');
    qSpan.className = 'interview-question';
    qSpan.textContent = q.question || '';

    const chevron = document.createElement('span');
    chevron.className = 'interview-chevron';
    chevron.textContent = '▾';

    header.appendChild(catSpan);
    header.appendChild(qSpan);
    header.appendChild(chevron);

    const body = document.createElement('div');
    body.className = 'interview-body';

    const why = document.createElement('p');
    why.className = 'interview-why';
    const strong = document.createElement('strong');
    strong.textContent = 'Why asked: ';
    why.appendChild(strong);
    why.appendChild(document.createTextNode(q.why_asked || ''));

    const ul = document.createElement('ul');
    ul.className = 'interview-points';
    (q.talking_points || []).forEach(pt => {
      const li = document.createElement('li');
      li.textContent = pt;
      ul.appendChild(li);
    });

    body.appendChild(why);
    body.appendChild(ul);
    item.appendChild(header);
    item.appendChild(body);
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
  try {
    const ttl = 7 * 24 * 60 * 60 * 1000; // 7 days
    const all = JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
    return all.filter(e => Date.now() - (e.timestamp || 0) < ttl);
  } catch { return []; }
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

    const titleEl = document.createElement('div');
    titleEl.className = 'history-card-title';
    titleEl.textContent = entry.profile;

    const metaEl = document.createElement('div');
    metaEl.className = 'history-card-meta';
    metaEl.appendChild(document.createTextNode(entry.job_snippet || ''));
    metaEl.appendChild(document.createElement('br'));
    metaEl.appendChild(document.createTextNode(`${t('history-template')} ${entry.template || ''}`));

    const timeEl = document.createElement('div');
    timeEl.className = 'history-card-time';
    timeEl.textContent = time;

    const actions = document.createElement('div');
    actions.className = 'history-card-actions';

    const redownloadBtn = document.createElement('button');
    redownloadBtn.className = 'btn-history';
    redownloadBtn.textContent = t('history-redownload');
    redownloadBtn.onclick = () => redownloadEntry(entry.id);
    actions.appendChild(redownloadBtn);

    if (entry.downloads?.preview) {
      const prevBtn = document.createElement('button');
      prevBtn.className = 'btn-history';
      prevBtn.textContent = t('history-preview');
      const previewUrl = entry.downloads.preview;
      prevBtn.onclick = () => showPreviewModal(previewUrl);
      actions.appendChild(prevBtn);
    }

    Object.entries(entry.downloads || {}).filter(([fmt]) => fmt !== 'preview').forEach(([fmt, url]) => {
      const a = document.createElement('a');
      a.className = 'btn-history';
      a.href = url;
      a.download = '';
      a.textContent = `↓ .${fmt}`;
      actions.appendChild(a);
    });

    const delBtn = document.createElement('button');
    delBtn.className = 'btn-history danger';
    delBtn.textContent = '✕';
    delBtn.onclick = () => deleteHistoryEntry(entry.id);
    actions.appendChild(delBtn);

    div.appendChild(titleEl);
    div.appendChild(metaEl);
    div.appendChild(timeEl);
    div.appendChild(actions);
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
  if (!confirm(t('clear-history-confirm'))) return;
  saveHistory([]);
  renderHistory();
}

// ── Shared UI helpers ─────────────────────────────────────────────────────────

let _countdownTimer = null;

function showError(msg, id = 'error-msg') {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.classList.toggle('hidden', !msg);
  if (msg) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

function startCountdown(seconds, errorId) {
  if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
  const el = document.getElementById(errorId);
  if (!el || seconds <= 0) return;
  let remaining = seconds;
  const span = document.createElement('span');
  span.className = 'retry-countdown';
  span.textContent = ` — retry in ${remaining}s`;
  el.appendChild(span);
  _countdownTimer = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      clearInterval(_countdownTimer);
      _countdownTimer = null;
      span.remove();
    } else {
      span.textContent = ` — retry in ${remaining}s`;
    }
  }, 1000);
}

function hideError(id = null) {
  if (_countdownTimer) { clearInterval(_countdownTimer); _countdownTimer = null; }
  if (id) {
    document.getElementById(id).classList.add('hidden');
  } else {
    document.getElementById('error-msg').classList.add('hidden');
    document.getElementById('error-msg-generate').classList.add('hidden');
  }
}

function _resetRightPanel() {
  document.getElementById('fit-card').classList.add('hidden');
  document.getElementById('generate-section').classList.add('hidden');
  document.getElementById('results').classList.add('hidden');
  document.getElementById('cl-results').classList.add('hidden');
  document.getElementById('interview-section').classList.add('hidden');
  hideError();
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
      btn.textContent = t('history-preview');
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

  // Restore UI language
  const savedUILang = localStorage.getItem('uiLang') || 'en';
  const uiLangBtn = document.querySelector(`.ui-lang-btn[data-lang="${savedUILang}"]`);
  setUILang(savedUILang, uiLangBtn);

  migrateIfNeeded();
  const activeId = initProfileSelector();
  const profiles  = getProfiles();
  _populateForm(profiles[activeId]?.data || {});

  renderHistory();

  // Auto-load profile from server-side profiles/ directory if current profile is empty
  if (!profiles[activeId]?.data?.name) {
    fetch('/auto-load-profile')
      .then(r => r.json())
      .then(data => {
        if (data.found && data.profile) {
          _populateForm(data.profile);
          scheduleSave();
          console.info(`Auto-loaded profile from profiles/${data.filename}`);
        }
      })
      .catch(() => {});  // silently ignore — auto-load is best-effort
  }

  // Auto-save on any change in profile panel
  document.getElementById('panel-info').addEventListener('input',  scheduleSave);
  document.getElementById('panel-info').addEventListener('change', scheduleSave);
});
