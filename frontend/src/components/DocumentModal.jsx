import React, { useState } from 'react';
import { createDocument, updateDocument } from '../services/api';

export default function DocumentModal({ isOpen, onClose, documents, conversationId, onDocumentCreated }) {
  const [tab, setTab] = useState('create'); // 'create' or 'update'
  const [title, setTitle] = useState('');
  const [instructions, setInstructions] = useState('');
  const [selectedDocId, setSelectedDocId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  if (!isOpen) return null;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!title.trim() || !instructions.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await createDocument({
        title,
        instructions,
        conversationId,
        fileFormat: 'docx'
      });
      setResult(res);
      if (onDocumentCreated) onDocumentCreated(res);
    } catch (err) {
      setError(err.message || 'Failed to create document');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!selectedDocId || !instructions.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await updateDocument({
        documentId: selectedDocId,
        instructions,
        conversationId
      });
      setResult(res);
      if (onDocumentCreated) onDocumentCreated(res);
    } catch (err) {
      setError(err.message || 'Failed to update document');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-lg bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">📄</span>
            <h3 className="font-semibold text-white text-sm">Document Assistant</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg"
          >
            ✕
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/50">
          <button
            onClick={() => { setTab('create'); setResult(null); setError(null); }}
            className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 transition ${
              tab === 'create'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            ➕ Create New Document
          </button>
          <button
            onClick={() => { setTab('update'); setResult(null); setError(null); }}
            className={`flex-1 py-2.5 text-xs font-medium text-center border-b-2 transition ${
              tab === 'update'
                ? 'border-indigo-500 text-indigo-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🔄 Modify Existing Document
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 flex-1 overflow-y-auto">
          {error && (
            <div className="p-3 rounded-xl bg-red-950/50 border border-red-800 text-red-300 text-xs">
              {error}
            </div>
          )}

          {result && (
            <div className="p-4 rounded-xl bg-emerald-950/50 border border-emerald-800 text-xs text-emerald-200 space-y-2">
              <div className="font-semibold text-emerald-300 flex items-center gap-1.5">
                <span>✅</span> {result.message}
              </div>
              <div className="text-slate-300 truncate">File: {result.filename}</div>
              <a
                href={result.download_url}
                download
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition shadow"
              >
                ⬇️ Download {result.filename}
              </a>
            </div>
          )}

          {tab === 'create' ? (
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Document Title
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. AI Trends in Healthcare Report 2026"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Generation Instructions
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="e.g. Include an executive summary, 4 key industry challenges, market analysis table, and a concluding recommendation."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-1.5 shadow"
                >
                  {loading ? 'Generating Document...' : 'Generate (.docx)'}
                </button>
              </div>
            </form>
          ) : (
            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Select Document to Modify
                </label>
                {documents.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">
                    No documents available in this session. Please upload a document first.
                  </p>
                ) : (
                  <select
                    value={selectedDocId}
                    onChange={(e) => setSelectedDocId(e.target.value)}
                    required
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="">-- Choose a document --</option>
                    {documents.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.filename} ({d.file_type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Modification Instructions
                </label>
                <textarea
                  required
                  rows={4}
                  placeholder="e.g. Add a summary conclusion section, correct grammatical mistakes, and reformat bullet points."
                  value={instructions}
                  onChange={(e) => setInstructions(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 resize-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={onClose}
                  className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading || documents.length === 0}
                  className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition flex items-center gap-1.5 shadow"
                >
                  {loading ? 'Updating Document...' : 'Apply & Save Copy'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
