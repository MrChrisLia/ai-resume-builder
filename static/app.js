'use strict';

// ── Storage keys ──────────────────────────────────────────────────────────────
const PROFILES_KEY = 'resumeProfiles';
const ACTIVE_KEY   = 'activeProfileId';
const HISTORY_KEY  = 'resumeHistory';
const APPLICATIONS_KEY = 'jobApplications';
const SAVED_SEARCHES_KEY = 'savedJobSearches';

// ── UI Translations ───────────────────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    'powered-by': 'Powered by Gemini',
    'step1-title': ' Your Profile', 'step2-title': ' Job & Generate',
    'tab-builder': 'Resume Builder', 'tab-job-search': 'Job Search', 'tab-tracker': 'Application Tracker',
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
    'job-board-title': 'Find your next role',
    'job-board-subtitle': 'Search remote postings for the United States, Japan, and Taiwan, then send the best match into your resume workflow.',
    'job-search-title': ' Job Search',
    'job-search-card-title': 'Find Open Roles',
    'job-title-label': 'Job Title or Keywords',
    'job-title-placeholder': 'Product Manager, React, Data Analyst',
    'job-location-search-label': 'City or Remote Keyword',
    'job-location-placeholder': 'Tokyo, Taipei, remote',
    'job-country-label': 'Country',
    'job-country-us': 'United States',
    'job-country-japan': 'Japan',
    'job-country-taiwan': 'Taiwan',
    'job-country-any': 'All target countries',
    'job-type-label': 'Job Type',
    'job-type-any': 'Any type',
    'job-type-full-time': 'Full time',
    'job-type-contract': 'Contract',
    'job-type-part-time': 'Part time',
    'job-type-freelance': 'Freelance',
    'job-type-internship': 'Internship',
    'job-deep-search-label': 'Deep search experimental sources',
    'btn-search-jobs': 'Search Jobs',
    'btn-cancel-search': 'Cancel Search',
    'job-search-cancelled': 'Search cancelled.',
    'job-results-title': 'Results',
    'job-empty-title': 'Search by title and location',
    'job-empty-copy': 'Results can be opened directly or sent into the resume builder.',
    'job-searching': 'Searching...',
    'job-no-results': 'No matching jobs found.',
    'job-results-count': '{count} jobs found',
    'job-source-label': 'Source',
    'job-posted-label': 'Posted',
    'job-salary-label': 'Salary',
    'job-use-description': 'Use Job Posting',
    'job-view-posting': 'View Posting',
    'job-open-maps': 'Open in Maps',
    'job-search-error-prefix': 'Job search failed: ',
    'job-filters-title': 'Filters',
    'job-clear-filters': 'Clear',
    'job-sort-label': 'Sort By',
    'job-sort-relevance': 'Relevance',
    'job-sort-newest': 'Newest',
    'job-sort-company': 'Company',
    'job-source-filter-label': 'Source',
    'job-source-any': 'Any source',
    'job-japanese-filter-label': 'Japanese Language',
    'job-japanese-any': 'Any',
    'job-japanese-none': 'No Japanese required',
    'job-japanese-required': 'Japanese required',
    'job-japanese-business': 'Business+',
    'job-japanese-fluent': 'Fluent',
    'job-english-filter-label': 'English Language',
    'job-english-any': 'Any',
    'job-english-none': 'No English required',
    'job-english-required': 'English required',
    'job-english-business': 'Business+',
    'job-english-fluent': 'Fluent',
    'job-english-only': 'English-only',
    'job-visa-filter-label': 'Visa Sponsorship',
    'job-visa-any': 'Any',
    'job-visa-available': 'Sponsorship available',
    'job-visa-unavailable': 'No sponsorship',
    'job-visa-auth-required': 'Work authorization required',
    'job-safety-filter-label': 'Public Safety',
    'job-safety-any': 'Any score',
    'job-safety-5': '5 stars',
    'job-safety-4': '4+ stars',
    'job-safety-3': '3+ stars',
    'job-clearance-filter-label': 'Security Clearance',
    'job-clearance-any': 'Any',
    'job-clearance-required': 'Required only',
    'job-clearance-not-required': 'No clearance required',
    'job-filter-note': 'Country matching includes regional eligibility such as Americas, Asia, APAC, and Worldwide.',
    'job-detail-empty-title': 'Select a job',
    'job-detail-empty-copy': 'Open a result to review the full posting before sending it into the resume builder.',
    'job-queued': 'Search queued...',
    'btn-save-search': 'Save Current Search',
    'job-save-search-hint': 'Reuse these keywords, country, location, and filters later.',
    'job-saved-searches-title': 'Saved Searches',
    'job-saved-search-empty': 'No saved searches yet.',
    'job-run-search': 'Run',
    'job-delete-search': 'Delete',
    'job-saved-search-saved': 'Search saved.',
    'job-new-results': '{count} new since last run',
    'job-last-run': 'Last run',
    'job-application-tracker-title': 'Application Tracker',
    'job-application-tracker-subtitle': 'Track saved roles, application status, notes, and generated resume links.',
    'job-application-tracker-empty': 'No tracked applications yet.',
    'job-application-clear-all': 'Clear Tracker',
    'job-application-clear-confirm': 'Clear all tracked applications?',
    'job-application-count': '{count} tracked applications',
    'job-application-delete': 'Delete',
    'job-application-status-label': 'Status',
    'job-application-notes-label': 'Notes',
    'job-application-notes-placeholder': 'Recruiter name, next step, follow-up date...',
    'job-application-updated': 'Updated',
    'job-application-open': 'Open',
    'job-resume-linked': 'Resume linked',
    'job-status-untracked': 'Not tracked',
    'job-status-interested': 'Interested',
    'job-status-applied': 'Applied',
    'job-status-interviewing': 'Interviewing',
    'job-status-offer': 'Offer',
    'job-status-rejected': 'Rejected',
    'job-status-archived': 'Archived',
    'job-description-title': 'Job Description',
    'job-match-hint': 'Send this posting to Job & Generate to check fit and tailor your resume.',
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
    'tpl-cert-year': 'Year Achieved',
  },
  ja: {
    'powered-by': 'Gemini搭載',
    'step1-title': ' プロフィール', 'step2-title': ' 求人・生成',
    'tab-builder': '履歴書作成', 'tab-job-search': '求人検索', 'tab-tracker': '応募管理',
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
    'job-board-title': '次の仕事を探す',
    'job-board-subtitle': '米国・日本・台湾向けのリモート求人を検索し、最適な求人を履歴書作成に送れます。',
    'job-search-title': ' 求人検索',
    'job-search-card-title': '募集中の求人を検索',
    'job-title-label': '職種・キーワード',
    'job-title-placeholder': 'Product Manager, React, Data Analyst',
    'job-location-search-label': '都市・リモート条件',
    'job-location-placeholder': 'Tokyo, Taipei, remote',
    'job-country-label': '国',
    'job-country-us': '米国',
    'job-country-japan': '日本',
    'job-country-taiwan': '台湾',
    'job-country-any': '対象国すべて',
    'job-type-label': '雇用形態',
    'job-type-any': 'すべて',
    'job-type-full-time': '正社員',
    'job-type-contract': '契約',
    'job-type-part-time': 'パートタイム',
    'job-type-freelance': 'フリーランス',
    'job-type-internship': 'インターン',
    'job-deep-search-label': '実験的な求人元も検索',
    'btn-search-jobs': '求人を検索',
    'btn-cancel-search': '検索をキャンセル',
    'job-search-cancelled': '検索をキャンセルしました。',
    'job-results-title': '検索結果',
    'job-empty-title': '職種と勤務地で検索',
    'job-empty-copy': '求人を開くか、履歴書作成に送ることができます。',
    'job-searching': '検索中...',
    'job-no-results': '一致する求人が見つかりません。',
    'job-results-count': '{count}件の求人',
    'job-source-label': '提供元',
    'job-posted-label': '掲載日',
    'job-salary-label': '給与',
    'job-use-description': '求人票を使用',
    'job-view-posting': '求人を見る',
    'job-open-maps': '地図で開く',
    'job-search-error-prefix': '求人検索に失敗しました: ',
    'job-filters-title': 'フィルター',
    'job-clear-filters': 'クリア',
    'job-sort-label': '並び替え',
    'job-sort-relevance': '関連度',
    'job-sort-newest': '新着順',
    'job-sort-company': '会社名',
    'job-source-filter-label': '提供元',
    'job-source-any': 'すべての提供元',
    'job-japanese-filter-label': '日本語条件',
    'job-japanese-any': 'すべて',
    'job-japanese-none': '日本語不要',
    'job-japanese-required': '日本語必須',
    'job-japanese-business': 'ビジネス以上',
    'job-japanese-fluent': '流暢',
    'job-english-filter-label': '英語条件',
    'job-english-any': 'すべて',
    'job-english-none': '英語不要',
    'job-english-required': '英語必須',
    'job-english-business': 'ビジネス以上',
    'job-english-fluent': '流暢',
    'job-english-only': '英語のみ',
    'job-visa-filter-label': 'ビザスポンサー',
    'job-visa-any': 'すべて',
    'job-visa-available': 'スポンサーあり',
    'job-visa-unavailable': 'スポンサーなし',
    'job-visa-auth-required': '就労資格必須',
    'job-safety-filter-label': '治安スコア',
    'job-safety-any': 'すべて',
    'job-safety-5': '5つ星',
    'job-safety-4': '4つ星以上',
    'job-safety-3': '3つ星以上',
    'job-clearance-filter-label': 'セキュリティクリアランス',
    'job-clearance-any': 'すべて',
    'job-clearance-required': '必須のみ',
    'job-clearance-not-required': '不要のみ',
    'job-filter-note': '国フィルターは Americas、Asia、APAC、Worldwide などの地域条件にも対応します。',
    'job-detail-empty-title': '求人を選択',
    'job-detail-empty-copy': '求人詳細を確認してから履歴書作成に送れます。',
    'job-queued': '検索をキューに追加しました...',
    'btn-save-search': '現在の検索を保存',
    'job-save-search-hint': 'キーワード、国、勤務地、フィルターを後で再利用できます。',
    'job-saved-searches-title': '保存した検索',
    'job-saved-search-empty': '保存した検索はまだありません。',
    'job-run-search': '実行',
    'job-delete-search': '削除',
    'job-saved-search-saved': '検索を保存しました。',
    'job-new-results': '前回から{count}件の新着',
    'job-last-run': '前回実行',
    'job-application-tracker-title': '応募管理',
    'job-application-tracker-subtitle': '保存した求人、応募ステータス、メモ、生成済み履歴書リンクを管理します。',
    'job-application-tracker-empty': '管理中の応募はまだありません。',
    'job-application-clear-all': '管理リストをクリア',
    'job-application-clear-confirm': '管理中の応募をすべて削除しますか？',
    'job-application-count': '{count}件の応募管理',
    'job-application-delete': '削除',
    'job-application-status-label': 'ステータス',
    'job-application-notes-label': 'メモ',
    'job-application-notes-placeholder': '担当者、次のステップ、フォロー日など...',
    'job-application-updated': '更新',
    'job-application-open': '開く',
    'job-resume-linked': '履歴書リンク済み',
    'job-status-untracked': '未管理',
    'job-status-interested': '興味あり',
    'job-status-applied': '応募済み',
    'job-status-interviewing': '面接中',
    'job-status-offer': '内定',
    'job-status-rejected': '不採用',
    'job-status-archived': 'アーカイブ',
    'job-description-title': '求人内容',
    'job-match-hint': 'この求人票を「求人・生成」に送って適性チェックと履歴書作成に使います。',
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
    'tpl-cert-year': '取得年',
  },
  tw: {
    'powered-by': '由 Gemini 驅動',
    'step1-title': ' 個人資料', 'step2-title': ' 職缺與生成',
    'tab-builder': '履歷產生器', 'tab-job-search': '職缺搜尋', 'tab-tracker': '應徵追蹤',
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
    'job-board-title': '尋找下一份工作',
    'job-board-subtitle': '搜尋美國、日本與台灣適用的遠端職缺，並將最合適的職缺送入履歷流程。',
    'job-search-title': ' 職缺搜尋',
    'job-search-card-title': '尋找開放職缺',
    'job-title-label': '職稱或關鍵字',
    'job-title-placeholder': 'Product Manager, React, Data Analyst',
    'job-location-search-label': '城市或遠端條件',
    'job-location-placeholder': 'Tokyo, Taipei, remote',
    'job-country-label': '國家',
    'job-country-us': '美國',
    'job-country-japan': '日本',
    'job-country-taiwan': '台灣',
    'job-country-any': '所有目標國家',
    'job-type-label': '工作類型',
    'job-type-any': '不限',
    'job-type-full-time': '全職',
    'job-type-contract': '約聘',
    'job-type-part-time': '兼職',
    'job-type-freelance': '自由接案',
    'job-type-internship': '實習',
    'job-deep-search-label': '深度搜尋實驗來源',
    'btn-search-jobs': '搜尋職缺',
    'btn-cancel-search': '取消搜尋',
    'job-search-cancelled': '已取消搜尋。',
    'job-results-title': '搜尋結果',
    'job-empty-title': '依職稱和地點搜尋',
    'job-empty-copy': '可直接開啟職缺，或送入履歷產生器。',
    'job-searching': '搜尋中...',
    'job-no-results': '找不到符合的職缺。',
    'job-results-count': '找到 {count} 個職缺',
    'job-source-label': '來源',
    'job-posted-label': '刊登',
    'job-salary-label': '薪資',
    'job-use-description': '使用職缺內容',
    'job-view-posting': '查看職缺',
    'job-open-maps': '在地圖開啟',
    'job-search-error-prefix': '職缺搜尋失敗：',
    'job-filters-title': '篩選',
    'job-clear-filters': '清除',
    'job-sort-label': '排序',
    'job-sort-relevance': '相關性',
    'job-sort-newest': '最新',
    'job-sort-company': '公司',
    'job-source-filter-label': '來源',
    'job-source-any': '不限來源',
    'job-japanese-filter-label': '日文條件',
    'job-japanese-any': '不限',
    'job-japanese-none': '不需日文',
    'job-japanese-required': '需日文',
    'job-japanese-business': '商務以上',
    'job-japanese-fluent': '流利',
    'job-english-filter-label': '英文條件',
    'job-english-any': '不限',
    'job-english-none': '不需英文',
    'job-english-required': '需英文',
    'job-english-business': '商務以上',
    'job-english-fluent': '流利',
    'job-english-only': '僅英文',
    'job-visa-filter-label': '簽證贊助',
    'job-visa-any': '不限',
    'job-visa-available': '提供簽證贊助',
    'job-visa-unavailable': '不提供贊助',
    'job-visa-auth-required': '需工作許可',
    'job-safety-filter-label': '公共安全',
    'job-safety-any': '不限分數',
    'job-safety-5': '5 星',
    'job-safety-4': '4 星以上',
    'job-safety-3': '3 星以上',
    'job-clearance-filter-label': '安全審查',
    'job-clearance-any': '不限',
    'job-clearance-required': '只看需要',
    'job-clearance-not-required': '不需審查',
    'job-filter-note': '國家篩選會納入 Americas、Asia、APAC、Worldwide 等地區資格。',
    'job-detail-empty-title': '選擇職缺',
    'job-detail-empty-copy': '先查看完整職缺，再送入履歷產生器。',
    'job-queued': '搜尋已排入佇列...',
    'btn-save-search': '儲存目前搜尋',
    'job-save-search-hint': '稍後可重複使用這些關鍵字、國家、地點與篩選條件。',
    'job-saved-searches-title': '已儲存搜尋',
    'job-saved-search-empty': '尚無已儲存搜尋。',
    'job-run-search': '執行',
    'job-delete-search': '刪除',
    'job-saved-search-saved': '搜尋已儲存。',
    'job-new-results': '比上次新增 {count} 筆',
    'job-last-run': '上次執行',
    'job-application-tracker-title': '應徵追蹤',
    'job-application-tracker-subtitle': '追蹤已儲存職缺、應徵狀態、備註與已產生履歷連結。',
    'job-application-tracker-empty': '尚無追蹤中的應徵。',
    'job-application-clear-all': '清除追蹤',
    'job-application-clear-confirm': '清除所有應徵追蹤？',
    'job-application-count': '追蹤 {count} 筆應徵',
    'job-application-delete': '刪除',
    'job-application-status-label': '狀態',
    'job-application-notes-label': '備註',
    'job-application-notes-placeholder': '招募人員、下一步、追蹤日期...',
    'job-application-updated': '更新',
    'job-application-open': '開啟',
    'job-resume-linked': '已連結履歷',
    'job-status-untracked': '未追蹤',
    'job-status-interested': '有興趣',
    'job-status-applied': '已投遞',
    'job-status-interviewing': '面試中',
    'job-status-offer': '錄取',
    'job-status-rejected': '未錄取',
    'job-status-archived': '封存',
    'job-description-title': '職缺內容',
    'job-match-hint': '將此職缺送至職缺與生成，用於適配分析與履歷客製化。',
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
    'tpl-cert-year': '取得年份',
  },
};

let saveTimer       = null;
let currentTemplate = 'modern';
let currentLanguage = 'english';
let currentUILang   = 'en';
let _lastResumeData = null; // cached for cover letter & interview prep
let _allJobSearchResults = [];
let _jobSearchResults = [];
let _jobSearchMeta = {};
let _selectedJobId = '';
let _jobSearchPrefilled = false;
let _jobSearchController = null;
let _jobSearchRequestId = 0;
let _jobSearchJobId = '';
let _jobSearchPollTimer = null;
let _jobDetailHydrationId = 0;
let _activeSavedSearchId = '';
let _pendingSavedSearchFilters = null;
let _activeTrackedJobKey = '';

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
  populateSourceFilter();
  renderSavedSearches();
  renderApplicationTrackerPanel();
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

function _saveProfileToServer(id, profile) {
  fetch('/save-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filename: profile.filename || '', name: profile.name, data: profile.data }),
  })
    .then(r => r.json())
    .then(res => {
      if (res.ok && res.filename && !profile.filename) {
        // Store the server-assigned filename so future saves hit the same file
        const profiles = getProfiles();
        if (profiles[id]) {
          profiles[id].filename = res.filename;
          saveProfiles(profiles);
        }
      }
    })
    .catch(() => {});  // best-effort — localStorage already saved
}

function _saveToStorage(id) {
  if (!id) return;
  const profiles = getProfiles();
  if (!profiles[id]) return;
  profiles[id].data = collectCandidate();
  saveProfiles(profiles);
  _saveProfileToServer(id, profiles[id]);
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
    const block = certList.lastElementChild;
    const certInput = block.querySelector('[name="cert"]');
    const yearInput = block.querySelector('[name="year"]');
    if (typeof c === 'string') {
      if (certInput) certInput.value = c;
    } else {
      if (certInput) certInput.value = c.name || c.cert || '';
      if (yearInput) yearInput.value = c.year || '';
    }
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
  ).map(b => ({
    name: b.querySelector('[name="cert"]')?.value.trim() || '',
    year: b.querySelector('[name="year"]')?.value.trim() || '',
  })).filter(cert => cert.name);

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

// ── Workspace tabs & job search ───────────────────────────────────────────────

function switchMainTab(tab) {
  const tabs = {
    'job-search': {
      panel: document.getElementById('job-search-tab'),
      button: document.getElementById('tab-job-search-btn'),
    },
    tracker: {
      panel: document.getElementById('application-tracker-tab'),
      button: document.getElementById('tab-tracker-btn'),
    },
    builder: {
      panel: document.getElementById('resume-builder-tab'),
      button: document.getElementById('tab-builder-btn'),
    },
  };
  const activeTab = tabs[tab] ? tab : 'job-search';
  Object.entries(tabs).forEach(([key, item]) => {
    const active = key === activeTab;
    item.panel.classList.toggle('active', active);
    item.button.classList.toggle('selected', active);
    item.button.setAttribute('aria-selected', String(active));
  });

  if (activeTab === 'tracker') renderApplicationTrackerPanel();

  if (activeTab === 'job-search' && !_jobSearchPrefilled) {
    const profileLocation = document.getElementById('location')?.value.trim();
    const countrySelect = document.getElementById('job-search-country');
    const searchLocation = document.getElementById('job-search-location-input');
    const inferredCountry = inferJobCountry(profileLocation);
    if (countrySelect && inferredCountry) {
      countrySelect.value = inferredCountry;
    }
    if (profileLocation && searchLocation && !searchLocation.value.trim() && !inferredCountry) {
      searchLocation.value = profileLocation;
    }
    _jobSearchPrefilled = true;
  }
}

function inferJobCountry(location) {
  const value = (location || '').toLowerCase();
  if (/\b(japan|tokyo|osaka|kyoto|yokohama|nagoya|fukuoka)\b/.test(value)) return 'japan';
  if (/\b(taiwan|taipei|taichung|kaohsiung|tainan|hsinchu)\b/.test(value)) return 'taiwan';
  if (/\b(united states|usa|u\.s\.|california|new york|texas|washington|florida|illinois)\b/.test(value)) return 'united_states';
  return '';
}

function setJobSearchLoading(on) {
  const btn = document.getElementById('btn-job-search');
  btn.disabled = false;
  btn.classList.toggle('cancel', on);
  btn.setAttribute('aria-busy', String(on));
  document.getElementById('btn-job-search-text').textContent = on ? t('btn-cancel-search') : t('btn-search-jobs');
  document.getElementById('btn-job-search-spinner').classList.toggle('hidden', !on);
}

function handleJobSearchButton() {
  if (_jobSearchController) {
    cancelJobSearch();
    return;
  }
  searchJobs();
}

async function cancelJobSearch() {
  if (!_jobSearchController) return;
  _jobSearchController.abort();
  if (_jobSearchPollTimer) {
    clearTimeout(_jobSearchPollTimer);
    _jobSearchPollTimer = null;
  }
  const jobId = _jobSearchJobId;
  _jobSearchJobId = '';
  _jobSearchController = null;
  _jobSearchRequestId += 1;
  if (jobId) {
    fetch(`/search-jobs/${encodeURIComponent(jobId)}/cancel`, { method: 'POST' }).catch(() => {});
  }
  setJobSearchLoading(false);
  showError(t('job-search-cancelled'), 'job-search-error');
}

function finishJobSearch(data, requestId) {
  if (requestId !== _jobSearchRequestId) return;
  _allJobSearchResults = data.jobs || [];
  _jobSearchMeta = data;
  _selectedJobId = _allJobSearchResults[0]?.id || '';
  populateSourceFilter();
  if (_pendingSavedSearchFilters) {
    restoreSavedSearchFilters(_pendingSavedSearchFilters);
    _pendingSavedSearchFilters = null;
  }
  const newSinceLast = updateSavedSearchAfterRun(_allJobSearchResults);
  if (_activeSavedSearchId) _jobSearchMeta.new_since_last = newSinceLast;
  applyJobFilters();
}

async function pollJobSearch(jobId, requestId, controller) {
  if (requestId !== _jobSearchRequestId || controller.signal.aborted) return;
  try {
    const res = await fetch(`/search-jobs/${encodeURIComponent(jobId)}`, { signal: controller.signal });
    if (requestId !== _jobSearchRequestId) return;
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (requestId !== _jobSearchRequestId) return;
    if (!res.ok || data.success === false) throw new Error(data.error || 'Search failed.');

    const sourceEl = document.getElementById('job-source-note');
    if (sourceEl && data.progress && data.status !== 'completed') sourceEl.textContent = data.progress;

    if (data.status === 'completed') {
      finishJobSearch(data, requestId);
      _jobSearchController = null;
      _jobSearchJobId = '';
      _jobSearchPollTimer = null;
      setJobSearchLoading(false);
      return;
    }
    if (data.status === 'cancelled') {
      _jobSearchController = null;
      _jobSearchJobId = '';
      _jobSearchPollTimer = null;
      setJobSearchLoading(false);
      showError(t('job-search-cancelled'), 'job-search-error');
      return;
    }
    _jobSearchPollTimer = setTimeout(() => pollJobSearch(jobId, requestId, controller), 1250);
  } catch (err) {
    if (err.name === 'AbortError' || requestId !== _jobSearchRequestId) return;
    _jobSearchController = null;
    _jobSearchJobId = '';
    _jobSearchPollTimer = null;
    setJobSearchLoading(false);
    showError(t('job-search-error-prefix') + err.message, 'job-search-error');
  }
}

async function searchJobs({ savedSearchId = '' } = {}) {
  if (_jobSearchController) {
    cancelJobSearch();
    return;
  }

  _activeSavedSearchId = savedSearchId;
  const searchState = collectSavedSearchState();
  const params = new URLSearchParams({
    title: searchState.title,
    country: searchState.country,
    location: searchState.location,
    job_type: searchState.job_type,
    deep_search: searchState.deep_search ? 'true' : 'false',
  });
  const controller = new AbortController();
  const requestId = ++_jobSearchRequestId;
  _jobSearchController = controller;

  setJobSearchLoading(true);
  hideError('job-search-error');

  try {
    const res = await fetch(`/search-jobs?${params.toString()}`, { signal: controller.signal });
    if (requestId !== _jobSearchRequestId) return;
    let data;
    try { data = await res.json(); } catch { throw new Error(`Server error (HTTP ${res.status})`); }
    if (requestId !== _jobSearchRequestId) return;
    if (!res.ok || !data.success) throw new Error(data.error || 'Search failed.');
    if (data.queued && data.job_id) {
      _jobSearchJobId = data.job_id;
      const sourceEl = document.getElementById('job-source-note');
      if (sourceEl) sourceEl.textContent = data.progress || t('job-queued');
      pollJobSearch(data.job_id, requestId, controller);
      return;
    }
    finishJobSearch(data, requestId);
  } catch (err) {
    if (err.name === 'AbortError' || requestId !== _jobSearchRequestId) return;
    showError(t('job-search-error-prefix') + err.message, 'job-search-error');
  } finally {
    if (requestId === _jobSearchRequestId && !_jobSearchJobId) {
      _jobSearchController = null;
      setJobSearchLoading(false);
    }
  }
}

function readStorageArray(key) {
  try {
    const parsed = JSON.parse(localStorage.getItem(key));
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStorageArray(key, list) {
  localStorage.setItem(key, JSON.stringify(Array.isArray(list) ? list : []));
}

function stableJobKey(job) {
  if (!job) return '';
  if (job.url) return `url:${job.url}`;
  return [
    job.source || '',
    job.company || '',
    job.title || '',
    job.location || '',
  ].join('|').toLowerCase().replace(/\s+/g, ' ').trim();
}

function jobResultKey(job) {
  return stableJobKey(job) || `id:${job?.id || ''}`;
}

function getApplications() {
  return readStorageArray(APPLICATIONS_KEY);
}

function saveApplications(applications) {
  writeStorageArray(APPLICATIONS_KEY, applications);
}

function applicationStatusLabel(status) {
  return t(`job-status-${status || 'untracked'}`);
}

function getApplicationForJob(job) {
  const key = stableJobKey(job);
  if (!key) return null;
  return getApplications().find(app => app.job_key === key) || null;
}

function upsertApplicationForJob(job, updates = {}) {
  const key = stableJobKey(job);
  if (!key) return null;
  const now = Date.now();
  const applications = getApplications();
  let app = applications.find(item => item.job_key === key);
  if (!app) {
    app = {
      id: genId(),
      job_key: key,
      title: job.title || 'Untitled role',
      company: job.company || '',
      location: job.location || '',
      source: job.source || '',
      url: job.url || '',
      status: 'interested',
      notes: '',
      created_at: now,
    };
    applications.unshift(app);
  }
  Object.assign(app, updates, {
    title: job.title || app.title,
    company: job.company || app.company,
    location: job.location || app.location,
    source: job.source || app.source,
    url: job.url || app.url,
    updated_at: now,
  });
  saveApplications(applications);
  renderApplicationTrackerPanel();
  return app;
}

function removeApplicationForJob(job) {
  const key = stableJobKey(job);
  if (!key) return;
  saveApplications(getApplications().filter(app => app.job_key !== key));
  renderApplicationTrackerPanel();
}

function updateApplicationById(appId, updates = {}) {
  const applications = getApplications();
  const app = applications.find(item => item.id === appId);
  if (!app) return;
  Object.assign(app, updates, { updated_at: Date.now() });
  saveApplications(applications);
  renderApplicationTrackerPanel();
  renderJobResults(_jobSearchResults, _jobSearchMeta);
  if (_selectedJobId) renderJobDetail(_selectedJobId);
}

function deleteApplication(appId) {
  saveApplications(getApplications().filter(app => app.id !== appId));
  renderApplicationTrackerPanel();
  renderJobResults(_jobSearchResults, _jobSearchMeta);
  if (_selectedJobId) renderJobDetail(_selectedJobId);
}

function clearApplications() {
  if (!confirm(t('job-application-clear-confirm'))) return;
  saveApplications([]);
  renderApplicationTrackerPanel();
  renderJobResults(_jobSearchResults, _jobSearchMeta);
  if (_selectedJobId) renderJobDetail(_selectedJobId);
}

function appendApplicationStatusBadge(container, job) {
  const app = getApplicationForJob(job);
  if (!app?.status) return;
  appendJobMetaBadge(container, applicationStatusLabel(app.status), `application-status status-${app.status}`);
}

function renderApplicationTrackerPanel() {
  const container = document.getElementById('application-tracker-list');
  const summaryEl = document.getElementById('application-tracker-summary');
  if (!container) return;
  const applications = getApplications()
    .slice()
    .sort((a, b) => (b.updated_at || b.created_at || 0) - (a.updated_at || a.created_at || 0));
  container.innerHTML = '';
  if (summaryEl) summaryEl.innerHTML = '';

  if (!applications.length) {
    const empty = document.createElement('div');
    empty.className = 'application-tracker-empty';
    empty.textContent = t('job-application-tracker-empty');
    container.appendChild(empty);
    return;
  }

  const summary = document.createElement('div');
  summary.className = 'application-tracker-summary';
  const total = document.createElement('span');
  total.textContent = t('job-application-count').replace('{count}', applications.length);
  summary.appendChild(total);
  ['interested', 'applied', 'interviewing', 'offer'].forEach(status => {
    const count = applications.filter(app => app.status === status).length;
    if (!count) return;
    const chip = document.createElement('span');
    chip.textContent = `${applicationStatusLabel(status)} ${count}`;
    summary.appendChild(chip);
  });
  if (summaryEl) {
    summaryEl.appendChild(summary);
  } else if (summary.childNodes.length) {
    container.appendChild(summary);
  }

  applications.forEach(app => {
    const item = document.createElement('div');
    item.className = 'application-tracker-item';

    const header = document.createElement('div');
    header.className = 'application-tracker-item-header';

    const titleGroup = document.createElement('div');
    titleGroup.className = 'application-tracker-title-group';
    const title = document.createElement('button');
    title.type = 'button';
    title.className = 'application-tracker-title';
    title.textContent = app.title || 'Untitled role';
    title.onclick = () => {
      const matchingJob = _allJobSearchResults.find(job => stableJobKey(job) === app.job_key);
      if (matchingJob) {
        switchMainTab('job-search');
        selectJob(matchingJob.id);
      } else if (app.url) {
        window.open(app.url, '_blank', 'noopener,noreferrer');
      }
    };

    const meta = document.createElement('div');
    meta.className = 'application-tracker-meta';
    meta.textContent = [app.company, app.location, app.source].filter(Boolean).join(' · ');

    titleGroup.appendChild(title);
    titleGroup.appendChild(meta);

    const statusSelect = document.createElement('select');
    statusSelect.className = 'application-status-select';
    ['interested', 'applied', 'interviewing', 'offer', 'rejected', 'archived'].forEach(status => {
      const option = document.createElement('option');
      option.value = status;
      option.textContent = applicationStatusLabel(status);
      option.selected = (app.status || 'interested') === status;
      statusSelect.appendChild(option);
    });
    statusSelect.onchange = () => updateApplicationById(app.id, { status: statusSelect.value });

    header.appendChild(titleGroup);
    header.appendChild(statusSelect);

    const notes = document.createElement('textarea');
    notes.className = 'application-notes-input';
    notes.rows = 3;
    notes.placeholder = t('job-application-notes-placeholder');
    notes.value = app.notes || '';
    notes.onchange = () => updateApplicationById(app.id, { notes: notes.value });

    const footer = document.createElement('div');
    footer.className = 'application-tracker-actions';
    const updated = document.createElement('span');
    const updatedParts = [];
    if (app.updated_at) updatedParts.push(`${t('job-application-updated')}: ${new Date(app.updated_at).toLocaleDateString()}`);
    if (app.resume_history_id) updatedParts.push(t('job-resume-linked'));
    updated.textContent = updatedParts.join(' · ');
    footer.appendChild(updated);

    if (app.url) {
      const open = document.createElement('a');
      open.href = app.url;
      open.target = '_blank';
      open.rel = 'noopener noreferrer';
      open.textContent = t('job-application-open');
      footer.appendChild(open);
    }

    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.textContent = t('job-application-delete');
    deleteBtn.onclick = () => deleteApplication(app.id);
    footer.appendChild(deleteBtn);

    item.appendChild(header);
    item.appendChild(notes);
    item.appendChild(footer);
    container.appendChild(item);
  });
}

function renderApplicationTrackerEditor(job) {
  const section = document.createElement('section');
  section.className = 'application-tracker-editor';
  const app = getApplicationForJob(job);

  const title = document.createElement('h4');
  title.textContent = t('job-application-tracker-title');
  section.appendChild(title);

  const statusField = document.createElement('label');
  statusField.className = 'tracker-field';
  const statusLabel = document.createElement('span');
  statusLabel.textContent = t('job-application-status-label');
  const statusSelect = document.createElement('select');
  [
    ['', 'job-status-untracked'],
    ['interested', 'job-status-interested'],
    ['applied', 'job-status-applied'],
    ['interviewing', 'job-status-interviewing'],
    ['offer', 'job-status-offer'],
    ['rejected', 'job-status-rejected'],
    ['archived', 'job-status-archived'],
  ].forEach(([value, labelKey]) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = t(labelKey);
    option.selected = (app?.status || '') === value;
    statusSelect.appendChild(option);
  });
  statusSelect.onchange = () => {
    if (!statusSelect.value) {
      removeApplicationForJob(job);
    } else {
      upsertApplicationForJob(job, { status: statusSelect.value });
    }
    renderJobResults(_jobSearchResults, _jobSearchMeta);
    renderJobDetail(job.id);
  };
  statusField.appendChild(statusLabel);
  statusField.appendChild(statusSelect);
  section.appendChild(statusField);

  const notesField = document.createElement('label');
  notesField.className = 'tracker-field';
  const notesLabel = document.createElement('span');
  notesLabel.textContent = t('job-application-notes-label');
  const notes = document.createElement('textarea');
  notes.rows = 3;
  notes.placeholder = t('job-application-notes-placeholder');
  notes.value = app?.notes || '';
  notes.onchange = () => upsertApplicationForJob(job, { notes: notes.value, status: statusSelect.value || 'interested' });
  notesField.appendChild(notesLabel);
  notesField.appendChild(notes);
  section.appendChild(notesField);

  if (app?.updated_at || app?.resume_history_id) {
    const updated = document.createElement('div');
    updated.className = 'application-tracker-updated';
    const parts = [];
    if (app.updated_at) parts.push(`${t('job-application-updated')}: ${new Date(app.updated_at).toLocaleDateString()}`);
    if (app.resume_history_id) parts.push(t('job-resume-linked'));
    updated.textContent = parts.join(' · ');
    section.appendChild(updated);
  }

  return section;
}

function collectSavedSearchState() {
  return {
    title: document.getElementById('job-search-title-input').value.trim(),
    location: document.getElementById('job-search-location-input').value.trim(),
    country: document.getElementById('job-search-country').value,
    job_type: document.getElementById('job-search-type').value,
    deep_search: Boolean(document.getElementById('job-deep-search')?.checked),
    filters: {
      sort: document.getElementById('job-search-sort').value,
      sources: getSelectedJobSources(),
      japanese: document.getElementById('job-japanese-filter').value,
      english: document.getElementById('job-english-filter').value,
      visa: document.getElementById('job-visa-filter').value,
      safety: document.getElementById('job-safety-filter').value,
      clearance: document.getElementById('job-clearance-filter').value,
    },
  };
}

function savedSearchSignature(search) {
  return JSON.stringify({
    title: search.title || '',
    location: search.location || '',
    country: search.country || 'any',
    job_type: search.job_type || 'any',
    deep_search: Boolean(search.deep_search),
    filters: search.filters || {},
  });
}

function getSavedSearches() {
  return readStorageArray(SAVED_SEARCHES_KEY);
}

function saveSavedSearches(searches) {
  writeStorageArray(SAVED_SEARCHES_KEY, searches);
}

function savedSearchName(search) {
  const countrySelect = document.getElementById('job-search-country');
  const countryText = countrySelect?.querySelector(`option[value="${search.country}"]`)?.textContent || search.country || 'Any country';
  return [
    search.title || 'Any role',
    search.location || countryText,
  ].filter(Boolean).join(' · ');
}

function saveCurrentSearch() {
  const state = collectSavedSearchState();
  const signature = savedSearchSignature(state);
  const searches = getSavedSearches();
  let search = searches.find(item => item.signature === signature);
  const now = Date.now();
  const resultKeys = _allJobSearchResults.map(jobResultKey).filter(Boolean);
  if (search) {
    Object.assign(search, state, {
      name: savedSearchName(state),
      updated_at: now,
      last_count: resultKeys.length || search.last_count || 0,
      last_result_keys: resultKeys.length ? resultKeys : (search.last_result_keys || []),
    });
  } else {
    search = {
      id: genId(),
      ...state,
      name: savedSearchName(state),
      signature,
      created_at: now,
      updated_at: now,
      last_count: resultKeys.length,
      last_result_keys: resultKeys,
    };
    searches.unshift(search);
  }
  saveSavedSearches(searches.slice(0, 20));
  _activeSavedSearchId = search.id;
  renderSavedSearches();
  const sourceEl = document.getElementById('job-source-note');
  if (sourceEl) sourceEl.textContent = t('job-saved-search-saved');
}

function restoreSavedSearchFields(search) {
  document.getElementById('job-search-title-input').value = search.title || '';
  document.getElementById('job-search-location-input').value = search.location || '';
  document.getElementById('job-search-country').value = search.country || 'any';
  document.getElementById('job-search-type').value = search.job_type || 'any';
  const deepSearch = document.getElementById('job-deep-search');
  if (deepSearch) deepSearch.checked = Boolean(search.deep_search);
  _pendingSavedSearchFilters = search.filters || null;
}

function restoreSavedSearchFilters(filters) {
  if (!filters) return;
  if (filters.sort) document.getElementById('job-search-sort').value = filters.sort;
  if (filters.japanese) document.getElementById('job-japanese-filter').value = filters.japanese;
  if (filters.english) document.getElementById('job-english-filter').value = filters.english;
  if (filters.visa) document.getElementById('job-visa-filter').value = filters.visa;
  if (filters.safety) document.getElementById('job-safety-filter').value = filters.safety;
  if (filters.clearance) document.getElementById('job-clearance-filter').value = filters.clearance;
  const sources = new Set(filters.sources || []);
  document.querySelectorAll('#job-source-filter input[type="checkbox"]').forEach(input => {
    input.checked = sources.has(input.value);
  });
}

function runSavedSearch(searchId) {
  const search = getSavedSearches().find(item => item.id === searchId);
  if (!search) return;
  restoreSavedSearchFields(search);
  searchJobs({ savedSearchId: search.id });
}

function deleteSavedSearch(searchId, event) {
  if (event) event.stopPropagation();
  saveSavedSearches(getSavedSearches().filter(search => search.id !== searchId));
  if (_activeSavedSearchId === searchId) _activeSavedSearchId = '';
  renderSavedSearches();
}

function updateSavedSearchAfterRun(jobs) {
  if (!_activeSavedSearchId) return 0;
  const searches = getSavedSearches();
  const search = searches.find(item => item.id === _activeSavedSearchId);
  if (!search) return 0;
  const previousKeys = new Set(search.last_result_keys || []);
  const resultKeys = jobs.map(jobResultKey).filter(Boolean);
  const newCount = resultKeys.filter(key => !previousKeys.has(key)).length;
  const state = collectSavedSearchState();
  Object.assign(search, state, {
    name: savedSearchName(state),
    signature: savedSearchSignature(state),
    last_run_at: Date.now(),
    last_count: jobs.length,
    last_result_keys: resultKeys,
    new_since_last: newCount,
  });
  saveSavedSearches(searches);
  renderSavedSearches();
  return newCount;
}

function renderSavedSearches() {
  const container = document.getElementById('saved-searches-list');
  if (!container) return;
  const searches = getSavedSearches();
  container.innerHTML = '';
  if (!searches.length) {
    const empty = document.createElement('span');
    empty.className = 'saved-search-empty';
    empty.textContent = t('job-saved-search-empty');
    container.appendChild(empty);
    return;
  }

  searches.slice(0, 6).forEach(search => {
    const card = document.createElement('div');
    card.className = `saved-search-card${search.id === _activeSavedSearchId ? ' active' : ''}`;

    const body = document.createElement('button');
    body.type = 'button';
    body.className = 'saved-search-main';
    body.onclick = () => runSavedSearch(search.id);

    const name = document.createElement('strong');
    name.textContent = search.name || savedSearchName(search);
    const meta = document.createElement('span');
    const parts = [];
    if (search.last_count) parts.push(`${search.last_count} jobs`);
    if (search.last_run_at) parts.push(`${t('job-last-run')}: ${new Date(search.last_run_at).toLocaleDateString()}`);
    if (search.new_since_last) parts.push(t('job-new-results').replace('{count}', search.new_since_last));
    meta.textContent = parts.join(' · ');
    body.appendChild(name);
    body.appendChild(meta);

    const actions = document.createElement('div');
    actions.className = 'saved-search-actions';
    const runBtn = document.createElement('button');
    runBtn.type = 'button';
    runBtn.textContent = t('job-run-search');
    runBtn.onclick = () => runSavedSearch(search.id);
    const deleteBtn = document.createElement('button');
    deleteBtn.type = 'button';
    deleteBtn.textContent = t('job-delete-search');
    deleteBtn.onclick = event => deleteSavedSearch(search.id, event);
    actions.appendChild(runBtn);
    actions.appendChild(deleteBtn);

    card.appendChild(body);
    card.appendChild(actions);
    container.appendChild(card);
  });
}

function resetJobFilters() {
  document.getElementById('job-search-type').value = 'any';
  document.getElementById('job-search-sort').value = 'relevance';
  document.querySelectorAll('#job-source-filter input[type="checkbox"]').forEach(input => {
    input.checked = false;
  });
  document.getElementById('job-japanese-filter').value = 'any';
  document.getElementById('job-english-filter').value = 'any';
  document.getElementById('job-visa-filter').value = 'any';
  document.getElementById('job-safety-filter').value = 'any';
  document.getElementById('job-clearance-filter').value = 'any';
  applyJobFilters();
}

function getSelectedJobSources() {
  return Array.from(document.querySelectorAll('#job-source-filter input[type="checkbox"]:checked'))
    .map(input => input.value)
    .filter(Boolean);
}

function populateSourceFilter() {
  const container = document.getElementById('job-source-filter');
  if (!container) return;
  const selectedSources = new Set(getSelectedJobSources());
  const sources = Array.from(new Set(_allJobSearchResults.map(job => job.source).filter(Boolean))).sort();
  container.innerHTML = '';
  if (!sources.length) {
    const empty = document.createElement('span');
    empty.className = 'job-source-empty';
    empty.textContent = t('job-source-any');
    container.appendChild(empty);
    return;
  }
  sources.forEach((source, index) => {
    const id = `job-source-${index}`;
    const label = document.createElement('label');
    label.className = 'job-source-option';
    label.setAttribute('for', id);

    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = id;
    input.value = source;
    input.checked = selectedSources.has(source);
    input.addEventListener('change', () => applyJobFilters());

    const text = document.createElement('span');
    text.textContent = source;

    label.appendChild(input);
    label.appendChild(text);
    container.appendChild(label);
  });
}

function matchesJapaneseFilter(job, filterValue) {
  if (filterValue === 'any') return true;
  const requirement = (job.japanese_requirement || '').toLowerCase();
  if (filterValue === 'none') return requirement.includes('no japanese');
  if (!requirement || requirement.includes('no japanese')) return false;
  if (filterValue === 'required') return true;
  if (filterValue === 'business') return requirement.includes('business') || requirement.includes('fluent');
  if (filterValue === 'fluent') return requirement.includes('fluent');
  return true;
}

function matchesEnglishFilter(job, filterValue) {
  if (filterValue === 'any') return true;
  const requirement = (job.english_requirement || '').toLowerCase();
  if (filterValue === 'none') return requirement.includes('no english');
  if (!requirement || requirement.includes('no english')) return false;
  if (filterValue === 'required') return true;
  if (filterValue === 'business') return requirement.includes('business') || requirement.includes('fluent') || requirement.includes('english-only');
  if (filterValue === 'fluent') return requirement.includes('fluent') || requirement.includes('english-only');
  if (filterValue === 'only') return requirement.includes('english-only');
  return true;
}

function matchesVisaFilter(job, filterValue) {
  if (filterValue === 'any') return true;
  const sponsorship = (job.visa_sponsorship || '').toLowerCase();
  if (!sponsorship) return false;
  if (filterValue === 'available') return sponsorship.includes('available');
  if (filterValue === 'unavailable') return sponsorship.includes('no visa') || sponsorship.includes('no sponsorship');
  if (filterValue === 'authorization_required') return sponsorship.includes('authorization required');
  return true;
}

function matchesSafetyFilter(job, filterValue) {
  if (filterValue === 'any') return true;
  const minimum = Number(filterValue);
  const score = Number(job.public_safety_score || 0);
  return Boolean(score) && score >= minimum;
}

function matchesClearanceFilter(job, filterValue) {
  if (filterValue === 'any') return true;
  const hasClearance = Boolean(job.security_clearance);
  if (filterValue === 'required') return hasClearance;
  if (filterValue === 'not_required') return !hasClearance;
  return true;
}

function applyJobFilters(keepSelection = true) {
  const jobType = document.getElementById('job-search-type').value;
  const sortBy = document.getElementById('job-search-sort').value;
  const selectedSources = getSelectedJobSources();
  const japaneseFilter = document.getElementById('job-japanese-filter').value;
  const englishFilter = document.getElementById('job-english-filter').value;
  const visaFilter = document.getElementById('job-visa-filter').value;
  const safetyFilter = document.getElementById('job-safety-filter').value;
  const clearanceFilter = document.getElementById('job-clearance-filter').value;

  let jobs = _allJobSearchResults.filter(job => {
    if (jobType !== 'any' && job.job_type !== jobType) return false;
    if (selectedSources.length && !selectedSources.includes(job.source)) return false;
    if (!matchesJapaneseFilter(job, japaneseFilter)) return false;
    if (!matchesEnglishFilter(job, englishFilter)) return false;
    if (!matchesVisaFilter(job, visaFilter)) return false;
    if (!matchesSafetyFilter(job, safetyFilter)) return false;
    if (!matchesClearanceFilter(job, clearanceFilter)) return false;
    return true;
  });

  if (sortBy === 'newest') {
    jobs = jobs.slice().sort((a, b) => (b.posted_at || '').localeCompare(a.posted_at || ''));
  } else if (sortBy === 'company') {
    jobs = jobs.slice().sort((a, b) => (a.company || '').localeCompare(b.company || ''));
  }

  _jobSearchResults = jobs;
  if (!keepSelection || !_selectedJobId || !jobs.some(job => job.id === _selectedJobId)) {
    _selectedJobId = jobs[0]?.id || '';
  }
  renderJobResults(jobs, _jobSearchMeta);
  renderJobDetail(_selectedJobId);
  hydrateSelectedJobDescription(_selectedJobId);
}

function renderJobResults(jobs, meta = {}) {
  const resultsEl = document.getElementById('job-results');
  const summaryEl = document.getElementById('job-results-summary');
  const sourceEl = document.getElementById('job-source-note');

  resultsEl.innerHTML = '';
  summaryEl.textContent = t('job-results-count').replace('{count}', jobs.length);
  if (Number(meta.new_since_last || 0) > 0) {
    summaryEl.textContent += ` · ${t('job-new-results').replace('{count}', meta.new_since_last)}`;
  }
  const sourceParts = [];
  if (meta.source) sourceParts.push(`${t('job-source-label')}: ${meta.source}${meta.cached ? ' cached' : ''}`);
  const sourceLabels = {
    '104-browser': '104 browser',
    '104': '104',
    'japan-dev': 'Japan Dev',
    gaijinpot: 'GaijinPot',
    daijob: 'Daijob',
    careercross: 'CareerCross',
    green: 'Green',
    mynavi: 'Mynavi',
    wantedly: 'Wantedly',
    findy: 'Findy',
    'michael-page': 'Michael Page',
    rgf: 'RGF Professional',
    tokyodev: 'TokyoDev',
    rakuten: 'Rakuten',
    mercari: 'Mercari',
    smartnews: 'SmartNews',
    'woven-toyota': 'Woven by Toyota',
    bizreach: 'BizReach',
    doda: 'doda',
    wexpats: 'WeXpats',
    openwork: 'OpenWork',
    forkwell: 'Forkwell',
    paiza: 'Paiza',
    lapras: 'LAPRAS',
    linkedin: 'LinkedIn',
    indeed: 'Indeed',
    dice: 'Dice',
    remoteok: 'RemoteOK',
    jobicy: 'Jobicy',
    arbeitnow: 'Arbeitnow',
    clearancejobs: 'ClearanceJobs',
    usajobs: 'USAJobs',
    builtin: 'Built In',
    wellfound: 'Wellfound',
    weworkremotely: 'We Work Remotely',
    ziprecruiter: 'ZipRecruiter',
    glassdoor: 'Glassdoor',
    '1111': '1111',
    taiwanjobs: 'TaiwanJobs',
    cake: 'Cake',
    yourator: 'Yourator',
    yes123: 'yes123',
    '518': '518',
    'meet-jobs': 'Meet.jobs',
    'ats-greenhouse': 'Greenhouse',
    'ats-lever': 'Lever',
    'ats-ashby': 'Ashby',
    'ats-workable': 'Workable',
  };
  const unavailable = Object.keys(meta.source_errors || {})
    .map(key => `${sourceLabels[key] || key} unavailable`);
  if (unavailable.length) sourceParts.push(unavailable.join(', '));
  sourceEl.textContent = sourceParts.join(' | ');

  if (!jobs.length) {
    const empty = document.createElement('div');
    empty.className = 'job-empty-state';
    const h3 = document.createElement('h3');
    h3.textContent = t('job-no-results');
    empty.appendChild(h3);
    resultsEl.appendChild(empty);
    renderJobDetail('');
    return;
  }

  jobs.forEach(job => resultsEl.appendChild(renderJobCard(job)));
}

function renderJobCard(job) {
  const card = document.createElement('article');
  card.className = `job-result-card${job.id === _selectedJobId ? ' selected' : ''}`;
  card.tabIndex = 0;
  card.onclick = () => selectJob(job.id);
  card.onkeydown = event => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      selectJob(job.id);
    }
  };

  const header = document.createElement('div');
  header.className = 'job-result-top';

  const titleGroup = document.createElement('div');
  const title = document.createElement('h3');
  title.textContent = job.title || 'Untitled role';
  const company = document.createElement('p');
  company.className = 'job-company';
  company.textContent = job.company || '';
  titleGroup.appendChild(title);
  titleGroup.appendChild(company);

  const source = document.createElement('span');
  source.className = 'job-source-pill';
  source.textContent = job.source || '';

  header.appendChild(titleGroup);
  const headerActions = document.createElement('div');
  headerActions.className = 'job-card-actions';
  headerActions.appendChild(source);
  header.appendChild(headerActions);

  const meta = document.createElement('div');
  meta.className = 'job-meta-row';
  [job.location, prettyJobType(job.job_type), job.category].filter(Boolean).forEach(value => {
    appendJobMetaBadge(meta, value);
  });
  appendJapaneseRequirementBadge(meta, job.japanese_requirement);
  appendEnglishRequirementBadge(meta, job.english_requirement);
  appendVisaSponsorshipBadge(meta, job.visa_sponsorship);
  appendSecurityClearanceBadge(meta, job.security_clearance);
  appendPublicSafetyBadge(meta, job);
  appendApplicationStatusBadge(meta, job);

  const details = document.createElement('div');
  details.className = 'job-detail-row';
  if (job.posted_at) {
    const posted = document.createElement('span');
    posted.textContent = `${t('job-posted-label')}: ${job.posted_at}`;
    details.appendChild(posted);
  }
  if (job.salary) {
    const salary = document.createElement('span');
    salary.textContent = `${t('job-salary-label')}: ${job.salary}`;
    details.appendChild(salary);
  }

  const desc = document.createElement('p');
  desc.className = 'job-description-preview';
  desc.textContent = summarizeJobDescription(job.description || '');

  card.appendChild(header);
  card.appendChild(meta);
  if (details.childNodes.length) card.appendChild(details);
  card.appendChild(desc);
  return card;
}

function selectJob(jobId) {
  _selectedJobId = jobId;
  renderJobResults(_jobSearchResults, _jobSearchMeta);
  renderJobDetail(jobId);
  hydrateSelectedJobDescription(jobId);
}

function renderJobDetail(jobId) {
  const panel = document.getElementById('job-detail-panel');
  const job = _jobSearchResults.find(item => item.id === jobId);
  panel.innerHTML = '';

  if (!job) {
    const empty = document.createElement('div');
    empty.className = 'job-empty-state compact';
    const h3 = document.createElement('h3');
    h3.textContent = t('job-detail-empty-title');
    const p = document.createElement('p');
    p.textContent = t('job-detail-empty-copy');
    empty.appendChild(h3);
    empty.appendChild(p);
    panel.appendChild(empty);
    return;
  }

  const top = document.createElement('div');
  top.className = 'job-detail-top';

  const title = document.createElement('h3');
  title.textContent = job.title || 'Untitled role';
  const company = document.createElement('p');
  company.textContent = job.company || '';

  top.appendChild(title);
  top.appendChild(company);

  const meta = document.createElement('div');
  meta.className = 'job-meta-row detail';
  [job.location, prettyJobType(job.job_type), job.category, job.source].filter(Boolean).forEach(value => {
    appendJobMetaBadge(meta, value);
  });
  appendJapaneseRequirementBadge(meta, job.japanese_requirement);
  appendEnglishRequirementBadge(meta, job.english_requirement);
  appendVisaSponsorshipBadge(meta, job.visa_sponsorship);
  appendSecurityClearanceBadge(meta, job.security_clearance);
  appendPublicSafetyBadge(meta, job);
  appendApplicationStatusBadge(meta, job);

  const details = document.createElement('div');
  details.className = 'job-detail-row';
  if (job.posted_at) details.appendChild(document.createTextNode(`${t('job-posted-label')}: ${job.posted_at}`));
  if (job.posted_at && job.salary) details.appendChild(document.createTextNode(' | '));
  if (job.salary) details.appendChild(document.createTextNode(`${t('job-salary-label')}: ${job.salary}`));

  const actions = document.createElement('div');
  actions.className = 'job-actions detail';

  const useBtn = document.createElement('button');
  useBtn.className = 'btn-job-action primary';
  useBtn.type = 'button';
  useBtn.textContent = t('job-use-description');
  useBtn.onclick = () => useJobPosting(job.id);
  actions.appendChild(useBtn);

  if (job.url) {
    const link = document.createElement('a');
    link.className = 'btn-job-action';
    link.href = job.url;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = t('job-view-posting');
    actions.appendChild(link);
  }
  const mapsUrl = googleMapsUrlForJob(job);
  if (mapsUrl) {
    const mapsLink = document.createElement('a');
    mapsLink.className = 'btn-job-action maps';
    mapsLink.href = mapsUrl;
    mapsLink.target = '_blank';
    mapsLink.rel = 'noopener noreferrer';
    mapsLink.textContent = t('job-open-maps');
    actions.appendChild(mapsLink);
  }

  const hint = document.createElement('p');
  hint.className = 'job-detail-hint';
  hint.textContent = t('job-match-hint');

  const descTitle = document.createElement('h4');
  descTitle.className = 'job-description-title';
  descTitle.textContent = t('job-description-title');

  const desc = document.createElement('div');
  desc.className = 'job-detail-description';
  desc.textContent = job._descriptionLoading
    ? `${job.description || ''}\n\nLoading full job details...`.trim()
    : (job.description || '');

  panel.appendChild(top);
  panel.appendChild(meta);
  if (details.textContent) panel.appendChild(details);
  panel.appendChild(actions);
  panel.appendChild(renderApplicationTrackerEditor(job));
  panel.appendChild(hint);
  panel.appendChild(descTitle);
  panel.appendChild(desc);
}

function canHydrateJobDescription(job) {
  if (!job || job.description_source === 'detail-page' || job._descriptionChecked || job._descriptionLoading) return false;
  if (!job.url) return false;
  try {
    const host = new URL(job.url).host.toLowerCase();
    return [
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
      'www.clearancejobs.com',
      'www.usajobs.gov',
      'builtin.com',
      'www.builtin.com',
      'weworkremotely.com',
      'www.weworkremotely.com',
      'www.ziprecruiter.com',
      'www.glassdoor.com',
      'www.1111.com.tw',
      'www.518.com.tw',
      'www.yes123.com.tw',
      'www.cake.me',
      'www.yourator.co',
      'meet.jobs',
      'www.tokyodev.com',
      'www.bizreach.jp',
      'doda.jp',
      'we-xpats.com',
      'www.openwork.jp',
      'jobs.forkwell.com',
      'paiza.jp',
      'lapras.com',
      'japan-job-en.rakuten.careers',
      'japan-job-jp.rakuten.careers',
      'global.rakuten.com',
      'careers.mercari.com',
      'woven.toyota',
      'boards.greenhouse.io',
      'job-boards.greenhouse.io',
      'jobs.lever.co',
      'app.ashbyhq.com',
      'apply.workable.com',
    ].includes(host);
  } catch {
    return false;
  }
}

function applyHydratedJobDescription(job, data) {
  if (!data?.success || !data.description || data.description.length <= (job.description || '').length + 40) {
    job._descriptionChecked = true;
    return false;
  }
  job.description = data.description;
  job.description_source = data.description_source || 'detail-page';
  if (data.japanese_requirement) job.japanese_requirement = data.japanese_requirement;
  if (data.english_requirement) job.english_requirement = data.english_requirement;
  if (data.visa_sponsorship) job.visa_sponsorship = data.visa_sponsorship;
  if (data.security_clearance) job.security_clearance = data.security_clearance;
  if (data.public_safety_score) {
    job.public_safety_score = data.public_safety_score;
    job.public_safety_label = data.public_safety_label;
    job.public_safety_city = data.public_safety_city;
  }
  job._descriptionChecked = true;
  return true;
}

async function hydrateJobDescription(jobId, { rerender = false } = {}) {
  const job = _jobSearchResults.find(item => item.id === jobId) ||
    _allJobSearchResults.find(item => item.id === jobId);
  if (!canHydrateJobDescription(job)) return job;

  const hydrationId = ++_jobDetailHydrationId;
  job._descriptionLoading = true;
  if (rerender && _selectedJobId === jobId) renderJobDetail(jobId);

  try {
    const res = await fetch('/job-detail-description', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(job),
    });
    let data = {};
    try { data = await res.json(); } catch {}
    if (res.ok) applyHydratedJobDescription(job, data);
  } catch {
    job._descriptionChecked = true;
  } finally {
    job._descriptionLoading = false;
    if (rerender && hydrationId === _jobDetailHydrationId && _selectedJobId === jobId) {
      renderJobResults(_jobSearchResults, _jobSearchMeta);
      renderJobDetail(jobId);
    }
  }
  return job;
}

function hydrateSelectedJobDescription(jobId) {
  hydrateJobDescription(jobId, { rerender: true });
}

function prettyJobType(value) {
  const labels = {
    full_time: t('job-type-full-time'),
    contract: t('job-type-contract'),
    part_time: t('job-type-part-time'),
    freelance: t('job-type-freelance'),
    internship: t('job-type-internship'),
  };
  return labels[value] || '';
}

function cleanJobMapLocation(location) {
  let value = String(location || '').trim();
  if (!value) return '';
  const lower = value.toLowerCase();
  if (/(^|\b)(remote|worldwide|global|anywhere|multiple locations|various locations|hybrid remote)(\b|$)/i.test(value)) return '';
  if (/^(asia|apac|americas|north america|united states|usa|japan|taiwan)$/i.test(value)) return '';

  value = value
    .replace(/^japan\s*[-:]\s*/i, '')
    .replace(/^taiwan\s*[-:]\s*/i, '')
    .replace(/^location:\s*/i, '')
    .replace(/\s*\([^)]*(office|園區|科技園區)[^)]*\)\s*/gi, ' ')
    .replace(/\s*-\s*(roppongi|namba|hakata)\s+office\s*/i, ', ')
    .replace(/,\s*,/g, ',')
    .replace(/\s+,/g, ',')
    .replace(/,\s*$/g, '')
    .replace(/\s+/g, ' ')
    .trim();

  if (!value || value.length < 3) return '';
  if (/^(remote|worldwide|global|anywhere|hybrid|onsite)$/i.test(value)) return '';
  if (lower.includes('palo alto') && lower.includes('united states')) return value;
  return value;
}

function googleMapsUrlForJob(job) {
  const location = cleanJobMapLocation(job?.location);
  if (!location) return '';
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(location)}`;
}

function normalizeJobMetaBadgeKey(value) {
  const normalized = String(value || '')
    .toLowerCase()
    .replace(/[\u2010-\u2015]/g, '-')
    .replace(/[()]/g, ' ')
    .replace(/[_/-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
  const aliases = {
    'full time': 'job-type:full-time',
    'fulltime': 'job-type:full-time',
    '正社員': 'job-type:full-time',
    '全職': 'job-type:full-time',
    'part time': 'job-type:part-time',
    'parttime': 'job-type:part-time',
    'contract': 'job-type:contract',
    'contractor': 'job-type:contract',
    'freelance': 'job-type:freelance',
    'intern': 'job-type:internship',
    'internship': 'job-type:internship',
  };
  return aliases[normalized] || normalized;
}

function appendJobMetaBadge(container, value, className = '') {
  if (!value) return;
  const key = `${className || 'generic'}:${normalizeJobMetaBadgeKey(value)}`;
  const existingKeys = container.dataset.metaBadgeKeys
    ? new Set(container.dataset.metaBadgeKeys.split('|').filter(Boolean))
    : new Set();
  if (existingKeys.has(key)) return;
  existingKeys.add(key);
  container.dataset.metaBadgeKeys = Array.from(existingKeys).join('|');

  const badge = document.createElement('span');
  badge.className = `job-meta-badge${className ? ` ${className}` : ''}`;
  badge.textContent = value;
  container.appendChild(badge);
}

function appendJapaneseRequirementBadge(container, requirement) {
  if (!requirement) return;
  const className = requirement.toLowerCase().includes('no japanese')
    ? 'japanese-clear'
    : 'japanese-required';
  appendJobMetaBadge(container, requirement, className);
}

function appendEnglishRequirementBadge(container, requirement) {
  if (!requirement) return;
  const lower = requirement.toLowerCase();
  const className = lower.includes('no english')
    ? 'english-clear'
    : lower.includes('english-only')
      ? 'english-only'
      : 'english-required';
  appendJobMetaBadge(container, requirement, className);
}

function appendVisaSponsorshipBadge(container, sponsorship) {
  if (!sponsorship) return;
  const lower = sponsorship.toLowerCase();
  if (lower.includes('no visa') || lower.includes('no sponsorship')) return;
  const className = lower.includes('available')
    ? 'visa-available'
    : 'visa-required';
  appendJobMetaBadge(container, sponsorship, className);
}

function appendSecurityClearanceBadge(container, clearance) {
  if (!clearance) return;
  appendJobMetaBadge(container, clearance, 'security-clearance');
}

function publicSafetyStars(score) {
  const value = Math.max(1, Math.min(5, Number(score) || 0));
  if (!value) return '';
  return `${'★'.repeat(value)}${'☆'.repeat(5 - value)}`;
}

function appendPublicSafetyBadge(container, job) {
  if (!job?.public_safety_score) return;
  const stars = publicSafetyStars(job.public_safety_score);
  appendJobMetaBadge(container, `Public Safety Score - ${stars}`, `public-safety safety-${job.public_safety_score}`);
}

function summarizeJobDescription(description) {
  const clean = (description || '').replace(/\s+/g, ' ').trim();
  if (clean.length <= 260) return clean;
  return `${clean.slice(0, 257).trim()}...`;
}

function formatJobPosting(job) {
  const publicSafety = job.public_safety_score
    ? `${publicSafetyStars(job.public_safety_score)} ${job.public_safety_label || 'Public safety'}${job.public_safety_city ? ` (${job.public_safety_city})` : ''}`
    : '';
  const metaLines = [
    job.title || '',
    job.company ? `Company: ${job.company}` : '',
    job.location ? `Location: ${job.location}` : '',
    prettyJobType(job.job_type) ? `Job Type: ${prettyJobType(job.job_type)}` : '',
    job.japanese_requirement ? `Japanese Requirement: ${job.japanese_requirement}` : '',
    job.english_requirement ? `English Requirement: ${job.english_requirement}` : '',
    job.visa_sponsorship ? `Visa Sponsorship: ${job.visa_sponsorship}` : '',
    job.security_clearance ? `Security Clearance: ${job.security_clearance}` : '',
    publicSafety ? `Public Safety: ${publicSafety}` : '',
    job.salary ? `Salary: ${job.salary}` : '',
    job.url ? `Apply: ${job.url}` : '',
  ].filter(Boolean);
  return [...metaLines, '', job.description || ''].join('\n');
}

async function useJobPosting(jobId) {
  const job = _jobSearchResults.find(item => item.id === jobId) ||
    _allJobSearchResults.find(item => item.id === jobId);
  if (!job) return;
  await hydrateJobDescription(jobId);
  _activeTrackedJobKey = stableJobKey(job);
  upsertApplicationForJob(job, { status: getApplicationForJob(job)?.status || 'interested' });
  _resetRightPanel();
  document.getElementById('job-description').value = formatJobPosting(job);
  switchMainTab('builder');
  document.getElementById('panel-job').scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    const historyId = addToHistory(candidate, jobDescription, data.resume, data.downloads, data.file_id);
    if (_activeTrackedJobKey) {
      const trackedJob = _allJobSearchResults.find(job => stableJobKey(job) === _activeTrackedJobKey);
      if (trackedJob) {
        upsertApplicationForJob(trackedJob, { resume_history_id: historyId });
      }
    }

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
  return entry.id;
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
  switchMainTab('job-search');

  migrateIfNeeded();
  const activeId = initProfileSelector();
  const profiles  = getProfiles();
  _populateForm(profiles[activeId]?.data || {});

  renderHistory();
  renderSavedSearches();
  renderApplicationTrackerPanel();

  // Merge profiles from server-side profiles/ directory into localStorage
  fetch('/auto-load-profile')
    .then(r => r.json())
    .then(data => {
      if (!data.found || !data.profiles?.length) return;
      const stored = getProfiles();
      const existingNames = new Set(Object.values(stored).map(p => p.name));
      let added = [];
      data.profiles.forEach(sp => {
        if (existingNames.has(sp.name)) return;  // already present — skip
        const id = genId();
        stored[id] = { name: sp.name, data: sp.profile, filename: sp.filename };
        added.push(id);
      });
      if (!added.length) return;
      saveProfiles(stored);
      // If the active profile is still the blank default, switch to the first new one
      const cur = stored[getActiveId()];
      if (!cur?.data?.name) {
        setActiveId(added[0]);
        _populateForm(stored[added[0]].data);
      }
      renderProfileSelect();
      console.info(`Auto-loaded ${added.length} profile(s) from profiles/ directory`);
    })
    .catch(() => {});  // silently ignore — auto-load is best-effort

  // Auto-save on any change in profile panel
  document.getElementById('panel-info').addEventListener('input',  scheduleSave);
  document.getElementById('panel-info').addEventListener('change', scheduleSave);

  ['job-search-title-input', 'job-search-location-input'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', event => {
      if (event.key === 'Enter') searchJobs();
    });
  });
});
