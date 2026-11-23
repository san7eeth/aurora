import { useEffect, useState } from 'react';
import VoiceMicOrb from './VoiceMicOrb';
import { useAssistantWebSocket } from '../hooks/useAssistantSocket';
import { apiRequest } from '../lib/api';

interface VoiceViewProps {
  isDarkMode: boolean;
}

export default function VoiceView({ isDarkMode }: VoiceViewProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [microphones, setMicrophones] = useState<MediaDeviceInfo[]>([]);
  const [microphoneId, setMicrophoneId] = useState('');
  const [speechRate, setSpeechRate] = useState(200);
  useEffect(() => {
    let active = true;
    apiRequest<{ id: string }>('/api/conversations', { method: 'POST', body: JSON.stringify({}) })
      .then((conversation) => { if (active) setConversationId(conversation.id); })
      .catch((reason: Error) => { if (active) setConnectionError(reason.message); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    let active = true;
    apiRequest<{ settings: Record<string, unknown> }>('/api/settings')
      .then(({ settings }) => {
        if (!active) return;
        const rate = Number(settings.speech_rate ?? 200);
        if (Number.isFinite(rate)) setSpeechRate(Math.max(100, Math.min(300, rate)));
      })
      .catch(() => undefined);
    navigator.mediaDevices?.enumerateDevices().then((devices) => {
      if (active) setMicrophones(devices.filter(device => device.kind === 'audioinput'));
    }).catch(() => undefined);
    return () => { active = false; };
  }, []);

  const { 
    isConnected, 
    messages, 
    transcript, 
    error,
    sendAudio,
    sendFlush,
    isPlayingAudio,
    stopSpeech,
  } = useAssistantWebSocket(conversationId, 'voice');
  
  const lastMessage = messages[messages.length - 1];
  const saveSpeechRate = async (value: number) => {
    setSpeechRate(value);
    try {
      await apiRequest('/api/settings', { method: 'POST', body: JSON.stringify({ speech_rate: value }) });
    } catch (reason) {
      setConnectionError(reason instanceof Error ? reason.message : 'Could not save speech rate.');
    }
  };

  return (
    <div className="text-center w-full h-full flex flex-col justify-center">
      <div className="mb-8 h-24 flex flex-col justify-center items-center">
        <p className={`text-2xl font-medium max-w-2xl mx-auto transition-colors duration-300 ${
          isDarkMode ? 'text-gray-100' : 'text-gray-800'
        }`}>
          {transcript || (lastMessage && lastMessage.message) || ''}
        </p>
      </div>

      <div className="flex-1 flex items-center justify-center">
        <VoiceMicOrb 
          isDarkMode={isDarkMode} 
          sendAudio={sendAudio} 
          isSpeaking={isPlayingAudio}
          microphoneId={microphoneId}
          sendFlush={sendFlush}
          onError={setConnectionError}
          onDevicesFound={setMicrophones}
          onStartRecording={stopSpeech}
        />
      </div>

      <section className={`mx-auto mt-6 w-full max-w-md rounded-xl border p-4 text-left ${isDarkMode ? 'border-gray-700 bg-gray-900/60' : 'border-gray-200 bg-white/70'}`}>
        <h2 className="mb-3 text-sm font-semibold">Voice settings</h2>
        <label className="mb-4 block text-sm">
          <span className="mb-1 block">Microphone</span>
          <select className="w-full rounded-md border bg-transparent p-2" value={microphoneId} onChange={(event) => setMicrophoneId(event.target.value)}>
            <option value="">System default</option>
            {microphones.map((device, index) => <option key={device.deviceId || index} value={device.deviceId}>{device.label || `Microphone ${index + 1}`}</option>)}
          </select>
        </label>
        <label className="block text-sm">
          <span className="mb-1 flex justify-between"><span>Speech rate</span><span>{speechRate} words/min</span></span>
          <input className="w-full" type="range" min="100" max="300" step="10" value={speechRate} onChange={(event) => void saveSpeechRate(Number(event.target.value))} />
        </label>
        {isPlayingAudio && <button className="mt-4 rounded-md bg-rose-600 px-3 py-2 text-sm text-white" onClick={stopSpeech}>Stop speech</button>}
      </section>

      <div className="h-16 mt-8">
        <p className={`text-sm transition-colors duration-300 ${
          isDarkMode ? 'text-gray-400' : 'text-gray-500'
        }`}>
          {error || connectionError || (isConnected ? 'Connected' : conversationId ? 'Connecting…' : 'Starting voice session…')}
        </p>
      </div>
    </div>
  );
}
