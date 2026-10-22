import React, { useState } from 'react';
import {
  downloadSampleCsvUrl,
  uploadAndValidateDataset,
  runSimulation,
} from '../api';
import {
  UploadCloud,
  Download,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Play,
  RefreshCw,
  XCircle,
  HelpCircle,
  Info
} from 'lucide-react';

export default function DatasetTesting({ onSimulationComplete }) {
  const [file, setFile] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState(null);
  const [fatalError, setFatalError] = useState(null);
  
  // Simulation launch state
  const [simulationName, setSimulationName] = useState('');
  const [isSimulating, setIsSimulating] = useState(false);
  const [simulationError, setSimulationError] = useState(null);

  const handleFileChange = async (e) => {
    const selectedFile = e.target.files[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setFatalError(null);
    setValidationResult(null);
    setSimulationError(null);
    setSimulationName(selectedFile.name.replace(/\.[^/.]+$/, '') + ' Simulation');

    // Auto-validate uploaded CSV
    try {
      setIsValidating(true);
      const res = await uploadAndValidateDataset(selectedFile);
      setValidationResult(res);
    } catch (err) {
      setFatalError(err.message || 'Fatal error parsing CSV dataset.');
    } finally {
      setIsValidating(false);
    }
  };

  const handleLaunchSimulation = async () => {
    if (!validationResult || !validationResult.preview_records) return;

    try {
      setIsSimulating(true);
      setSimulationError(null);

      // Extract all records to send to simulation engine
      const recordsToSimulate = validationResult.preview_records.map((r) => ({
        record_id: r.record_id,
        source_ip: r.source_ip,
        destination_ip: r.destination_ip,
        destination_port: r.destination_port === 'N/A' ? '' : r.destination_port,
        protocol: r.protocol,
      }));

      const payload = {
        simulation_name: simulationName.trim() || undefined,
        records: recordsToSimulate,
      };

      const result = await runSimulation(payload);
      onSimulationComplete(result.id);
    } catch (err) {
      setSimulationError(err.message || 'Simulation execution failed.');
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <span>Network Traffic Dataset Testing</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Upload CSV packet capture logs to test and simulate rule evaluations.
          </p>
        </div>

        <a
          href={downloadSampleCsvUrl}
          download="boho_traffic_sample.csv"
          className="px-3.5 py-2 text-xs font-semibold text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-800/80 rounded-lg flex items-center space-x-2 shrink-0 shadow-sm"
        >
          <Download className="w-4 h-4 text-cyan-400" />
          <span>Download Sample CSV</span>
        </a>
      </div>

      {/* Upload Zone */}
      <div className="p-8 rounded-2xl border-2 border-dashed border-slate-700 hover:border-cyan-500/60 bg-[#111726] transition-all text-center">
        <input
          type="file"
          id="csv-file-input"
          accept=".csv"
          onChange={handleFileChange}
          className="hidden"
        />
        <label
          htmlFor="csv-file-input"
          className="cursor-pointer flex flex-col items-center justify-center space-y-3"
        >
          <div className="w-14 h-14 rounded-full bg-cyan-950/80 border border-cyan-600/30 flex items-center justify-center text-cyan-400">
            <UploadCloud className="w-7 h-7" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-200">
              {file ? file.name : 'Select or drop a traffic CSV file'}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Required headers: <span className="font-mono text-cyan-400">source_ip, destination_ip, destination_port, protocol</span>
            </p>
          </div>
          <span className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-200 rounded-lg border border-slate-600">
            Browse Files
          </span>
        </label>
      </div>

      {/* Validation Status */}
      {isValidating && (
        <div className="p-8 text-center text-slate-400 flex flex-col items-center space-y-2">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span className="text-xs font-mono">Parsing and validating CSV records...</span>
        </div>
      )}

      {/* Fatal File Error */}
      {fatalError && (
        <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs flex items-start space-x-3">
          <XCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
          <div>
            <h4 className="font-bold text-red-200">Fatal File Error</h4>
            <p className="mt-1 leading-relaxed">{fatalError}</p>
          </div>
        </div>
      )}

      {/* Validation Results Summary */}
      {validationResult && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#111726] border border-slate-800">
              <span className="text-xs font-medium text-slate-400">Total Traffic Records</span>
              <p className="text-2xl font-bold font-mono text-slate-100 mt-1">
                {validationResult.total_records}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#111726] border border-emerald-900/40">
              <span className="text-xs font-medium text-emerald-400">Valid Records</span>
              <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                {validationResult.valid_count}
              </p>
            </div>

            <div className="p-4 rounded-xl bg-[#111726] border border-amber-900/40">
              <span className="text-xs font-medium text-amber-400">Malformed Records</span>
              <p className="text-2xl font-bold font-mono text-amber-400 mt-1">
                {validationResult.invalid_count}
              </p>
            </div>
          </div>

          {/* Individual Row Errors Warning */}
          {validationResult.validation_issues.length > 0 && (
            <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-800/60 space-y-3">
              <div className="flex items-center space-x-2 text-amber-400 font-semibold text-xs">
                <AlertTriangle className="w-4 h-4 shrink-0" />
                <span>
                  {validationResult.invalid_count} record(s) contain validation errors (will receive default DENY)
                </span>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1 text-xs font-mono text-slate-300">
                {validationResult.validation_issues.map((issue, idx) => (
                  <div key={idx} className="p-2 bg-slate-900/80 rounded border border-slate-800 flex items-start space-x-2">
                    <span className="text-amber-400 shrink-0 font-bold">Row {issue.row_number}:</span>
                    <span className="text-slate-400 shrink-0">[{issue.record_id}]</span>
                    <span className="text-red-300">{issue.errors.join('; ')}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Simulation Launcher Card */}
          <div className="p-6 rounded-xl bg-[#111726] border border-cyan-800/40 shadow-xl space-y-4">
            <h3 className="text-sm font-bold text-slate-100 flex items-center space-x-2">
              <Play className="w-4 h-4 text-cyan-400" />
              <span>Launch Firewall Simulation</span>
            </h3>

            <div className="flex flex-col sm:flex-row items-center gap-4">
              <div className="w-full sm:flex-1 space-y-1">
                <label className="text-xs font-medium text-slate-300">Simulation Name</label>
                <input
                  type="text"
                  value={simulationName}
                  onChange={(e) => setSimulationName(e.target.value)}
                  placeholder="e.g. Q4 Web Traffic Audit"
                  className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="w-full sm:w-auto pt-5">
                <button
                  onClick={handleLaunchSimulation}
                  disabled={isSimulating}
                  className="w-full sm:w-auto px-6 py-2.5 bg-cyan-400 hover:bg-cyan-300 text-slate-950 font-bold text-xs rounded-lg shadow-[0_0_20px_rgba(6,182,212,0.35)] flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  {isSimulating ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Simulating Rules...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 fill-slate-950" />
                      <span>Run Simulation</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {simulationError && (
              <p className="text-xs text-red-400 mt-2">{simulationError}</p>
            )}
          </div>

          {/* Dataset Preview Table */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold text-slate-200">
                Uploaded Records Preview ({validationResult.preview_records.length} shown)
              </h3>
              {validationResult.file_warning && (
                <span className="text-xs text-amber-400 font-medium">
                  {validationResult.file_warning}
                </span>
              )}
            </div>

            <div className="border border-slate-800 rounded-xl overflow-hidden bg-[#111726]">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Row</th>
                    <th className="py-2.5 px-3">Record ID</th>
                    <th className="py-2.5 px-3">Source IP</th>
                    <th className="py-2.5 px-3">Destination IP</th>
                    <th className="py-2.5 px-3">Port</th>
                    <th className="py-2.5 px-3">Protocol</th>
                    <th className="py-2.5 px-3">Validation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800 font-mono">
                  {validationResult.preview_records.map((rec) => (
                    <tr key={rec.row_number} className="hover:bg-slate-900/50">
                      <td className="py-2.5 px-3 text-slate-500">{rec.row_number}</td>
                      <td className="py-2.5 px-3 text-cyan-400 font-semibold">{rec.record_id}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rec.source_ip}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rec.destination_ip}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rec.destination_port || 'N/A'}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rec.protocol}</td>
                      <td className="py-2.5 px-3">
                        {rec.is_valid ? (
                          <span className="inline-flex items-center space-x-1 text-emerald-400 font-semibold text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Valid</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center space-x-1 text-amber-400 font-semibold text-[11px]" title={rec.errors.join('; ')}>
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>Malformed</span>
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
