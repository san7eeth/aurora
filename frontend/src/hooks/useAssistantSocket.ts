import { useEffect, useState, useRef } from 'react';

interface AssistantResponse {
  message: string;
  session_id?: string; // Add session_id to the interface
}

interface TranscriptUpdate {
  transcript: string;
}

export const useAssistantWebSocket = () => {
  const [chatSocket, setChatSocket] = useState<WebSocket | null>(null);
  const [audioSocket, setAudioSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<AssistantResponse[]>([]);
  const [transcript, setTranscript] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null); // New state for session_id

  const lastAudioAtRef = useRef<number>(0);
  const browserTTSRef = useRef<boolean>(true);

  useEffect(() => {
    const wsBase = (import.meta as any).env?.VITE_WS_BASE || 'ws://localhost:8000';
    // Chat WebSocket
    const wsChat = new WebSocket(`${wsBase}/ws`);

    wsChat.onopen = () => {
      console.log('Chat WebSocket connected');
      setIsConnected(true);
      setError(null);
    };

    wsChat.onmessage = async (event) => { // Made async to use await for audio processing
      if (typeof event.data === 'string') {
        const data: AssistantResponse = JSON.parse(event.data);
        if (data.message) {
          setMessages(prev => [...prev, { message: data.message }]);
          if (data.session_id) {
            setSessionId(data.session_id);
          }
          // Browser TTS fallback if no binary audio arrives
          const now = Date.now();
          const elapsed = now - lastAudioAtRef.current;
          if (browserTTSRef.current && (typeof window !== 'undefined') && 'speechSynthesis' in window) {
            // If no audio Blob in last 1.5s, speak via browser
            if (elapsed > 1500) {
              try {
                const utter = new SpeechSynthesisUtterance(data.message);
                utter.rate = 1;
                utter.pitch = 1;
                window.speechSynthesis.cancel();
                window.speechSynthesis.speak(utter);
              } catch (e) {
                console.warn('Browser TTS failed:', e);
              }
            }
          }
        } else if ((data as any).transcript) {
          setTranscript((data as any).transcript);
        } else if ((data as any).error) {
          setError((data as any).error);
        }
      } else if (event.data instanceof Blob) {
        // Handle binary audio data
        try {
          lastAudioAtRef.current = Date.now();
          const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
          const arrayBuffer = await event.data.arrayBuffer();
          const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
          const source = audioContext.createBufferSource();
          source.buffer = audioBuffer;
          source.connect(audioContext.destination);
          source.start(0);
        } catch (e) {
          console.error("Error playing audio:", e);
          setError("Error playing audio.");
        }
      }
    };

    wsChat.onclose = () => {
      console.log('Chat WebSocket disconnected');
      setIsConnected(false);
    };

    wsChat.onerror = (err) => {
      console.error('Chat WebSocket error:', err);
      setError('Chat connection error');
    };

    setChatSocket(wsChat);

    return () => {
      wsChat.close();
    };
  }, []);

  useEffect(() => {
    if (sessionId) {
      const wsBase = (import.meta as any).env?.VITE_WS_BASE || 'ws://localhost:8000';
      // Audio WebSocket - only connect once sessionId is available
      const wsAudio = new WebSocket(`${wsBase}/ws/audio?session_id=${sessionId}`);

      wsAudio.onopen = () => {
        console.log('Audio WebSocket connected');
      };

      wsAudio.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.transcript) {
          setTranscript(data.transcript);
        } else if (data.error) {
          setError(data.error);
        }
      };

      wsAudio.onclose = () => {
        console.log('Audio WebSocket disconnected');
      };

      wsAudio.onerror = (err) => {
        console.error('Audio WebSocket error:', err);
        setError('Audio connection error');
      };

      setAudioSocket(wsAudio);

      return () => {
        wsAudio.close();
      };
    }
  }, [sessionId]); // This effect runs when sessionId changes

  const sendMessage = (message: string) => {
    if (chatSocket?.readyState === WebSocket.OPEN) {
      chatSocket.send(JSON.stringify({ message }));
    }
  };

  const sendAudio = (audioChunk: Blob) => {
    if (audioSocket?.readyState === WebSocket.OPEN) {
      audioSocket.send(audioChunk);
    }
  };

  return {
    isConnected,
    messages,
    transcript,
    error,
    sendMessage,
    sendAudio,
  };
};