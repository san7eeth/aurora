import { useCallback, useEffect, useState } from 'react';
import { BookOpen, Bot, Brain, Clock3, Cpu, LayoutDashboard, MessageSquare, Plus } from 'lucide-react';
import Header from './components/Header';
import VoiceView from './components/VoiceView';
import DashboardView from './components/DashboardView';
import ChatView from './components/ChatView';
import ConversationHistoryView from './components/ConversationHistoryView';
import ModelManagementView from './components/ModelManagementView';
import KnowledgeBaseView from './components/KnowledgeBaseView';
import MemoryManagementView from './components/MemoryManagementView';
import { apiRequest } from './lib/api';

type Page = 'chat' | 'history' | 'models' | 'knowledge' | 'memory' | 'voice' | 'dashboard';

const navItems: { id: Page; label: string; icon: typeof MessageSquare }[] = [
  { id: 'chat', label: 'Chat', icon: MessageSquare },
  { id: 'history', label: 'History', icon: Clock3 },
  { id: 'models', label: 'Models', icon: Cpu },
  { id: 'knowledge', label: 'Knowledge', icon: BookOpen },
  { id: 'memory', label: 'Memory', icon: Brain },
  { id: 'voice', label: 'Voice', icon: Bot },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
];

function App() {
  const [page, setPage] = useState<Page>('chat');
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [activeModel, setActiveModel] = useState('');

  useEffect(() => {
    apiRequest<{ active: string }>('/api/models/active')
      .then((result) => setActiveModel(result.active))
      .catch(() => setActiveModel(''));
  }, []);

  const handleConversationChange = useCallback((id: string | null) => {
    setConversationId(id);
  }, []);

  const startNewChat = () => {
    setConversationId(null);
    setPage('chat');
  };

  const textMuted = isDarkMode ? 'text-slate-400' : 'text-slate-500';

  return (
    <div className={`h-screen overflow-hidden transition-colors duration-300 ${isDarkMode ? 'bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950' : 'bg-gradient-to-br from-slate-100 via-white to-cyan-50'}`}>
      <div className="mx-auto flex h-full max-w-screen-2xl flex-col gap-3 p-3 md:flex-row md:gap-4 md:p-5">
        <aside className={`flex shrink-0 flex-row items-center gap-2 rounded-2xl border p-2 md:w-56 md:flex-col md:items-stretch md:p-4 ${isDarkMode ? 'border-slate-800 bg-slate-900/80' : 'border-slate-200 bg-white/80'}`}>
          <button onClick={startNewChat} className={`hidden items-center gap-2 px-2 pb-4 pt-1 text-left text-lg font-semibold md:flex ${isDarkMode ? 'text-white' : 'text-slate-900'}`}>
            <span className="rounded-xl bg-cyan-400/15 p-2 text-cyan-300"><Bot size={20} /></span>Aurora
          </button>
          <button onClick={startNewChat} className="flex shrink-0 items-center gap-2 rounded-xl bg-cyan-500 px-3 py-2.5 text-sm font-medium text-slate-950 hover:bg-cyan-400">
            <Plus size={17} /><span className="hidden sm:inline">New chat</span>
          </button>
          <nav aria-label="Main navigation" className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto md:flex-col md:items-stretch md:gap-1">
            {navItems.map(({ id, label, icon: Icon }) => (
              <button key={id} onClick={() => setPage(id)} aria-current={page === id ? 'page' : undefined} className={`flex shrink-0 items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${page === id
                ? isDarkMode ? 'bg-slate-700 text-white' : 'bg-slate-100 text-slate-900'
                : `${textMuted} ${isDarkMode ? 'hover:bg-slate-800 hover:text-slate-100' : 'hover:bg-slate-100 hover:text-slate-900'}`}`}>
                <Icon size={17} /><span>{label}</span>
              </button>
            ))}
          </nav>
          <div className={`hidden border-t pt-3 text-xs md:block ${isDarkMode ? 'border-slate-800 text-slate-500' : 'border-slate-200 text-slate-500'}`}>Private, local AI</div>
        </aside>

        <main className={`flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden rounded-2xl border shadow-xl ${isDarkMode ? 'border-slate-800 bg-slate-900/70 shadow-black/20' : 'border-white/70 bg-white/70 shadow-slate-300/30'}`}>
          <div className={`shrink-0 border-b px-4 pt-4 md:px-7 ${isDarkMode ? 'border-slate-800' : 'border-slate-200'}`}>
            <Header onToggleView={() => setPage('chat')} onToggleDarkMode={() => setIsDarkMode((value) => !value)} isDarkMode={isDarkMode} activeModel={activeModel} />
          </div>
          <div className="min-h-0 flex-1">
            {page === 'chat' && <ChatView isDarkMode={isDarkMode} conversationId={conversationId} onConversationChange={handleConversationChange} />}
            {page === 'history' && <ConversationHistoryView isDarkMode={isDarkMode} onNew={startNewChat} onSelect={(id) => { setConversationId(id); setPage('chat'); }} />}
            {page === 'models' && <ModelManagementView isDarkMode={isDarkMode} onActiveModelChange={setActiveModel} />}
            {page === 'knowledge' && <KnowledgeBaseView isDarkMode={isDarkMode} />}
            {page === 'memory' && <MemoryManagementView isDarkMode={isDarkMode} />}
            {page === 'voice' && <VoiceView isDarkMode={isDarkMode} />}
            {page === 'dashboard' && <div className="h-full overflow-y-auto p-4"><DashboardView onToggleView={() => setPage('chat')} isDarkMode={isDarkMode} /></div>}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
