import { FormEvent, useCallback, useEffect, useState } from 'react';
import { Brain, Check, Pencil, Plus, Trash2, X } from 'lucide-react';
import { apiRequest, formatTimestamp } from '../lib/api';

interface MemoryRecord {
  id: string;
  content: string;
  summary: string | null;
  importance: number;
  source: string | null;
  created_at: string | null;
  access_count: number;
}

interface Props { isDarkMode: boolean }

export default function MemoryManagementView({ isDarkMode }: Props) {
  const [memories, setMemories] = useState<MemoryRecord[]>([]);
  const [draft, setDraft] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDraft, setEditDraft] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const result = await apiRequest<{ memories: MemoryRecord[] }>('/api/memories?limit=100');
      setMemories(result.memories || []);
      setError(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load memories.');
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const add = async (event: FormEvent) => {
    event.preventDefault();
    const content = draft.trim();
    if (!content) return;
    setSaving(true);
    try {
      await apiRequest('/api/memories', { method: 'POST', body: JSON.stringify({ content, source: 'user', importance: 0.6 }) });
      setDraft('');
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not save memory.');
    } finally { setSaving(false); }
  };

  const beginEdit = (memory: MemoryRecord) => {
    setEditingId(memory.id);
    setEditDraft(memory.content);
  };

  const saveEdit = async (id: string) => {
    const content = editDraft.trim();
    if (!content) return;
    try {
      await apiRequest(`/api/memories/${id}`, { method: 'PATCH', body: JSON.stringify({ content }) });
      setEditingId(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not update memory.');
    }
  };

  const remove = async (id: string) => {
    try {
      await apiRequest(`/api/memories/${id}`, { method: 'DELETE' });
      setMemories((items) => items.filter((item) => item.id !== id));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete memory.');
    }
  };

  const titleColor = isDarkMode ? 'text-slate-100' : 'text-slate-900';
  const mutedColor = isDarkMode ? 'text-slate-400' : 'text-slate-500';
  const fieldClass = `w-full rounded-xl border bg-transparent px-3 py-2.5 outline-none focus:border-cyan-500 ${isDarkMode ? 'border-slate-600 text-slate-100 placeholder:text-slate-500' : 'border-slate-200 text-slate-900 placeholder:text-slate-400'}`;

  return (
    <section className="mx-auto flex h-full w-full max-w-4xl flex-col px-3 py-6 sm:px-8">
      <div className="mb-5">
        <h2 className={`text-2xl font-semibold ${titleColor}`}>Long-term memory</h2>
        <p className={`mt-1 text-sm ${mutedColor}`}>Review, add, or remove facts Aurora can use to personalize future chats.</p>
      </div>

      <form onSubmit={(event) => void add(event)} className={`mb-5 rounded-2xl border p-4 ${isDarkMode ? 'border-slate-700 bg-slate-800/50' : 'border-slate-200 bg-white/70'}`}>
        <label htmlFor="memory-content" className={`mb-2 block text-sm font-medium ${titleColor}`}>Add a memory</label>
        <div className="flex gap-2">
          <input id="memory-content" value={draft} onChange={(event) => setDraft(event.target.value)} maxLength={1000} placeholder="For example: I prefer concise answers." className={fieldClass} />
          <button disabled={!draft.trim() || saving} className="flex shrink-0 items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2 text-sm font-medium text-slate-950 hover:bg-cyan-400 disabled:opacity-40"><Plus size={17} />Save</button>
        </div>
      </form>

      {error && <p role="alert" className="mb-3 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-400">{error}</p>}
      <div className="min-h-0 flex-1 overflow-y-auto">
        {loading ? <p className={`py-8 text-center text-sm ${mutedColor}`}>Loading memories…</p> : memories.length === 0 ? (
          <div className={`rounded-2xl border border-dashed p-10 text-center ${isDarkMode ? 'border-slate-600 text-slate-400' : 'border-slate-300 text-slate-500'}`}><Brain className="mx-auto mb-3" size={25} />No saved memories yet. You can add one above; Aurora may also save stable facts from chats.</div>
        ) : (
          <div className="space-y-2">
            {memories.map((memory) => (
              <article key={memory.id} className={`rounded-2xl border p-4 ${isDarkMode ? 'border-slate-700 bg-slate-800/60' : 'border-slate-200 bg-white/70'}`}>
                {editingId === memory.id ? (
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <input value={editDraft} onChange={(event) => setEditDraft(event.target.value)} maxLength={1000} aria-label="Edit memory" className={fieldClass} />
                    <div className="flex gap-2">
                      <button onClick={() => void saveEdit(memory.id)} aria-label="Save memory" className="rounded-lg bg-cyan-500 p-2 text-slate-950"><Check size={17} /></button>
                      <button onClick={() => setEditingId(null)} aria-label="Cancel editing" className={`rounded-lg p-2 ${mutedColor}`}><X size={17} /></button>
                    </div>
                  </div>
                ) : (
                  <>
                    <p className={`whitespace-pre-wrap leading-6 ${titleColor}`}>{memory.content}</p>
                    <div className={`mt-2 flex flex-wrap items-center gap-x-3 text-xs ${mutedColor}`}>
                      <span>{memory.source === 'conversation' ? 'Learned from chat' : 'Added by you'}</span>
                      <span>{formatTimestamp(memory.created_at)}</span>
                      <span>Importance {Math.round(memory.importance * 100)}%</span>
                      {memory.access_count > 0 && <span>Used {memory.access_count} times</span>}
                    </div>
                  </>
                )}
                {editingId !== memory.id && <div className="mt-3 flex justify-end gap-1">
                  <button onClick={() => beginEdit(memory)} aria-label="Edit memory" className={`rounded-lg p-2 ${mutedColor} hover:bg-cyan-500/10 hover:text-cyan-400`}><Pencil size={16} /></button>
                  <button onClick={() => void remove(memory.id)} aria-label="Delete memory" className="rounded-lg p-2 text-slate-500 hover:bg-red-500/10 hover:text-red-400"><Trash2 size={16} /></button>
                </div>}
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
