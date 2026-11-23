import { useCallback, useEffect, useState } from 'react';
import { MessageSquare, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { apiRequest, ConversationSummary, formatTimestamp } from '../lib/api';

interface Props {
  isDarkMode: boolean;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export default function ConversationHistoryView({ isDarkMode, onSelect, onNew }: Props) {
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await apiRequest<{ conversations: ConversationSummary[] }>('/api/conversations?limit=100');
      setConversations(result.conversations || []);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load conversations.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const remove = async (id: string) => {
    try {
      await apiRequest(`/api/conversations/${id}`, { method: 'DELETE' });
      setConversations((items) => items.filter((item) => item.id !== id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete conversation.');
    }
  };

  return (
    <section className="mx-auto flex h-full w-full max-w-4xl flex-col px-3 py-6 sm:px-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>Conversation history</h2>
          <p className={`mt-1 text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Your chats are stored locally on this device.</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => void refresh()} aria-label="Refresh conversations" className={`rounded-xl border p-2.5 ${isDarkMode ? 'border-slate-600 text-slate-300 hover:bg-slate-700' : 'border-slate-200 text-slate-600 hover:bg-white'}`}><RefreshCw size={18} /></button>
          <button onClick={onNew} className="flex items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2.5 text-sm font-medium text-slate-950 hover:bg-cyan-400"><Plus size={18} />New chat</button>
        </div>
      </div>

      {error && <p role="alert" className="mb-4 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-400">{error}</p>}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? (
          <p className={`py-10 text-center text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Loading conversations…</p>
        ) : conversations.length === 0 ? (
          <div className={`rounded-2xl border border-dashed p-10 text-center ${isDarkMode ? 'border-slate-600 text-slate-400' : 'border-slate-300 text-slate-500'}`}>
            <MessageSquare className="mx-auto mb-3" size={24} />No conversations yet. Start a chat with Aurora.
          </div>
        ) : (
          <div className="space-y-2">
            {conversations.map((conversation) => (
              <div key={conversation.id} className={`group flex items-center gap-3 rounded-2xl border p-4 transition ${isDarkMode ? 'border-slate-700 bg-slate-800/60 hover:border-slate-500' : 'border-slate-200 bg-white/70 hover:border-slate-300'}`}>
                <button onClick={() => onSelect(conversation.id)} className="min-w-0 flex-1 text-left">
                  <div className={`truncate font-medium ${isDarkMode ? 'text-slate-100' : 'text-slate-800'}`}>{conversation.title || 'New Conversation'}</div>
                  <div className={`mt-1 flex flex-wrap gap-x-3 text-xs ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                    <span>{formatTimestamp(conversation.updated_at)}</span>
                    {conversation.model_name && <span>{conversation.model_name}</span>}
                  </div>
                </button>
                <button onClick={() => void remove(conversation.id)} aria-label={`Delete ${conversation.title || 'conversation'}`} className="rounded-lg p-2 text-slate-500 transition hover:bg-red-500/10 hover:text-red-400"><Trash2 size={17} /></button>
              </div>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
