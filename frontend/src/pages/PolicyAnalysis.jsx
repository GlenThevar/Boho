import React, { useState, useEffect } from 'react';
import {
  runPolicyAnalysis,
  getLatestPolicyAnalysis,
  getPolicyAnalyses,
  dismissFinding,
  restoreFinding,
} from '../api';
import FindingDetailModal from '../components/FindingDetailModal';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  RefreshCw,
  Search,
  Filter,
  Eye,
  CheckCircle2,
  XCircle,
  EyeOff,
  RotateCcw,
  Layers,
  Sparkles,
  Info
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Cell
} from 'recharts';

export default function PolicyAnalysis({ onNavigateToRules }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('ACTIVE'); // 'ACTIVE', 'DISMISSED', 'ALL'

  // Modal
  const [selectedFinding, setSelectedFinding] = useState(null);

  const loadLatest = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getLatestPolicyAnalysis();
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load policy analysis.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLatest();
  }, []);

  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      setError(null);
      await runPolicyAnalysis();
      await loadLatest();
    } catch (err) {
      setError(err.message || 'Policy analysis execution failed.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleDismiss = async (findingId, reason) => {
    const updated = await dismissFinding(findingId, reason);
    setData((prev) => ({
      ...prev,
      findings: prev.findings.map((f) => (f.id === findingId ? updated : f)),
    }));
    if (selectedFinding && selectedFinding.id === findingId) {
      setSelectedFinding(updated);
    }
  };

  const handleRestore = async (findingId) => {
    const updated = await restoreFinding(findingId);
    setData((prev) => ({
      ...prev,
      findings: prev.findings.map((f) => (f.id === findingId ? updated : f)),
    }));
    if (selectedFinding && selectedFinding.id === findingId) {
      setSelectedFinding(updated);
    }
  };

  const analysis = data?.analysis;
  const findings = data?.findings || [];

  // Filtered findings
  const filteredFindings = findings.filter((f) => {
    if (severityFilter && f.severity !== severityFilter) return false;
    if (categoryFilter && f.category !== categoryFilter) return false;
    if (typeFilter && f.finding_type !== typeFilter) return false;
    if (statusFilter === 'ACTIVE' && f.is_dismissed) return false;
    if (statusFilter === 'DISMISSED' && !f.is_dismissed) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = f.title.toLowerCase().includes(q);
      const matchRule = f.rule_name.toLowerCase().includes(q);
      const matchExp = f.explanation.toLowerCase().includes(q);
      const matchCat = f.category.toLowerCase().includes(q);
      if (!matchTitle && !matchRule && !matchExp && !matchCat) return false;
    }
    return true;
  });

  // Chart data
  const severityChartData = [
    { name: 'Critical', count: analysis?.severity_distribution?.Critical || 0, color: '#ef4444' },
    { name: 'High', count: analysis?.severity_distribution?.High || 0, color: '#f97316' },
    { name: 'Medium', count: analysis?.severity_distribution?.Medium || 0, color: '#f59e0b' },
    { name: 'Low', count: analysis?.severity_distribution?.Low || 0, color: '#06b6d4' },
  ];

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

  const getTypeBadge = (type) => {
    switch (type) {
      case 'SHADOWING':
        return 'bg-purple-950/70 text-purple-400 border-purple-800/60';
      case 'REDUNDANCY':
        return 'bg-blue-950/70 text-blue-400 border-blue-800/60';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
              <span>Firewall Policy Analysis & Security Audit</span>
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 font-mono">
              Stage 2
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Detects fully shadowed rules, redundant policies, and overly permissive security risks using deterministic formal checks.
          </p>
        </div>

        <button
          onClick={handleRunAnalysis}
          disabled={isAnalyzing}
          className="px-4 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg flex items-center space-x-2 shadow-[0_0_15px_rgba(6,182,212,0.3)] disabled:opacity-50 self-start sm:self-auto"
        >
          {isAnalyzing ? (
            <>
              <RefreshCw className="w-4 h-4 animate-spin" />
              <span>Analyzing Rules...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-4 h-4" />
              <span>Run Policy Analysis</span>
            </>
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadLatest}
            className="px-3 py-1 bg-red-900/60 hover:bg-red-800 rounded text-white text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      )}

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Analyzed */}
        <div className="p-5 rounded-xl bg-[#111726] border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Enabled Rules Analyzed</span>
            <Layers className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-slate-100 mt-2">
            {analysis?.rules_analyzed_count || 0}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">Active policies in evaluation order</p>
        </div>

        {/* Fully Shadowed */}
        <div className="p-5 rounded-xl bg-[#111726] border border-purple-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-purple-400">Fully Shadowed Rules</span>
            <ShieldAlert className="w-4 h-4 text-purple-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-purple-400 mt-2">
            {analysis?.shadowed_count || 0}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">Unreachable rules blocked by earlier rules</p>
        </div>

        {/* Confirmed Redundant */}
        <div className="p-5 rounded-xl bg-[#111726] border border-blue-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-blue-400">Confirmed Redundant</span>
            <RotateCcw className="w-4 h-4 text-blue-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-blue-400 mt-2">
            {analysis?.redundant_count || 0}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">Removing causes zero decision change</p>
        </div>

        {/* Security Findings */}
        <div className="p-5 rounded-xl bg-[#111726] border border-red-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-red-400">Active Security Findings</span>
            <AlertTriangle className="w-4 h-4 text-red-400" />
          </div>
          <p className="text-2xl font-bold font-mono text-red-400 mt-2">
            {filteredFindings.filter((f) => !f.is_dismissed).length}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            {analysis?.severity_distribution?.Critical || 0} Critical, {analysis?.severity_distribution?.High || 0} High
          </p>
        </div>
      </div>

      {/* Visual Telemetry Chart & Overview */}
      {findings.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Severity Chart */}
          <div className="p-6 rounded-xl bg-[#111726] border border-slate-800 shadow-lg lg:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-slate-200">Security Severity Distribution</h3>
                <p className="text-xs text-slate-400">Active findings categorized by risk severity</p>
              </div>
            </div>

            <div className="h-56 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={severityChartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <RechartsTooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#f1f5f9', fontSize: '12px' }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {severityChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Quick Category Summary */}
          <div className="p-6 rounded-xl bg-[#111726] border border-slate-800 shadow-lg space-y-3">
            <h3 className="text-sm font-semibold text-slate-200">Finding Categories</h3>
            <p className="text-xs text-slate-400 mb-2">Breakdown by policy inspection focus</p>

            <div className="space-y-2">
              {Object.entries(analysis?.category_distribution || {}).map(([cat, count]) => (
                <div key={cat} className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                  <span className="text-slate-300 font-medium">{cat}</span>
                  <span className="font-mono font-bold text-cyan-400 px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800/60">
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Findings Table & Toolbar */}
      <div className="space-y-4">
        {/* Filters Toolbar */}
        <div className="p-4 rounded-xl bg-[#111726] border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          {/* Search */}
          <div className="relative w-full md:w-80">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search findings, rules, categories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          {/* Filter Dropdowns */}
          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Severity */}
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Severities</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>

            {/* Type */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Finding Types</option>
              <option value="SECURITY_RISK">Security Risks</option>
              <option value="SHADOWING">Shadowing</option>
              <option value="REDUNDANCY">Redundancy</option>
            </select>

            {/* Status (Active / Dismissed) */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
            >
              <option value="ACTIVE">Active Findings</option>
              <option value="DISMISSED">Dismissed Only</option>
              <option value="ALL">All Statuses</option>
            </select>
          </div>
        </div>

        {/* Table */}
        {loading ? (
          <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
            <span className="text-xs font-mono">Running policy analysis checks...</span>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="p-12 rounded-xl bg-[#111726] border border-slate-800 text-center space-y-3">
            <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto" />
            <h3 className="text-base font-bold text-slate-200">Zero Findings Match Filters</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto">
              No rule shadowing, redundancies, or security risks were identified under the current filter criteria.
            </p>
          </div>
        ) : (
          <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-3 px-3 w-24">Severity</th>
                  <th className="py-3 px-3 w-28">Type</th>
                  <th className="py-3 px-4">Finding Title</th>
                  <th className="py-3 px-4">Affected Rule</th>
                  <th className="py-3 px-3">Category</th>
                  <th className="py-3 px-3 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {filteredFindings.map((f) => (
                  <tr
                    key={f.id}
                    className={`hover:bg-slate-900/50 transition-colors ${f.is_dismissed ? 'opacity-40 bg-slate-950/40' : ''}`}
                  >
                    {/* Severity */}
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getSeverityBadge(f.severity)}`}>
                        {f.severity}
                      </span>
                    </td>

                    {/* Type */}
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${getTypeBadge(f.finding_type)}`}>
                        {f.finding_type.replace('_', ' ')}
                      </span>
                    </td>

                    {/* Title */}
                    <td className="py-3 px-4 font-sans font-medium text-slate-200">
                      {f.title}
                    </td>

                    {/* Affected Rule */}
                    <td className="py-3 px-4 font-sans">
                      <span className="text-cyan-400 font-mono font-bold mr-1">#{f.rule_priority}</span>
                      <span className="text-slate-300 truncate">{f.rule_name}</span>
                    </td>

                    {/* Category */}
                    <td className="py-3 px-3 text-slate-400 font-sans">{f.category}</td>

                    {/* Status */}
                    <td className="py-3 px-3 text-center">
                      {f.is_dismissed ? (
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 text-[10px] border border-slate-700">
                          Dismissed
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 text-[10px] border border-emerald-800/60">
                          Active
                        </span>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => setSelectedFinding(f)}
                        className="px-2.5 py-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-800/80 rounded"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Finding Detail Modal */}
      <FindingDetailModal
        finding={selectedFinding}
        onClose={() => setSelectedFinding(null)}
        onDismiss={handleDismiss}
        onRestore={handleRestore}
      />
    </div>
  );
}
