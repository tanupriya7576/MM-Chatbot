import React, { useState } from 'react';

export default function MessageItem({ message, onSpeak, isSpeaking }) {
  const isUser = message.role === 'user';
  const [showSources, setShowSources] = useState(false);

  // Parse metadata if needed
  let meta = message.metadata || {};
  if (typeof message.metadata_json === 'string' && message.metadata_json) {
    try {
      meta = { ...meta, ...JSON.parse(message.metadata_json) };
    } catch (e) {}
  }

  const queryType = meta.query_type;
  const sources = meta.sources || [];
  const createdDoc = meta.created_document;

  const renderBadge = () => {
    if (!queryType || isUser) return null;
    const badges = {
      image_generation: { label: '🎨 AI Image Generated', color: 'bg-fuchsia-950 text-fuchsia-300 border-fuchsia-800' },
      web_image_search: { label: '📷 Web Image Result', color: 'bg-teal-950 text-teal-300 border-teal-800' },
      rag: { label: '📄 Document RAG Grounding', color: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
      web_search: { label: '🌐 Web Search Grounded', color: 'bg-blue-950 text-blue-300 border-blue-800' },
      hybrid: { label: '⚡ RAG + Web Synthesis', color: 'bg-purple-950 text-purple-300 border-purple-800' },
      document_creation: { label: '📝 Document Generated', color: 'bg-amber-950 text-amber-300 border-amber-800' },
      document_update: { label: '🔄 Document Updated', color: 'bg-cyan-950 text-cyan-300 border-cyan-800' },
      general: { label: '🤖 Assistant', color: 'bg-slate-800 text-slate-300 border-slate-700' }
    };
    const b = badges[queryType] || badges.general;
    return (
      <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full border mb-1.5 ${b.color}`}>
        {b.label}
      </span>
    );
  };

  return (
    <div className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} my-3`}>
      <div
        className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3.5 shadow-sm transition ${
          isUser
            ? 'bg-indigo-600 text-white rounded-br-none'
            : 'bg-slate-900 border border-slate-800 text-slate-100 rounded-bl-none'
        }`}
      >
        {/* Modality Badge */}
        {renderBadge()}

        {/* Message Content */}
        <div className="text-sm leading-relaxed whitespace-pre-wrap break-words font-sans">
          {message.content}
        </div>

        {/* Generated / Updated Document Download Card */}
        {createdDoc && (
          <div className="mt-3 p-3 bg-slate-950/70 border border-emerald-800/60 rounded-xl flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 truncate">
              <span className="text-2xl">📑</span>
              <div className="truncate">
                <div className="font-medium text-xs text-white truncate">{createdDoc.filename}</div>
                <div className="text-[10px] text-emerald-400">Microsoft Word Document (.docx)</div>
              </div>
            </div>
            <a
              href={createdDoc.download_url}
              download
              target="_blank"
              rel="noreferrer"
              className="flex-shrink-0 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition shadow"
            >
              ⬇️ Download
            </a>
          </div>
        )}

        {/* Sources / Citations Drawer */}
        {sources && sources.length > 0 && (
          <div className="mt-3 border-t border-slate-800 pt-2">
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-300 font-medium transition"
            >
              <span>{showSources ? '▼' : '▶'}</span>
              <span>Cited Sources & Evidence ({sources.length})</span>
            </button>

            {showSources && (
              <div className="mt-2 space-y-1.5">
                {sources.map((s, idx) => (
                  <div
                    key={idx}
                    className="p-2 rounded-lg bg-slate-950/60 border border-slate-800 text-[11px] text-slate-300"
                  >
                    <div className="flex items-center justify-between font-medium text-slate-200">
                      <span className="truncate">
                        {s.type === 'document' ? '📄 ' : '🌐 '}
                        {s.title}
                      </span>
                      {s.score && (
                        <span className="text-[10px] text-emerald-400 font-mono ml-2">
                          match: {Math.round(s.score * 100)}%
                        </span>
                      )}
                    </div>
                    {s.url && (
                      <a
                        href={s.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-indigo-400 hover:underline truncate block mt-0.5 text-[10px]"
                      >
                        {s.url}
                      </a>
                    )}
                    {s.snippet && (
                      <p className="text-slate-400 mt-1 line-clamp-2 italic">
                        "{s.snippet}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Message Footer: Timestamp & Audio TTS */}
        <div className="mt-2 pt-1 flex items-center justify-between text-[10px] text-slate-400">
          <span>
            {message.created_at
              ? new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              : 'just now'}
          </span>

          {!isUser && onSpeak && (
            <button
              onClick={() => onSpeak(message.content)}
              title="Read response aloud (Text-to-Speech)"
              className="hover:text-indigo-300 text-slate-400 p-1 rounded transition"
            >
              {isSpeaking ? '🔊 Speaking...' : '🔈 Read Aloud'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
