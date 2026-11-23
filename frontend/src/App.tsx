import { useCallback, useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { BookOpen, Bot, Brain, Clock3, Cpu, LayoutDashboard, ListTodo, MessageSquare, Plus, X } from 'lucide-react';
import Header from './components/Header';
import VoiceView from './components/VoiceView';
import DashboardView from './components/DashboardView';
import ChatView from './components/ChatView';
import ConversationHistoryView from './components/ConversationHistoryView';
import ModelManagementView from './components/ModelManagementView';
import KnowledgeBaseView from './components/KnowledgeBaseView';
import MemoryManagementView from './components/MemoryManagementView';
import AgentManagementView from './components/AgentManagementView';
import FirstRunWizard from './components/FirstRunWizard';
import ErrorBoundary from './components/ErrorBoundary';
import { apiRequest } from './lib/api';

type Page = 'chat' | 'history' | 'models' | 'knowledge' | 'memory' | 'voice' | 'agent' | 'dashboard';
const navItems: { id: Page; label: string; icon: typeof MessageSquare }[] = [
  { id: 'chat', label: 'Chat', icon: MessageSquare }, { id: 'history', label: 'History', icon: Clock3 },
  { id: 'models', label: 'Models', icon: Cpu }, { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'memory', label: 'Memory', icon: Brain }, { id: 'voice', label: 'Voice', icon: Bot },
  { id: 'agent', label: 'Agent', icon: ListTodo }, { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

function App() {
  const [page, setPage] = useState<Page>('chat');
  const [isDarkMode, setIsDarkMode] = useState(() => localStorage.getItem('aurora.theme') !== 'light');
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState('');
  const [userName, setUserName] = useState('');
  const [showSetup, setShowSetup] = useState(() => localStorage.getItem('aurora.setup.complete') !== 'true');
  const [showShortcuts, setShowShortcuts] = useState(false);

  useEffect(() => {
    apiRequest<{ active: string }>('/api/models/active').then((result) => setActiveModel(result.active)).catch(() => setActiveModel(''));
    apiRequest<{ settings: Record<string, unknown> }>('/api/settings').then(({ settings }) => setUserName(String(settings.user_name || ''))).catch(() => undefined);
  }, []);

  useEffect(() => {
    document.documentElement.style.colorScheme = isDarkMode ? 'dark' : 'light';
    localStorage.setItem('aurora.theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  const startNewChat = useCallback(() => { setConversationId(null); setPage('chat'); }, []);
  const handleConversationChange = useCallback((id: string | null) => setConversationId(id), []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      if (target?.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target?.tagName || '')) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'n') { event.preventDefault(); startNewChat(); return; }
      if (event.key === '?' && !event.ctrlKey && !event.metaKey) { event.preventDefault(); setShowShortcuts((value) => !value); return; }
      if (event.altKey && /^[1-8]$/.test(event.key)) { event.preventDefault(); setPage(navItems[Number(event.key) - 1].id); }
      if (event.key === 'Escape') { setShowShortcuts(false); setShowSetup(false); }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [startNewChat]);

  const muted = isDarkMode ? 'text-slate-400' : 'text-slate-500';
  const pageView = () => {
    if (page === 'chat') return <ChatView isDarkMode={isDarkMode} conversationId={conversationId} onConversationChange={handleConversationChange} />;
    if (page === 'history') return <ConversationHistoryView isDarkMode={isDarkMode} onNew={startNewChat} onSelect={(id) => { setConversationId(id); setPage('chat'); }} />;
    if (page === 'models') return <ModelManagementView isDarkMode={isDarkMode} onActiveModelChange={setActiveModel} />;
    if (page === 'knowledge') return <KnowledgeBaseView isDarkMode={isDarkMode} />;
    if (page === 'memory') return <MemoryManagementView isDarkMode={isDarkMode} />;
    if (page === 'voice') return <VoiceView isDarkMode={isDarkMode} />;
    if (page === 'agent') return <AgentManagementView isDarkMode={isDarkMode} />;
    return <div className="h-full overflow-y-auto"><DashboardView onToggleView={startNewChat} onOpenSetup={() => setShowSetup(true)} onOpenKnowledge={() => setPage('knowledge')} isDarkMode={isDarkMode} userName={userName} /></div>;
  };

  return <div className={`h-screen overflow-hidden transition-colors duration-300 ${isDarkMode ? 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black' : 'bg-gradient-to-br from-slate-100 via-white to-cyan-50'}`}>
    <div className="mx-auto flex h-full max-w-screen-2xl flex-col gap-3 p-3 md:flex-row md:gap-4 md:p-5">
      <aside className={`flex shrink-0 flex-row items-center gap-2 rounded-2xl border p-2 md:w-56 md:flex-col md:items-stretch md:p-4 ${isDarkMode ? 'border-slate-800 bg-slate-900/90' : 'border-slate-200 bg-white/90'}`}>
        <button onClick={startNewChat} className={`hidden items-center gap-2 px-2 pb-4 pt-1 text-left text-lg font-semibold md:flex ${isDarkMode ? 'text-white' : 'text-slate-900'}`}><span className="rounded-xl bg-cyan-400/15 p-2 text-cyan-300"><Bot size={20} /></span>Aurora</button>
        <button onClick={startNewChat} title="New chat (Ctrl+N)" className="flex shrink-0 items-center gap-2 rounded-xl bg-cyan-400 px-3 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300"><Plus size={17} /><span className="hidden sm:inline">New chat</span></button>
        <nav aria-label="Main navigation" className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto md:flex-col md:items-stretch md:gap-1">
          {navItems.map(({ id, label, icon: Icon }, index) => <button key={id} onClick={() => setPage(id)} aria-current={page === id ? 'page' : undefined} title={`${label} (Alt+${index + 1})`} className={`flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${page === id ? (isDarkMode ? 'bg-slate-700/90 text-white shadow-inner shadow-white/5' : 'bg-slate-100 text-slate-900') : (isDarkMode ? 'text-slate-400 hover:bg-slate-800 hover:text-slate-100' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-900')}`}><Icon size={17} /><span>{label}</span><kbd className="ml-auto hidden text-[10px] opacity-40 md:block">Alt+{index + 1}</kbd></button>)}
        </nav>
        <button onClick={() => setShowShortcuts(true)} className={`hidden border-t pt-3 text-left text-xs md:block ${isDarkMode ? 'border-slate-800 text-slate-500 hover:text-slate-300' : 'border-slate-200 text-slate-500'}`} aria-label="Keyboard shortcuts">? Keyboard shortcuts</button>
      </aside>
      <main className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border shadow-xl ${isDarkMode ? 'border-slate-800 bg-slate-950/70 shadow-black/30' : 'border-white/70 bg-white/80 shadow-slate-300/30'}`}>
        <div className={`shrink-0 border-b px-4 pt-4 md:px-7 ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}><Header onToggleView={startNewChat} onToggleDarkMode={() => setIsDarkMode((value) => !value)} onOpenSetup={() => setShowSetup(true)} isDarkMode={isDarkMode} activeModel={activeModel} /></div>
        <div className="min-h-0 flex-1"><AnimatePresence mode="wait" initial={false}><motion.div key={page} className="h-full" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: .16, ease: 'easeOut' }}>{pageView()}</motion.div></AnimatePresence></div>
      </main>
    </div>
    {showSetup && <FirstRunWizard isDarkMode={isDarkMode} onClose={(name) => { setUserName(name); setShowSetup(false); apiRequest<{ active: string }>('/api/models/active').then((result) => setActiveModel(result.active)).catch(() => undefined); }} />}
    {showShortcuts && <div className="fixed inset-0 z-40 grid place-items-center bg-black/60 p-4" onMouseDown={(event) => { if (event.target === event.currentTarget) setShowShortcuts(false); }}><section role="dialog" aria-modal="true" aria-labelledby="shortcuts-title" className={`w-full max-w-sm rounded-2xl border p-5 shadow-2xl ${isDarkMode ? 'border-slate-700 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-900'}`}><div className="mb-4 flex items-center justify-between"><h2 id="shortcuts-title" className="font-semibold">Keyboard shortcuts</h2><button onClick={() => setShowShortcuts(false)} aria-label="Close shortcuts"><X size={18} /></button></div><div className={`space-y-3 text-sm ${muted}`}><p className="flex justify-between"><span>New chat</span><kbd>Ctrl / ⌘ + N</kbd></p><p className="flex justify-between"><span>Open screen</span><kbd>Alt + 1–8</kbd></p><p className="flex justify-between"><span>Show this guide</span><kbd>?</kbd></p><p className="flex justify-between"><span>Close dialog</span><kbd>Esc</kbd></p></div></section></div>}
  </div>;
}

export default function AppWithErrorBoundary() { return <ErrorBoundary><App /></ErrorBoundary>; }
