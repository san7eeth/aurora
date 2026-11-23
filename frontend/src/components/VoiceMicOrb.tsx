import { useState, useEffect, useRef } from 'react';

interface VoiceMicOrbProps {
  isDarkMode: boolean;
  sendAudio: (data: Blob) => void;
  isSpeaking: boolean;
  microphoneId: string;
  sendFlush: () => void;
  onError: (message: string) => void;
  onDevicesFound: (devices: MediaDeviceInfo[]) => void;
  onStartRecording: () => void;
}

export default function VoiceMicOrb({ isDarkMode, sendAudio, isSpeaking, microphoneId, sendFlush, onError, onDevicesFound, onStartRecording }: VoiceMicOrbProps) {
  const [isListening, setIsListening] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [waveformData, setWaveformData] = useState<number[]>(Array(12).fill(0));
  const waveformDataRef = useRef(waveformData);
  waveformDataRef.current = waveformData;
  const [isHovered, setIsHovered] = useState(false);
  const orbRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const workletRef = useRef<AudioWorkletNode | null>(null);
  const pcmPendingRef = useRef<number[]>([]);
  const resampleInputRef = useRef<number[]>([]);
  const resamplePositionRef = useRef(0);

  // Animation effect
  useEffect(() => {
    let lastWaveform = Array(12).fill(0);

    const animate = () => {
      if (isListening || isSpeaking) {
        if (isSpeaking) {
          const newLevel = audioLevel + (Math.random() * 0.4 - 0.2) * 0.05;
          setAudioLevel(Math.max(0.1, Math.min(0.9, newLevel)));
          const newWaveform = lastWaveform.map((val) => {
            const target = Math.random() * 0.6 + 0.2;
            return val + (target - val) * 0.05;
          });
          setWaveformData(newWaveform);
          lastWaveform = newWaveform;
        } else if (isListening && analyserRef.current) {
            const dataArray = new Uint8Array(analyserRef.current.frequencyBinCount);
            analyserRef.current.getByteFrequencyData(dataArray);
            const level = dataArray.reduce((acc, val) => acc + val, 0) / dataArray.length / 255;
            setAudioLevel(level);

            const newWaveform = lastWaveform.map((val, i) => {
                const target = (dataArray[i * 8] / 255) * 0.8 + 0.2;
                return val + (target - val) * 0.2;
            });
            setWaveformData(newWaveform);
            lastWaveform = newWaveform;
        } else {
          const time = Date.now() * 0.001;
          const gentleLevel = 0.3 + Math.sin(time) * 0.15;
          setAudioLevel(gentleLevel);
          const gentleWaveform = lastWaveform.map((val, i) => {
            const target = 0.4 + Math.sin(time + i * 0.3) * 0.15;
            return val + (target - val) * 0.05;
          });
          setWaveformData(gentleWaveform);
          lastWaveform = gentleWaveform;
        }
        animationRef.current = requestAnimationFrame(animate);
      } else {
        const fadeOut = lastWaveform.map(val => val * 0.95);
        setWaveformData(fadeOut);
        lastWaveform = fadeOut;
        if (fadeOut.every(val => val < 0.01)) {
          setAudioLevel(0);
          setWaveformData(Array(12).fill(0));
          if (animationRef.current) {
            cancelAnimationFrame(animationRef.current);
          }
        } else {
          animationRef.current = requestAnimationFrame(animate);
        }
      }
    };

    if (isListening || isSpeaking || waveformDataRef.current.some(val => val > 0)) {
      animationRef.current = requestAnimationFrame(animate);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isListening, isSpeaking, audioLevel]);

  const startRecording = async () => {
    try {
      onStartRecording();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: {
        ...(microphoneId ? { deviceId: { exact: microphoneId } } : {}),
        echoCancellation: true, noiseSuppression: true, autoGainControl: true,
      } });
      mediaStreamRef.current = stream;
      const AudioContextConstructor = window.AudioContext ?? window.webkitAudioContext;
      if (!AudioContextConstructor) throw new Error('Web Audio is not supported by this browser.');
      audioContextRef.current = new AudioContextConstructor();
      const audioContext = audioContextRef.current;

      onDevicesFound((await navigator.mediaDevices.enumerateDevices()).filter(device => device.kind === 'audioinput'));
      analyserRef.current = audioContext.createAnalyser();
      analyserRef.current.fftSize = 256;

      // Create a MediaStreamSource from the microphone input
      sourceRef.current = audioContext.createMediaStreamSource(stream);
      sourceRef.current.connect(analyserRef.current);
      await audioContext.audioWorklet.addModule('/pcm-processor.js');
      workletRef.current = new AudioWorkletNode(audioContext, 'aurora-pcm-capture');
      workletRef.current.port.onmessage = (event: MessageEvent<Float32Array>) => {
        const input = event.data as Float32Array;
        const ratio = audioContext.sampleRate / 16000;
        let position = resamplePositionRef.current;
        const combined = resampleInputRef.current.concat(Array.from(input));
        while (position + 1 < combined.length) {
          const lower = Math.floor(position);
          const sample = combined[lower] + (combined[lower + 1] - combined[lower]) * (position - lower);
          pcmPendingRef.current.push(Math.max(-1, Math.min(1, sample)));
          position += ratio;
        }
        const consumed = Math.floor(position);
        const remainder = combined.slice(consumed);
        resampleInputRef.current = remainder;
        resamplePositionRef.current = position - consumed;
        while (pcmPendingRef.current.length >= 480) {
          const samples = pcmPendingRef.current.splice(0, 480);
          const pcm = new Int16Array(480);
          samples.forEach((value, index) => { pcm[index] = value < 0 ? value * 32768 : value * 32767; });
          sendAudio(new Blob([pcm.buffer], { type: 'application/x-pcm' }));
        }
      };
      sourceRef.current.connect(workletRef.current);
      workletRef.current.connect(audioContext.destination);

      setIsListening(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      onError(error instanceof Error ? error.message : 'Could not access the microphone. Check browser permissions.');
      stopRecording(false);
    }
  };

  const stopRecording = (flush = true) => {
    if (flush && isListening) {
      if (pcmPendingRef.current.length) {
        const samples = [...pcmPendingRef.current, ...Array(480 - pcmPendingRef.current.length).fill(0)];
        const pcm = new Int16Array(480);
        samples.forEach((value, index) => { pcm[index] = value < 0 ? value * 32768 : value * 32767; });
        sendAudio(new Blob([pcm.buffer], { type: 'application/x-pcm' }));
      }
      sendFlush();
    }
    workletRef.current?.disconnect();
    workletRef.current = null;
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach(track => track.stop());
    }
    if(sourceRef.current) {
        sourceRef.current.disconnect();
    }
    if(analyserRef.current) {
        analyserRef.current.disconnect();
    }
    if(audioContextRef.current) {
        audioContextRef.current.close();
    }
    setIsListening(false);
    pcmPendingRef.current = [];
    resampleInputRef.current = [];
    resamplePositionRef.current = 0;
  };

  useEffect(() => () => {
    workletRef.current?.disconnect();
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    void audioContextRef.current?.close();
  }, []);

  const handleClick = () => {
    if (!isListening) {
      startRecording();
    } else {
      stopRecording();
    }
  };

  const getOrbGradient = () => {
    if (isSpeaking) return 'linear-gradient(135deg, #a855f7 0%, #ec4899 50%, #f97316 100%)';
    if (isListening) return 'linear-gradient(135deg, #3b82f6 0%, #06b6d4 50%, #10b981 100%)';
    return 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)';
  };

  const getGlowColor = () => {
    if (isSpeaking) return 'rgba(168, 85, 247, 0.4)';
    if (isListening) return 'rgba(59, 130, 246, 0.4)';
    return 'rgba(251, 191, 36, 0.3)';
  };

  return (
    <div className="flex flex-col items-center mt-12">
      <div
        ref={orbRef}
        className="relative cursor-pointer transition-transform duration-300 ease-out"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={handleClick}
      >
        {/* Waveform visualization particles */}
        {(isListening || isSpeaking) && waveformData.map((level, i) => (
          <div
            key={i}
            className="absolute w-1.5 h-1.5 rounded-full"
            style={{
              background: isSpeaking 
                ? 'linear-gradient(45deg, #a855f7, #ec4899)' 
                : isListening
                ? 'linear-gradient(45deg, #3b82f6, #06b6d4)'
                : 'linear-gradient(45deg, #fbbf24, #f59e0b)',
              left: '50%',
              top: '50%',
              transform: `translate(-50%, -50%) rotate(${i * 30}deg) translateY(-${60 + level * 30}px)`,
              opacity: level,
              transition: 'all 0.1s ease-out', // Smooth transitions
            }}
          />
        ))}

        {/* Outer glow ring */}
        <div 
          className="absolute inset-0 rounded-full transition-all duration-300"
          style={{
            background: `radial-gradient(circle, ${getGlowColor()} 0%, transparent 70%)`,
            width: `${120 + audioLevel * 40}px`,
            height: `${120 + audioLevel * 40}px`,
            transform: 'translate(-50%, -50%)',
            left: '50%',
            top: '50%',
            opacity: isHovered || isListening || isSpeaking ? 0.3 : 0.2,
            scale: isHovered || isListening || isSpeaking ? 1.25 : 1,
          }}
        />
        
        {/* Main orb with fluid morphing */}
        <div 
          className="relative transition-all duration-300 flex items-center justify-center"
          style={{
            width: `${64 + audioLevel * 20}px`,
            height: `${64 + audioLevel * 20}px`,
            background: getOrbGradient(),
            boxShadow: isSpeaking 
              ? '0 12px 40px rgba(168, 85, 247, 0.5), inset 0 2px 12px rgba(255, 255, 255, 0.3)'
              : isListening
              ? '0 8px 32px rgba(59, 130, 246, 0.4), inset 0 2px 8px rgba(255, 255, 255, 0.3)'
              : isHovered
              ? '0 8px 32px rgba(251, 191, 36, 0.4), inset 0 2px 8px rgba(255, 255, 255, 0.3)'
              : '0 4px 16px rgba(251, 191, 36, 0.3), inset 0 2px 8px rgba(255, 255, 255, 0.2)',
            borderRadius: isSpeaking 
              ? `${50 - audioLevel * 10}% ${50 + audioLevel * 10}% ${50 + audioLevel * 5}% ${50 - audioLevel * 5}%`
              : '50%',
            transform: `scale(${isHovered || isListening || isSpeaking ? 1.1 : 1})`,
          }}
        >
          {/* Inner highlight */}
          <div 
            className="absolute rounded-full opacity-60"
            style={{
              width: `${12 + audioLevel * 4}px`,
              height: `${12 + audioLevel * 4}px`,
              top: '12px',
              left: '12px',
              background: 'radial-gradient(circle, rgba(255, 255, 255, 0.9) 0%, rgba(255, 255, 255, 0) 70%)',
              transition: 'all 0.1s ease-out',
            }}
          />
          
          {/* Pulsing core */}
          <div 
            className="absolute inset-0 rounded-full transition-all duration-1000"
            style={{
              background: 'radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0) 60%)',
              animation: isHovered || isListening || isSpeaking ? 'pulse 2s infinite' : 'none',
            }}
          />
          
          {/* Center dot */}
          <div 
            className="absolute top-1/2 left-1/2 rounded-full transform -translate-x-1/2 -translate-y-1/2"
            style={{
              width: `${8 + audioLevel * 2}px`,
              height: `${8 + audioLevel * 2}px`,
              background: 'rgba(255, 255, 255, 0.9)',
              boxShadow: '0 0 4px rgba(255, 255, 255, 0.5)',
              transition: 'all 0.1s ease-out',
            }}
          />
        </div>

        {/* Floating particles on hover */}
        {(isHovered || isListening || isSpeaking) && (
          <>
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: isSpeaking ? '#a855f7' : isListening ? '#3b82f6' : '#fbbf24',
                top: '10px',
                right: '15px',
                animationDelay: '0s',
                animationDuration: '2.5s',
              }}
            />
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: isSpeaking ? '#ec4899' : isListening ? '#06b6d4' : '#f59e0b',
                bottom: '12px',
                left: '18px',
                animationDelay: '0.5s',
                animationDuration: '2.5s',
              }}
            />
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: isSpeaking ? '#f97316' : isListening ? '#10b981' : '#d97706',
                top: '20px',
                left: '10px',
                animationDelay: '1s',
                animationDuration: '2.5s',
              }}
            />
          </>
        )}

        {/* State indicator text */}
        <div className="absolute -bottom-16 left-1/2 transform -translate-x-1/2 text-center">
          <div className={`text-xs font-medium transition-colors duration-300 ${
            isDarkMode ? 'text-gray-300' : 'text-gray-600'
          }`}>
            {isSpeaking ? 'Aurora is speaking...' : isListening ? 'Listening...' : ''}
          </div>
          
          {/* Voice level bars */}
          {(isListening || isSpeaking) && (
            <div className="flex justify-center gap-1 mt-3">
              {[...Array(8)].map((_, i) => (
                <div
                  key={i}
                  className="w-0.5 bg-current rounded-full transition-all duration-100"
                  style={{
                    height: `${4 + (waveformData[i] || 0) * 8}px`,
                    opacity: (waveformData[i] || 0) > 0.3 ? 1 : 0.4,
                    color: isSpeaking ? '#a855f7' : isListening ? '#3b82f6' : '#fbbf24',
                    filter: isDarkMode ? 'brightness(1.2)' : 'brightness(1)',
                    transition: 'height 0.1s ease-out, opacity 0.1s ease-out',
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
