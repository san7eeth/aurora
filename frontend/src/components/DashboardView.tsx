import { useEffect, useState } from 'react';
import { Activity, BookOpen, Cpu, Database, Gauge, MessageSquare, Settings2 } from 'lucide-react';
import { apiRequest } from '../lib/api';

interface Props { onToggleView: () => void; onOpenSetup: () => void; onOpenKnowledge: () => void; isDarkMode: boolean; userName: string }
interface Health { status: string; database: string; ollama: boolean; model: string }

export default function DashboardView({ onToggleView, onOpenSetup, onOpenKnowledge, isDarkMode, userName }: Props) {
  const [health, setHealth] = useState<Health | null>(null);
  const [activeModel, setActiveModel] = useState('');
  const [memory, setMemory] = useState<string>('Checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  useEffect(() => {
    let active = true;
    const refresh = async () => {
      try {
        const [value, selected] = await Promise.all([
          apiRequest<Health>('/health'),
          apiRequest<{ active: string }>('/api/models/active').catch(() => ({ active: '' })),
        ]);
        if (active) { setHealth(value); setActiveModel(selected.active || value.model); setLastChecked(new Date()); }
      } catch {
        if (active) { setHealth(null); setActiveModel(''); setLastChecked(new Date()); }
      }
      const perf = performance as Performance & { memory?: { usedJSHeapSize: number; jsHeapSizeLimit: number } };
      if (active) setMemory(perf.memory ? `${Math.round(perf.memory.usedJSHeapSize / 1024 / 1024)} MB / ${Math.round(perf.memory.jsHeapSizeLimit / 1024 / 1024)} MB heap` : 'Not exposed by this browser');
    };
    void refresh();
    const timer = window.setInterval(() => void refresh(), 15000);
    return () => { active = false; window.clearInterval(timer); };
  }, []);

  const card = isDarkMode ? 'border-slate-800 bg-slate-900/70' : 'border-slate-200 bg-white';
  const muted = isDarkMode ? 'text-slate-400' : 'text-slate-500';
  const statusText = health?.ollama ? 'Connected' : health ? 'Unavailable' : 'Backend unavailable';
  const statusColor = health?.ollama ? 'text-emerald-400' : health ? 'text-amber-400' : 'text-rose-400';

  return <section className="mx-auto w-full max-w-6xl px-4 py-8 sm:px-8" aria-labelledby="dashboard-heading">
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4"><div><p className="mb-2 text-sm font-medium uppercase tracking-[.18em] text-cyan-400">Your local assistant</p><h2 id="dashboard-heading" className={`text-3xl font-semibold tracking-tight sm:text-4xl ${isDarkMode ? 'text-white' : 'text-slate-950'}`}>Welcome{userName ? `, ${userName}` : ''}</h2><p className={`mt-2 ${muted}`}>Private AI tools, running on your device.</p></div><button onClick={onOpenSetup} className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm ${card} ${muted}`}><Settings2 size={16} />Personalize</button></div>
    <div className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <article className={`rounded-2xl border p-4 ${card}`}><div className={`mb-3 flex items-center gap-2 text-xs uppercase tracking-wide ${muted}`}><Activity size={15} />Ollama service</div><p className={`font-medium ${statusColor}`}>{statusText}</p><p className={`mt-1 text-xs ${muted}`}>{health?.database === 'ok' ? 'Backend database ready' : health ? 'Database needs attention' : 'Waiting for backend'}</p></article>
      <article className={`rounded-2xl border p-4 ${card}`}><div className={`mb-3 flex items-center gap-2 text-xs uppercase tracking-wide ${muted}`}><Cpu size={15} />Active model</div><p className={`truncate font-medium ${isDarkMode ? 'text-slate-100' : 'text-slate-900'}`} title={activeModel}>{activeModel || 'Not available'}</p><p className={`mt-1 text-xs ${muted}`}>Selected local model</p></article>
      <article className={`rounded-2xl border p-4 ${card}`}><div className={`mb-3 flex items-center gap-2 text-xs uppercase tracking-wide ${muted}`}><Database size={15} />Browser memory</div><p className={`truncate font-medium ${isDarkMode ? 'text-slate-100' : 'text-slate-900'}`} title={memory}>{memory}</p><p className={`mt-1 text-xs ${muted}`}>JavaScript heap estimate</p></article>
      <article className={`rounded-2xl border p-4 ${card}`}><div className={`mb-3 flex items-center gap-2 text-xs uppercase tracking-wide ${muted}`}><Gauge size={15} />System check</div><p className={`font-medium ${health?.status === 'ok' ? 'text-emerald-400' : health ? 'text-amber-400' : 'text-rose-400'}`}>{health?.status === 'ok' ? 'All available' : health ? 'Degraded' : 'Offline'}</p><p className={`mt-1 text-xs ${muted}`}>{lastChecked ? `Checked ${lastChecked.toLocaleTimeString()}` : 'Checking services'}</p></article>
    </div>
    <div className="grid gap-4 md:grid-cols-2"><button onClick={onToggleView} className={`group rounded-3xl border p-6 text-left transition hover:-translate-y-0.5 hover:border-cyan-400/50 ${card}`}><div className="mb-5 inline-flex rounded-2xl bg-cyan-400/10 p-3 text-cyan-400"><MessageSquare /></div><h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>Start a conversation</h3><p className={`mt-2 text-sm ${muted}`}>Chat with your selected local model and continue previous conversations.</p></button><button onClick={onOpenKnowledge} className={`group rounded-3xl border p-6 text-left transition hover:-translate-y-0.5 hover:border-cyan-400/50 ${card}`}><div className="mb-5 inline-flex rounded-2xl bg-cyan-400/10 p-3 text-cyan-400"><BookOpen /></div><h3 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>Explore your knowledge base</h3><p className={`mt-2 text-sm ${muted}`}>Manage local documents and memories used to ground assistant responses.</p></button></div>
  </section>;
}
