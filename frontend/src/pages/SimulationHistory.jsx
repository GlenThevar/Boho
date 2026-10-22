import React, { useState, useEffect } from 'react';
import {
  getSimulations,
  deleteSimulation,
  getExportSimulationCsvUrl,
  getSimulationDetail,
} from '../api';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import SnapshotModal from '../components/SnapshotModal';
import {
  History,
  ArrowUpRight,
  Download,
  Trash2,
  Camera,
  RefreshCw,
  Shield,
  Layers
} from 'lucide-react';

export default function SimulationHistory({ onOpenSimulation }) {
  const [simulations, setSimulations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modals
  const [simToDelete, setSimToDelete] = useState(null);
  const [snapshotSim, setSnapshotSim] = useState(null);
  const [snapshotRules, setSnapshotRules] = useState([]);
  const [isSnapshotLoading, setIsSnapshotLoading] = useState(false);

  const loadSimulations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getSimulations();
      setSimulations(data);
    } catch (err) {
      setError(err.message || 'Failed to load historical simulations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSimulations();
  }, []);

  const handleDelete = async () => {
    if (!simToDelete) return;
    try {
      await deleteSimulation(simToDelete.id);
      setSimulations(simulations.filter((s) => s.id !== simToDelete.id));
      setSimToDelete(null);
    } catch (err) {
      alert(`Failed to delete simulation: ${err.message}`);
    }
  };

  const handleOpenSnapshot = async (sim) => {
    try {
      setIsSnapshotLoading(true);
      setSnapshotSim(sim);
      const detail = await getSimulationDetail(sim.id, { page_size: 1 });
      setSnapshotRules(detail.rules_snapshot || []);
    } catch (err) {
      alert(`Failed to load rule snapshot: ${err.message}`);
    } finally {
      setIsSnapshotLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <span>Simulation History</span>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
              {simulations.length} runs saved
            </span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Reopen previous simulation runs, view exact historical rule snapshots, and export reports.
          </p>
        </div>

        <button
          onClick={loadSimulations}
          className="px-3.5 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg flex items-center space-x-1.5 self-start sm:self-auto"
        >
          <RefreshCw className="w-3.5 h-3.5 text-cyan-400" />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span className="text-xs font-mono">Loading simulation records...</span>
        </div>
      ) : simulations.length === 0 ? (
        <div className="p-12 rounded-xl bg-[#111726] border border-slate-800 text-center space-y-3">
          <History className="w-12 h-12 text-slate-600 mx-auto" />
          <h3 className="text-base font-bold text-slate-200">No Simulations Found</h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Upload a traffic dataset in Dataset Testing to record your first simulation session.
          </p>
        </div>
      ) : (
        <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726] shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3 px-4 font-semibold">Simulation Name</th>
                <th className="py-3 px-4 font-semibold">Timestamp</th>
                <th className="py-3 px-3 font-semibold text-center">Total Records</th>
                <th className="py-3 px-3 font-semibold text-center">Allowed</th>
                <th className="py-3 px-3 font-semibold text-center">Denied</th>
                <th className="py-3 px-3 font-semibold text-center">Invalid</th>
                <th className="py-3 px-4 font-semibold text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 font-mono">
              {simulations.map((sim) => (
                <tr key={sim.id} className="hover:bg-slate-900/50 transition-colors">
                  <td className="py-3 px-4 font-sans font-medium text-slate-100">
                    <button
                      onClick={() => onOpenSimulation(sim.id)}
                      className="text-left hover:text-cyan-400 font-semibold transition-colors"
                    >
                      {sim.name}
                    </button>
                  </td>
                  <td className="py-3 px-4 text-slate-400 text-[11px]">
                    {new Date(sim.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-3 text-center text-slate-200">{sim.total_records}</td>
                  <td className="py-3 px-3 text-center">
                    <span className="text-emerald-400 font-bold">{sim.allowed_records}</span>
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="text-red-400 font-bold">{sim.denied_records}</span>
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span className="text-amber-400 font-bold">{sim.invalid_records}</span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => onOpenSimulation(sim.id)}
                        className="px-2.5 py-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-800/80 rounded flex items-center space-x-1"
                        title="Inspect full results"
                      >
                        <span>Open Results</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>

                      <button
                        onClick={() => handleOpenSnapshot(sim)}
                        className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
                        title="View Rule Snapshot"
                      >
                        <Camera className="w-4 h-4" />
                      </button>

                      <a
                        href={getExportSimulationCsvUrl(sim.id)}
                        download
                        className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded"
                        title="Export CSV"
                      >
                        <Download className="w-4 h-4" />
                      </a>

                      <button
                        onClick={() => setSimToDelete(sim)}
                        className="p-1 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded"
                        title="Delete Simulation"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Snapshot Modal */}
      <SnapshotModal
        isOpen={!!snapshotSim}
        onClose={() => setSnapshotSim(null)}
        rules={snapshotRules}
        simulationName={snapshotSim ? snapshotSim.name : ''}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={!!simToDelete}
        onClose={() => setSimToDelete(null)}
        onConfirm={handleDelete}
        title="Delete Simulation History"
        message="Are you sure you want to delete this historical simulation and all of its evaluated packet records? This action cannot be undone."
        itemName={simToDelete ? `Simulation #${simToDelete.id}: ${simToDelete.name}` : ''}
      />
    </div>
  );
}
