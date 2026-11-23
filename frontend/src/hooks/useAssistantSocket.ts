import { useCallback, useEffect, useRef, useState } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant';
  message: string;
  sources?: { source_file: string; page_number: number | null; chunk_index: number | null }[];
}

type ConnectionMode = 'chat' | 'voice';

const wsBase = () => (import.meta as any).env?.VITE_WS_BASE || 'ws://localhost:8000';

export function useAssistantWebSocket(
  conversationId: string | null,
  mode: ConnectionMode = 'chat',
  onConversationId?: (id: string) => void,
) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const audioSocketRef = useRef<WebSocket | null>(null);
  const pendingMessagesRef = useRef<string[]>([]);
  const onConversationIdRef = useRef(onConversationId);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const playbackSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  useEffect(() => {
    onConversationIdRef.current = onConversationId;
  }, [onConversationId]);

  useEffect(() => {
    setMessages([]);
    setError(null);
    setSessionId(null);
    pendingMessagesRef.current = [];
    if (!conversationId) {
      setIsConnected(false);
      return;
    }

    const query = new URLSearchParams({ conversation_id: conversationId, mode });
    const socket = new WebSocket(`${wsBase()}/ws?${query.toString()}`);
    socketRef.current = socket;

    socket.onopen = () => {
      setIsConnected(true);
      setError(null);
      for (const message of pendingMessagesRef.current.splice(0)) {
        socket.send(JSON.stringify({ message }));
      }
    };
    socket.onmessage = async (event) => {
      if (typeof event.data !== 'string') {
        if (event.data instanceof Blob && mode === 'voice') {
          try {
            playbackSourceRef.current?.stop();
            await playbackContextRef.current?.close();
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            playbackContextRef.current = audioContext;
            const buffer = await audioContext.decodeAudioData(await event.data.arrayBuffer());
            const source = audioContext.createBufferSource();
            playbackSourceRef.current = source;
            source.onended = () => { setIsPlayingAudio(false); playbackSourceRef.current = null; };
            source.buffer = buffer;
            source.connect(audioContext.destination);
            source.start(0);
            setIsPlayingAudio(true);
          } catch {
            setError('Could not play the assistant audio response.');
          }
        }
        return;
      }

      try {
        const data = JSON.parse(event.data);
        if (data.type === 'connected') {
          if (data.session_id) setSessionId(data.session_id);
          if (data.conversation_id) onConversationIdRef.current?.(data.conversation_id);
        } else if (data.type === 'start') {
          setIsStreaming(true);
        } else if (data.type === 'token') {
          const token = String(data.content ?? '');
          setMessages((current) => {
            const last = current[current.length - 1];
            if (last?.role === 'assistant') {
              return [...current.slice(0, -1), { role: 'assistant', message: last.message + token }];
            }
            return [...current, { role: 'assistant', message: token }];
          });
        } else if (data.type === 'done') {
          if (typeof data.message === 'string') {
            setMessages((current) => {
              const last = current[current.length - 1];
              if (last?.role === 'assistant') {
                return [...current.slice(0, -1), { role: 'assistant', message: data.message, sources: data.sources || [] }];
              }
              return [...current, { role: 'assistant', message: data.message, sources: data.sources || [] }];
            });
          }
          if (data.conversation_id) onConversationIdRef.current?.(data.conversation_id);
          setIsStreaming(false);
        } else if (data.type === 'message' && data.message) {
          setMessages((current) => [...current, { role: 'assistant', message: data.message }]);
        } else if (data.type === 'error' || data.error) {
          setError(data.message || data.error || 'The assistant could not respond.');
          setIsStreaming(false);
        } else if (data.message && data.message !== 'connected') {
          setMessages((current) => [...current, { role: 'assistant', message: data.message }]);
        } else if (data.transcript !== undefined) {
          setTranscript(data.transcript);
        }
      } catch {
        setError('Received an unreadable response from Aurora.');
      }
    };
    socket.onclose = () => setIsConnected(false);
    socket.onerror = () => setError('Chat connection failed. Check that Aurora is running.');

    return () => {
      playbackSourceRef.current?.stop();
      void playbackContextRef.current?.close();
      playbackSourceRef.current = null;
      playbackContextRef.current = null;
      setIsPlayingAudio(false);
      socket.close();
      if (socketRef.current === socket) socketRef.current = null;
      audioSocketRef.current?.close();
      audioSocketRef.current = null;
    };
  }, [conversationId, mode]);

  useEffect(() => {
    if (mode !== 'voice' || !sessionId) return;
    const socket = new WebSocket(`${wsBase()}/ws/audio?session_id=${encodeURIComponent(sessionId)}`);
    audioSocketRef.current = socket;
    socket.onmessage = (event) => {
      if (typeof event.data !== 'string') return;
      try {
        const data = JSON.parse(event.data);
        if (data.transcript !== undefined) setTranscript(data.transcript);
        if (data.error) setError(data.error);
      } catch {
        setError('Received an unreadable audio response.');
      }
    };
    socket.onerror = () => setError('Audio connection failed.');
    return () => {
      socket.close();
      if (audioSocketRef.current === socket) audioSocketRef.current = null;
    };
  }, [mode, sessionId]);

  const sendMessage = useCallback((message: string) => {
    const trimmed = message.trim();
    if (!trimmed) return false;
    setMessages((current) => [...current, { role: 'user', message: trimmed }]);
    setError(null);
    const socket = socketRef.current;
    if (socket?.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ message: trimmed }));
    } else {
      pendingMessagesRef.current.push(trimmed);
    }
    return true;
  }, []);

  const sendAudio = useCallback((audioChunk: Blob) => {
    if (audioSocketRef.current?.readyState === WebSocket.OPEN) {
      audioSocketRef.current.send(audioChunk);
    }
  }, []);

  const sendFlush = useCallback(() => {
    if (audioSocketRef.current?.readyState === WebSocket.OPEN) audioSocketRef.current.send(JSON.stringify({ type: 'flush' }));
  }, []);

  const stopSpeech = useCallback(() => {
    playbackSourceRef.current?.stop();
    playbackSourceRef.current = null;
    void playbackContextRef.current?.close();
    playbackContextRef.current = null;
    setIsPlayingAudio(false);
    if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(JSON.stringify({ type: 'interrupt' }));
  }, []);

  return { isConnected, messages, transcript, error, isStreaming, sendMessage, sendAudio, sendFlush, isPlayingAudio, stopSpeech };
}
