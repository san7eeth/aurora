import { useCallback, useEffect, useState } from 'react';
import { Check, ClipboardCheck, Loader2, Mic, Play, ShieldAlert, X } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { captureVoiceSample } from '../lib/captureVoiceSample';

interface PlanStep {
  tool: string;
  arguments: Record<string, unknown>;
  reason: string;
  sensitive: boolean;
}
interface AgentRun {
  id: string;
  task: string;
  status: string;
  created_at: string;
  result?: { summary?: string; steps?: { tool: string; ok: boolean; output?: unknown; error?: string }[] } | null;
}

interface Props { isDarkMode: boolean }

export default function AgentManagementView({ isDarkMode }: Props) {
  const [task, setTask] = useState('');
  const [plan, setPlan] = useState<{ plan_id: string; steps: PlanStep[] } | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [enrolled, setEnrolled] = useState(false);
  const [voiceMatch, setVoiceMatch] = useState('');

  const refresh = useCallback(async () => {
    const [history, voiceStatus] = await Promise.all([
      apiRequest<{ runs: AgentRun[] }>('/api/agent/history'),
      apiRequest<{ enrolled: boolean }>('/api/voice-auth/status'),
    ]);
    setRuns(history.runs);
    setEnrolled(voiceStatus.enrolled);
  }, []);

  useEffect(() => { void refresh().catch((reason: Error) => setError(reason.message)); }, [refresh]);

  const createPlan = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true); setError(''); setNotice('');
    try {
      const result = await apiRequest<{ plan_id: string; steps: PlanStep[] }>('/api/agent/plan', { method: 'POST', body: JSON.stringify({ task }) });
      setPlan(result); await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not plan this task.'); }
    finally { setBusy(false); }
  };

  const executePlan = async () => {
    if (!plan) return;
    setBusy(true); setError('');
    try {
      const result = await apiRequest<{ summary: string; results: unknown[] }>('/api/agent/execute', { method: 'POST', body: JSON.stringify({ plan_id: plan.plan_id, confirmed: true }) });
      setNotice(result.summary); setPlan(null); await refresh();
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not execute the plan.'); }
    finally { setBusy(false); }
  };

  const cancelPlan = async () => {
    if (!plan) return;
    setBusy(true);
    try { await apiRequest(`/api/agent/${plan.plan_id}/cancel`, { method: 'POST' }); setPlan(null); await refresh(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not cancel the plan.'); }
    finally { setBusy(false); }
  };

  const voiceAction = async (action: 'enroll' | 'verify') => {
    setBusy(true); setError(''); setVoiceMatch(''); setNotice('Recording a 4 second sample…');
    try {
      const sample = await captureVoiceSample();
      if (action === 'enroll') {
        await apiRequest('/api/voice-auth/enroll', { method: 'POST', body: sample, headers: { 'Content-Type': 'application/octet-stream' } });
        setEnrolled(true); setNotice('Voice profile saved on this device. This is an approximate match, not an access control.');
      } else {
        const result = await apiRequest<{ matched: boolean; score: number; warning: string }>('/api/voice-auth/verify', { method: 'POST', body: sample, headers: { 'Content-Type': 'application/octet-stream' } });
        setVoiceMatch(`${result.matched ? 'Voice sample matched' : 'No match'} · similarity ${result.score}`);
        setNotice(result.warning);
      }
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Voice sample could not be processed.'); setNotice(''); }
    finally { setBusy(false); }
  };

  const removeVoiceProfile = async () => {
    setBusy(true);
    try { await apiRequest('/api/voice-auth/profile', { method: 'DELETE' }); setEnrolled(false); setVoiceMatch(''); setNotice('Voice profile removed from this device.'); }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not remove voice profile.'); }
    finally { setBusy(false); }
  };

  const card = `rounded-2xl border p-5 ${isDarkMode ? 'border-slate-700 bg-slate-800/60 text-slate-100' : 'border-slate-200 bg-white/80 text-slate-900'}`;
  const muted = isDarkMode ? 'text-slate-400' : 'text-slate-500';

  return <div className="h-full overflow-y-auto p-4 md:p-7">
    <div className="mx-auto max-w-4xl space-y-6">
      <header><h1 className="text-2xl font-semibold">Agent tasks</h1><p className={`mt-1 text-sm ${muted}`}>Plan local actions, review every step, then approve execution.</p></header>
      <form onSubmit={(event) => void createPlan(event)} className={card}>
        <label className="mb-2 block text-sm font-medium" htmlFor="agent-task">What should Aurora do?</label>
        <textarea id="agent-task" value={task} onChange={event => setTask(event.target.value)} maxLength={1000} rows={3} className="w-full rounded-xl border border-slate-600 bg-slate-950/30 p-3 outline-none focus:border-cyan-500" placeholder="For example: show me my uploaded files and system information" />
        <button disabled={busy || Boolean(plan) || task.trim().length < 2} className="mt-3 inline-flex items-center gap-2 rounded-xl bg-cyan-500 px-4 py-2.5 font-medium text-slate-950 disabled:opacity-50">{busy ? <Loader2 className="animate-spin" size={17} /> : <Play size={16} />}Create reviewable plan</button>
      </form>

      {plan && <section className={`${card} border-amber-500/50`}>
        <h2 className="mb-3 flex items-center gap-2 font-semibold"><ShieldAlert size={18} className="text-amber-400" />Review before execution</h2>
        <ol className="space-y-3">{plan.steps.map((step, index) => <li key={`${step.tool}-${index}`} className="rounded-xl bg-slate-950/20 p-3">
          <div className="flex flex-wrap items-center gap-2"><span className="font-medium">{index + 1}. {step.tool.replace(/_/g, ' ')}</span>{step.sensitive && <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-xs text-amber-300">Sensitive · confirmation required</span>}</div>
          <p className={`mt-1 text-sm ${muted}`}>{step.reason}</p>
          {Object.keys(step.arguments).length > 0 && <pre className="mt-2 overflow-auto text-xs">{JSON.stringify(step.arguments, null, 2)}</pre>}
        </li>)}</ol>
        <p className="mt-3 text-xs text-amber-300">Every planned step runs only after you approve it. Clipboard results are omitted from saved history.</p>
        <div className="mt-4 flex gap-2"><button disabled={busy} onClick={() => void executePlan()} className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2 text-sm font-medium text-slate-950"><Check size={16} />Approve and run</button><button disabled={busy} onClick={() => void cancelPlan()} className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-4 py-2 text-sm"><X size={16} />Cancel</button></div>
      </section>}

      {(notice || voiceMatch || error) && <div role={error ? 'alert' : 'status'} className={`${card} ${error ? 'border-rose-500/50 text-rose-300' : ''}`}>{voiceMatch && <p className="font-medium">{voiceMatch}</p>}{notice && <p className="text-sm">{notice}</p>}{error && <p>{error}</p>}</div>}

      <section className={card}>
        <h2 className="font-semibold">Optional voice profile</h2>
        <p className={`mt-1 text-sm ${muted}`}>Stores a compact voice feature vector locally; it does not retain the recording. Speaker matching is approximate and must not protect actions or data.</p>
        <div className="mt-3 flex flex-wrap gap-2"><button disabled={busy} onClick={() => void voiceAction(enrolled ? 'verify' : 'enroll')} className="inline-flex items-center gap-2 rounded-lg border border-slate-600 px-3 py-2 text-sm"><Mic size={16} />{enrolled ? 'Verify voice sample' : 'Record and enroll'}</button>{enrolled && <><button disabled={busy} onClick={() => void voiceAction('enroll')} className="rounded-lg border border-slate-600 px-3 py-2 text-sm">Replace profile</button><button disabled={busy} onClick={() => void removeVoiceProfile()} className="rounded-lg border border-rose-500/40 px-3 py-2 text-sm text-rose-300">Delete profile</button></>}</div>
      </section>

      <section className={card}>
        <h2 className="mb-3 flex items-center gap-2 font-semibold"><ClipboardCheck size={18} />Execution history</h2>
        {runs.length === 0 ? <p className={`text-sm ${muted}`}>No agent tasks yet.</p> : <div className="space-y-3">{runs.map(run => <article key={run.id} className="border-t border-slate-700/60 pt-3"><div className="flex flex-wrap justify-between gap-2"><span className="font-medium">{run.task}</span><span className={`text-xs ${muted}`}>{run.status} · {new Date(run.created_at).toLocaleString()}</span></div>{run.result?.summary && <p className={`mt-1 text-sm ${muted}`}>{run.result.summary}</p>}</article>)}</div>}
      </section>
    </div>
  </div>;
}
