import React, { useRef, useState, useEffect } from 'react';

export default function InputBar({
  onSendMessage,
  isLoading,
  attachedFiles,
  onAttachFile,
  onRemoveFile,
  webSearchToggled,
  setWebSearchToggled,
  ragToggled,
  setRagToggled
}) {
  const [text, setText] = useState('');
  const [isListening, setIsListening] = useState(false);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-resize textarea as user types
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [text]);

  const handleSubmit = (e) => {
    if (e) e.preventDefault();
    if ((!text.trim() && attachedFiles.length === 0) || isLoading) return;

    onSendMessage(text);
    setText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach((f) => onAttachFile(f));
    e.target.value = '';
  };

  // Speech-to-Text using Web Speech API
  const toggleSpeechRecognition = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
      return;
    }

    if (isListening) {
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => setIsListening(false);
      recognition.onerror = () => setIsListening(false);

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
      };

      recognition.start();
    } catch (err) {
      console.error(err);
      setIsListening(false);
    }
  };

  return (
    <div className="border-t border-slate-800 bg-slate-900/90 backdrop-blur-md p-3 sm:p-4">
      <div className="max-w-4xl mx-auto space-y-2">
        {/* Attached Files Tray */}
        {attachedFiles.length > 0 && (
          <div className="flex flex-wrap gap-2 pb-1">
            {attachedFiles.map((f, idx) => (
              <div
                key={idx}
                className="flex items-center gap-2 bg-slate-800 border border-slate-700 text-slate-200 text-xs px-2.5 py-1.5 rounded-xl shadow-sm"
              >
                {f.previewUrl ? (
                  <img src={f.previewUrl} alt="preview" className="w-5 h-5 object-cover rounded" />
                ) : (
                  <span>{f.name.endsWith('.pdf') ? '📕' : f.name.endsWith('.docx') ? '📘' : '📄'}</span>
                )}
                <span className="max-w-[140px] truncate">{f.name}</span>
                <button
                  type="button"
                  onClick={() => onRemoveFile(idx)}
                  className="text-slate-400 hover:text-red-400 font-bold ml-1"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Query Mode Badges */}
        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => setWebSearchToggled(!webSearchToggled)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              webSearchToggled
                ? 'bg-blue-600/30 border-blue-500 text-blue-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>🌐</span> Web Search {webSearchToggled ? 'ON' : 'Auto'}
          </button>

          <button
            type="button"
            onClick={() => setRagToggled(!ragToggled)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-lg border text-xs font-medium transition ${
              ragToggled
                ? 'bg-emerald-600/30 border-emerald-500 text-emerald-300'
                : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
          >
            <span>📄</span> RAG Grounding {ragToggled ? 'ON' : 'Auto'}
          </button>
        </div>

        {/* Input Bar Main Box */}
        <div className="flex items-end gap-2 bg-slate-950 border border-slate-800 rounded-2xl p-2 focus-within:border-indigo-500 transition shadow-inner">
          {/* File Attachment Button */}
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp"
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            title="Attach documents (PDF, DOCX, TXT) or images"
            className="p-2 text-slate-400 hover:text-indigo-400 hover:bg-slate-800/80 rounded-xl transition"
          >
            📎
          </button>

          {/* Voice Input Button */}
          <button
            type="button"
            onClick={toggleSpeechRecognition}
            title={isListening ? 'Listening... click to stop' : 'Voice Input (Speech-to-Text)'}
            className={`p-2 rounded-xl transition ${
              isListening
                ? 'bg-red-500/20 text-red-400 animate-pulse'
                : 'text-slate-400 hover:text-indigo-400 hover:bg-slate-800/80'
            }`}
          >
            🎤
          </button>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            rows={1}
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question, upload docs, or type 'Create a report on AI'..."
            className="flex-1 bg-transparent border-0 outline-none resize-none text-slate-100 placeholder-slate-500 text-sm py-1.5 px-2 max-h-40 leading-relaxed font-sans"
          />

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={(!text.trim() && attachedFiles.length === 0) || isLoading}
            className={`p-2.5 rounded-xl font-medium transition flex items-center justify-center ${
              (!text.trim() && attachedFiles.length === 0) || isLoading
                ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-md shadow-indigo-600/30 active:scale-95'
            }`}
          >
            {isLoading ? (
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              '➤'
            )}
          </button>
        </div>

        <div className="text-[11px] text-center text-slate-500">
          Press <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">Shift + Enter</kbd> for new line
        </div>
      </div>
    </div>
  );
}
