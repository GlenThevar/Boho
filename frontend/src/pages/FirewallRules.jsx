import React, { useState, useEffect } from 'react';
import {
  getRules,
  createRule,
  updateRule,
  toggleRule,
  reorderRules,
  deleteRule,
  seedDefaultRules,
  aiSuggestImprovements,
} from '../api';
import RuleModal from '../components/RuleModal';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import AIExplanationPanel from '../components/AIExplanationPanel';
import {
  Add01Icon as Plus,
  Shield01Icon as Shield,
  ArrowUp01Icon as ArrowUp,
  ArrowDown01Icon as ArrowDown,
  Edit01Icon as Edit2,
  Delete01Icon as Trash2,
  CheckmarkCircle01Icon as CheckCircle2,
  Cancel01Icon as XCircle,
  HelpCircleIcon as HelpCircle,
  SparklesIcon as Sparkles,
  RefreshIcon as RefreshCw,
  AlertCircleIcon as AlertCircle,
  InformationCircleIcon as Info,
} from 'hugeicons-react';

export default function FirewallRules() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Modals state
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [ruleToEdit, setRuleToEdit] = useState(null);
  const [ruleToDelete, setRuleToDelete] = useState(null);

  const loadRules = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getRules();
      setRules(data);
    } catch (err) {
      setError(err.message || 'Failed to load firewall rules.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleSaveRule = async (formData) => {
    if (ruleToEdit) {
      await updateRule(ruleToEdit.id, formData);
    } else {
      await createRule(formData);
    }
    await loadRules();
  };

  const handleToggle = async (id, currentStatus) => {
    try {
      await toggleRule(id, !currentStatus);
      setRules(rules.map((r) => (r.id === id ? { ...r, enabled: !currentStatus } : r)));
    } catch (err) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const handleDelete = async () => {
    if (!ruleToDelete) return;
    try {
      await deleteRule(ruleToDelete.id);
      setRules(rules.filter((r) => r.id !== ruleToDelete.id));
      setRuleToDelete(null);
    } catch (err) {
      alert(`Failed to delete rule: ${err.message}`);
    }
  };

  const handleMove = async (index, direction) => {
    const targetIndex = direction === 'up' ? index - 1 : index + 1;
    if (targetIndex < 0 || targetIndex >= rules.length) return;

    // Swap priorities between rules[index] and rules[targetIndex]
    const updated = [...rules];
    const tempPriority = updated[index].priority;
    updated[index].priority = updated[targetIndex].priority;
    updated[targetIndex].priority = tempPriority;

    // If both had identical priorities, ensure distinct order
    if (updated[index].priority === updated[targetIndex].priority) {
      if (direction === 'up') {
        updated[index].priority = Math.max(1, updated[targetIndex].priority - 1);
      } else {
        updated[index].priority = updated[targetIndex].priority + 1;
      }
    }

    try {
      const reorderPayload = updated.map((r) => ({ id: r.id, priority: r.priority }));
      const newRules = await reorderRules(reorderPayload);
      setRules(newRules);
    } catch (err) {
      alert(`Failed to reorder rules: ${err.message}`);
      await loadRules();
    }
  };

  const handleSeedDefaults = async () => {
    try {
      setLoading(true);
      const seeded = await seedDefaultRules();
      setRules(seeded);
    } catch (err) {
      alert(`Failed to seed defaults: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <span>Firewall Policy Rules</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
              {rules.length} configured
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Rules are evaluated deterministically in ascending priority order (1, 2, 3...). First match determines the action.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {rules.length === 0 && (
            <button
              onClick={handleSeedDefaults}
              className="px-3.5 py-2 text-xs font-semibold text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-700/60 rounded-lg flex items-center space-x-1.5 shadow-sm"
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Seed Default Rules</span>
            </button>
          )}

          <button
            onClick={() => {
              setRuleToEdit(null);
              setIsRuleModalOpen(true);
            }}
            className="px-4 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg flex items-center space-x-2 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
          >
            <Plus className="w-4 h-4" />
            <span>Add Rule</span>
          </button>
        </div>
      </div>

      {/* AI Suggest Improvements */}
      {rules.length > 0 && (
        <AIExplanationPanel
          title="Suggest Rule Improvements (AI)"
          onFetch={() =>
            aiSuggestImprovements({
              rules: rules.map((r) => ({
                priority: r.priority,
                name: r.name,
                source_ip: r.source_ip,
                destination_ip: r.destination_ip,
                destination_port: r.destination_port,
                protocol: r.protocol,
                action: r.action,
                enabled: r.enabled,
              })),
            }).then((res) => ({
              success: res.success,
              ai_enabled: res.ai_enabled,
              explanation: res.raw_text || (res.suggestions?.map(
                (s, i) => `**${i + 1}. ${s.title}**\n${s.description}\n\nRationale: ${s.rationale}\nImpact: ${s.impact}`
              ).join('\n\n')),
              error: res.error,
              disclaimer: res.disclaimer,
            }))
          }
        />
      )}

      {/* Default Policy Banner */}
      <div className="p-4 rounded-xl bg-[#111726] border border-slate-800 flex items-start space-x-3 text-xs">
        <Info className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-200">
            Default Fallback Policy: <span className="font-mono text-red-400 font-bold uppercase">DENY</span>
          </p>
          <p className="text-slate-400 leading-relaxed">
            If a network traffic packet does not match any enabled rule in this list, the evaluation engine immediately enforces a default <strong className="text-red-400 font-mono">DENY</strong> decision. Disabled rules are ignored during evaluation.
          </p>
        </div>
      </div>

      {/* Rules Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span className="text-xs font-mono">Loading firewall rule sets...</span>
        </div>
      ) : rules.length === 0 ? (
        <div className="p-12 rounded-xl bg-[#111726] border border-slate-800 text-center space-y-4">
          <Shield className="w-12 h-12 text-slate-600 mx-auto" />
          <div>
            <h3 className="text-base font-bold text-slate-200">No Firewall Rules Configured</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Create custom rules or click "Seed Default Rules" to load standard baseline cybersecurity policies.
            </p>
          </div>
          <button
            onClick={handleSeedDefaults}
            className="px-4 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg"
          >
            Load Sample Rules
          </button>
        </div>
      ) : (
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-3 w-16 text-center font-semibold">Priority</th>
                <th className="py-3 px-4 font-semibold">Rule Name</th>
                <th className="py-3 px-3 font-semibold">Proto</th>
                <th className="py-3 px-3 font-semibold">Source IP/CIDR</th>
                <th className="py-3 px-3 font-semibold">Destination IP/CIDR</th>
                <th className="py-3 px-3 font-semibold">Port</th>
                <th className="py-3 px-3 font-semibold">Action</th>
                <th className="py-3 px-3 font-semibold text-center">Status</th>
                <th className="py-3 px-4 font-semibold text-right">Order & Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {rules.map((rule, idx) => (
                <tr
                  key={rule.id}
                  className={`hover:bg-slate-900/50 transition-colors ${!rule.enabled ? 'opacity-50 bg-slate-950/40' : ''}`}
                >
                  {/* Priority */}
                  <td className="py-3 px-3 text-center">
                    <span className="font-bold text-cyan-400 bg-cyan-950/70 border border-cyan-800/60 px-2 py-0.5 rounded text-xs">
                      #{rule.priority}
                    </span>
                  </td>

                  {/* Name & Description */}
                  <td className="py-3 px-4 font-sans">
                    <p className="font-semibold text-slate-100">{rule.name}</p>
                    {rule.description && (
                      <p className="text-[11px] text-slate-500 truncate max-w-xs">{rule.description}</p>
                    )}
                  </td>

                  {/* Protocol */}
                  <td className="py-3 px-3 font-semibold text-slate-300">
                    <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-[11px]">
                      {rule.protocol}
                    </span>
                  </td>

                  {/* Source IP */}
                  <td className="py-3 px-3 text-slate-300">{rule.source_ip}</td>

                  {/* Destination IP */}
                  <td className="py-3 px-3 text-slate-300">{rule.destination_ip}</td>

                  {/* Port */}
                  <td className="py-3 px-3 text-slate-300">{rule.destination_port}</td>

                  {/* Action */}
                  <td className="py-3 px-3">
                    <span className={`px-2.5 py-0.5 rounded text-[11px] font-bold ${
                      rule.action === 'ALLOW'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-red-500/20 text-red-400 border border-red-500/40'
                    }`}>
                      {rule.action}
                    </span>
                  </td>

                  {/* Enabled Toggle Switch */}
                  <td className="py-3 px-3 text-center">
                    <button
                      onClick={() => handleToggle(rule.id, rule.enabled)}
                      className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                        rule.enabled ? 'bg-cyan-500' : 'bg-slate-700'
                      }`}
                      title={rule.enabled ? 'Click to disable rule' : 'Click to enable rule'}
                    >
                      <span
                        className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow-lg ring-0 transition duration-200 ease-in-out ${
                          rule.enabled ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </button>
                  </td>

                  {/* Actions & Reordering */}
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-1">
                      {/* Move Up */}
                      <button
                        onClick={() => handleMove(idx, 'up')}
                        disabled={idx === 0}
                        title="Move Up (Increase Priority)"
                        className="p-1 text-slate-400 hover:text-cyan-400 disabled:opacity-20 hover:bg-slate-800 rounded"
                      >
                        <ArrowUp className="w-3.5 h-3.5" />
                      </button>

                      {/* Move Down */}
                      <button
                        onClick={() => handleMove(idx, 'down')}
                        disabled={idx === rules.length - 1}
                        title="Move Down (Decrease Priority)"
                        className="p-1 text-slate-400 hover:text-cyan-400 disabled:opacity-20 hover:bg-slate-800 rounded"
                      >
                        <ArrowDown className="w-3.5 h-3.5" />
                      </button>

                      <div className="w-[1px] h-3 bg-slate-700 mx-1"></div>

                      {/* Edit */}
                      <button
                        onClick={() => {
                          setRuleToEdit(rule);
                          setIsRuleModalOpen(true);
                        }}
                        title="Edit Rule"
                        className="p-1 text-slate-400 hover:text-slate-100 hover:bg-slate-800 rounded"
                      >
                        <Edit2 className="w-3.5 h-3.5" />
                      </button>

                      {/* Delete */}
                      <button
                        onClick={() => setRuleToDelete(rule)}
                        title="Delete Rule"
                        className="p-1 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Rule Create/Edit Modal */}
      <RuleModal
        isOpen={isRuleModalOpen}
        onClose={() => {
          setIsRuleModalOpen(false);
          setRuleToEdit(null);
        }}
        onSave={handleSaveRule}
        ruleToEdit={ruleToEdit}
        existingRulesCount={rules.length}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!ruleToDelete}
        onClose={() => setRuleToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Firewall Rule"
        message="Are you sure you want to delete this firewall rule? Note: Previously executed simulations will preserve their historical rule snapshots intact."
        itemName={ruleToDelete ? `Rule #${ruleToDelete.priority}: ${ruleToDelete.name}` : ''}
      />
    </div>
  );
}
