import { useEffect, useState } from 'react';
import { Cpu, Moon, Sun, Sparkles } from 'lucide-react';

type ServiceStatus = 'checking' | 'online' | 'degraded' | 'offline';

interface HeaderProps {
  onToggleView: () => void;
  onToggleDarkMode: () => void;
  isDarkMode: boolean;
  activeModel: string;
}

export default function Header({ onToggleView, onToggleDarkMode, isDarkMode, activeModel }: HeaderProps) {
  const [now, setNow] = useState(() => new Date());
  const [serviceStatus, setServiceStatus] = useState<ServiceStatus>('checking');

  useEffect(() => {
    const clock = window.setInterval(() => setNow(new Date()), 30_000);
    let active = true;
    const checkHealth = async () => {
      try {
        const response = await fetch('/health', { signal: AbortSignal.timeout(3000) });
        if (!response.ok) throw new Error(`Health check failed: ${response.status}`);
        const health = await response.json();
        if (active) setServiceStatus(health.status === 'ok' ? 'online' : 'degraded');
      } catch {
        if (active) setServiceStatus('offline');
      }
    };
    void checkHealth();
    const healthTimer = window.setInterval(checkHealth, 5000);
    return () => {
      active = false;
      window.clearInterval(clock);
      window.clearInterval(healthTimer);
    };
  }, []);

  const statusColor = serviceStatus === 'online'
    ? 'bg-emerald-500'
    : serviceStatus === 'degraded'
      ? 'bg-amber-500'
      : serviceStatus === 'offline'
        ? 'bg-red-500'
        : 'bg-gray-400 animate-pulse';
  const statusLabel = serviceStatus === 'online'
    ? 'Backend and Ollama online'
    : serviceStatus === 'degraded'
      ? 'Backend online; a service is degraded'
      : serviceStatus === 'offline'
        ? 'Backend offline'
        : 'Checking backend';

  return (
    <div className="flex justify-between items-center mb-8">
      <button onClick={onToggleView} className={`text-2xl font-bold transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>Aurora</button>
      
      <div className={`flex items-center gap-2 text-sm transition-colors duration-300 ${
        isDarkMode ? 'text-gray-400' : 'text-gray-500'
      }`}>
        <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${statusColor}`} aria-label={statusLabel} title={statusLabel}></div>
        <span>{now.toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' })} • {now.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}</span>
        <span className="mx-1 opacity-40">·</span>
        <Cpu size={14} aria-hidden="true" />
        <span className="max-w-32 truncate" title={activeModel || 'No active model'}>{activeModel || 'No active model'}</span>
      </div>
      
      <div className="flex items-center gap-3">
        <button 
          className={`p-2 transition-colors duration-300 ${
            isDarkMode 
              ? 'text-gray-400 hover:text-white' 
              : 'text-gray-600 hover:text-gray-900'
          }`}
          onClick={onToggleDarkMode}
        >
          {isDarkMode ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button className={`p-2 transition-colors duration-300 ${
          isDarkMode 
            ? 'text-gray-400 hover:text-white' 
            : 'text-gray-600 hover:text-gray-900'
        }`}>
          <Sparkles size={20} />
        </button>
      </div>
    </div>
  );
}
