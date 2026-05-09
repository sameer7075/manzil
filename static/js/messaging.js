let selectedFile = null;
let pollInterval;

document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('message-form');
    const fileInput = document.getElementById('file-input');
    const fileLabel = document.querySelector('.file-label');
    const messageInput = document.getElementById('message-input');
    const charCount = document.getElementById('char-count');

    if (messageForm) {
        messageForm.addEventListener('submit', handleSendMessage);
        
        fileInput.addEventListener('change', handleFileSelect);
        fileLabel.addEventListener('click', () => fileInput.click());
        
        messageInput.addEventListener('input', updateCharCount);

        // Event delegation for edit/delete buttons
        document.addEventListener('click', handleMessageActions);

        // Load existing conversations
        loadConversations();

        // Start polling for new messages
        startPolling();
    }
});

function handleMessageActions(e) {
    const msgId = e.target.dataset.msgId;
    
    if (e.target.classList.contains('edit-btn')) {
        showEditForm(msgId);
    } else if (e.target.classList.contains('delete-btn')) {
        deleteMessage(msgId);
    } else if (e.target.classList.contains('edit-save')) {
        saveEdit(msgId);
    } else if (e.target.classList.contains('edit-cancel')) {
        cancelEdit(msgId);
    }
}

function updateCharCount() {
    const input = document.getElementById('message-input');
    const count = document.getElementById('char-count');
    count.textContent = input.value.length + '/1000';
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit');
        e.target.value = '';
        return;
    }

    const allowedExtensions = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'];
    const fileExtension = file.name.split('.').pop().toLowerCase();

    if (!allowedExtensions.includes(fileExtension)) {
        alert('File type not allowed');
        e.target.value = '';
        return;
    }

    selectedFile = file;
    showFilePreview(file.name);
}

function showFilePreview(fileName) {
    const preview = document.getElementById('file-preview');
    const fileSize = (selectedFile.size / 1024).toFixed(2);
    
    preview.innerHTML = `
        <span class="file-preview-name">📎 ${fileName} (${fileSize}KB)</span>
        <button type="button" class="file-preview-clear" onclick="clearFilePreview()">Remove</button>
    `;
    preview.classList.add('show');
}

function clearFilePreview() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('file-preview').classList.remove('show');
}

function handleSendMessage(e) {
    e.preventDefault();

    const conversationId = convId; 
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();

    if (!content && !selectedFile) {
        alert('Message cannot be empty');
        return;
    }

    if (content.length > 1000) {
        alert('Message exceeds 1000 character limit');
        return;
    }

    const formData = new FormData();
    formData.append('conversation_id', conversationId);
    formData.append('content', content);

    if (selectedFile) {
        formData.append('file', selectedFile);
    }

    const sendBtn = document.querySelector('.send-btn');
    sendBtn.disabled = true;

    fetch('/messages/send', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        messageInput.value = '';
        clearFilePreview();
        updateCharCount();
        sendBtn.disabled = false;
        loadMessages();
    })
    .catch(err => {
        console.error('Error sending message:', err);
        sendBtn.disabled = false;
    });
}

function loadMessages() {
    const conversationId = convId; 
    const currentUserId = document.getElementById('current-user-id').value;

    fetch(`/messages/api/${conversationId}`)
        .then(res => res.json())
        .then(data => {
            const thread = document.getElementById('messages-thread');
            thread.innerHTML = '';

            data.messages.forEach(msg => {
                const msgElement = createMessageElement(msg, currentUserId);
                thread.appendChild(msgElement);
            });

            // Scroll to bottom
            thread.scrollTop = thread.scrollHeight;
        });
}

function createMessageElement(message, currentUserId) {
    const container = document.createElement('div');
    container.className = 'message-group';
    container.dataset.messageId = message.id;

    if (parseInt(message.sender_id) === parseInt(currentUserId)) {
        container.classList.add('sender');
    }

    if (message.is_deleted) {
        container.innerHTML = `
            <div class="message deleted-message">
                <span class="message-text">[Message deleted]</span>
            </div>
        `;
    } else {
        let attachmentHTML = '';
        if (message.attachment) {
            attachmentHTML = `
                <div class="message-attachment">
                    <a href="/static/uploads/messages/${message.attachment}" download>
                        📎 ${message.attachment.split('_').slice(1).join('_')}
                    </a>
                </div>
            `;
        }

        let actionsHTML = '';
        if (parseInt(message.sender_id) === parseInt(currentUserId)) {
            actionsHTML = `
                <div class="message-actions">
                    <button class="msg-btn edit-btn" data-msg-id="${message.id}">Edit</button>
                    <button class="msg-btn delete-btn" data-msg-id="${message.id}">Delete</button>
                </div>
            `;
        }

        let editedLabel = '';
        if (message.edited_at) {
            editedLabel = `<span class="edited-label">edited</span>`;
        }

        const messageClass = parseInt(message.sender_id) === parseInt(currentUserId) ? 'sender' : 'receiver';
        
        // Display content or attachment indicator
        const messageContent = message.content ? `<p class="message-text">${escapeHtml(message.content)}</p>` : 
                              (message.attachment ? '<p class="message-text"><em>📎 Attachment</em></p>' : '');

        container.innerHTML = `
            <div class="message ${messageClass}" data-msg-id="${message.id}">
                <div class="message-content">
                    ${messageContent}
                    ${attachmentHTML}
                </div>
                ${actionsHTML}
                <div class="message-meta">
                    <span class="message-time">${message.created_at}</span>
                    ${editedLabel}
                </div>
            </div>
            <div class="edit-form" id="edit-form-${message.id}" style="display: none;">
                <textarea class="edit-textarea" maxlength="1000" id="edit-text-${message.id}">${escapeHtml(message.content || '')}</textarea>
                <div class="edit-actions">
                    <button class="edit-save" type="button" data-msg-id="${message.id}">Save</button>
                    <button class="edit-cancel" type="button" data-msg-id="${message.id}">Cancel</button>
                </div>
            </div>
        `;
    }

    return container;
}

function showEditForm(messageId) {
    const form = document.getElementById(`edit-form-${messageId}`);
    if (form) {
        form.style.display = 'block';
        document.getElementById(`edit-text-${messageId}`).focus();
    }
}

function cancelEdit(messageId) {
    const form = document.getElementById(`edit-form-${messageId}`);
    if (form) {
        form.style.display = 'none';
    }
}

function saveEdit(messageId) {
    const textarea = document.getElementById(`edit-text-${messageId}`);
    const newContent = textarea.value.trim();

    if (!newContent) {
        alert('Message cannot be empty');
        return;
    }

    if (newContent.length > 1000) {
        alert('Message exceeds 1000 character limit');
        return;
    }

    const formData = new FormData();
    formData.append('content', newContent);

    fetch(`/messages/${messageId}/edit`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        loadMessages();
    })
    .catch(err => console.error('Error editing message:', err));
}

function deleteMessage(messageId) {
    if (!confirm('Are you sure you want to delete this message?')) {
        return;
    }

    fetch(`/messages/${messageId}/delete`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        loadMessages();
    })
    .catch(err => console.error('Error deleting message:', err));
}

function startPolling() {
    loadMessages();
    pollInterval = setInterval(loadMessages, 3000);
}

function stopPolling() {
    clearInterval(pollInterval);
}

function loadConversations() {
    const sidebarList = document.querySelector('.conversations-list');
    if (!sidebarList) return;

    fetch('/messages')
        .then(res => res.text())
        .then(html => {
            const tempDiv = document.createElement('div');
            tempDiv.innerHTML = html;
            const newList = tempDiv.querySelector('.conversations-list');
            if (newList) {
                sidebarList.innerHTML = newList.innerHTML;
            }
        });
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

window.addEventListener('beforeunload', stopPolling);