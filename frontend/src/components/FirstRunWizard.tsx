import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { ArrowLeft, ArrowRight, Check, Loader2, Mic, Sparkles, X } from 'lucide-react';
import { apiRequest } from '../lib/api';
import { captureVoiceSample } from '../lib/captureVoiceSample';

interface Props { isDarkMode: boolean; onClose: (name: string) => void }

export default function FirstRunWizard({ isDarkMode, onClose }: Props) {
  const [step, setStep] = useState(0);
  const [name, setName] = useState('');
  const [models, setModels] = useState<string[]>([]);
  const [model, setModel] = useState('');
  const [voiceSaved, setVoiceSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([
      apiRequest<{ settings: Record<string, unknown> }>('/api/settings'),
      apiRequest<{ models: string[] }>('/api/models'),
      apiRequest<{ active: string }>('/api/models/active'),
    ]).then(([settingResult, modelResult, activeResult]) => {
      setName(String(settingResult.settings.user_name || ''));
      setModels(modelResult.models || []);
      setModel(activeResult.active || '');
    }).catch((reason: Error) => setError(reason.message));
  }, []);

  const saveAndClose = async () => {
    setBusy(true); setError('');
    try {
      const cleanName = name.trim().slice(0, 60) || 'Aurora User';
      await apiRequest('/api/settings', { method: 'POST', body: JSON.stringify({ user_name: cleanName }) });
      if (model) await apiRequest('/api/models/active', { method: 'PUT', body: JSON.stringify({ model }) });
      localStorage.setItem('aurora.setup.complete', 'true');
      onClose(cleanName);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Setup could not be saved.'); }
    finally { setBusy(false); }
  };

  const enrollVoice = async () => {
    setBusy(true); setError('');
    try {
      const sample = await captureVoiceSample();
      await apiRequest('/api/voice-auth/enroll', { method: 'POST', body: sample, headers: { 'Content-Type': 'application/octet-stream' } });
      setVoiceSaved(true);
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Voice enrollment could not be completed.'); }
    finally { setBusy(false); }
  };
  const skipSetup = () => { localStorage.setItem('aurora.setup.complete', 'true'); onClose(name.trim()); };

  const card = isDarkMode ? 'border-slate-700 bg-slate-900 text-slate-100' : 'border-slate-200 bg-white text-slate-900';
  const muted = isDarkMode ? 'text-slate-400' : 'text-slate-500';
  return <div className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4 backdrop-blur-sm" role="dialog" aria-modal="true" aria-labelledby="setup-title">
    <motion.section initial={{ opacity: 0, y: 14, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} className={`w-full max-w-xl rounded-3xl border p-6 shadow-2xl sm:p-8 ${card}`}>
      <div className="mb-6 flex items-start justify-between"><div><div className="mb-2 inline-flex rounded-xl bg-cyan-400/10 p-2 text-cyan-400"><Sparkles size={20} /></div><h2 id="setup-title" className="text-2xl font-semibold">Set up Aurora</h2><p className={`mt-1 text-sm ${muted}`}>A few choices personalize this local assistant.</p></div><button onClick={skipSetup} className={`rounded-lg p-2 ${muted}`} aria-label="Skip setup"><X size={18} /></button></div>
      <div className="mb-6 flex gap-2" aria-label={`Step ${step + 1} of 3`}>{[0,1,2].map((item) => <div key={item} className={`h-1.5 flex-1 rounded-full ${item <= step ? 'bg-cyan-400' : isDarkMode ? 'bg-slate-700' : 'bg-slate-200'}`} />)}</div>
      <AnimatePresence mode="wait"><motion.div key={step} initial={{ opacity: 0, x: 10 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -10 }}>
        {step === 0 && <div><label htmlFor="setup-name" className="mb-2 block text-sm font-medium">What should Aurora call you?</label><input id="setup-name" autoFocus value={name} onChange={(event) => setName(event.target.value)} maxLength={60} placeholder="Your name" className={`w-full rounded-xl border px-4 py-3 outline-none focus:border-cyan-400 ${isDarkMode ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-white'}`} /></div>}
        {step === 1 && <div><label htmlFor="setup-model" className="mb-2 block text-sm font-medium">Choose an installed Ollama model</label><select id="setup-model" value={model} onChange={(event) => setModel(event.target.value)} className={`w-full rounded-xl border px-4 py-3 ${isDarkMode ? 'border-slate-700 bg-slate-800' : 'border-slate-200 bg-white'}`}><option value="">Keep current selection</option>{models.map((item) => <option key={item} value={item}>{item}</option>)}</select><p className={`mt-2 text-sm ${muted}`}>{models.length ? 'You can change the model later.' : 'Ollama is unavailable or has no installed models. You can configure it later.'}</p></div>}
        {step === 2 && <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/5 p-5"><Mic className="mb-3 text-cyan-400" /><h3 className="font-medium">Optional voice profile</h3><p className={`mt-1 text-sm ${muted}`}>Record a short sample for approximate voice matching. It is stored locally and is not authentication.</p><button disabled={busy || voiceSaved} onClick={() => void enrollVoice()} className="mt-4 inline-flex items-center gap-2 rounded-xl border border-slate-600 px-4 py-2 text-sm disabled:opacity-60">{busy ? <Loader2 className="animate-spin" size={16} /> : voiceSaved ? <Check size={16} /> : <Mic size={16} />}{voiceSaved ? 'Voice profile saved' : 'Record sample'}</button></div>}
      </motion.div></AnimatePresence>
      {error && <p role="alert" className="mt-4 text-sm text-rose-400">{error}</p>}
      <div className="mt-8 flex items-center justify-between"><button disabled={step === 0 || busy} onClick={() => setStep((value) => value - 1)} className={`inline-flex items-center gap-2 rounded-xl px-3 py-2 text-sm ${muted} disabled:opacity-40`}><ArrowLeft size={16} />Back</button><div className="flex items-center gap-3">{step === 2 && <button onClick={skipSetup} className={`text-sm ${muted}`}>Skip for now</button>}{step < 2 ? <button onClick={() => setStep((value) => value + 1)} className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950">Continue<ArrowRight size={16} /></button> : <button disabled={busy} onClick={() => void saveAndClose()} className="inline-flex items-center gap-2 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-semibold text-slate-950 disabled:opacity-60">{busy && <Loader2 size={16} className="animate-spin" />}Finish setup<Check size={16} /></button>}</div></div>
    </motion.section>
  </div>;
}
