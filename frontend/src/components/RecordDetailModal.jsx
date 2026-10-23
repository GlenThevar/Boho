import React from 'react';
import {
  Cancel01Icon as X,
  CheckmarkCircle01Icon as CheckCircle,
  Cancel01Icon as XCircle,
  AlertCircleIcon as AlertTriangle,
  Shield01Icon as Shield,
  ArrowRight01Icon as ArrowRight,
} from 'hugeicons-react';

export default function RecordDetailModal({ record, onClose }) {
  if (!record) return null;

  const isAllowed = record.decision === 'ALLOW';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-[#111726] border border-slate-700 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${isAllowed ? 'bg-emerald-950/80 border border-emerald-500/40 text-emerald-400' : 'bg-red-950/80 border border-red-500/40 text-red-400'}`}>
              {isAllowed ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-slate-100 font-mono">
                  {record.record_id}
                </h3>
                <span className={`px-2 py-0.5 text-xs font-bold rounded ${
                  isAllowed ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40' : 'bg-red-500/20 text-red-400 border border-red-500/40'
                }`}>
                  {record.decision}
                </span>
                {record.is_default_policy && (
                  <span className="px-2 py-0.5 text-[11px] rounded bg-slate-800 text-slate-400 border border-slate-700">
                    Default Policy
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400">Detailed packet evaluation diagnostics</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {/* Packet Flow Visualizer */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between text-xs">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Source</span>
              <p className="font-mono text-sm text-cyan-400 font-semibold">{record.source_ip}</p>
            </div>

            <div className="flex flex-col items-center px-4">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 mb-1">
                {record.protocol} {record.destination_port ? `:${record.destination_port}` : ''}
              </span>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </div>

            <div className="space-y-1 text-right">
              <span className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Destination</span>
              <p className="font-mono text-sm text-cyan-400 font-semibold">{record.destination_ip}</p>
            </div>
          </div>

          {/* Validation Errors Notice */}
          {record.validation_errors && (
            <div className="p-3.5 rounded-lg bg-red-950/40 border border-red-800 text-red-300 text-xs space-y-1">
              <div className="flex items-center space-x-1.5 font-bold text-red-400">
                <AlertTriangle className="w-4 h-4" />
                <span>Input Record Validation Errors</span>
              </div>
              <p className="text-slate-300 font-mono text-[11px]">{record.validation_errors}</p>
            </div>
          )}

          {/* Decision Breakdown & Explanation */}
          <div className="space-y-2">
            <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Decision Explanation
            </label>
            <div className="p-4 rounded-lg bg-slate-950 border border-slate-800 font-mono text-xs leading-relaxed text-slate-300">
              {record.explanation}
            </div>
          </div>

          {/* Rule Match Details */}
          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500">Matched Rule ID</span>
              <p className="font-mono font-semibold text-slate-200">
                {record.matched_rule_id ? `#${record.matched_rule_id}` : 'None (No Rule Matched)'}
              </p>
            </div>

            <div className="p-3 rounded-lg bg-slate-900/60 border border-slate-800 space-y-1">
              <span className="text-slate-500">Matched Rule Name</span>
              <p className="font-semibold text-slate-200 truncate">
                {record.matched_rule_name || 'N/A (Applied Default DENY)'}
              </p>
            </div>
          </div>
        </div>

        <div className="px-6 py-3 bg-slate-900/60 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
