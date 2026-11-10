/**
 * SMART PEOPLE ANALYTICS — EVENT HISTORY LOGIC
 * Manages event filtering, paginated table rendering, and CSV exports
 */

let currentPage = 1;
let currentLimit = 25;

document.addEventListener('DOMContentLoaded', () => {
  const startDateInput = document.getElementById('filter-start-date');
  const endDateInput = document.getElementById('filter-end-date');
  const directionSelect = document.getElementById('filter-direction');
  const sourceSelect = document.getElementById('filter-source');
  const pageSizeSelect = document.getElementById('filter-page-size');
  const btnReset = document.getElementById('btn-reset-filters');
  const btnExport = document.getElementById('btn-export-csv');
  const btnPrev = document.getElementById('btn-page-prev');
  const btnNext = document.getElementById('btn-page-next');

  // Load initial data
  loadHistoryData();

  // Filter change listeners
  [startDateInput, endDateInput, directionSelect, sourceSelect].forEach(el => {
    if (el) {
      el.addEventListener('change', () => {
        currentPage = 1;
        loadHistoryData();
      });
    }
  });

  if (pageSizeSelect) {
    pageSizeSelect.addEventListener('change', () => {
      currentLimit = parseInt(pageSizeSelect.value) || 25;
      currentPage = 1;
      loadHistoryData();
    });
  }

  if (btnReset) {
    btnReset.addEventListener('click', () => {
      if (startDateInput) startDateInput.value = '';
      if (endDateInput) endDateInput.value = '';
      if (directionSelect) directionSelect.value = '';
      if (sourceSelect) sourceSelect.value = '';
      currentPage = 1;
      loadHistoryData();
    });
  }

  if (btnExport) {
    btnExport.addEventListener('click', handleExportCSV);
  }

  if (btnPrev) {
    btnPrev.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        loadHistoryData();
      }
    });
  }

  if (btnNext) {
    btnNext.addEventListener('click', () => {
      currentPage++;
      loadHistoryData();
    });
  }
});

/**
 * Fetch events from backend API and render rows
 */
async function loadHistoryData() {
  const tbody = document.getElementById('table-events-body');
  if (!tbody) return;

  const startDate = document.getElementById('filter-start-date')?.value || '';
  const endDate = document.getElementById('filter-end-date')?.value || '';
  const direction = document.getElementById('filter-direction')?.value || '';
  const source = document.getElementById('filter-source')?.value || '';

  const queryParams = new URLSearchParams({
    page: currentPage,
    limit: currentLimit
  });

  if (startDate) queryParams.append('start_date', startDate);
  if (endDate) queryParams.append('end_date', endDate);
  if (direction) queryParams.append('direction', direction);
  if (source) queryParams.append('source', source);

  tbody.innerHTML = `
    <tr>
      <td colspan="7" style="text-align: center; color: var(--text-dim); padding: 30px;">
        <span class="spinner" style="margin-right: 8px;"></span> Memuat log kejadian...
      </td>
    </tr>
  `;

  try {
    const res = await fetch(`/api/events?${queryParams.toString()}`);
    const json = await res.json();

    if (json.status === 'success') {
      const events = json.data.events;
      const pagination = json.data.pagination;

      renderTableRows(events);
      updatePaginationControls(pagination);
    } else {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-out); padding: 20px;">Gagal memuat data</td></tr>`;
    }
  } catch (err) {
    console.error('Error fetching event history:', err);
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--color-out); padding: 20px;">Error koneksi server</td></tr>`;
  }
}

/**
 * Render individual rows inside the table
 */
function renderTableRows(events) {
  const tbody = document.getElementById('table-events-body');
  if (!tbody) return;

  if (events.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 35px;">
          Tidak ada kejadian yang cocok dengan filter yang dipilih.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = '';

  events.forEach(e => {
    const tr = document.createElement('tr');

    const directionBadge = e.direction === 'IN' 
      ? '<span class="badge-tag badge-in"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M7 17l9.2-9.2M17 17V7H7"/></svg> IN</span>'
      : '<span class="badge-tag badge-out"><svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M17 7l-9.2 9.2M7 7v10h10"/></svg> OUT</span>';

    const sourceBadge = e.source === 'YOLO'
      ? '<span class="badge-tag badge-yolo">YOLO (CAM)</span>'
      : '<span class="badge-tag badge-simulated">SIMULATED</span>';

    const confDisplay = e.confidence 
      ? `${(e.confidence * 100).toFixed(1)}%` 
      : '<span style="color: var(--text-dim);">-</span>';

    tr.innerHTML = `
      <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-dim);">#${e.id}</td>
      <td style="font-family: var(--font-mono); font-size: 0.82rem;">${e.occurred_at}</td>
      <td>${directionBadge}</td>
      <td style="font-family: var(--font-mono); font-size: 0.82rem; color: #a5b4fc;">${e.track_id || '-'}</td>
      <td style="font-family: var(--font-mono); font-size: 0.82rem;">${confDisplay}</td>
      <td>${sourceBadge}</td>
      <td style="font-size: 0.82rem; color: var(--text-muted);">${e.camera_id}</td>
    `;

    tbody.appendChild(tr);
  });
}

/**
 * Updates pagination bar and counters
 */
function updatePaginationControls(pagination) {
  const summaryEl = document.getElementById('table-record-summary');
  const infoEl = document.getElementById('pagination-info');
  const btnPrev = document.getElementById('btn-page-prev');
  const btnNext = document.getElementById('btn-page-next');

  if (summaryEl) {
    const startRecord = (pagination.page - 1) * pagination.limit + 1;
    const endRecord = Math.min(pagination.page * pagination.limit, pagination.total_records);
    if (pagination.total_records === 0) {
      summaryEl.textContent = 'Menampilkan 0 dari 0 kejadian';
    } else {
      summaryEl.textContent = `Menampilkan ${startRecord.toLocaleString()} - ${endRecord.toLocaleString()} dari ${pagination.total_records.toLocaleString()} total kejadian`;
    }
  }

  if (infoEl) {
    infoEl.textContent = `Halaman ${pagination.page} dari ${pagination.total_pages || 1}`;
  }

  if (btnPrev) btnPrev.disabled = !pagination.has_prev;
  if (btnNext) btnNext.disabled = !pagination.has_next;
}

/**
 * Triggers CSV download
 */
function handleExportCSV() {
  const startDate = document.getElementById('filter-start-date')?.value || '';
  const endDate = document.getElementById('filter-end-date')?.value || '';
  const direction = document.getElementById('filter-direction')?.value || '';
  const source = document.getElementById('filter-source')?.value || '';

  const queryParams = new URLSearchParams();
  if (startDate) queryParams.append('start_date', startDate);
  if (endDate) queryParams.append('end_date', endDate);
  if (direction) queryParams.append('direction', direction);
  if (source) queryParams.append('source', source);

  // Trigger download via direct window navigation
  window.location.href = `/api/events/export?${queryParams.toString()}`;
}

window.loadHistoryData = loadHistoryData;
