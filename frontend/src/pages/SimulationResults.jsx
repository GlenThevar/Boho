import React, { useState, useEffect } from 'react';
import {
  getSimulationDetail,
  getExportSimulationCsvUrl,
} from '../api';
import RecordDetailModal from '../components/RecordDetailModal';
import SnapshotModal from '../components/SnapshotModal';
import {
  Download01Icon as Download,
  Camera01Icon as Camera,
  Search01Icon as Search,
  FilterIcon as Filter,
  CheckmarkCircle01Icon as CheckCircle2,
  Cancel01Icon as XCircle,
  EyeIcon as Eye,
  RefreshIcon as RefreshCw,
  ArrowLeft01Icon as ChevronLeft,
  ArrowRight01Icon as ChevronRight,
  Shield01Icon as Shield,
  ArrowRight01Icon as ArrowRight,
} from 'hugeicons-react';

export default function SimulationResults({ simulationId, onBackToHistory }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters & Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [decisionFilter, setDecisionFilter] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('');
  const [matchedRuleFilter, setMatchedRuleFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [isSnapshotOpen, setIsSnapshotOpen] = useState(false);

  const loadResults = async () => {
    if (!simulationId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await getSimulationDetail(simulationId, {
        page,
        page_size: pageSize,
        decision: decisionFilter,
        protocol: protocolFilter,
        matched_rule_id: matchedRuleFilter,
        search: searchQuery,
      });
      setData(res);
    } catch (err) {
      setError(err.message || 'Failed to load simulation results.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResults();
  }, [simulationId, page, decisionFilter, protocolFilter, matchedRuleFilter]);

  // Handle Search on Submit
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    loadResults();
  };

  if (!simulationId) {
    return (
      <div className="p-12 text-center text-slate-400 space-y-3">
        <Shield className="w-12 h-12 text-slate-600 mx-auto" />
        <h3 className="text-base font-bold text-slate-200">No Simulation Selected</h3>
        <p className="text-xs text-slate-500">Run a simulation from Dataset Testing or select one from Simulation History.</p>
        <button
          onClick={onBackToHistory}
          className="px-4 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg"
        >
          View Simulation History
        </button>
      </div>
    );
  }

  const sim = data?.simulation;
  const records = data?.records?.items || [];
  const totalPages = data?.records?.total_pages || 1;
  const totalFiltered = data?.records?.total || 0;
  const ruleSnapshots = data?.rules_snapshot || [];

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header bar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <h2 className="text-xl font-bold text-slate-100 font-mono">
              {sim ? sim.name : `Simulation #${simulationId}`}
            </h2>
            {sim && (
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono border border-slate-700">
                {new Date(sim.created_at).toLocaleString()}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Evaluated against preserved snapshot of {ruleSnapshots.length} firewall rules.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsSnapshotOpen(true)}
            className="px-3.5 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg flex items-center space-x-1.5 shadow-sm"
          >
            <Camera className="w-4 h-4 text-cyan-400" />
            <span>View Rule Snapshot</span>
          </button>

          <a
            href={getExportSimulationCsvUrl(simulationId)}
            download
            className="px-3.5 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg flex items-center space-x-1.5 shadow-[0_0_15px_rgba(6,182,212,0.3)]"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Decision Summary KPI Bar */}
      {sim && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-3.5 rounded-xl bg-[#111726] border border-slate-800">
            <span className="text-[11px] text-slate-400">Total Evaluated</span>
            <p className="text-xl font-bold font-mono text-slate-100 mt-0.5">{sim.total_records}</p>
          </div>
          <div className="p-3.5 rounded-xl bg-[#111726] border border-emerald-900/40">
            <span className="text-[11px] text-emerald-400">Allowed</span>
            <p className="text-xl font-bold font-mono text-emerald-400 mt-0.5">{sim.allowed_records}</p>
          </div>
          <div className="p-3.5 rounded-xl bg-[#111726] border border-red-900/40">
            <span className="text-[11px] text-red-400">Denied</span>
            <p className="text-xl font-bold font-mono text-red-400 mt-0.5">{sim.denied_records}</p>
          </div>
          <div className="p-3.5 rounded-xl bg-[#111726] border border-amber-900/40">
            <span className="text-[11px] text-amber-400">Invalid Records</span>
            <p className="text-xl font-bold font-mono text-amber-400 mt-0.5">{sim.invalid_records}</p>
          </div>
        </div>
      )}

      {/* Filters & Search Toolbar */}
      <div className="p-4 rounded-xl bg-[#111726] border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search record ID, IP, or rule..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
          />
        </form>

        {/* Filter Dropdowns */}
        <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
          {/* Decision */}
          <select
            value={decisionFilter}
            onChange={(e) => {
              setDecisionFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Decisions</option>
            <option value="ALLOW">ALLOWED Only</option>
            <option value="DENY">DENIED Only</option>
          </select>

          {/* Protocol */}
          <select
            value={protocolFilter}
            onChange={(e) => {
              setProtocolFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Protocols</option>
            <option value="TCP">TCP</option>
            <option value="UDP">UDP</option>
            <option value="ICMP">ICMP</option>
          </select>

          {/* Matched Rule */}
          <select
            value={matchedRuleFilter}
            onChange={(e) => {
              setMatchedRuleFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-cyan-500 max-w-xs truncate"
          >
            <option value="">All Matched Rules</option>
            <option value="default">Default Policy (No Rule)</option>
            {ruleSnapshots.map((r) => (
              <option key={r.id} value={r.original_rule_id || r.id}>
                #{r.priority} {r.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Table */}
      {loading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span className="text-xs font-mono">Filtering evaluation records...</span>
        </div>
      ) : records.length === 0 ? (
        <div className="p-12 rounded-xl bg-[#111726] border border-slate-800 text-center space-y-2">
          <Shield className="w-10 h-10 text-slate-600 mx-auto" />
          <p className="text-sm font-semibold text-slate-300">No Records Match Active Filters</p>
          <p className="text-xs text-slate-500">Try clearing your search query or filters.</p>
        </div>
      ) : (
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-3">Record ID</th>
                <th className="py-3 px-3">Source IP</th>
                <th className="py-3 px-3">Destination IP</th>
                <th className="py-3 px-2">Port</th>
                <th className="py-3 px-2">Proto</th>
                <th className="py-3 px-3">Decision</th>
                <th className="py-3 px-3">Matched Rule</th>
                <th className="py-3 px-4">Explanation Summary</th>
                <th className="py-3 px-3 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {records.map((rec) => (
                <tr key={rec.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-2.5 px-3 font-semibold text-cyan-400">{rec.record_id}</td>
                  <td className="py-2.5 px-3 text-slate-300">{rec.source_ip}</td>
                  <td className="py-2.5 px-3 text-slate-300">{rec.destination_ip}</td>
                  <td className="py-2.5 px-2 text-slate-300">{rec.destination_port || 'N/A'}</td>
                  <td className="py-2.5 px-2 text-slate-300">{rec.protocol}</td>
                  <td className="py-2.5 px-3">
                    <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                      rec.decision === 'ALLOW'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                        : 'bg-red-500/20 text-red-400 border border-red-500/40'
                    }`}>
                      {rec.decision}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-sans">
                    {rec.matched_rule_name ? (
                      <span className="text-slate-200 font-medium truncate block max-w-[150px]" title={rec.matched_rule_name}>
                        {rec.matched_rule_name}
                      </span>
                    ) : (
                      <span className="text-slate-500 italic text-[11px]">Default Policy</span>
                    )}
                  </td>
                  <td className="py-2.5 px-4 font-sans text-slate-400 truncate max-w-xs" title={rec.explanation}>
                    {rec.explanation}
                  </td>
                  <td className="py-2.5 px-3 text-right">
                    <button
                      onClick={() => setSelectedRecord(rec)}
                      className="px-2.5 py-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-800/80 rounded"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination bar */}
          <div className="px-4 py-3 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <div>
              Showing <span className="font-mono text-slate-200 font-bold">{records.length}</span> of{' '}
              <span className="font-mono text-slate-200 font-bold">{totalFiltered}</span> records
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
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page >= totalPages}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-30"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Inspect Record Modal */}
      <RecordDetailModal
        record={selectedRecord}
        onClose={() => setSelectedRecord(null)}
      />

      {/* Snapshot Modal */}
      <SnapshotModal
        isOpen={isSnapshotOpen}
        onClose={() => setIsSnapshotOpen(false)}
        rules={ruleSnapshots}
        simulationName={sim ? sim.name : ''}
      />
    </div>
  );
}
