import { Calendar, TrendingUp, Plane, ChevronRight } from 'lucide-react';
import AIOrb from './AIOrb';

interface DashboardViewProps {
  onToggleView: () => void;
  isDarkMode: boolean;
}

export default function DashboardView({ onToggleView, isDarkMode }: DashboardViewProps) {
  return (
    <div className="text-center w-full">
      <h2 className={`text-4xl font-bold mb-2 leading-tight transition-colors duration-300 ${
        isDarkMode ? 'text-white' : 'text-gray-900'
      }`}>
        Good Morning, Ayoub!
      </h2>
      <p className={`text-xl mb-8 transition-colors duration-300 ${
        isDarkMode ? 'text-gray-300' : 'text-gray-600'
      }`}>How can I assist you today?</p>
      
      <div className="grid grid-cols-3 gap-4 max-w-5xl mx-auto mb-6">
        {/* Upcoming Events */}
        <div className={`backdrop-blur-sm rounded-2xl p-4 shadow-sm transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-gray-700/80 shadow-gray-900/20' 
            : 'bg-white/80 shadow-gray-900/10'
        }`}>
          <div className="flex items-center gap-2 mb-4">
            <Calendar size={16} className={`transition-colors duration-300 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`} />
            <h3 className={`text-sm font-medium transition-colors duration-300 ${
              isDarkMode ? 'text-gray-200' : 'text-gray-700'
            }`}>Upcoming</h3>
          </div>
          
          <div className="space-y-3 text-left">
            <div className={`border-l-2 pl-4 transition-colors duration-300 ${
              isDarkMode ? 'border-gray-600' : 'border-gray-300'
            }`}>
              <div className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>10AM • Meeting with John</div>
              <div className={`text-xs transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Conference room A</div>
            </div>
            
            <div className={`border-l-2 pl-4 transition-colors duration-300 ${
              isDarkMode ? 'border-gray-600' : 'border-gray-300'
            }`}>
              <div className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>11:30AM • Team Lunch</div>
              <div className={`text-xs transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Le Marley, Casablanca</div>
            </div>
            
            <div className={`border-l-2 pl-4 transition-colors duration-300 ${
              isDarkMode ? 'border-gray-600' : 'border-gray-300'
            }`}>
              <div className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>12:45 AM • Submit final report</div>
              <div className={`text-xs transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Le Marley, Casablanca</div>
            </div>
          </div>
        </div>
        
        {/* AI Insights */}
        <div className={`backdrop-blur-sm rounded-2xl p-4 shadow-sm transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-gray-700/80 shadow-gray-900/20' 
            : 'bg-white/80 shadow-gray-900/10'
        }`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className={`transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`} />
              <h3 className={`text-sm font-medium transition-colors duration-300 ${
                isDarkMode ? 'text-gray-200' : 'text-gray-700'
              }`}>AI Insights</h3>
            </div>
            <ChevronRight size={16} className={`transition-colors duration-300 ${
              isDarkMode ? 'text-gray-500' : 'text-gray-400'
            }`} />
          </div>
          
          <div className="text-left space-y-4">
            <div>
              <div className={`text-3xl font-light mb-1 transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>20</div>
              <div className={`text-xs transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Less productive than usual.</div>
              <div className={`w-full h-1 rounded mt-2 transition-colors duration-300 ${
                isDarkMode ? 'bg-red-900/50' : 'bg-red-100'
              }`}>
                <div className="bg-red-400 h-1 rounded" style={{ width: '30%' }}></div>
              </div>
            </div>
            
            <div>
              <div className={`text-2xl font-light mb-1 transition-colors duration-300 ${
                isDarkMode ? 'text-white' : 'text-gray-900'
              }`}>
                9<span className={`text-lg transition-colors duration-300 ${
                  isDarkMode ? 'text-gray-500' : 'text-gray-400'
                }`}>/23</span>
              </div>
              <div className={`text-xs mb-2 transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Tasks completed this week.</div>
              <div className={`text-xs transition-colors duration-300 ${
                isDarkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>Work for 25mins, take 5mins break.</div>
            </div>
          </div>
        </div>
        
        {/* Vacation Eligibility */}
        <div className={`backdrop-blur-sm rounded-2xl p-4 shadow-sm transition-colors duration-300 ${
          isDarkMode 
            ? 'bg-gray-700/80 shadow-gray-900/20' 
            : 'bg-white/80 shadow-gray-900/10'
        }`}>
          <div className="flex items-center gap-2 mb-4">
            <Plane size={16} className={`transition-colors duration-300 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`} />
            <h3 className={`text-sm font-medium transition-colors duration-300 ${
              isDarkMode ? 'text-gray-200' : 'text-gray-700'
            }`}>Vacation Eligibility</h3>
          </div>
          
          <div className="text-center">
            <div className={`flex justify-center gap-4 mb-4 text-xs transition-colors duration-300 ${
              isDarkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              <span>Days</span>
              <span>Hours</span>
            </div>
            
            <div className="relative inline-block">
              <svg className="transform -rotate-90 w-20 h-20">
                <circle
                  cx="40"
                  cy="40"
                  r="30"
                  stroke={isDarkMode ? "#374151" : "#f3f4f6"}
                  strokeWidth="6"
                  fill="none"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="30"
                  stroke="url(#gradient)"
                  strokeWidth="6"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 30 * 0.6} ${2 * Math.PI * 30}`}
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#fed7aa" />
                    <stop offset="100%" stopColor="#fdba74" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-2xl font-light transition-colors duration-300 ${
                  isDarkMode ? 'text-white' : 'text-gray-900'
                }`}>12</span>
                <span className={`text-xs transition-colors duration-300 ${
                  isDarkMode ? 'text-gray-400' : 'text-gray-500'
                }`}>Days left</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-4">
        <AIOrb onToggleView={onToggleView} isDarkMode={isDarkMode} />
      </div>
    </div>
  );
}
