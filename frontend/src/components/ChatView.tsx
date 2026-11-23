import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from 'react';
import { ArrowUp, Loader2, Sparkles } from 'lucide-react';
import { apiRequest, StoredMessage } from '../lib/api';
import { useAssistantWebSocket } from '../hooks/useAssistantSocket';

interface ChatViewProps {
  isDarkMode: boolean;
  conversationId: string | null;
  onConversationChange: (id: string | null) => void;
}

export default function ChatView({ isDarkMode, conversationId, onConversationChange }: ChatViewProps) {
  const [activeId, setActiveId] = useState<string | null>(conversationId);
  const [history, setHistory] = useState<StoredMessage[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [draft, setDraft] = useState('');
  const [pendingFirstMessage, setPendingFirstMessage] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { isConnected, messages, error, isStreaming, sendMessage } = useAssistantWebSocket(
    activeId,
    'chat',
    onConversationChange,
  );

  useEffect(() => {
    setActiveId(conversationId);
  }, [conversationId]);

  useEffect(() => {
    let cancelled = false;
    setHistory([]);
    if (!activeId) {
      setHistoryLoading(false);
      return;
    }
    setHistoryLoading(true);
    apiRequest<{ messages: StoredMessage[] }>(`/api/conversations/${activeId}`)
      .then((result) => { if (!cancelled) setHistory(result.messages || []); })
      .catch((reason: Error) => { if (!cancelled) setHistory([]); console.error(reason); })
      .finally(() => { if (!cancelled) setHistoryLoading(false); });
    return () => { cancelled = true; };
  }, [activeId]);

  useEffect(() => {
    if (isConnected && pendingFirstMessage) {
      sendMessage(pendingFirstMessage);
      setPendingFirstMessage(null);
    }
  }, [isConnected, pendingFirstMessage, sendMessage]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [history, messages, isStreaming]);

  const submitMessage = async (event?: FormEvent) => {
    event?.preventDefault();
    const text = draft.trim();
    if (!text || isStreaming) return;
    setDraft('');
    if (!activeId) {
      try {
        const created = await apiRequest<{ id: string }>('/api/conversations', {
          method: 'POST', body: JSON.stringify({}),
        });
        setActiveId(created.id);
        onConversationChange(created.id);
        setPendingFirstMessage(text);
      } catch (reason) {
        setDraft(text);
        console.error(reason);
      }
      return;
    }
    sendMessage(text);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void submitMessage();
    }
  };

  const textPrimary = isDarkMode ? 'text-slate-100' : 'text-slate-900';
  const textMuted = isDarkMode ? 'text-slate-400' : 'text-slate-500';
  const allMessages = [
    ...history.map((item) => ({ role: item.role, message: item.content, sources: item.metadata?.sources })),
    ...messages,
  ].filter((item) => item.role === 'user' || item.role === 'assistant');

  return (
    <div className="mx-auto flex h-full min-h-0 w-full max-w-5xl flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto px-3 py-6 sm:px-8">
        {allMessages.length === 0 && !historyLoading ? (
          <div className="flex h-full flex-col items-center justify-center text-center">
            <div className={`mb-5 rounded-2xl p-4 ${isDarkMode ? 'bg-cyan-400/10 text-cyan-300' : 'bg-cyan-50 text-cyan-700'}`}>
              <Sparkles size={28} />
            </div>
            <h2 className={`text-3xl font-semibold ${textPrimary}`}>What can I help with?</h2>
            <p className={`mt-3 max-w-md ${textMuted}`}>Your messages stay on this device. Start a conversation with Aurora.</p>
          </div>
        ) : historyLoading ? (
          <div className={`flex h-full items-center justify-center gap-2 ${textMuted}`}><Loader2 className="animate-spin" size={18} />Loading conversation…</div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {allMessages.map((item, index) => (
              <div key={`${index}-${item.role}`} className={`flex ${item.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className="max-w-[88%]">
                  <div className={`whitespace-pre-wrap rounded-2xl px-4 py-3 leading-7 ${item.role === 'user'
                    ? isDarkMode ? 'bg-cyan-500/20 text-cyan-50' : 'bg-cyan-100 text-slate-900'
                    : isDarkMode ? 'bg-slate-700/70 text-slate-100' : 'bg-white/80 text-slate-800 shadow-sm'}`}>
                    {item.message || (isStreaming && index === allMessages.length - 1 ? <span className="animate-pulse">…</span> : '')}
                  </div>
                  {item.role === 'assistant' && item.sources && item.sources.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {item.sources.map((source, sourceIndex) => (
                        <span key={`${source.source_file}-${source.page_number}-${sourceIndex}`} className={`rounded-lg border px-2 py-1 text-xs ${isDarkMode ? 'border-slate-600 bg-slate-800 text-slate-300' : 'border-slate-200 bg-white text-slate-600'}`}>
                          {source.source_file}{source.page_number ? ` · p. ${source.page_number}` : ''}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isStreaming && messages[messages.length - 1]?.role === 'user' && (
              <div className={`flex items-center gap-2 pl-2 text-sm ${textMuted}`}><Loader2 className="animate-spin" size={15} />Aurora is thinking…</div>
            )}
            {error && <p role="alert" className="rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-400">{error}</p>}
          </div>
        )}
      </div>

      <div className="mx-auto w-full max-w-3xl px-2 pb-4 pt-3 sm:px-4">
        <form onSubmit={(event) => void submitMessage(event)} className={`rounded-2xl border p-2 shadow-lg ${isDarkMode ? 'border-slate-600 bg-slate-800/90' : 'border-slate-200 bg-white/90'}`}>
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Message Aurora…"
            rows={2}
            aria-label="Message Aurora"
            className={`max-h-40 min-h-14 w-full resize-y bg-transparent px-3 py-2 outline-none ${textPrimary} placeholder:text-slate-500`}
          />
          <div className="flex items-center justify-between px-2 pb-1">
            <span className={`text-xs ${textMuted}`}>{activeId ? isConnected ? 'Connected' : 'Connecting…' : 'New conversation'} · Enter to send</span>
            <button type="submit" disabled={!draft.trim() || isStreaming || historyLoading} aria-label="Send message" className="rounded-xl bg-cyan-500 p-2.5 text-slate-950 transition hover:bg-cyan-400 disabled:cursor-not-allowed disabled:opacity-40">
              {isStreaming ? <Loader2 className="animate-spin" size={18} /> : <ArrowUp size={18} />}
            </button>
          </div>
        </form>
        <p className={`mt-2 text-center text-xs ${textMuted}`}>Aurora can make mistakes. Check important information.</p>
      </div>
    </div>
  );
}
