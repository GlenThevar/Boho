import React, { useState } from 'react';
import {
  X,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  CheckCircle,
  Copy,
  Info,
  RotateCcw,
  EyeOff
} from 'lucide-react';

export default function FindingDetailModal({ finding, onClose, onDismiss, onRestore }) {
  const [dismissReason, setDismissReason] = useState('');
  const [isDismissing, setIsDismissing] = useState(false);
  const [showDismissInput, setShowDismissInput] = useState(false);

  if (!finding) return null;

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'Critical':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'High':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'Medium':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      default:
        return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40';
    }
  };

  const handleDismissSubmit = async (e) => {
    e.preventDefault();
    if (!dismissReason.trim()) return;
    try {
      setIsDismissing(true);
      await onDismiss(finding.id, dismissReason.trim());
      setShowDismissInput(false);
      setDismissReason('');
    } catch (err) {
      alert(`Failed to dismiss finding: ${err.message}`);
    } finally {
      setIsDismissing(false);
    }
  };

  const handleRestoreClick = async () => {
    try {
      await onRestore(finding.id);
    } catch (err) {
      alert(`Failed to restore finding: ${err.message}`);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-[#111726] border border-slate-700 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <span className={`px-2.5 py-1 text-xs font-bold rounded border uppercase font-mono ${getSeverityBadge(finding.severity)}`}>
              {finding.severity}
            </span>
            <div>
              <h3 className="text-sm font-bold text-slate-100">{finding.title}</h3>
              <p className="text-xs text-slate-400">
                Rule #{finding.rule_priority}: <span className="font-semibold text-slate-200">{finding.rule_name}</span> | {finding.category}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-5 text-xs">
          {/* Dismissed Banner */}
          {finding.is_dismissed && (
            <div className="p-3.5 rounded-lg bg-slate-900 border border-slate-700 flex items-start justify-between">
              <div className="space-y-1">
                <span className="font-semibold text-slate-300 flex items-center space-x-1.5">
                  <EyeOff className="w-3.5 h-3.5 text-slate-400" />
                  <span>Finding Dismissed</span>
                </span>
                <p className="text-slate-400">
                  Reason: <span className="text-slate-200 italic">{finding.dismissed_reason}</span>
                </p>
                {finding.dismissed_at && (
                  <p className="text-[10px] text-slate-500">
                    Dismissed on: {new Date(finding.dismissed_at).toLocaleString()}
                  </p>
                )}
              </div>
              <button
                onClick={handleRestoreClick}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-400 rounded text-xs font-semibold flex items-center space-x-1"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Restore</span>
              </button>
            </div>
          )}

          {/* Explanation */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
              Diagnostic Explanation
            </label>
            <div className="p-3.5 rounded-lg bg-slate-900/80 border border-slate-800 leading-relaxed text-slate-200">
              {finding.explanation}
            </div>
          </div>

          {/* Evidence */}
          {finding.evidence && (
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Audited Rule Evidence
              </label>
              <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-cyan-300 overflow-x-auto">
                <pre>{JSON.stringify(finding.evidence, null, 2)}</pre>
              </div>
            </div>
          )}

          {/* Remediation */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Recommended Remediation</span>
            </label>
            <div className="p-3.5 rounded-lg bg-emerald-950/20 border border-emerald-900/50 leading-relaxed text-emerald-200">
              {finding.remediation}
            </div>
          </div>

          {/* Dismiss Form */}
          {!finding.is_dismissed && showDismissInput && (
            <form onSubmit={handleDismissSubmit} className="p-4 rounded-lg bg-slate-900 border border-slate-700 space-y-3">
              <label className="text-xs font-semibold text-slate-200 block">
                Dismiss Finding (Business Exception Reason)
              </label>
              <input
                type="text"
                placeholder="e.g. Approved exception: Dedicated jumpbox with MFA"
                value={dismissReason}
                onChange={(e) => setDismissReason(e.target.value)}
                required
                className="w-full px-3 py-2 bg-slate-950 border border-slate-700 rounded-lg text-slate-100 text-xs focus:outline-none focus:border-cyan-500"
              />
              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowDismissInput(false)}
                  className="px-3 py-1.5 text-slate-400 hover:text-slate-200 rounded text-xs"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isDismissing || !dismissReason.trim()}
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white font-bold rounded text-xs disabled:opacity-50"
                >
                  {isDismissing ? 'Dismissing...' : 'Confirm Dismissal'}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-3 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between shrink-0">
          <div>
            {!finding.is_dismissed && !showDismissInput && (
              <button
                onClick={() => setShowDismissInput(true)}
                className="px-3 py-1.5 text-xs font-semibold text-amber-400 hover:text-amber-300 bg-amber-950/40 hover:bg-amber-900/50 border border-amber-800/60 rounded flex items-center space-x-1.5"
              >
                <EyeOff className="w-3.5 h-3.5" />
                <span>Dismiss Finding</span>
              </button>
            )}
          </div>

          <button
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-300 bg-slate-800 hover:bg-slate-700 rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
