import { useCallback, useEffect, useState } from 'react';
import { Check, Cpu, RefreshCw } from 'lucide-react';
import { apiRequest } from '../lib/api';

interface Props {
  isDarkMode: boolean;
  onActiveModelChange: (model: string) => void;
}

export default function ModelManagementView({ isDarkMode, onActiveModelChange }: Props) {
  const [models, setModels] = useState<string[]>([]);
  const [active, setActive] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [modelResult, activeResult] = await Promise.all([
        apiRequest<{ models: string[] }>('/api/models'),
        apiRequest<{ active: string }>('/api/models/active'),
      ]);
      setModels(modelResult.models || []);
      setActive(activeResult.active);
      onActiveModelChange(activeResult.active);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load Ollama models.');
    } finally {
      setLoading(false);
    }
  }, [onActiveModelChange]);

  useEffect(() => { void refresh(); }, [refresh]);

  const choose = async (model: string) => {
    setSaving(model);
    setError(null);
    try {
      const result = await apiRequest<{ active: string }>('/api/models/active', {
        method: 'PUT', body: JSON.stringify({ model }),
      });
      setActive(result.active);
      onActiveModelChange(result.active);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not select this model.');
    } finally {
      setSaving(null);
    }
  };

  return (
    <section className="mx-auto h-full w-full max-w-4xl overflow-y-auto px-3 py-6 sm:px-8">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h2 className={`text-2xl font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>Models</h2>
          <p className={`mt-1 text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Choose an installed local Ollama model for new responses.</p>
        </div>
        <button onClick={() => void refresh()} aria-label="Refresh models" className={`rounded-xl border p-2.5 ${isDarkMode ? 'border-slate-600 text-slate-300 hover:bg-slate-700' : 'border-slate-200 text-slate-600 hover:bg-white'}`}><RefreshCw size={18} /></button>
      </div>

      {error && <div role="alert" className="mb-4 rounded-xl bg-amber-500/10 px-4 py-3 text-sm text-amber-300">{error}. Make sure Ollama is running and has a model installed.</div>}
      {loading ? (
        <p className={`py-10 text-center text-sm ${isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>Loading installed models…</p>
      ) : models.length === 0 ? (
        <div className={`rounded-2xl border border-dashed p-10 text-center ${isDarkMode ? 'border-slate-600 text-slate-400' : 'border-slate-300 text-slate-500'}`}><Cpu className="mx-auto mb-3" size={26} />No Ollama models are available.</div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {models.map((model) => {
            const selected = active === model;
            return (
              <button key={model} disabled={saving !== null} onClick={() => void choose(model)} className={`flex items-center gap-4 rounded-2xl border p-5 text-left transition ${selected
                ? 'border-cyan-400/70 bg-cyan-400/10'
                : isDarkMode ? 'border-slate-700 bg-slate-800/60 hover:border-slate-500' : 'border-slate-200 bg-white/70 hover:border-slate-300'}`}>
                <div className={`rounded-xl p-3 ${selected ? 'bg-cyan-400/15 text-cyan-300' : isDarkMode ? 'bg-slate-700 text-slate-300' : 'bg-slate-100 text-slate-600'}`}><Cpu size={20} /></div>
                <div className="min-w-0 flex-1">
                  <div className={`truncate font-medium ${isDarkMode ? 'text-slate-100' : 'text-slate-800'}`}>{model}</div>
                  <div className={`mt-1 text-xs ${selected ? 'text-cyan-300' : isDarkMode ? 'text-slate-400' : 'text-slate-500'}`}>
                    {saving === model ? 'Applying…' : selected ? 'Active model' : 'Select model'}
                  </div>
                </div>
                {selected && <Check size={19} className="text-cyan-400" />}
              </button>
            );
          })}
        </div>
      )}
      <p className={`mt-6 text-xs ${isDarkMode ? 'text-slate-500' : 'text-slate-500'}`}>Ollama is the local model runtime. Model downloads and installation are managed by Ollama.</p>
    </section>
  );
}
