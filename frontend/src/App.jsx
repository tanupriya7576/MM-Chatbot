import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import MessageList from './components/MessageList';
import InputBar from './components/InputBar';
import DocumentModal from './components/DocumentModal';
import {
  checkHealth,
  listConversations,
  createConversation,
  getConversation,
  deleteConversation,
  uploadFile,
  sendChatMessage
} from './services/api';

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [attachedFiles, setAttachedFiles] = useState([]); // { file, id, name, previewUrl }
  const [isLoading, setIsLoading] = useState(false);
  const [health, setHealth] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [docModalOpen, setDocModalOpen] = useState(false);
  const [webSearchToggled, setWebSearchToggled] = useState(false);
  const [ragToggled, setRagToggled] = useState(false);
  const [speakingMessageId, setSpeakingMessageId] = useState(null);

  // Initialize
  useEffect(() => {
    loadHealth();
    loadConversations();
  }, []);

  const loadHealth = async () => {
    try {
      const data = await checkHealth();
      setHealth(data);
    } catch (e) {
      setHealth({ status: 'offline', llm_provider: 'offline', search_engine: 'offline' });
    }
  };

  const loadConversations = async () => {
    try {
      const list = await listConversations();
      setConversations(list);
      if (list.length > 0 && !activeConversationId) {
        selectConversation(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load conversations:', err);
    }
  };

  const selectConversation = async (id) => {
    setActiveConversationId(id);
    setAttachedFiles([]);
    try {
      const detail = await getConversation(id);
      setMessages(detail.messages || []);
      setDocuments(detail.documents || []);
    } catch (err) {
      console.error('Failed to fetch conversation:', err);
    }
  };

  const handleNewConversation = async () => {
    try {
      const newConv = await createConversation('New Conversation');
      setConversations((prev) => [newConv, ...prev]);
      setActiveConversationId(newConv.id);
      setMessages([]);
      setDocuments([]);
      setAttachedFiles([]);
      setSidebarOpen(false);
    } catch (err) {
      console.error('Failed to create conversation:', err);
    }
  };

  const handleDeleteConversation = async (id) => {
    try {
      await deleteConversation(id);
      const remaining = conversations.filter((c) => c.id !== id);
      setConversations(remaining);
      if (activeConversationId === id) {
        if (remaining.length > 0) {
          selectConversation(remaining[0].id);
        } else {
          setActiveConversationId(null);
          setMessages([]);
          setDocuments([]);
        }
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleAttachFile = async (file) => {
    try {
      let previewUrl = null;
      if (file.type.startsWith('image/')) {
        previewUrl = URL.createObjectURL(file);
      }

      // Upload file immediately to get Document ID and index chunks for RAG
      const doc = await uploadFile(file, activeConversationId);
      setAttachedFiles((prev) => [
        ...prev,
        {
          file,
          id: doc.id,
          name: doc.filename,
          previewUrl
        }
      ]);
      setDocuments((prev) => [doc, ...prev]);
    } catch (err) {
      alert(`File upload failed: ${err.message}`);
    }
  };

  const handleRemoveFile = (index) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSendMessage = async (text) => {
    if (!text.trim() && attachedFiles.length === 0) return;

    // Optimistic user message
    const tempUserMsg = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
      metadata: { attached_file_ids: attachedFiles.map((f) => f.id) }
    };

    setMessages((prev) => [...prev, tempUserMsg]);
    setIsLoading(true);

    const fileIdsToSend = attachedFiles.map((f) => f.id);
    const forceWeb = webSearchToggled ? true : null;
    const forceRag = ragToggled ? true : null;

    // Clear attached files tray
    setAttachedFiles([]);

    try {
      const res = await sendChatMessage({
        message: text,
        conversationId: activeConversationId,
        attachedFileIds: fileIdsToSend,
        enableWebSearch: forceWeb,
        enableRAG: forceRag
      });

      // Update active conversation ID if it was newly created
      if (!activeConversationId && res.conversation_id) {
        setActiveConversationId(res.conversation_id);
      }

      // Add assistant response
      const assistantMsg = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: res.response,
        created_at: new Date().toISOString(),
        metadata: {
          query_type: res.query_type,
          sources: res.sources,
          created_document: res.created_document
        }
      };

      setMessages((prev) => [...prev, assistantMsg]);
      // Refresh conversations list to update titles
      loadConversations();
    } catch (err) {
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ **Error Processing Request:** ${err.message}`,
        created_at: new Date().toISOString(),
        metadata: { query_type: 'general' }
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Text-to-Speech handler
  const handleSpeak = (text) => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported in this browser.');
      return;
    }

    if (window.speechSynthesis.speaking) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      return;
    }

    // Clean markdown symbols for cleaner speech
    const cleanText = text.replace(/[#*`_\[\]()>-]/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);

    setSpeakingMessageId(true);
    window.speechSynthesis.speak(utterance);
  };

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans antialiased overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelectConversation={selectConversation}
        onNewConversation={handleNewConversation}
        onDeleteConversation={handleDeleteConversation}
        health={health}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onOpenDocModal={() => setDocModalOpen(true)}
      />

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col h-full lg:pl-72 relative">
        {/* Top Navbar */}
        <header className="h-14 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-4 flex items-center justify-between z-20">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
            >
              ☰
            </button>
            <div className="font-semibold text-sm text-slate-200 truncate">
              {conversations.find((c) => c.id === activeConversationId)?.title || 'Multimodal AI Assistant'}
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setDocModalOpen(true)}
              className="px-3 py-1.5 rounded-lg bg-indigo-600/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-600/30 text-xs font-medium transition"
            >
              📄 Document Tools
            </button>
          </div>
        </header>

        {/* Messages Stream */}
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onPromptClick={handleSendMessage}
          onSpeak={handleSpeak}
          speakingMessageId={speakingMessageId}
        />

        {/* Input Bar */}
        <InputBar
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          attachedFiles={attachedFiles}
          onAttachFile={handleAttachFile}
          onRemoveFile={handleRemoveFile}
          webSearchToggled={webSearchToggled}
          setWebSearchToggled={setWebSearchToggled}
          ragToggled={ragToggled}
          setRagToggled={setRagToggled}
        />
      </main>

      {/* Document Create/Update Modal */}
      <DocumentModal
        isOpen={docModalOpen}
        onClose={() => setDocModalOpen(false)}
        documents={documents}
        conversationId={activeConversationId}
        onDocumentCreated={(newDoc) => {
          setDocuments((prev) => [newDoc, ...prev]);
        }}
      />
    </div>
  );
}
