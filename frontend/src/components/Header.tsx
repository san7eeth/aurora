import React from 'react';
import { Moon, Sun, Sparkles } from 'lucide-react';

interface HeaderProps {
  onToggleView: () => void;
  onToggleDarkMode: () => void;
  isDarkMode: boolean;
}

export default function Header({ onToggleView, onToggleDarkMode, isDarkMode }: HeaderProps) {
  return (
    <div className="flex justify-between items-center mb-8">
      <h1 className={`text-2xl font-bold transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>Aurora</h1>
      
      <div className={`flex items-center gap-2 text-sm transition-colors duration-300 ${
        isDarkMode ? 'text-gray-400' : 'text-gray-500'
      }`}>
        <div className={`w-2 h-2 rounded-full transition-colors duration-300 ${
          isDarkMode ? 'bg-gray-600' : 'bg-gray-300'
        }`}></div>
        <span>Thursday 11, 2024 • 09:23AM</span>
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