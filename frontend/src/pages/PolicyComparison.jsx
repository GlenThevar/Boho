import React, { useState, useEffect } from 'react';
import {
  getSimulations,
  getSimulationDetail,
  createPolicyComparison,
  getPolicyComparisonDetail,
  getExportComparisonCsvUrl,
} from '../api';
import RuleModal from '../components/RuleModal';
import {
  GitCompare,
  ArrowRight,
  Plus,
  Trash2,
  Edit2,
  ArrowUp,
  ArrowDown,
  Download,
  Play,
  RefreshCw,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  RotateCcw,
  Layers,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

export default function PolicyComparison() {
  const [simulations, setSimulations] = useState([]);
  const [selectedSimId, setSelectedSimId] = useState('');
  const [loadingSims, setLoadingSims] = useState(true);

  // Proposed Rules State
  const [proposedRules, setProposedRules] = useState([]);
  const [originalSimDetail, setOriginalSimDetail] = useState(null);
  const [loadingOriginal, setLoadingOriginal] = useState(false);
  const [comparisonName, setComparisonName] = useState('');

  // Execution & Results State
  const [activeTab, setActiveTab] = useState('config'); // 'config' or 'results'
  const [comparisonSummary, setComparisonSummary] = useState(null);
  const [comparisonDetail, setComparisonDetail] = useState(null);
  const [loadingComparison, setLoadingComparison] = useState(false);
  const [error, setError] = useState(null);

  // Result table filters
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [changeTypeFilter, setChangeTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Rule Edit Modal
  const [isRuleModalOpen, setIsRuleModalOpen] = useState(false);
  const [editingRuleIndex, setEditingRuleIndex] = useState(null);
  const [ruleToEdit, setRuleToEdit] = useState(null);

  // Load completed simulations on mount
  useEffect(() => {
    async function fetchSims() {
      try {
        setLoadingSims(true);
        const data = await getSimulations();
        setSimulations(data);
        if (data.length > 0) {
          setSelectedSimId(data[0].id.toString());
        }
      } catch (err) {
        setError(err.message || 'Failed to load historical simulations.');
      } finally {
        setLoadingSims(false);
      }
    }
    fetchSims();
  }, []);

  // When selected simulation changes, load its snapshot as base for proposed rules
  useEffect(() => {
    if (!selectedSimId) return;

    async function loadSimData() {
      try {
        setLoadingOriginal(true);
        setError(null);
        const detail = await getSimulationDetail(Number(selectedSimId), { page_size: 1 });
        setOriginalSimDetail(detail);
        setComparisonName(`Comparison vs ${detail.simulation.name}`);

        // Populate proposed rules initialized with original snapshot rules
        const initialRules = detail.rules_snapshot.map((r, idx) => ({
          name: r.name,
          priority: r.priority,
          source_ip: r.source_ip,
          destination_ip: r.destination_ip,
          destination_port: r.destination_port,
          protocol: r.protocol,
          action: r.action,
          enabled: r.enabled,
          description: r.description || '',
        }));
        setProposedRules(initialRules);
        setActiveTab('config');
        setComparisonSummary(null);
        setComparisonDetail(null);
      } catch (err) {
        setError(err.message || 'Failed to load simulation detail.');
      } finally {
        setLoadingOriginal(false);
      }
    }
    loadSimData();
  }, [selectedSimId]);

  // Load paginated comparison results
  const loadComparisonResults = async (compId) => {
    try {
      setLoadingComparison(true);
      const res = await getPolicyComparisonDetail(compId, {
        page,
        page_size: pageSize,
        change_type: changeTypeFilter,
        search: searchQuery,
      });
      setComparisonDetail(res);
    } catch (err) {
      setError(err.message || 'Failed to load comparison records.');
    } finally {
      setLoadingComparison(false);
    }
  };

  useEffect(() => {
    if (comparisonSummary?.id) {
      loadComparisonResults(comparisonSummary.id);
    }
  }, [comparisonSummary?.id, page, changeTypeFilter]);

  const handleRunComparison = async () => {
    if (!selectedSimId || proposedRules.length === 0) return;
    try {
      setLoadingComparison(true);
      setError(null);

      const payload = {
        simulation_id: Number(selectedSimId),
        name: comparisonName.trim() || undefined,
        proposed_rules: proposedRules,
      };

      const res = await createPolicyComparison(payload);
      setComparisonSummary(res);
      setActiveTab('results');
      setPage(1);
      await loadComparisonResults(res.id);
    } catch (err) {
      setError(err.message || 'Comparison failed to execute.');
    } finally {
      setLoadingComparison(false);
    }
  };

  // Rule management functions for proposed rules
  const handleToggleRule = (index) => {
    const updated = [...proposedRules];
    updated[index].enabled = !updated[index].enabled;
    setProposedRules(updated);
  };

  const handleDeleteRule = (index) => {
    const updated = proposedRules.filter((_, i) => i !== index);
    setProposedRules(updated);
  };

  const handleMoveRule = (index, direction) => {
    const target = direction === 'up' ? index - 1 : index + 1;
    if (target < 0 || target >= proposedRules.length) return;

    const updated = [...proposedRules];
    const tempP = updated[index].priority;
    updated[index].priority = updated[target].priority;
    updated[target].priority = tempP;

    // Swap positions
    const tempObj = updated[index];
    updated[index] = updated[target];
    updated[target] = tempObj;

    setProposedRules(updated);
  };

  const handleSaveModalRule = (ruleData) => {
    if (editingRuleIndex !== null) {
      const updated = [...proposedRules];
      updated[editingRuleIndex] = ruleData;
      setProposedRules(updated);
    } else {
      setProposedRules([...proposedRules, ruleData]);
    }
    setIsRuleModalOpen(false);
    setRuleToEdit(null);
    setEditingRuleIndex(null);
  };

  const getChangeBadge = (ctype) => {
    switch (ctype) {
      case 'ALLOW_TO_DENY':
        return 'bg-red-950/80 text-red-400 border-red-700/60 font-bold';
      case 'DENY_TO_ALLOW':
        return 'bg-emerald-950/80 text-emerald-400 border-emerald-700/60 font-bold';
      case 'SAME_DECISION_DIFFERENT_RULE':
        return 'bg-purple-950/80 text-purple-400 border-purple-700/60';
      default:
        return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <span>Before-and-After Policy Impact Comparison</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Simulate policy changes against historical traffic datasets to identify permitted and blocked traffic diffs before deployment.
          </p>
        </div>

        {/* View Switcher if results are ready */}
        {comparisonSummary && (
          <div className="flex bg-slate-900 p-1 rounded-lg border border-slate-800 self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('config')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                activeTab === 'config' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Configure Policy
            </button>
            <button
              onClick={() => setActiveTab('results')}
              className={`px-3 py-1.5 text-xs font-semibold rounded-md transition-all ${
                activeTab === 'results' ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Comparison Report
            </button>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center space-x-2">
          <AlertTriangle className="w-5 h-5 text-red-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Simulation Selector Bar */}
      <div className="p-5 rounded-xl bg-[#111726] border border-slate-800 shadow-lg flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-1/2 space-y-1">
          <label className="text-xs font-medium text-slate-300">Base Historical Simulation Dataset</label>
          <select
            value={selectedSimId}
            onChange={(e) => setSelectedSimId(e.target.value)}
            disabled={loadingSims}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
          >
            {simulations.map((s) => (
              <option key={s.id} value={s.id}>
                #{s.id} {s.name} ({s.total_records} records, {s.allowed_records} allowed, {s.denied_records} denied)
              </option>
            ))}
          </select>
        </div>

        <div className="w-full md:w-1/2 space-y-1">
          <label className="text-xs font-medium text-slate-300">Proposed Comparison Name</label>
          <input
            type="text"
            value={comparisonName}
            onChange={(e) => setComparisonName(e.target.value)}
            placeholder="e.g. Test Strict Inbound Policy"
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Tab 1: Proposed Policy Rule Editor */}
      {activeTab === 'config' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-200">
                Proposed Policy Configuration ({proposedRules.length} rules)
              </h3>
              <p className="text-xs text-slate-400">
                Edit, add, disable, or reorder rules to model the proposed firewall changes.
              </p>
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={() => {
                  setEditingRuleIndex(null);
                  setRuleToEdit(null);
                  setIsRuleModalOpen(true);
                }}
                className="px-3.5 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg flex items-center space-x-1.5"
              >
                <Plus className="w-4 h-4 text-cyan-400" />
                <span>Add Proposed Rule</span>
              </button>

              <button
                onClick={handleRunComparison}
                disabled={loadingComparison || proposedRules.length === 0}
                className="px-5 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg flex items-center space-x-2 shadow-[0_0_15px_rgba(6,182,212,0.3)] disabled:opacity-50"
              >
                {loadingComparison ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Evaluating Diff...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-slate-950" />
                    <span>Run Policy Comparison</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Rules Table */}
          <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 text-center">Priority</th>
                  <th className="py-2.5 px-4">Rule Name</th>
                  <th className="py-2.5 px-3">Proto</th>
                  <th className="py-2.5 px-3">Source IP</th>
                  <th className="py-2.5 px-3">Destination IP</th>
                  <th className="py-2.5 px-3">Port</th>
                  <th className="py-2.5 px-3">Action</th>
                  <th className="py-2.5 px-3 text-center">Enabled</th>
                  <th className="py-2.5 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {proposedRules.map((rule, idx) => (
                  <tr
                    key={idx}
                    className={`hover:bg-slate-900/40 transition-colors ${!rule.enabled ? 'opacity-40 bg-slate-950/40' : ''}`}
                  >
                    <td className="py-2.5 px-3 text-center font-bold text-cyan-400">#{rule.priority}</td>
                    <td className="py-2.5 px-4 font-sans font-medium text-slate-200">{rule.name}</td>
                    <td className="py-2.5 px-3 text-slate-300">{rule.protocol}</td>
                    <td className="py-2.5 px-3 text-slate-300">{rule.source_ip}</td>
                    <td className="py-2.5 px-3 text-slate-300">{rule.destination_ip}</td>
                    <td className="py-2.5 px-3 text-slate-300">{rule.destination_port}</td>
                    <td className="py-2.5 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        rule.action === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                      }`}>
                        {rule.action}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <button
                        onClick={() => handleToggleRule(idx)}
                        className={`text-[11px] font-bold px-2 py-0.5 rounded ${
                          rule.enabled ? 'text-emerald-400 bg-emerald-950/60' : 'text-slate-500 bg-slate-800'
                        }`}
                      >
                        {rule.enabled ? 'Yes' : 'No'}
                      </button>
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-1">
                        <button
                          onClick={() => handleMoveRule(idx, 'up')}
                          disabled={idx === 0}
                          className="p-1 text-slate-400 hover:text-cyan-400 disabled:opacity-20"
                        >
                          <ArrowUp className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleMoveRule(idx, 'down')}
                          disabled={idx === proposedRules.length - 1}
                          className="p-1 text-slate-400 hover:text-cyan-400 disabled:opacity-20"
                        >
                          <ArrowDown className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            setEditingRuleIndex(idx);
                            setRuleToEdit(rule);
                            setIsRuleModalOpen(true);
                          }}
                          className="p-1 text-slate-400 hover:text-slate-200"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => handleDeleteRule(idx)}
                          className="p-1 text-slate-400 hover:text-red-400"
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
        </div>
      )}

      {/* Tab 2: Comparison Results Report */}
      {activeTab === 'results' && comparisonSummary && (
        <div className="space-y-6">
          {/* Export Header */}
          <div className="flex items-center justify-between">
            <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
              <GitCompare className="w-5 h-5 text-cyan-400" />
              <span>Comparison Report: {comparisonSummary.name}</span>
            </h3>

            <a
              href={getExportComparisonCsvUrl(comparisonSummary.id)}
              download
              className="px-3.5 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg flex items-center space-x-1.5 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
            >
              <Download className="w-4 h-4" />
              <span>Export Comparison CSV</span>
            </a>
          </div>

          {/* Decision Comparison KPI Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
            <div className="p-3.5 rounded-xl bg-[#111726] border border-slate-800">
              <span className="text-[11px] text-slate-400">Total Records</span>
              <p className="text-xl font-bold font-mono text-slate-100 mt-1">{comparisonSummary.total_records}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#111726] border border-cyan-900/40">
              <span className="text-[11px] text-cyan-400 font-bold">Decisions Changed</span>
              <p className="text-xl font-bold font-mono text-cyan-400 mt-1">{comparisonSummary.changed_decisions}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#111726] border border-red-900/40">
              <span className="text-[11px] text-red-400">ALLOW &rarr; DENY</span>
              <p className="text-xl font-bold font-mono text-red-400 mt-1">{comparisonSummary.allow_to_deny}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#111726] border border-emerald-900/40">
              <span className="text-[11px] text-emerald-400">DENY &rarr; ALLOW</span>
              <p className="text-xl font-bold font-mono text-emerald-400 mt-1">{comparisonSummary.deny_to_allow}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#111726] border border-slate-800">
              <span className="text-[11px] text-slate-400">Original ALLOW</span>
              <p className="text-xl font-bold font-mono text-slate-200 mt-1">{comparisonSummary.original_allowed}</p>
            </div>

            <div className="p-3.5 rounded-xl bg-[#111726] border border-slate-800">
              <span className="text-[11px] text-emerald-400">Proposed ALLOW</span>
              <p className="text-xl font-bold font-mono text-emerald-300 mt-1">{comparisonSummary.proposed_allowed}</p>
            </div>
          </div>

          {/* Filter Toolbar */}
          <div className="p-4 rounded-xl bg-[#111726] border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search record ID or IPs..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <div className="flex items-center space-x-3 w-full md:w-auto">
              <select
                value={changeTypeFilter}
                onChange={(e) => {
                  setChangeTypeFilter(e.target.value);
                  setPage(1);
                }}
                className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
              >
                <option value="">All Records</option>
                <option value="CHANGED_ONLY">Changed Decisions Only</option>
                <option value="ALLOW_TO_DENY">ALLOW to DENY Only</option>
                <option value="DENY_TO_ALLOW">DENY to ALLOW Only</option>
                <option value="SAME_DECISION_DIFFERENT_RULE">Rule Shift (Same Decision)</option>
                <option value="UNCHANGED">Unchanged Only</option>
              </select>
            </div>
          </div>

          {/* Comparison Records Table */}
          {loadingComparison ? (
            <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-2">
              <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
              <span className="text-xs font-mono">Filtering comparison records...</span>
            </div>
          ) : (
            <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Record ID</th>
                    <th className="py-2.5 px-3">Traffic Space</th>
                    <th className="py-2.5 px-3">Original Decision</th>
                    <th className="py-2.5 px-3">Proposed Decision</th>
                    <th className="py-2.5 px-3">Impact Classification</th>
                    <th className="py-2.5 px-4">Evaluation Diff Explanation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {comparisonDetail?.records?.items.map((r) => (
                    <tr key={r.id} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 text-cyan-400 font-semibold">{r.record_id}</td>
                      <td className="py-2.5 px-3 text-slate-300">
                        {r.source_ip} &rarr; {r.destination_ip} ({r.protocol} {r.destination_port ? `:${r.destination_port}` : ''})
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.original_decision === 'ALLOW' ? 'text-emerald-400 bg-emerald-950/60' : 'text-red-400 bg-red-950/60'
                        }`}>
                          {r.original_decision}
                        </span>
                        <span className="block text-[10px] text-slate-500 font-sans mt-0.5 truncate max-w-[120px]">
                          {r.original_rule_name || 'Default DENY'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          r.proposed_decision === 'ALLOW' ? 'text-emerald-400 bg-emerald-950/60' : 'text-red-400 bg-red-950/60'
                        }`}>
                          {r.proposed_decision}
                        </span>
                        <span className="block text-[10px] text-slate-500 font-sans mt-0.5 truncate max-w-[120px]">
                          {r.proposed_rule_name || 'Default DENY'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] border ${getChangeBadge(r.change_type)}`}>
                          {r.change_type.replace(/_/g, ' ')}
                        </span>
                      </td>
                      <td className="py-2.5 px-4 font-sans text-slate-300 leading-relaxed text-[11px] max-w-sm">
                        {r.explanation}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination */}
              <div className="px-4 py-3 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <div>
                  Showing {comparisonDetail?.records?.items?.length || 0} of{' '}
                  <span className="font-bold text-slate-200">{comparisonDetail?.records?.total || 0}</span> records
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page <= 1}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-30"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-mono text-slate-300">
                    Page {page} of {comparisonDetail?.records?.total_pages || 1}
                  </span>
                  <button
                    onClick={() => setPage(Math.min(comparisonDetail?.records?.total_pages || 1, page + 1))}
                    disabled={page >= (comparisonDetail?.records?.total_pages || 1)}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-30"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Rule Add/Edit Modal */}
      <RuleModal
        isOpen={isRuleModalOpen}
        onClose={() => {
          setIsRuleModalOpen(false);
          setRuleToEdit(null);
          setEditingRuleIndex(null);
        }}
        onSave={handleSaveModalRule}
        ruleToEdit={ruleToEdit}
        existingRulesCount={proposedRules.length}
      />
    </div>
  );
}
