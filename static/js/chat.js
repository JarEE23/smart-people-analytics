/**
 * SMART PEOPLE ANALYTICS — AI CHAT ANALYST CLIENT LOGIC
 * Manages conversation sessions, prompt chips, tool execution evidence display
 */

let activeSessionId = localStorage.getItem('spa_current_session') || null;

document.addEventListener('DOMContentLoaded', () => {
  const inputEl = document.getElementById('chat-input-text');
  const btnSend = document.getElementById('btn-send-message');
  const btnNewChat = document.getElementById('btn-new-chat');
  const btnClearChat = document.getElementById('btn-clear-chat');
  const promptChips = document.querySelectorAll('.prompt-chip');

  // Load chat sessions
  loadSessions();

  // If active session exists, load its messages
  if (activeSessionId) {
    loadSessionMessages(activeSessionId);
  }

  // Send button listener
  if (btnSend) {
    btnSend.addEventListener('click', handleSendMessage);
  }

  // Enter key in input
  if (inputEl) {
    inputEl.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    });
  }

  // New Chat button
  if (btnNewChat) {
    btnNewChat.addEventListener('click', async () => {
      await createNewSession();
    });
  }

  // Clear/Delete Chat button
  if (btnClearChat) {
    btnClearChat.addEventListener('click', async () => {
      if (!activeSessionId) return;
      if (!confirm('Apakah Anda yakin ingin menghapus sesi percakapan ini?')) return;
      await deleteSession(activeSessionId);
    });
  }

  // Prompt Chips
  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const promptText = chip.getAttribute('data-prompt');
      if (inputEl) inputEl.value = promptText;
      handleSendMessage();
    });
  });
});

/**
 * Fetch and list all sessions in the sidebar
 */
async function loadSessions() {
  const listEl = document.getElementById('chat-session-list');
  if (!listEl) return;

  try {
    const res = await fetch('/api/chat/sessions');
    const json = await res.json();
    if (json.status === 'success') {
      listEl.innerHTML = '';
      const sessions = json.data;

      if (sessions.length === 0) {
        listEl.innerHTML = '<div style="font-size: 0.8rem; color: var(--text-dim); text-align: center; padding: 12px 0;">Belum ada sesi percakapan</div>';
        return;
      }

      sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'session-item' + (s.id === activeSessionId ? ' active' : '');
        item.setAttribute('data-id', s.id);
        item.innerHTML = `
          <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">
            ${escapeHtml(s.title)}
          </div>
          <span style="font-size: 0.7rem; color: var(--text-dim);">
            ${formatTime(s.created_at)}
          </span>
        `;
        item.addEventListener('click', () => {
          switchSession(s.id, s.title);
        });
        listEl.appendChild(item);
      });
    }
  } catch (err) {
    console.error('Error loading sessions:', err);
  }
}

/**
 * Create a new chat session
 */
async function createNewSession() {
  try {
    const res = await fetch('/api/chat/sessions', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({title: 'Percakapan baru'})
    });
    const json = await res.json();
    if (json.status === 'success') {
      activeSessionId = json.session_id;
      localStorage.setItem('spa_current_session', activeSessionId);
      await loadSessions();
      resetChatWindow('Percakapan Baru');
    }
  } catch (err) {
    console.error('Error creating new session:', err);
  }
}

/**
 * Switch to an existing session
 */
async function switchSession(sessionId, title) {
  activeSessionId = sessionId;
  localStorage.setItem('spa_current_session', activeSessionId);
  const titleEl = document.getElementById('chat-active-session-title');
  if (titleEl) titleEl.textContent = title || 'Sesi Analisis';

  // Update active state in sidebar
  document.querySelectorAll('.session-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-id') === sessionId);
  });

  await loadSessionMessages(sessionId);
}

/**
 * Delete a session
 */
async function deleteSession(sessionId) {
  try {
    await fetch(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
    activeSessionId = null;
    localStorage.removeItem('spa_current_session');
    await loadSessions();
    resetChatWindow('Percakapan Baru');
  } catch (err) {
    console.error('Error deleting session:', err);
  }
}

/**
 * Load all messages in an active session
 */
async function loadSessionMessages(sessionId) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  try {
    const res = await fetch(`/api/chat/sessions/${sessionId}`);
    const json = await res.json();
    if (json.status === 'success') {
      const messages = json.messages;
      container.innerHTML = '';

      if (messages.length === 0) {
        // Welcome bubble
        renderWelcomeMessage();
        return;
      }

      messages.forEach(m => {
        appendMessageBubble(m.role, m.content, m.evidence);
      });
      scrollToBottom();
    }
  } catch (err) {
    console.error('Error loading messages:', err);
  }
}

/**
 * Reset chat window to default state
 */
function resetChatWindow(title = 'Percakapan Baru') {
  const titleEl = document.getElementById('chat-active-session-title');
  if (titleEl) titleEl.textContent = title;
  const container = document.getElementById('chat-messages-container');
  if (container) {
    container.innerHTML = '';
    renderWelcomeMessage();
  }
}

function renderWelcomeMessage() {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;
  const welcome = document.createElement('div');
  welcome.className = 'chat-message assistant';
  welcome.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble">
      <p style="font-weight: 700; margin-bottom: 6px; color: var(--accent-cyan);">Halo Fajar! 👋</p>
      <p style="margin-bottom: 10px;">
        Saya adalah <strong>AI Chat Analyst</strong> untuk sistem <em>Smart People Analytics</em>. Saya dapat menganalisis data pergerakan orang masuk (IN), keluar (OUT), jam sibuk, perbandingan antarhari, dan estimasi okupansi ruangan.
      </p>
      <p style="font-size: 0.85rem; color: var(--text-muted);">
        Silakan ketik pertanyaan Anda atau pilih salah satu contoh pertanyaan di bawah untuk memulai:
      </p>
    </div>
  `;
  container.appendChild(welcome);
}

/**
 * Handles sending user query to backend API
 */
async function handleSendMessage() {
  const inputEl = document.getElementById('chat-input-text');
  const btnSend = document.getElementById('btn-send-message');
  const text = inputEl ? inputEl.value.trim() : '';

  if (!text) return;

  // Clear input
  inputEl.value = '';

  // Render user message immediately
  appendMessageBubble('user', text);
  scrollToBottom();

  // Show thinking indicator
  const thinkingBubbleId = showThinkingBubble();
  scrollToBottom();

  // Disable send button while processing
  if (btnSend) btnSend.disabled = true;

  try {
    const provider = localStorage.getItem('spa_ai_provider') || 'builtin';
    const apiKey = localStorage.getItem('spa_ai_key') || '';

    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        message: text,
        session_id: activeSessionId,
        provider: provider,
        api_key: apiKey
      })
    });

    const data = await res.json();
    removeThinkingBubble(thinkingBubbleId);

    if (data.status === 'success') {
      if (!activeSessionId) {
        activeSessionId = data.session_id;
        localStorage.setItem('spa_current_session', activeSessionId);
        loadSessions();
      }
      appendMessageBubble('assistant', data.answer, data.evidence);
    } else {
      appendMessageBubble('assistant', `⚠️ ${data.answer || 'Terjadi kesalahan sistem saat menganalisis data.'}`);
    }
  } catch (err) {
    removeThinkingBubble(thinkingBubbleId);
    appendMessageBubble('assistant', `⚠️ Gagal menghubungi server: ${err.message}`);
  } finally {
    if (btnSend) btnSend.disabled = false;
    scrollToBottom();
    if (inputEl) inputEl.focus();
  }
}

/**
 * Displays user or assistant chat bubble
 */
function appendMessageBubble(role, content, evidence = null) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  const msgDiv = document.createElement('div');
  msgDiv.className = `chat-message ${role}`;

  const avatarText = role === 'user' ? 'ME' : 'AI';
  const formattedContent = parseMarkdownText(content);

  let evidenceHtml = '';
  if (role === 'assistant' && evidence) {
    evidenceHtml = `
      <div class="evidence-card">
        <div class="evidence-header" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'">
          <div style="display: flex; align-items: center; gap: 8px;">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
            <span>Bukti Analitik Backend (Tool: ${escapeHtml(evidence.tool || evidence.tool_called || 'get_data')})</span>
          </div>
          <span class="evidence-badge">
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"></polyline></svg>
            Tervalidasi Database
          </span>
        </div>
        <div class="evidence-content" style="display: none;">
          <pre>${escapeHtml(JSON.stringify(evidence, null, 2))}</pre>
        </div>
      </div>
    `;
  }

  msgDiv.innerHTML = `
    <div class="msg-avatar">${avatarText}</div>
    <div class="msg-bubble">
      <div>${formattedContent}</div>
      ${evidenceHtml}
    </div>
  `;

  container.appendChild(msgDiv);
}

/**
 * Shows temporary typing animation
 */
function showThinkingBubble() {
  const container = document.getElementById('chat-messages-container');
  const bubbleId = 'thinking-' + Date.now();
  const div = document.createElement('div');
  div.id = bubbleId;
  div.className = 'chat-message assistant';
  div.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-bubble" style="display: flex; align-items: center; gap: 10px;">
      <span class="spinner"></span>
      <span style="font-size: 0.85rem; color: var(--text-muted);">Memeriksa database SQLite & mengeksekusi analitik...</span>
    </div>
  `;
  container.appendChild(div);
  return bubbleId;
}

function removeThinkingBubble(bubbleId) {
  const el = document.getElementById(bubbleId);
  if (el) el.remove();
}

function scrollToBottom() {
  const container = document.getElementById('chat-messages-container');
  if (container) {
    container.scrollTop = container.scrollHeight;
  }
}

/**
 * Basic markdown parsing for chat responses
 */
function parseMarkdownText(text) {
  if (!text) return '';
  let str = escapeHtml(text);

  // Bold **text**
  str = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Italic *text*
  str = str.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Newlines to breaks
  str = str.replace(/\n\n/g, '<div style="height: 8px;"></div>');
  str = str.replace(/\n/g, '<br>');

  // Bullet items
  str = str.replace(/<br>- (.*?)/g, '<br>• $1');

  return str;
}

function escapeHtml(string) {
  const entityMap = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };
  return String(string).replace(/[&<>"']/g, s => entityMap[s]);
}

function formatTime(isoStr) {
  if (!isoStr) return '';
  try {
    const d = new Date(isoStr);
    return `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
  } catch {
    return '';
  }
}
