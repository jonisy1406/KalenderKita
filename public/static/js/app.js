const MONTH_NAMES = [
  "Januari",
  "Februari",
  "Maret",
  "April",
  "Mei",
  "Juni",
  "Juli",
  "Agustus",
  "September",
  "Oktober",
  "November",
  "Desember",
];

const TYPE_LABELS = {
  libur_nasional: "Libur nasional",
  cuti_bersama: "Cuti bersama",
};

const state = {
  activeDate: new Date(),
  holidaysByYear: new Map(),
  loadingYears: new Set(),
};

const elements = {
  title: document.querySelector("#calendar-title"),
  grid: document.querySelector("#calendar-grid"),
  agendaTitle: document.querySelector("#agenda-title"),
  agendaList: document.querySelector("#agenda-list"),
  syncStatus: document.querySelector("#sync-status"),
  yearSummary: document.querySelector("#year-summary"),
  holidayCount: document.querySelector("#holiday-count"),
  leaveCount: document.querySelector("#leave-count"),
  monthFilter: document.querySelector("#month-filter"),
  yearFilter: document.querySelector("#year-filter"),
  prevMonth: document.querySelector("#prev-month"),
  nextMonth: document.querySelector("#next-month"),
  today: document.querySelector("#today"),
  themeToggle: document.querySelector("#theme-toggle"),
  themeLabel: document.querySelector("#theme-label"),
};

function pad(value) {
  return String(value).padStart(2, "0");
}

function toISODate(year, monthIndex, day) {
  return `${year}-${pad(monthIndex + 1)}-${pad(day)}`;
}

function getActiveYear() {
  return state.activeDate.getFullYear();
}

function getActiveMonth() {
  return state.activeDate.getMonth();
}

function getTodayISO() {
  const now = new Date();
  return toISODate(now.getFullYear(), now.getMonth(), now.getDate());
}

function getYearItems(year) {
  return state.holidaysByYear.get(year)?.items ?? [];
}

function groupByDate(items) {
  return items.reduce((grouped, item) => {
    if (!grouped.has(item.date)) {
      grouped.set(item.date, []);
    }
    grouped.get(item.date).push(item);
    return grouped;
  }, new Map());
}

async function loadYear(year) {
  if (state.holidaysByYear.has(year)) {
    return;
  }

  if (state.loadingYears.has(year)) {
    return;
  }

  state.loadingYears.add(year);
  updateStatus("Memuat data...");

  try {
    const response = await fetch(`/api/holidays?year=${year}`);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.detail || payload.error || "Gagal memuat data");
    }

    state.holidaysByYear.set(year, payload);
    render();
  } catch (error) {
    state.holidaysByYear.set(year, {
      year,
      items: [],
      meta: {
        cache_status: "error",
        sync_error: error.message,
      },
    });
    render();
  } finally {
    state.loadingYears.delete(year);
  }
}

function render() {
  const year = getActiveYear();
  const month = getActiveMonth();
  const monthName = MONTH_NAMES[month];
  const items = getYearItems(year);
  const meta = state.holidaysByYear.get(year)?.meta ?? {};
  const itemsByDate = groupByDate(items);

  elements.title.textContent = `${monthName} ${year}`;
  elements.agendaTitle.textContent = monthName;
  syncFilters(year, month);
  renderCalendar(year, month, itemsByDate);
  renderAgenda(year, month, items);
  renderSummary(year, items, meta);
}

function renderCalendar(year, month, itemsByDate) {
  const firstDay = new Date(year, month, 1).getDay();
  const mondayOffset = (firstDay + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const todayISO = getTodayISO();
  const cells = [];

  for (let index = 0; index < mondayOffset; index += 1) {
    cells.push(`<div class="day-cell is-empty" aria-hidden="true"></div>`);
  }

  for (let day = 1; day <= daysInMonth; day += 1) {
    const isoDate = toISODate(year, month, day);
    const dayEvents = itemsByDate.get(isoDate) ?? [];
    const hasHoliday = dayEvents.some((item) => item.type === "libur_nasional");
    const hasLeave = dayEvents.some((item) => item.type === "cuti_bersama");
    const weekday = new Date(year, month, day).getDay();
    const classes = [
      "day-cell",
      weekday === 0 || weekday === 6 ? "is-weekend" : "",
      isoDate === todayISO ? "is-today" : "",
      dayEvents.length ? "has-event" : "",
      hasHoliday ? "has-holiday" : "",
      hasLeave ? "has-leave" : "",
    ]
      .filter(Boolean)
      .join(" ");

    const chips = dayEvents
      .map((item) => {
        const chipClass = item.type === "libur_nasional" ? "holiday" : "leave";
        return `<span class="event-chip ${chipClass}" title="${escapeHTML(item.name)}">${escapeHTML(item.name)}</span>`;
      })
      .join("");

    cells.push(`
      <div class="${classes}">
        <span class="date-number">${day}</span>
        <div class="event-stack">${chips}</div>
      </div>
    `);
  }

  const trailingCells = (7 - (cells.length % 7)) % 7;
  for (let index = 0; index < trailingCells; index += 1) {
    cells.push(`<div class="day-cell is-empty" aria-hidden="true"></div>`);
  }

  elements.grid.innerHTML = cells.join("");
}

function renderAgenda(year, month, items) {
  const monthItems = items
    .filter((item) => item.date.startsWith(`${year}-${pad(month + 1)}-`))
    .sort((left, right) => left.date.localeCompare(right.date));

  if (monthItems.length === 0) {
    elements.agendaList.innerHTML = `<li class="empty-agenda">Tidak ada libur nasional atau cuti bersama bulan ini.</li>`;
    return;
  }

  elements.agendaList.innerHTML = monthItems
    .map((item) => {
      const day = Number(item.date.slice(8, 10));
      const typeClass = item.type === "libur_nasional" ? "holiday" : "leave";
      return `
        <li class="agenda-item ${typeClass}">
          <time class="agenda-date" datetime="${item.date}">
            ${day}
            <span>${MONTH_NAMES[month].slice(0, 3)}</span>
          </time>
          <div class="agenda-copy">
            <strong>${escapeHTML(item.name)}</strong>
            <small>${TYPE_LABELS[item.type] ?? item.type}</small>
          </div>
        </li>
      `;
    })
    .join("");
}

function renderSummary(year, items, meta) {
  const holidayTotal = items.filter((item) => item.type === "libur_nasional").length;
  const leaveTotal = items.filter((item) => item.type === "cuti_bersama").length;
  elements.holidayCount.textContent = holidayTotal;
  elements.leaveCount.textContent = leaveTotal;
  elements.yearSummary.textContent = items.length ? `${items.length} tanggal pada ${year}` : "";

  if (meta.cache_status === "fresh") {
    updateStatus("Data diperbarui otomatis.");
  } else if (meta.cache_status === "cached") {
    updateStatus("Data siap ditampilkan.");
  } else if (meta.cache_status === "stale") {
    updateStatus("Data sementara ditampilkan. Pembaruan otomatis belum berhasil.");
  } else if (meta.cache_status === "error") {
    updateStatus("Data tahun ini belum tersedia dari provider.");
  } else {
    updateStatus("Menunggu data.");
  }
}

function updateStatus(message) {
  elements.syncStatus.textContent = message;
}

function moveMonth(delta) {
  state.activeDate = new Date(getActiveYear(), getActiveMonth() + delta, 1);
  render();
  loadYear(getActiveYear());
}

function setActiveMonthYear(month, year) {
  state.activeDate = new Date(year, month, 1);
  render();
  loadYear(year);
}

function syncFilters(year, month) {
  elements.monthFilter.value = String(month);
  elements.yearFilter.value = String(year);
}

function setupFilters() {
  elements.monthFilter.innerHTML = MONTH_NAMES.map(
    (name, index) => `<option value="${index}">${name}</option>`,
  ).join("");
  syncFilters(getActiveYear(), getActiveMonth());
}

function getInitialTheme() {
  const savedTheme = localStorage.getItem("kalender-theme");
  if (savedTheme === "light" || savedTheme === "dark") {
    return savedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  elements.themeToggle.checked = theme === "dark";
  elements.themeLabel.textContent = theme === "dark" ? "Dark" : "Light";
  localStorage.setItem("kalender-theme", theme);
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[char];
  });
}

elements.prevMonth.addEventListener("click", () => moveMonth(-1));
elements.nextMonth.addEventListener("click", () => moveMonth(1));
elements.today.addEventListener("click", () => {
  state.activeDate = new Date();
  render();
  loadYear(getActiveYear());
});
elements.themeToggle.addEventListener("change", () => {
  applyTheme(elements.themeToggle.checked ? "dark" : "light");
});
elements.monthFilter.addEventListener("change", () => {
  setActiveMonthYear(Number(elements.monthFilter.value), getActiveYear());
});
elements.yearFilter.addEventListener("change", () => {
  const year = Number(elements.yearFilter.value);
  if (!Number.isInteger(year) || year < 1900 || year > 2200) {
    syncFilters(getActiveYear(), getActiveMonth());
    return;
  }
  setActiveMonthYear(getActiveMonth(), year);
});

applyTheme(getInitialTheme());
setupFilters();
render();
loadYear(getActiveYear());
