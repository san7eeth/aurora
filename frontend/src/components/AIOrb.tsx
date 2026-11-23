import { useState, useEffect, useRef } from 'react';

interface AIOrbProps {
  onToggleView: () => void;
  isDarkMode: boolean;
}

export default function AIOrb({ onToggleView, isDarkMode }: AIOrbProps) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);
  const orbRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (orbRef.current) {
        const rect = orbRef.current.getBoundingClientRect();
        const orbCenterX = rect.left + rect.width / 2;
        const orbCenterY = rect.top + rect.height / 2;
        
        const deltaX = e.clientX - orbCenterX;
        const deltaY = e.clientY - orbCenterY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
        
        // Only track mouse if it's within 200px of the orb
        if (distance < 200) {
          const maxOffset = 8; // Maximum pixels the orb can move
          const influence = Math.max(0, 1 - distance / 200);
          
          setMousePosition({
            x: (deltaX / distance) * maxOffset * influence,
            y: (deltaY / distance) * maxOffset * influence
          });
        } else {
          setMousePosition({ x: 0, y: 0 });
        }
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="flex justify-center">
      <div
        ref={orbRef}
        className="relative cursor-pointer transition-transform duration-200 ease-out"
        style={{
          transform: `translate(${mousePosition.x}px, ${mousePosition.y}px)`
        }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        onClick={onToggleView}
      >
        {/* Outer glow ring */}
        <div 
          className={`absolute inset-0 rounded-full transition-all duration-300 ${
            isHovered ? 'scale-125 opacity-30' : 'scale-100 opacity-20'
          }`}
          style={{
            background: isDarkMode 
              ? 'radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, rgba(251, 191, 36, 0) 70%)'
              : 'radial-gradient(circle, rgba(251, 191, 36, 0.3) 0%, rgba(251, 191, 36, 0) 70%)',
            width: '120px',
            height: '120px',
            transform: 'translate(-50%, -50%)',
            left: '50%',
            top: '50%'
          }}
        />
        
        {/* Main orb */}
        <div 
          className={`relative w-16 h-16 rounded-full transition-all duration-300 ${
            isHovered ? 'scale-110' : 'scale-100'
          }`}
          style={{
            background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 50%, #d97706 100%)',
            boxShadow: isHovered 
              ? '0 8px 32px rgba(251, 191, 36, 0.4), inset 0 2px 8px rgba(255, 255, 255, 0.3)'
              : isDarkMode
              ? '0 4px 16px rgba(251, 191, 36, 0.4), inset 0 2px 8px rgba(255, 255, 255, 0.2)'
              : '0 4px 16px rgba(251, 191, 36, 0.3), inset 0 2px 8px rgba(255, 255, 255, 0.2)'
          }}
        >
          {/* Inner highlight */}
          <div 
            className="absolute top-2 left-2 w-3 h-3 rounded-full opacity-60"
            style={{
              background: 'radial-gradient(circle, rgba(255, 255, 255, 0.8) 0%, rgba(255, 255, 255, 0) 70%)'
            }}
          />
          
          {/* Pulsing core */}
          <div 
            className={`absolute inset-0 rounded-full transition-all duration-1000 ${
              isHovered ? 'animate-pulse' : ''
            }`}
            style={{
              background: 'radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, rgba(255, 255, 255, 0) 60%)'
            }}
          />
          
          {/* Center dot */}
          <div 
            className="absolute top-1/2 left-1/2 w-2 h-2 rounded-full transform -translate-x-1/2 -translate-y-1/2"
            style={{
              background: 'rgba(255, 255, 255, 0.9)',
              boxShadow: '0 0 4px rgba(255, 255, 255, 0.5)'
            }}
          />
        </div>
        
        {/* Floating particles */}
        {isHovered && (
          <>
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: '#fbbf24',
                top: '10px',
                right: '15px',
                animationDelay: '0s',
                animationDuration: '2s'
              }}
            />
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: '#f59e0b',
                bottom: '12px',
                left: '18px',
                animationDelay: '0.5s',
                animationDuration: '2s'
              }}
            />
            <div 
              className="absolute w-1 h-1 rounded-full animate-ping"
              style={{
                background: '#d97706',
                top: '20px',
                left: '10px',
                animationDelay: '1s',
                animationDuration: '2s'
              }}
            />
          </>
        )}
      </div>
    </div>
  );
}
