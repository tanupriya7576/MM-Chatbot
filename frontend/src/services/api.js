const API_BASE = '';

export async function checkHealth() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function listConversations() {
  const res = await fetch(`${API_BASE}/api/conversations`);
  if (!res.ok) throw new Error('Failed to fetch conversations');
  return res.json();
}

export async function createConversation(title = 'New Conversation') {
  const res = await fetch(`${API_BASE}/api/conversations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title })
  });
  if (!res.ok) throw new Error('Failed to create conversation');
  return res.json();
}

export async function getConversation(id) {
  const res = await fetch(`${API_BASE}/api/conversations/${id}`);
  if (!res.ok) throw new Error('Failed to fetch conversation details');
  return res.json();
}

export async function deleteConversation(id) {
  const res = await fetch(`${API_BASE}/api/conversations/${id}`, {
    method: 'DELETE'
  });
  if (!res.ok) throw new Error('Failed to delete conversation');
  return res.json();
}

export async function uploadFile(file, conversationId = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (conversationId) {
    formData.append('conversation_id', conversationId);
  }

  const res = await fetch(`${API_BASE}/api/files/upload`, {
    method: 'POST',
    body: formData
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function listDocuments(conversationId = null) {
  const url = conversationId
    ? `${API_BASE}/api/documents?conversation_id=${encodeURIComponent(conversationId)}`
    : `${API_BASE}/api/documents`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function createDocument({ title, instructions, conversationId, fileFormat = 'docx' }) {
  const res = await fetch(`${API_BASE}/api/documents/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title,
      instructions,
      conversation_id: conversationId,
      file_format: fileFormat
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to create document' }));
    throw new Error(err.detail || 'Failed to create document');
  }
  return res.json();
}

export async function updateDocument({ documentId, instructions, conversationId }) {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}/update`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      instructions,
      conversation_id: conversationId
    })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to update document' }));
    throw new Error(err.detail || 'Failed to update document');
  }
  return res.json();
}

export async function sendChatMessage({
  message,
  conversationId,
  attachedFileIds = [],
  enableWebSearch = null,
  enableRAG = null
}) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      attached_file_ids: attachedFileIds,
      enable_web_search: enableWebSearch,
      enable_rag: enableRAG
    })
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Assistant request failed' }));
    throw new Error(err.detail || 'Assistant request failed');
  }
  return res.json();
}

export async function performSearch(query) {
  const res = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  });
  if (!res.ok) throw new Error('Web search failed');
  return res.json();
}
