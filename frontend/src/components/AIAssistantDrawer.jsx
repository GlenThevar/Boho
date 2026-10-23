import React, { useState, useRef, useEffect } from 'react';
import {
  AiChat01Icon as Bot,
  Cancel01Icon as X,
  SentIcon as Send,
  Loading01Icon as Loader2,
  SparklesIcon as Sparkles,
  AlertCircleIcon as AlertTriangle,
} from 'hugeicons-react';
import { aiAssistant } from '../api';
import { useTheme } from '../context/ThemeContext';

export default function AIAssistantDrawer({ open, onClose }) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: "Hi! I'm the Boho AI Assistant. Ask me anything about your firewall rules, policy findings, or simulation results.",
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, loading]);

  const sendMessage = async () => {
    const q = input.trim();
    if (!q || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setLoading(true);

    try {
      const res = await aiAssistant({ question: q });
      if (res.success && res.answer) {
        setMessages((prev) => [
          ...prev,
          { role: 'assistant', text: res.answer, disclaimer: res.disclaimer },
        ]);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: 'error',
            text: res.error || 'AI is currently unavailable. Please try again later.',
          },
        ]);
      }
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'error', text: err.message || 'Request failed.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 bg-black/40 z-30"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <aside
        className={`fixed top-0 right-0 h-full w-full sm:w-[420px] z-40 flex flex-col shadow-2xl border-l border-border transition-transform duration-300 ${
          open ? 'translate-x-0' : 'translate-x-full'
        } bg-card`}
      >
        {/* Header */}
        <div className="h-16 border-b border-border px-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-2">
            <Bot className="w-5 h-5" />
            <span className="font-semibold">AI Assistant</span>
            <span className="ai-badge">
              <Sparkles className="w-2.5 h-2.5" />
              Amazon Bedrock
            </span>
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() =>
                setMessages([
                  {
                    role: 'assistant',
                    text: "Hi! I'm the Boho AI Assistant. Ask me anything about your firewall rules, policy findings, or simulation results.",
                  },
                ])
              }
              className="text-xs px-2 py-1 rounded border border-border hover:bg-hover"
              title="Clear conversation"
            >
              Clear
            </button>
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-hover border border-border"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg} />
          ))}

          {loading && (
            <div className="flex items-center space-x-2 text-sm">
              <div className="w-7 h-7 rounded-full border border-border flex items-center justify-center flex-shrink-0">
                <Bot className="w-3.5 h-3.5" />
              </div>
              <div className="flex space-x-1 items-center">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span className="text-xs">Thinking…</span>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Suggested prompts */}
        {messages.length === 1 && (
          <div className="px-4 pb-3 space-y-1.5">
            <p className="text-[10px] uppercase font-semibold tracking-widest">Suggested</p>
            {[
              'What shadowed rules do I have?',
              'Are there any overly permissive rules?',
              'Summarize my current firewall policy.',
            ].map((s) => (
              <button
                key={s}
                onClick={() => setInput(s)}
                className="w-full text-left text-xs px-3 py-2 rounded-md border border-border bg-card hover:bg-hover transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="flex-shrink-0 border-t border-border px-4 py-3">
          <div className="flex items-end space-x-2">
            <textarea
              className="flex-1 resize-none rounded-lg border border-border bg-input text-sm px-3 py-2 focus:outline-none placeholder-muted leading-relaxed"
              rows={2}
              placeholder="Ask about rules, findings, or comparisons…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKey}
              disabled={loading}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="h-10 w-10 flex-shrink-0 flex items-center justify-center rounded-lg border border-border transition-colors hover:bg-hover disabled:opacity-40"
            >
              {loading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>
          </div>
          <p className="text-[10px] mt-1.5">
            Press Enter to send · Shift+Enter for new line
          </p>
        </div>
      </aside>
    </>
  );
}

function MessageBubble({ msg }) {
  const isUser = msg.role === 'user';
  const isError = msg.role === 'error';

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-tr-sm px-3 py-2 text-sm border border-border">
          {msg.text}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-start space-x-2">
        <div className="w-7 h-7 rounded-full border border-border flex items-center justify-center flex-shrink-0">
          <AlertTriangle className="w-3.5 h-3.5" />
        </div>
        <div className="max-w-[85%] rounded-2xl rounded-tl-sm px-3 py-2 text-sm border border-border">
          {msg.text}
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-2">
      <div className="w-7 h-7 rounded-full border border-border flex items-center justify-center flex-shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5" />
      </div>
      <div className="max-w-[85%] space-y-1">
        <div className="rounded-2xl rounded-tl-sm px-3 py-2 text-sm leading-relaxed border border-border">
          <FormattedText text={msg.text} />
        </div>
        {msg.disclaimer && (
          <p className="text-[10px] italic px-1">⚠ {msg.disclaimer}</p>
        )}
      </div>
    </div>
  );
}

function FormattedText({ text }) {
  const lines = text.split('\n');
  return (
    <div className="space-y-1">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-0.5" />;
        const parts = line.split(/\*\*(.+?)\*\*/g);
        return (
          <p key={i}>
            {parts.map((p, j) =>
              j % 2 === 1 ? <strong key={j}>{p}</strong> : p
            )}
          </p>
        );
      })}
    </div>
  );
}
