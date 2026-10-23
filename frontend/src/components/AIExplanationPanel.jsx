import React, { useState } from 'react';
import {
  AiChat01Icon as Bot,
  ArrowDown01Icon as ChevronDown,
  ArrowUp01Icon as ChevronUp,
  AlertCircleIcon as AlertTriangle,
  Loading01Icon as Loader2,
  SparklesIcon as Sparkles,
} from 'hugeicons-react';

export default function AIExplanationPanel({ title = 'AI Explanation', onFetch, defaultOpen = false }) {
  const [open, setOpen] = useState(defaultOpen);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [fetched, setFetched] = useState(false);

  const handleToggle = async () => {
    if (!open && !fetched) {
      setLoading(true);
      try {
        const result = await onFetch();
        setData(result);
      } catch (err) {
        setData({ success: false, error: err.message, ai_enabled: true });
      } finally {
        setLoading(false);
        setFetched(true);
      }
    }
    setOpen((prev) => !prev);
  };

  const handleRefetch = async () => {
    setLoading(true);
    setFetched(false);
    try {
      const result = await onFetch();
      setData(result);
    } catch (err) {
      setData({ success: false, error: err.message, ai_enabled: true });
    } finally {
      setLoading(false);
      setFetched(true);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden mt-4">
      {/* Header */}
      <button
        onClick={handleToggle}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-hover transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 flex-shrink-0" />
          <span className="font-semibold text-sm">{title}</span>
          <span className="ai-badge">
            <Sparkles className="w-2.5 h-2.5" />
            AI-Generated
          </span>
        </div>
        <div className="flex items-center space-x-2">
          {loading && <Loader2 className="w-4 h-4 animate-spin" />}
          {open ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </button>

      {/* Body */}
      {open && (
        <div className="px-4 pb-4 border-t border-border">
          {loading ? (
            <div className="flex items-center justify-center py-8 space-x-2">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="text-sm">Generating AI explanation…</span>
            </div>
          ) : data ? (
            <>
              {!data.success || data.error ? (
                <div className="mt-3 flex items-start space-x-2 text-sm rounded-md p-3 border border-border">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold">AI unavailable</p>
                    <p className="text-xs mt-0.5">{data.error || 'Unknown error'}</p>
                    {fetched && (
                      <button
                        onClick={handleRefetch}
                        className="mt-2 text-xs underline"
                      >
                        Retry
                      </button>
                    )}
                  </div>
                </div>
              ) : (
                <>
                  <div className="mt-3 prose prose-sm max-w-none">
                    <FormattedAIText text={data.explanation || data.answer || ''} />
                  </div>
                  {data.disclaimer && (
                    <p className="mt-3 text-xs italic border-t border-border pt-2">
                      ⚠ {data.disclaimer}
                    </p>
                  )}
                  <button
                    onClick={handleRefetch}
                    className="mt-2 text-xs underline"
                  >
                    Regenerate
                  </button>
                </>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

function FormattedAIText({ text }) {
  if (!text) return null;

  const lines = text.split('\n');

  return (
    <div className="space-y-1.5 text-sm leading-relaxed">
      {lines.map((line, i) => {
        if (!line.trim()) return <div key={i} className="h-1" />;

        const headerMatch = line.match(/^\*\*(.+?)\*\*\s*[—–-]?\s*(.*)/);
        if (headerMatch && line.startsWith('**')) {
          return (
            <div key={i}>
              <span className="font-bold underline">{headerMatch[1]}</span>
              {headerMatch[2] && (
                <span> — {renderInline(headerMatch[2])}</span>
              )}
            </div>
          );
        }

        const numMatch = line.match(/^(\d+)\.\s+\*\*(.+?)\*\*\s*[—–-]?\s*(.*)/);
        if (numMatch) {
          return (
            <div key={i} className="flex space-x-1.5">
              <span className="font-mono font-semibold flex-shrink-0">{numMatch[1]}.</span>
              <span>
                <span className="font-bold">{numMatch[2]}</span>
                {numMatch[3] && <span> — {renderInline(numMatch[3])}</span>}
              </span>
            </div>
          );
        }

        if (line.match(/^[-•*]\s/)) {
          return (
            <div key={i} className="flex space-x-1.5 ml-2">
              <span className="flex-shrink-0">•</span>
              <span>{renderInline(line.replace(/^[-•*]\s/, ''))}</span>
            </div>
          );
        }

        return <p key={i}>{renderInline(line)}</p>;
      })}
    </div>
  );
}

function renderInline(text) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i} className="font-bold">{part}</strong> : part
  );
}
