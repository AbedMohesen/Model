/**
 * تطبيق بوابة المواد الدراسية - قسم هندسة الحاسوب والاتصالات
 * Academic Courses Portal - Client Logic with Lucide Icons
 */

// حالة التطبيق العامة
let currentCategory = 'all';
let searchQuery = '';
let activeCourse = null;

// تهيئة التطبيق عند اكتمال تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setupEventListeners();
  renderCourses();
  if (window.lucide) {
    lucide.createIcons();
  }
});

/**
 * تهيئة وتحميل المظهر (Theme: Dark / Light)
 */
function initTheme() {
  const savedTheme = localStorage.getItem('portal_theme') || 'light';
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-theme');
    themeToggleBtn.innerHTML = '<i data-lucide="sun" class="lucide-sm"></i>';
  } else {
    document.body.classList.remove('dark-theme');
    themeToggleBtn.innerHTML = '<i data-lucide="moon" class="lucide-sm"></i>';
  }

  themeToggleBtn.addEventListener('click', () => {
    const isDark = document.body.classList.toggle('dark-theme');
    themeToggleBtn.innerHTML = isDark 
      ? '<i data-lucide="sun" class="lucide-sm"></i>' 
      : '<i data-lucide="moon" class="lucide-sm"></i>';
    localStorage.setItem('portal_theme', isDark ? 'dark' : 'light');
    if (window.lucide) lucide.createIcons();
  });
}

/**
 * إعداد مستمعي الأحداث للعناصر التفاعلية
 */
function setupEventListeners() {
  // شريط البحث
  const searchInput = document.getElementById('courseSearchInput');
  const clearBtn = document.getElementById('clearSearchBtn');

  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      searchQuery = e.target.value.trim().toLowerCase();
      if (clearBtn) clearBtn.style.display = searchQuery ? 'block' : 'none';
      renderCourses();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (searchInput) {
        searchInput.value = '';
        searchQuery = '';
        clearBtn.style.display = 'none';
        renderCourses();
        searchInput.focus();
      }
    });
  }

  // أزرار الفلترة بالتصنيف
  const filterTabs = document.querySelectorAll('.category-tab');
  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      filterTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      currentCategory = tab.dataset.category;
      renderCourses();
    });
  });

  // إغلاق النوافذ عند النقر على الخلفية
  window.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
      e.target.style.display = 'none';
    }
  });

  // إغلاق بزر Esc
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(modal => {
        modal.style.display = 'none';
      });
    }
  });
}

/**
 * تصفية وعرض قائمة المقررات في الشبكة
 */
function renderCourses() {
  const container = document.getElementById('coursesGrid');
  const noResults = document.getElementById('noResults');

  if (!container) return;

  // تصفية حسب التصنيف والبحث
  const filtered = COURSES_DATA.filter(course => {
    const matchesCategory = currentCategory === 'all' || course.category === currentCategory;
    
    if (!matchesCategory) return false;
    if (!searchQuery) return true;

    const inTitle = course.title.toLowerCase().includes(searchQuery);
    const inEngTitle = course.englishTitle.toLowerCase().includes(searchQuery);
    const inCode = course.code.toLowerCase().includes(searchQuery);
    const inDesc = course.description.toLowerCase().includes(searchQuery);

    const inSections = course.sections && course.sections.some(sec => {
      const inSecTitle = sec.title.toLowerCase().includes(searchQuery);
      const inItems = sec.items && sec.items.some(item => item.title.toLowerCase().includes(searchQuery));
      return inSecTitle || inItems;
    });

    return inTitle || inEngTitle || inCode || inDesc || inSections;
  });

  if (filtered.length === 0) {
    container.innerHTML = '';
    if (noResults) noResults.style.display = 'block';
    return;
  }

  if (noResults) noResults.style.display = 'none';
  container.innerHTML = filtered.map(course => createCourseCardHTML(course)).join('');

  if (window.lucide) {
    lucide.createIcons();
  }
}

/**
 * توليد كود HTML لبطاقة المقرر الواحد بتصميم HP و Lucide
 */
function createCourseCardHTML(course) {
  // واجب مستحق إن وجد
  let assignmentHTML = '';
  if (course.upcomingAssignments && course.upcomingAssignments.length > 0) {
    const ass = course.upcomingAssignments[0];
    assignmentHTML = `
      <div class="card-assignment-tag">
        <i data-lucide="alert-circle" class="lucide-sm"></i>
        <span>واجب مستحق: <strong>${ass.title}</strong> (${ass.dueDate.split('-')[0]})</span>
      </div>
    `;
  }

  // روابط التواصل السريعة
  let quickLinksHTML = '';
  if (course.socialLinks && course.socialLinks.length > 0) {
    quickLinksHTML = `
      <div class="card-quick-links-wrap">
        ${course.socialLinks.map(link => {
          const isWa = link.type === 'whatsapp';
          const cssClass = isWa ? 'chip-whatsapp' : 'chip-telegram';
          const iconName = isWa ? 'message-circle' : 'send';
          let shortLabel = link.label;
          if (link.label.includes('طلاب') || link.label.includes('Male')) {
            shortLabel = 'واتساب (طلاب)';
          } else if (link.label.includes('طالبات') || link.label.includes('Female')) {
            shortLabel = 'واتساب (طالبات)';
          } else if (link.label.length > 20) {
            shortLabel = link.label.substring(0, 18) + '...';
          }
          return `
            <a href="${link.url}" target="_blank" rel="noopener noreferrer" class="card-social-chip ${cssClass}" title="${link.note || link.label}">
              <i data-lucide="${iconName}" class="lucide-sm"></i>
              <span>${shortLabel}</span>
            </a>
          `;
        }).join('')}
      </div>
    `;
  }

  // زر الإجراء الرئيسي: إما الانتقال لصفحة المادة أو تصفح تجارب وملفات المعمل
  let actionBtnHTML = '';
  const isLab = course.category === 'lab';
  if (course.pageUrl) {
    const btnText = isLab ? 'دخول صفحة المعمل والتجارب' : 'دخول صفحة المقرر';
    const btnIcon = isLab ? 'flask-conical' : 'arrow-left';
    actionBtnHTML = `
      <a href="${course.pageUrl}" class="btn btn-primary" style="width: 100%;">
        <i data-lucide="${btnIcon}" class="lucide-sm"></i>
        <span>${btnText}</span>
      </a>
    `;
  } else if (isLab) {
    const itemCount = course.sections ? course.sections.reduce((acc, s) => acc + (s.items ? s.items.length : 0), 0) : 0;
    const btnLabel = itemCount > 0 
      ? `تصفح تجارب وملفات المعمل (${itemCount})` 
      : 'تصفح تجارب وملفات المعمل';
    actionBtnHTML = `
      <button class="btn btn-primary" onclick="openCourseModal('${course.id}')" style="width: 100%;">
        <i data-lucide="flask-conical" class="lucide-sm"></i>
        <span>${btnLabel}</span>
      </button>
    `;
  } else {
    actionBtnHTML = `
      <button class="btn btn-primary" onclick="openCourseModal('${course.id}')" style="width: 100%;">
        <span>تصفح المواد والملفات</span>
        <i data-lucide="folder-open" class="lucide-sm"></i>
      </button>
    `;
  }

  const badgeHTML = isLab
    ? `<span class="card-code-badge" style="background: rgba(30, 77, 43, 0.1); color: var(--color-primary); border-color: rgba(30, 77, 43, 0.3);">معمل عملي • ${course.code}</span>`
    : `<span class="card-code-badge">مقرر نظري • ${course.code}</span>`;

  return `
    <article class="course-card">
      <div>
        <div class="card-top-row">
          ${badgeHTML}
          <span class="card-icon-square">
            <i data-lucide="${course.icon || (isLab ? 'flask-conical' : 'book-open')}"></i>
          </span>
        </div>

        <h3 class="card-title">
          ${course.pageUrl ? `<a href="${course.pageUrl}">${course.title}</a>` : `<a href="javascript:void(0)" onclick="openCourseModal('${course.id}')">${course.title}</a>`}
        </h3>
        <span class="card-eng-subtitle">${course.englishTitle}</span>
        <p class="card-description">${course.description}</p>

        ${assignmentHTML}
        ${quickLinksHTML}
      </div>

      <div class="card-footer-action">
        ${actionBtnHTML}
      </div>
    </article>
  `;
}

/**
 * فتح نافذة تفاصيل المادة وأرشيف المودل (للمواد الاحتياطية إن وجدت)
 */
function openCourseModal(courseId) {
  const course = COURSES_DATA.find(c => c.id === courseId);
  if (!course) return;

  activeCourse = course;

  document.getElementById('modalCourseCode').textContent = course.code;
  document.getElementById('modalCourseTitle').textContent = course.title;
  document.getElementById('modalCourseEngTitle').textContent = `${course.englishTitle} • ${course.semester}`;

  // روابط التواصل
  const socialContainer = document.getElementById('modalSocialLinks');
  if (course.socialLinks && course.socialLinks.length > 0) {
    socialContainer.innerHTML = course.socialLinks.map(link => {
      const isWa = link.type === 'whatsapp';
      const icon = isWa ? 'message-circle' : 'send';
      const cssClass = isWa ? 'chip-whatsapp' : 'chip-telegram';
      return `
        <a href="${link.url}" target="_blank" rel="noopener noreferrer" class="card-social-chip ${cssClass}">
          <i data-lucide="${icon}" class="lucide-sm"></i>
          <span>${link.label}</span>
        </a>
      `;
    }).join('');
  } else {
    socialContainer.innerHTML = '<span style="font-size: 13px; color: var(--color-graphite);">لا توجد روابط مجموعات حالياً.</span>';
  }

  // التكليفات والواجبات
  const assSection = document.getElementById('modalAssignmentsSection');
  const assList = document.getElementById('modalAssignmentsList');
  if (course.upcomingAssignments && course.upcomingAssignments.length > 0) {
    assSection.style.display = 'block';
    assList.innerHTML = course.upcomingAssignments.map(ass => `
      <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; background: var(--color-paper); padding: 8px 12px; border-radius: var(--rounded-sm); border: 1px solid var(--color-hairline);">
        <div>
          <strong style="font-size: 13.5px;">${ass.title}</strong>
          <div style="font-size: 12px; color: var(--color-bloom-deep);">موعد التسليم: ${ass.dueDate}</div>
        </div>
        <a href="${ass.path}" download class="btn btn-primary btn-sm">
          <i data-lucide="download" class="lucide-sm"></i>
          <span>تحميل</span>
        </a>
      </div>
    `).join('');
  } else {
    assSection.style.display = 'none';
  }

  // فصول المقرر والملفات
  renderModalSections(course);

  // إظهار النافذة
  document.getElementById('courseModal').style.display = 'flex';

  if (window.lucide) {
    lucide.createIcons();
  }
}

/**
 * عرض فصول وملفات المادة داخل المودال
 */
function renderModalSections(course) {
  const container = document.getElementById('modalSectionsList');
  if (!course.sections || course.sections.length === 0) {
    container.innerHTML = '<p style="color: var(--color-graphite); font-size: 13.5px;">يرجى الانضمام لمجموعة الواتساب الموضحة أعلاه لمتابعة المهام.</p>';
    return;
  }

  container.innerHTML = course.sections.map((section, idx) => {
    const itemsHTML = section.items && section.items.length > 0
      ? section.items.map(item => createFileItemHTML(item)).join('')
      : '<p style="padding: 8px; font-size: 13px; color: var(--color-graphite);">لا توجد ملفات في هذا الفصل حالياً.</p>';

    return `
      <div style="background-color: var(--color-cloud); border: 1px solid var(--color-hairline); border-radius: var(--rounded-md); overflow: hidden;">
        <div style="padding: 10px 14px; background: var(--color-cloud); display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px; font-weight: 600; font-size: 14px;">
            <i data-lucide="${section.icon || 'folder'}" class="lucide-sm" style="color: var(--color-primary);"></i>
            <span>${section.title}</span>
          </div>
        </div>
        <div style="padding: 10px 14px; background: var(--color-paper); border-top: 1px solid var(--color-hairline);">
          <div class="moodle-files-list">
            ${itemsHTML}
          </div>
        </div>
      </div>
    `;
  }).join('');
}

/**
 * توليد كود HTML لعنصر الملف أو المحاضرة مع Lucide Icons
 */
function createFileItemHTML(item) {
  let iconName = 'file-text';
  let badgeText = 'ملف PDF';

  if (item.type === 'video') {
    iconName = 'play-circle';
    badgeText = 'تسجيل فيديو';
  } else if (item.type === 'assignment') {
    iconName = 'clipboard-list';
    badgeText = item.badge || 'واجب';
  } else if (item.type === 'link') {
    iconName = 'external-link';
    badgeText = 'رابط خارجي';
  } else if (item.type === 'ppt') {
    iconName = 'presentation';
    badgeText = 'PowerPoint';
  } else if (item.type === 'docx') {
    iconName = 'file-check';
    badgeText = 'Word';
  }

  const isExternal = item.path.startsWith('http://') || item.path.startsWith('https://');
  const targetAttr = isExternal ? 'target="_blank" rel="noopener noreferrer"' : 'download';
  const actionText = isExternal ? 'فتح الرابط' : 'تحميل';
  const actionIcon = isExternal ? 'external-link' : 'download';

  return `
    <div class="moodle-file-row">
      <div class="file-row-left">
        <div class="file-type-square">
          <i data-lucide="${iconName}"></i>
        </div>
        <div class="file-meta-text">
          <div class="file-name-heading" title="${item.title}">${item.title}</div>
          <span class="file-subinfo">${badgeText}</span>
        </div>
      </div>
      <div class="file-row-actions">
        <a href="${item.path}" ${targetAttr} class="btn btn-primary btn-sm" title="${actionText}">
          <i data-lucide="${actionIcon}" class="lucide-sm"></i>
          <span>${actionText}</span>
        </a>
        <button class="btn btn-outline-ink btn-sm btn-copy" onclick="copyFilePath('${item.path}')" title="نسخ المسار">
          <i data-lucide="copy" class="lucide-sm"></i>
        </button>
      </div>
    </div>
  `;
}

/**
 * إغلاق نافذة تفاصيل المادة
 */
function closeCourseModal() {
  document.getElementById('courseModal').style.display = 'none';
  activeCourse = null;
}

/**
 * نسخ مسار الملف
 */
function copyFilePath(path) {
  navigator.clipboard.writeText(path).then(() => {
    showToast('تم نسخ مسار الملف بنجاح!');
  }).catch(() => {
    const tempInput = document.createElement('input');
    tempInput.value = path;
    document.body.appendChild(tempInput);
    tempInput.select();
    document.execCommand('copy');
    document.body.removeChild(tempInput);
    showToast('تم نسخ مسار الملف بنجاح!');
  });
}

/**
 * إظهار تنبيه Toast
 */
function showToast(message) {
  const toast = document.getElementById('toastNotification');
  const toastMsg = document.getElementById('toastMessage');
  if (toastMsg) toastMsg.textContent = message;
  if (toast) {
    toast.style.display = 'flex';
    if (window.lucide) lucide.createIcons();
    setTimeout(() => {
      toast.style.display = 'none';
    }, 2800);
  }
}

function dismissAnnouncement() {
  const bar = document.getElementById('topAnnouncement');
  if (bar) bar.style.display = 'none';
}

function resetFilters() {
  currentCategory = 'all';
  searchQuery = '';
  document.getElementById('courseSearchInput').value = '';
  document.getElementById('clearSearchBtn').style.display = 'none';

  const filterTabs = document.querySelectorAll('.category-tab');
  filterTabs.forEach(t => {
    t.classList.toggle('active', t.dataset.category === 'all');
  });

  renderCourses();
}
