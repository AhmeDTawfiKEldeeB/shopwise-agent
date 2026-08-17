(function () {
  const API_BASE = '/api/v1';

  const feed = document.getElementById('feed');
  const feedInner = document.getElementById('feed-inner');
  const greeting = document.getElementById('greeting');
  const chatInput = document.getElementById('chat-input');
  const sendBtn = document.getElementById('send-btn');
  const threadList = document.getElementById('thread-list');
  const threadEmpty = document.getElementById('thread-empty');
  const threadLoading = document.getElementById('thread-loading');
  const newChatBtn = document.getElementById('new-chat-btn');
  const chatTitle = document.getElementById('chat-title');
  const mobileTitle = document.getElementById('mobile-title');
  const errorBanner = document.getElementById('error-banner');
  const menuToggle = document.getElementById('menu-toggle');
  const sidenav = document.getElementById('sidenav');
  const sidenavBackdrop = document.getElementById('sidenav-backdrop');

  let currentThreadId = null;
  let isStreaming = false;
  let threadsCache = [];

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function toHtml(text) {
    return escapeHtml(text).replace(/\n/g, '<br>');
  }

  function scrollToBottom() {
    feed.scrollTop = feed.scrollHeight;
  }

  function setTitle(text) {
    chatTitle.textContent = text;
    mobileTitle.textContent = text;
  }

  function showError(message) {
    errorBanner.textContent = message;
    errorBanner.classList.remove('hidden');
    setTimeout(() => errorBanner.classList.add('hidden'), 5000);
  }

  function openSidenav() {
    sidenav.classList.add('open');
    sidenavBackdrop.classList.add('open');
  }
  function closeSidenav() {
    sidenav.classList.remove('open');
    sidenavBackdrop.classList.remove('open');
  }
  menuToggle.addEventListener('click', openSidenav);
  sidenavBackdrop.addEventListener('click', closeSidenav);

  // ---------- Message rendering ----------

  function clearFeed() {
    feedInner.innerHTML = '';
    const divider = document.createElement('div');
    divider.className = 'flex justify-center my-4';
    divider.innerHTML = '<span class="text-label-sm font-label-sm text-outline bg-surface-container-low px-3 py-1 rounded-full">Today</span>';
    feedInner.appendChild(divider);
  }

  function showGreeting() {
    clearFeed();
    feedInner.appendChild(greeting);
  }

  function renderUserMessage(text) {
    const wrap = document.createElement('div');
    wrap.className = 'flex gap-4 max-w-[85%] self-end justify-end';
    wrap.innerHTML = `
      <div class="flex flex-col gap-1 items-end">
        <div class="text-label-sm font-label-sm text-outline mr-1">You</div>
        <div class="bg-secondary text-on-secondary rounded-2xl rounded-tr-sm px-5 py-3.5 shadow-sm leading-relaxed whitespace-pre-wrap">${toHtml(text)}</div>
      </div>`;
    feedInner.appendChild(wrap);
    scrollToBottom();
  }

  function renderAgentMessage(text) {
    const wrap = document.createElement('div');
    wrap.className = 'flex gap-4 max-w-[85%] self-start group';
    wrap.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-on-secondary font-bold shadow-sm flex-shrink-0 mt-1">SW</div>
      <div class="flex flex-col gap-1">
        <div class="text-label-sm font-label-sm text-outline ml-1">ShopWise Agent</div>
        <div class="bubble-text bg-secondary-container border border-surface-variant rounded-2xl rounded-tl-sm px-5 py-3.5 shadow-sm text-on-secondary-container leading-relaxed"></div>
      </div>`;
    feedInner.appendChild(wrap);
    scrollToBottom();
    return wrap.querySelector('.bubble-text');
  }

  function renderTypingBubble() {
    const wrap = document.createElement('div');
    wrap.className = 'flex gap-4 max-w-[85%] self-start';
    wrap.innerHTML = `
      <div class="w-8 h-8 rounded-full bg-secondary flex items-center justify-center text-on-secondary font-bold shadow-sm flex-shrink-0 mt-1">SW</div>
      <div class="flex flex-col gap-1">
        <div class="text-label-sm font-label-sm text-outline ml-1">ShopWise Agent</div>
        <div class="bg-secondary-container border border-surface-variant rounded-2xl rounded-tl-sm px-5 py-4 shadow-sm flex items-center gap-1.5">
          <span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>
        </div>
      </div>`;
    feedInner.appendChild(wrap);
    scrollToBottom();
    return wrap;
  }

  // ---------- Threads ----------

  async function loadThreads() {
    threadLoading.classList.remove('hidden');
    try {
      const res = await fetch(`${API_BASE}/threads`);
      if (!res.ok) throw new Error('Failed to load threads');
      const json = await res.json();
      threadsCache = json.data || [];
      renderThreadList();
    } catch (err) {
      console.error(err);
    } finally {
      threadLoading.classList.add('hidden');
    }
  }

  function renderThreadList() {
    threadList.querySelectorAll('.thread-item').forEach(el => el.remove());
    if (!threadsCache.length) {
      threadEmpty.classList.remove('hidden');
      return;
    }
    threadEmpty.classList.add('hidden');
    threadsCache.forEach(t => {
      const item = document.createElement('button');
      item.className = 'thread-item flex flex-col items-start text-left gap-0.5 px-3 py-2 rounded-lg hover:bg-surface-container-high transition-colors' + (t.thread_id === currentThreadId ? ' active' : '');
      item.dataset.threadId = t.thread_id;
      item.innerHTML = `
        <span class="text-label-md font-label-md text-on-surface truncate w-full">${escapeHtml(t.title || t.thread_id)}</span>
        <span class="text-label-sm font-label-sm text-outline">${t.message_count} message${t.message_count === 1 ? '' : 's'}</span>`;
      item.addEventListener('click', () => openThread(t.thread_id, t.title));
      threadList.appendChild(item);
    });
  }

  async function openThread(threadId, title) {
    closeSidenav();
    currentThreadId = threadId;
    setTitle(title || threadId);
    renderThreadList();
    clearFeed();
    const loadingBubble = renderTypingBubble();
    try {
      const res = await fetch(`${API_BASE}/threads/${encodeURIComponent(threadId)}/history`);
      const json = await res.json();
      loadingBubble.remove();
      if (json.status !== 'success') {
        showError(json.message || 'Could not load this conversation.');
        return;
      }
      if (!json.data.length) {
        showGreeting();
        return;
      }
      json.data.forEach(msg => {
        if (msg.role === 'user') renderUserMessage(msg.content);
        else renderAgentMessage('').innerHTML = toHtml(msg.content);
      });
      scrollToBottom();
    } catch (err) {
      loadingBubble.remove();
      showError('Could not reach the server to load this conversation.');
    }
  }

  newChatBtn.addEventListener('click', () => {
    closeSidenav();
    currentThreadId = null;
    setTitle('New Chat');
    showGreeting();
    renderThreadList();
    chatInput.focus();
  });

  // ---------- Sending messages ----------

  function autoResize() {
    chatInput.style.height = '';
    chatInput.style.height = chatInput.scrollHeight + 'px';
  }
  chatInput.addEventListener('input', autoResize);
  chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  sendBtn.addEventListener('click', sendMessage);

  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isStreaming) return;

    chatInput.value = '';
    autoResize();
    isStreaming = true;
    sendBtn.disabled = true;

    renderUserMessage(text);
    const typingBubble = renderTypingBubble();

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, thread_id: currentThreadId }),
      });

      if (!res.ok || !res.body) {
        let msg = 'Something went wrong sending your message.';
        try {
          const errJson = await res.json();
          msg = errJson.message || msg;
        } catch (_) {}
        typingBubble.remove();
        renderAgentMessage(msg);
        showError(msg);
        return;
      }

      typingBubble.remove();
      let bubble = null;
      let agentText = '';
      let gotToken = false;

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const chunks = buffer.split('\n\n');
        buffer = chunks.pop();

        for (const chunk of chunks) {
          const line = chunk.trim();
          if (!line.startsWith('data:')) continue;
          const payloadStr = line.slice(5).trim();
          if (!payloadStr) continue;

          let payload;
          try {
            payload = JSON.parse(payloadStr);
          } catch (_) {
            continue;
          }

          if (payload.tool) {
            if (!bubble) {
              typingBubble.remove();
              bubble = renderAgentMessage('');
            }
            bubble.innerHTML = '<div class="flex items-center gap-2 text-on-secondary-container/70"><span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span><span class="ml-1 text-sm italic">' + toHtml(payload.tool) + '</span></div>';
            scrollToBottom();
          }

          if (payload.thinking_done) {
            if (!bubble) {
              typingBubble.remove();
              bubble = renderAgentMessage('');
            }
            bubble.innerHTML = '';
          }

          if (payload.token) {
            gotToken = true;
            if (!bubble) {
              typingBubble.remove();
              bubble = renderAgentMessage('');
            }
            agentText += payload.token;
            bubble.innerHTML = toHtml(agentText);
            scrollToBottom();
          }
          if (payload.done) {
            currentThreadId = payload.thread_id;
          }
        }
      }

      if (!gotToken) {
        if (!bubble) {
          typingBubble.remove();
          bubble = renderAgentMessage('');
        }
        bubble.innerHTML = toHtml('(No response received.)');
      }

      await loadThreads();
      if (currentThreadId) {
        const t = threadsCache.find(x => x.thread_id === currentThreadId);
        setTitle(t ? t.title : currentThreadId);
        renderThreadList();
      }
    } catch (err) {
      console.error(err);
      typingBubble.remove();
      renderAgentMessage('I ran into a connection problem. Please try again.');
      showError('Could not reach the server. Please try again.');
    } finally {
      isStreaming = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  // ---------- Init ----------
  loadThreads();
  chatInput.focus();
})();
