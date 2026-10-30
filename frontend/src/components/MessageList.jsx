import React, { useRef, useEffect } from 'react';
import MessageItem from './MessageItem';

export default function MessageList({
  messages,
  isLoading,
  onPromptClick,
  onSpeak,
  speakingMessageId
}) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const starterPrompts = [
    {
      icon: '📄',
      title: 'Analyze & Summarize Document',
      prompt: 'Summarize the main findings and conclusions of my uploaded document.'
    },
    {
      icon: '🌐',
      title: 'Real-time Web Research',
      prompt: 'What are the latest developments and breakthrough models in multimodal AI today?'
    },
    {
      icon: '📝',
      title: 'Generate Professional Report',
      prompt: 'Create a comprehensive report on Artificial Intelligence with introduction, key architectures, and future trends.'
    },
    {
      icon: '🖼️',
      title: 'Multimodal Vision Query',
      prompt: 'Please explain the structure, diagrams, and text shown in this image.'
    }
  ];

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 ? (
          <div className="py-12 flex flex-col items-center text-center">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-500 to-cyan-400 flex items-center justify-center text-3xl shadow-xl shadow-indigo-500/20 mb-4 animate-bounce">
              🤖
            </div>
            <h2 className="text-xl font-bold text-white mb-2">
              How can I assist you today?
            </h2>
            <p className="text-sm text-slate-400 max-w-md mb-8">
              I can answer general questions, ground responses in your uploaded documents with RAG, search the web, analyze images, and create or update documents.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl text-left">
              {starterPrompts.map((p, idx) => (
                <div
                  key={idx}
                  onClick={() => onPromptClick(p.prompt)}
                  className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 hover:bg-slate-800/80 cursor-pointer transition shadow-sm group"
                >
                  <div className="text-2xl mb-1.5">{p.icon}</div>
                  <div className="text-xs font-semibold text-slate-200 group-hover:text-indigo-300">
                    {p.title}
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-2">
                    {p.prompt}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          messages.map((m) => (
            <MessageItem
              key={m.id}
              message={m}
              onSpeak={onSpeak}
              isSpeaking={speakingMessageId === m.id}
            />
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div className="flex justify-start my-3">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl px-4 py-3 flex items-center gap-3 text-slate-300 text-xs shadow-sm">
              <span className="w-4 h-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
              <span>Synthesizing response, routing query & retrieving sources...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  );
}
