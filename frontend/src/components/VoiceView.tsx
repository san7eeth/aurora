import { useEffect, useState } from 'react';
import VoiceMicOrb from './VoiceMicOrb';
import { useAssistantWebSocket } from '../hooks/useAssistantSocket';

interface VoiceViewProps {
  isDarkMode: boolean;
}

export default function VoiceView({ isDarkMode }: VoiceViewProps) {
  const { 
    isConnected, 
    messages, 
    transcript, 
    sendMessage, 
    sendAudio 
  } = useAssistantWebSocket();
  
  const [isSpeaking, setIsSpeaking] = useState(false);

  const lastMessage = messages[messages.length - 1];

  useEffect(() => {
    if (lastMessage) {
      setIsSpeaking(true);
      // A simple way to estimate when the assistant has finished speaking
      const estimatedSpeakTime = lastMessage.message.length * 50; // 50ms per character
      const timer = setTimeout(() => setIsSpeaking(false), estimatedSpeakTime);
      return () => clearTimeout(timer);
    }
  }, [lastMessage]);

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
          isSpeaking={isSpeaking} 
        />
      </div>

      <div className="h-16 mt-8">
        <p className={`text-sm transition-colors duration-300 ${
          isDarkMode ? 'text-gray-400' : 'text-gray-500'
        }`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </p>
      </div>
    </div>
  );
}
