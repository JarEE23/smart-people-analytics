/**
 * SMART PEOPLE ANALYTICS — DASHBOARD LOGIC
 * Manages metric updates, Chart.js instances, and date filtering
 */

let hourlyChartInstance = null;
let dailyChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
  const datePicker = document.getElementById('dashboard-date-picker');
  const btnToday = document.getElementById('btn-quick-today');
  const btnYesterday = document.getElementById('btn-quick-yesterday');
  const btnRefresh = document.getElementById('btn-quick-refresh');

  // Initial load
  loadDashboardData();

  // Event Listeners
  if (datePicker) {
    datePicker.addEventListener('change', () => {
      loadDashboardData(datePicker.value);
    });
  }

  if (btnToday) {
    btnToday.addEventListener('click', () => {
      const todayStr = new Date().toISOString().split('T')[0];
      if (datePicker) datePicker.value = todayStr;
      loadDashboardData(todayStr);
    });
  }

  if (btnYesterday) {
    btnYesterday.addEventListener('click', () => {
      const d = new Date();
      d.setDate(d.getDate() - 1);
      const yesterdayStr = d.toISOString().split('T')[0];
      if (datePicker) datePicker.value = yesterdayStr;
      loadDashboardData(yesterdayStr);
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener('click', () => {
      const curDate = datePicker ? datePicker.value : null;
      loadDashboardData(curDate);
    });
  }
});

/**
 * Main dashboard loader function
 */
async function loadDashboardData(targetDate = null) {
  const dateInput = document.getElementById('dashboard-date-picker');
  const activeDate = targetDate || (dateInput ? dateInput.value : '');

  try {
    // 1. Fetch Summary & Peak Hour
    const summaryUrl = activeDate ? `/api/dashboard/summary?date=${activeDate}` : '/api/dashboard/summary';
    const sumRes = await fetch(summaryUrl);
    const sumJson = await sumRes.json();

    if (sumJson.status === 'success') {
      const s = sumJson.data.summary;
      const peak = sumJson.data.peak_period;
      const comp = sumJson.data.comparison_to_previous_day;

      // Update Cards
      animateCounter('val-total-in', s.total_in);
      animateCounter('val-total-out', s.total_out);
      animateCounter('val-occupancy', s.estimated_occupancy);

      const netEl = document.getElementById('val-net-flow');
      if (netEl) {
        const sign = s.net_flow > 0 ? '+' : '';
        netEl.textContent = `Net: ${sign}${s.net_flow} orang`;
      }

      // Peak Period
      const peakHourEl = document.getElementById('val-peak-hour');
      const peakCountEl = document.getElementById('val-peak-count');
      if (peakHourEl && peakCountEl) {
        if (peak && peak.has_data) {
          peakHourEl.textContent = peak.peak_hour;
          peakCountEl.textContent = `${peak.count} orang masuk`;
        } else {
          peakHourEl.textContent = 'Tidak Ada Data';
          peakCountEl.textContent = '0 orang';
        }
      }

      // Comparison Badge
      const trendBadge = document.getElementById('badge-trend-in');
      const textCompare = document.getElementById('text-compare-in');
      if (trendBadge && comp) {
        trendBadge.textContent = comp.change_percent_str;
        trendBadge.className = 'trend-badge ' + (comp.trend === 'NAIK' ? 'trend-up' : (comp.trend === 'TURUN' ? 'trend-down' : 'trend-neutral'));
        if (textCompare) {
          textCompare.textContent = `vs ${comp.period_previous.start} (${comp.period_previous.count} orang)`;
        }
      }

      // Source Badge
      const sourceBadge = document.getElementById('badge-source-label');
      if (sourceBadge && s.source) {
        sourceBadge.textContent = `SUMBER: ${s.source}`;
        sourceBadge.className = 'badge-tag ' + (s.source.includes('YOLO') ? 'badge-yolo' : 'badge-simulated');
      }

      // If active date was empty, sync input to returned date
      if (dateInput && !activeDate && s.period.start) {
        dateInput.value = s.period.start;
      }
    }

    // 2. Fetch Hourly Activity for Chart 1
    const hourlyUrl = activeDate ? `/api/analytics/hourly?date=${activeDate}` : '/api/analytics/hourly';
    const hourlyRes = await fetch(hourlyUrl);
    const hourlyJson = await hourlyRes.json();
    if (hourlyJson.status === 'success') {
      renderHourlyChart(hourlyJson.data);
      const subtitle = document.getElementById('subtitle-hourly-date');
      if (subtitle) {
        subtitle.textContent = `Distribusi 24 jam untuk tanggal ${hourlyJson.data.date}`;
      }
    }

    // 3. Fetch Daily Trends for Chart 2
    const dailyUrl = activeDate ? `/api/analytics/daily?end_date=${activeDate}` : '/api/analytics/daily';
    const dailyRes = await fetch(dailyUrl);
    const dailyJson = await dailyRes.json();
    if (dailyJson.status === 'success') {
      renderDailyChart(dailyJson.data);
    }

  } catch (err) {
    console.error('Error fetching dashboard data:', err);
  }
}

/**
 * Renders Hourly Bar & Line combo Chart
 */
function renderHourlyChart(data) {
  const canvas = document.getElementById('hourlyActivityChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (hourlyChartInstance) {
    hourlyChartInstance.destroy();
  }

  // Create Chart.js instance with sleek dark styling
  hourlyChartInstance = new Chart(ctx, {
    data: {
      labels: data.hours,
      datasets: [
        {
          type: 'bar',
          label: 'Masuk (IN)',
          data: data.in_counts,
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          hoverBackgroundColor: '#34d399',
          borderRadius: 4,
          order: 2
        },
        {
          type: 'bar',
          label: 'Keluar (OUT)',
          data: data.out_counts,
          backgroundColor: 'rgba(244, 63, 94, 0.65)',
          hoverBackgroundColor: '#fb7185',
          borderRadius: 4,
          order: 2
        },
        {
          type: 'line',
          label: 'Akumulasi Okupansi',
          data: data.cumulative_occupancy,
          borderColor: '#38bdf8',
          borderWidth: 2.5,
          pointBackgroundColor: '#38bdf8',
          pointRadius: 2,
          pointHoverRadius: 5,
          tension: 0.35,
          fill: false,
          order: 1
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 12 },
            usePointStyle: true,
            boxWidth: 8
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: 'rgba(255, 255, 255, 0.1)',
          borderWidth: 1,
          padding: 12,
          cornerRadius: 8,
          titleFont: { family: 'Plus Jakarta Sans', weight: 'bold' }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.06)' },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 11 } },
          beginAtZero: true
        }
      }
    }
  });
}

/**
 * Renders 7-Day Trend Chart
 */
function renderDailyChart(data) {
  const canvas = document.getElementById('dailyTrendChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  if (dailyChartInstance) {
    dailyChartInstance.destroy();
  }

  const labels = data.trends.map(t => {
    // Format YYYY-MM-DD to DD/MM
    const parts = t.date.split('-');
    return `${parts[2]}/${parts[1]}`;
  });
  const inValues = data.trends.map(t => t.IN);
  const outValues = data.trends.map(t => t.OUT);

  dailyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Total IN',
          data: inValues,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.12)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 4,
          pointBackgroundColor: '#10b981'
        },
        {
          label: 'Total OUT',
          data: outValues,
          borderColor: '#f43f5e',
          backgroundColor: 'rgba(244, 63, 94, 0.06)',
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          pointBackgroundColor: '#f43f5e'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: {
            color: '#94a3b8',
            font: { family: 'Plus Jakarta Sans', size: 11 },
            usePointStyle: true,
            boxWidth: 6
          }
        },
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.95)',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          padding: 10,
          cornerRadius: 8
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#64748b', font: { family: 'JetBrains Mono', size: 10 } },
          beginAtZero: true
        }
      }
    }
  });
}

/**
 * Animated counter effect for numbers
 */
function animateCounter(elementId, targetNumber) {
  const el = document.getElementById(elementId);
  if (!el) return;

  const current = parseInt(el.textContent.replace(/[^0-9]/g, '')) || 0;
  if (current === targetNumber) {
    el.textContent = targetNumber.toLocaleString();
    return;
  }

  const duration = 500;
  const start = performance.now();

  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const value = Math.floor(current + (targetNumber - current) * progress);
    el.textContent = value.toLocaleString();

    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      el.textContent = targetNumber.toLocaleString();
    }
  }

  requestAnimationFrame(step);
}

// Attach globally for external triggers
window.loadDashboardData = loadDashboardData;
