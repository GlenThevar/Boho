import React from 'react';
import {
  Shield01Icon,
  ComputerTerminal01Icon,
  Sun01Icon,
  Moon01Icon,
  AiChat01Icon,
} from 'hugeicons-react';
import { useTheme } from '../context/ThemeContext';

export default function Navbar({ onOpenAssistant }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <header className="h-16 px-6 flex items-center justify-between sticky top-0 z-20 bg-card">
      {/* Brand */}
      <div className="flex items-center space-x-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center">
          <Shield01Icon className="w-5 h-5" />
        </div>
        <span className="font-bold text-lg tracking-wider font-mono">BOHO</span>
      </div>

      {/* Controls */}
      <div className="flex items-center space-x-3">
        {/* Offline indicator */}
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs">
          <span className="w-2 h-2 rounded-full border border-current" />
          <span className="font-mono font-semibold">Offline Simulation Engine</span>
          <span>|</span>
          <span>Host OS Safe</span>
        </div>

        {/* Version */}
        <div className="hidden sm:flex items-center space-x-1.5 text-xs font-mono px-3 py-1.5 rounded-md">
          <ComputerTerminal01Icon className="w-3.5 h-3.5" />
          <span>v3.0</span>
        </div>

        {/* AI Assistant button */}
        <button
          onClick={onOpenAssistant}
          title="Open AI Assistant"
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors hover:bg-hover"
        >
          <AiChat01Icon className="w-4 h-4" />
          <span className="hidden sm:inline">AI Assistant</span>
        </button>

        {/* Theme toggle button */}
        <button
          onClick={toggleTheme}
          title={isDark ? 'Switch to Pure White Mode' : 'Switch to Pure Dark Mode'}
          className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors hover:bg-hover"
        >
          {isDark ? (
            <>
              <Sun01Icon className="w-4 h-4" />
              <span className="font-mono">Light</span>
            </>
          ) : (
            <>
              <Moon01Icon className="w-4 h-4" />
              <span className="font-mono">Dark</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
