import React, { useState, useEffect } from 'react';
import {
  Cancel01Icon as X,
  AlertCircleIcon as AlertCircle,
  HelpCircleIcon as HelpCircle,
} from 'hugeicons-react';

export default function RuleModal({ isOpen, onClose, onSave, ruleToEdit, existingRulesCount = 0 }) {
  const [formData, setFormData] = useState({
    name: '',
    priority: 10,
    source_ip: '',
    destination_ip: '',
    destination_port: '',
    protocol: 'TCP',
    action: 'ALLOW',
    enabled: true,
    description: '',
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (ruleToEdit) {
      setFormData({
        name: ruleToEdit.name || '',
        priority: ruleToEdit.priority || 10,
        source_ip: ruleToEdit.source_ip || '',
        destination_ip: ruleToEdit.destination_ip || '',
        destination_port: ruleToEdit.destination_port || '',
        protocol: ruleToEdit.protocol || 'TCP',
        action: ruleToEdit.action || 'ALLOW',
        enabled: ruleToEdit.enabled !== undefined ? ruleToEdit.enabled : true,
        description: ruleToEdit.description || '',
      });
    } else {
      setFormData({
        name: '',
        priority: (existingRulesCount + 1) * 10,
        source_ip: '',
        destination_ip: '',
        destination_port: '',
        protocol: 'TCP',
        action: 'ALLOW',
        enabled: true,
        description: '',
      });
    }
    setErrors({});
  }, [ruleToEdit, isOpen, existingRulesCount]);

  if (!isOpen) return null;

  const validate = () => {
    const errs = {};
    if (!formData.name.trim()) errs.name = 'Rule name is required.';
    if (!formData.priority || Number(formData.priority) < 1) errs.priority = 'Priority must be a positive integer.';
    
    // Source IP
    if (!formData.source_ip.trim()) {
      errs.source_ip = "Source IP cannot be blank. Enter IP, CIDR, or click 'ANY'.";
    }
    
    // Dest IP
    if (!formData.destination_ip.trim()) {
      errs.destination_ip = "Destination IP cannot be blank. Enter IP, CIDR, or click 'ANY'.";
    }

    // Port
    if (formData.protocol !== 'ICMP' && !formData.destination_port.trim()) {
      errs.destination_port = "Destination port is required for TCP/UDP. Enter port, range, or click 'ANY'.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      setIsSubmitting(true);
      // For ICMP, if port is blank, normalize to ANY
      const submissionData = {
        ...formData,
        priority: Number(formData.priority),
        destination_port: formData.protocol === 'ICMP' && !formData.destination_port.trim() ? 'ANY' : formData.destination_port.trim(),
      };
      await onSave(submissionData);
      onClose();
    } catch (err) {
      setErrors({ form: err.message || 'Failed to save firewall rule.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
      <div className="bg-[#111726] border border-slate-700 w-full max-w-xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-slate-100">
              {ruleToEdit ? 'Edit Firewall Rule' : 'Create New Firewall Rule'}
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Rules are evaluated strictly by priority order. Lowest number is evaluated first.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.form && (
            <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-red-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{errors.form}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-1">
              <label className="text-xs font-medium text-slate-300">Rule Name *</label>
              <input
                type="text"
                placeholder="e.g. Allow Web HTTPS"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
              />
              {errors.name && <p className="text-xs text-red-400">{errors.name}</p>}
            </div>

            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300">Priority Order *</label>
              <input
                type="number"
                min="1"
                placeholder="10"
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-500 font-mono"
              />
              {errors.priority && <p className="text-xs text-red-400">{errors.priority}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Protocol */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300">Protocol *</label>
              <select
                value={formData.protocol}
                onChange={(e) => {
                  const newProto = e.target.value;
                  setFormData({
                    ...formData,
                    protocol: newProto,
                    destination_port: newProto === 'ICMP' ? 'ANY' : formData.destination_port
                  });
                }}
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
              >
                <option value="TCP">TCP</option>
                <option value="UDP">UDP</option>
                <option value="ICMP">ICMP (Ping / Diagnostic)</option>
                <option value="ANY">ANY (All Protocols)</option>
              </select>
            </div>

            {/* Action */}
            <div className="space-y-1">
              <label className="text-xs font-medium text-slate-300">Action *</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, action: 'ALLOW' })}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all ${
                    formData.action === 'ALLOW'
                      ? 'bg-emerald-600 text-white border border-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.3)]'
                      : 'bg-slate-900 text-slate-400 border border-slate-700 hover:border-slate-600'
                  }`}
                >
                  ALLOW
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, action: 'DENY' })}
                  className={`py-2 px-3 rounded-lg text-xs font-bold transition-all ${
                    formData.action === 'DENY'
                      ? 'bg-red-600 text-white border border-red-400 shadow-[0_0_10px_rgba(239,68,68,0.3)]'
                      : 'bg-slate-900 text-slate-400 border border-slate-700 hover:border-slate-600'
                  }`}
                >
                  DENY
                </button>
              </div>
            </div>
          </div>

          {/* Source IP */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300">Source IP or CIDR *</label>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, source_ip: 'ANY' })}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-mono"
              >
                [Set ANY]
              </button>
            </div>
            <input
              type="text"
              placeholder="e.g. 192.168.1.0/24, 10.0.0.5, or ANY"
              value={formData.source_ip}
              onChange={(e) => setFormData({ ...formData, source_ip: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
            {errors.source_ip && <p className="text-xs text-red-400">{errors.source_ip}</p>}
          </div>

          {/* Destination IP */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300">Destination IP or CIDR *</label>
              <button
                type="button"
                onClick={() => setFormData({ ...formData, destination_ip: 'ANY' })}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 font-mono"
              >
                [Set ANY]
              </button>
            </div>
            <input
              type="text"
              placeholder="e.g. 10.0.0.10, 172.16.0.0/16, or ANY"
              value={formData.destination_ip}
              onChange={(e) => setFormData({ ...formData, destination_ip: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
            {errors.destination_ip && <p className="text-xs text-red-400">{errors.destination_ip}</p>}
          </div>

          {/* Destination Port */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label className="text-xs font-medium text-slate-300">
                Destination Port {formData.protocol === 'ICMP' ? '(N/A for ICMP)' : '*'}
              </label>
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, destination_port: 'ANY' })}
                  className="text-[11px] text-cyan-400 hover:text-cyan-300 font-mono"
                >
                  [Set ANY]
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, destination_port: '80' })}
                  className="text-[11px] text-slate-400 hover:text-slate-300 font-mono"
                >
                  80
                </button>
                <button
                  type="button"
                  onClick={() => setFormData({ ...formData, destination_port: '443' })}
                  className="text-[11px] text-slate-400 hover:text-slate-300 font-mono"
                >
                  443
                </button>
              </div>
            </div>
            <input
              type="text"
              placeholder="e.g. 80, 80-443, or ANY"
              value={formData.destination_port}
              onChange={(e) => setFormData({ ...formData, destination_port: e.target.value })}
              disabled={formData.protocol === 'ICMP'}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500 disabled:opacity-50"
            />
            {errors.destination_port && <p className="text-xs text-red-400">{errors.destination_port}</p>}
            <p className="text-[11px] text-slate-500">
              Supports single port (1-65535), port range (e.g. 8000-8080), or explicit wildcard ANY.
            </p>
          </div>

          {/* Description */}
          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-300">Description (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Inbound traffic policy for web cluster"
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Enabled toggle */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-800">
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="rule-enabled"
                checked={formData.enabled}
                onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
                className="w-4 h-4 rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0"
              />
              <label htmlFor="rule-enabled" className="text-xs text-slate-300 font-medium cursor-pointer">
                Enable rule immediately
              </label>
            </div>
            <div className="flex space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-xs font-medium text-slate-300 hover:bg-slate-800 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-5 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.3)] disabled:opacity-50"
              >
                {isSubmitting ? 'Saving...' : ruleToEdit ? 'Save Changes' : 'Create Rule'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
