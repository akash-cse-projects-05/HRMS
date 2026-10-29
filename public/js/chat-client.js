// public/js/chat-client.js
// Client-side controller for team chat channels & direct messaging

let currentChatType = 'CHANNEL';
let currentChannelName = 'general';
let currentRecipientId = null;
let pollInterval = null;

function selectChannel(name, el) {
  currentChatType = 'CHANNEL';
  currentChannelName = name;
  currentRecipientId = null;

  document.querySelectorAll('.channel-item').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.dm-item').forEach(e => e.classList.remove('active'));

  const target = el || document.querySelector(`.channel-item[data-channel="${name}"]`);
  if (target && target.classList) target.classList.add('active');

  const titleEl = document.getElementById('activeChatTitle');
  const subEl = document.getElementById('activeChatSubtitle');
  if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-hashtag"></i> ${name}`;
  if (subEl) subEl.innerText = `Company channel: #${name}`;

  loadMessages();
}

function selectDirectUser(userId, userName, el) {
  currentChatType = 'DIRECT';
  currentRecipientId = userId;

  document.querySelectorAll('.channel-item').forEach(e => e.classList.remove('active'));
  document.querySelectorAll('.dm-item').forEach(e => e.classList.remove('active'));

  const target = el || document.querySelector(`.dm-item[data-user-id="${userId}"]`);
  if (target && target.classList) target.classList.add('active');

  const titleEl = document.getElementById('activeChatTitle');
  const subEl = document.getElementById('activeChatSubtitle');
  if (titleEl) titleEl.innerHTML = `<i class="fa-solid fa-user"></i> ${userName}`;
  if (subEl) subEl.innerText = `1-on-1 private conversation`;

  loadMessages();
}

async function loadMessages() {
  const stream = document.getElementById('messageStream');
  if (!stream) return;

  const url = currentChatType === 'CHANNEL'
    ? `/chat/channel/${currentChannelName}`
    : `/chat/direct/${currentRecipientId}`;

  try {
    const res = await fetch(url);
    const data = await res.json();
    if (data.success && data.messages) {
      renderMessages(data.messages);
    }
  } catch (err) {
    console.error('Error fetching chat messages:', err);
  }
}

function renderMessages(messages) {
  const stream = document.getElementById('messageStream');
  if (!stream) return;

  if (messages.length === 0) {
    stream.innerHTML = `<div style="text-align: center; color: #94a3b8; padding: 40px;">
      <i class="fa-solid fa-comments" style="font-size: 32px; margin-bottom: 10px; display: block;"></i>
      No messages here yet. Start the conversation!
    </div>`;
    return;
  }

  stream.innerHTML = messages.map(msg => {
    const sender = msg.senderId || {};
    let name = 'Colleague';
    if (sender.firstName) {
      name = `${sender.firstName} ${sender.lastName || ''}`.trim();
    } else if (sender._id === '000000000000000000000000' || !msg.senderId) {
      name = 'HR Admin';
    }

    const initial = name.charAt(0).toUpperCase();
    const time = msg.createdAt
      ? new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      : '';

    let cardHtml = '';
    if (msg.contextCard && msg.contextCard.cardType && msg.contextCard.cardType !== 'NONE') {
      cardHtml = `<div style="margin-top: 10px; padding: 10px 14px; background: #f1f5f9; border-left: 3px solid #2563eb; border-radius: 6px; font-size: 13px;">
        <strong><i class="fa-solid fa-id-card-clip"></i> ${msg.contextCard.title || 'HRMS Card'}</strong>
        <p style="margin: 4px 0 0 0; color: #475569;">${msg.contextCard.subtitle || ''}</p>
      </div>`;
    }

    return `
      <div class="message-row">
        <span class="msg-avatar">${initial}</span>
        <div class="msg-content-wrapper">
          <div class="msg-author-row">
            <strong class="msg-author">${name}</strong>
            <span class="msg-time">${time}</span>
          </div>
          <div class="msg-bubble">
            ${escapeHtml(msg.messageText || '')}
            ${cardHtml}
          </div>
        </div>
      </div>
    `;
  }).join('');

  stream.scrollTop = stream.scrollHeight;
}

async function handleSendMessage(e) {
  if (e && e.preventDefault) e.preventDefault();

  const input = document.getElementById('chatInputText');
  if (!input) return;

  const text = input.value.trim();
  if (!text) return;

  const payload = {
    type: currentChatType,
    channelName: currentChannelName,
    recipientId: currentRecipientId,
    messageText: text
  };

  try {
    const res = await fetch('/chat/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.success) {
      input.value = '';
      loadMessages();
    } else {
      alert(data.error || 'Failed to send message.');
    }
  } catch (err) {
    alert('Failed to send message: ' + err.message);
  }
}

function promptContextCard() {
  const cardTitle = prompt('Enter Card Title (e.g., Leave Request #401, October Payslip):');
  if (!cardTitle) return;

  const input = document.getElementById('chatInputText');
  if (input) {
    input.value += ` [Card: ${cardTitle}]`;
    input.focus();
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Initial load & 4s polling + keyboard handling
window.addEventListener('load', () => {
  loadMessages();
  pollInterval = setInterval(loadMessages, 4000);

  // Send on Enter, Shift+Enter for newline
  const input = document.getElementById('chatInputText');
  if (input) {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage(e);
      }
    });
  }
});
