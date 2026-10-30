import React from 'react';

export default function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  health,
  isOpen,
  onClose,
  onOpenDocModal
}) {
  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`fixed top-0 bottom-0 left-0 z-40 w-72 bg-slate-900 border-r border-slate-800 text-slate-100 flex flex-col transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Brand Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <span className="text-xl">✨</span>
            </div>
            <div>
              <h1 className="font-semibold text-sm leading-tight text-white">Multimodal AI</h1>
              <p className="text-xs text-slate-400">Personal Assistant</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Action Buttons */}
        <div className="p-3 space-y-2">
          <button
            onClick={onNewConversation}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition shadow-sm hover:shadow-indigo-500/25 active:scale-[0.98]"
          >
            <span>➕</span> New Conversation
          </button>

          <button
            onClick={onOpenDocModal}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium border border-slate-700 transition"
          >
            <span>📄</span> Create / Update Document
          </button>
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider px-2 py-1">
            Recent Chats
          </div>

          {conversations.length === 0 ? (
            <div className="px-3 py-6 text-center text-xs text-slate-500">
              No chat sessions yet.<br />Start a new conversation!
            </div>
          ) : (
            conversations.map((c) => {
              const isActive = c.id === activeConversationId;
              return (
                <div
                  key={c.id}
                  className={`group relative flex items-center justify-between rounded-xl px-3 py-2 text-xs transition cursor-pointer ${
                    isActive
                      ? 'bg-slate-800 text-white font-medium border border-slate-700'
                      : 'text-slate-300 hover:bg-slate-800/60 hover:text-white'
                  }`}
                  onClick={() => onSelectConversation(c.id)}
                >
                  <div className="flex items-center gap-2 truncate pr-6">
                    <span className="text-slate-400">💬</span>
                    <span className="truncate">{c.title || 'Conversation'}</span>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(c.id);
                    }}
                    title="Delete conversation"
                    className="opacity-0 group-hover:opacity-100 text-slate-400 hover:text-red-400 transition p-1"
                  >
                    🗑️
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Health & System Status Footer */}
        <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-xs text-slate-400 space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
              System Status
            </span>
            <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
              {health?.status || 'checking...'}
            </span>
          </div>
          <div className="text-[11px] text-slate-500 flex justify-between">
            <span>LLM: {health?.llm_provider || 'gemini'}</span>
            <span>Search: {health?.search_engine || 'duckduckgo'}</span>
          </div>
        </div>
      </aside>
    </>
  );
}
