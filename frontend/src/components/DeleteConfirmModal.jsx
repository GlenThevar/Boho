import React from 'react';
import { AlertTriangle, X } from 'lucide-react';

export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, title, message, itemName }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-[#111726] border border-red-900/60 w-full max-w-md rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="p-6 space-y-4">
          <div className="flex items-center space-x-3 text-red-400">
            <div className="p-2.5 rounded-full bg-red-950/80 border border-red-700/60">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="text-base font-bold text-slate-100">{title || 'Confirm Deletion'}</h3>
          </div>

          <p className="text-xs text-slate-300 leading-relaxed">
            {message || 'Are you sure you want to permanently delete this item? This action cannot be undone.'}
          </p>

          {itemName && (
            <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800 text-xs font-mono text-cyan-300 truncate">
              {itemName}
            </div>
          )}

          <div className="flex justify-end space-x-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 rounded-lg"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={async () => {
                await onConfirm();
                onClose();
              }}
              className="px-4 py-2 text-xs font-bold text-white bg-red-600 hover:bg-red-500 rounded-lg shadow-[0_0_15px_rgba(239,68,68,0.4)]"
            >
              Delete
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
