import React, { useState } from 'react';
import Header from './components/Header';
import VoiceView from './components/VoiceView';
import DashboardView from './components/DashboardView';

function App() {
  const [currentView, setCurrentView] = useState<'assistant' | 'dashboard'>('dashboard');
  const [isDarkMode, setIsDarkMode] = useState(false);
  
  const toggleView = () => {
    setCurrentView(prev => prev === 'assistant' ? 'dashboard' : 'assistant');
  };

  const toggleDarkMode = () => {
    setIsDarkMode(prev => !prev);
  };

  return (
    <div className={`h-screen relative overflow-hidden transition-colors duration-300 ${
      isDarkMode 
        ? 'bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900' 
        : 'bg-gradient-to-br from-stone-200 via-stone-100 to-amber-50'
    }`}>
      {/* Background decorative element */}
      <div className={`absolute bottom-0 right-0 w-96 h-96 opacity-5 ${
        isDarkMode ? 'opacity-10' : 'opacity-5'
      }`}>
        <div className={`w-full h-full rounded-full border-4 ${
          isDarkMode ? 'border-gray-100' : 'border-gray-900'
        }`}></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
          <div className={`w-4 h-4 rounded-full ${
            isDarkMode ? 'bg-gray-100' : 'bg-gray-900'
          }`}></div>
          <div className={`w-2 h-2 rounded-full mt-2 mx-auto ${
            isDarkMode ? 'bg-gray-100' : 'bg-gray-900'
          }`}></div>
        </div>
      </div>
      
      {/* Added h-full to this div to pass down the screen height */}
      <div className="relative z-10 h-full"> 
        {/* Changed pb-12 to pb-6 for symmetrical padding */}
        <div className="max-w-7xl mx-auto px-6 pt-6 pb-6 h-full"> 
          <div className={`backdrop-blur-md rounded-3xl p-6 shadow-lg h-full flex-1 flex flex-col transition-colors duration-300 ${
            isDarkMode 
              ? 'bg-gray-800/60 shadow-gray-900/20' 
              : 'bg-white/60 shadow-gray-900/10'
          }`}>
            <Header onToggleView={toggleView} onToggleDarkMode={toggleDarkMode} isDarkMode={isDarkMode} />
            
            <div className="flex-1 flex items-center justify-center">
              {currentView === 'dashboard' ? (
                <DashboardView onToggleView={toggleView} isDarkMode={isDarkMode} />
              ) : (
                <VoiceView isDarkMode={isDarkMode} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;