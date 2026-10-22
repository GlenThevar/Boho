import React, { useEffect, useState } from 'react';
import { getDashboardStats } from '../api';
import {
  ShieldCheck,
  ShieldAlert,
  Activity,
  Layers,
  AlertTriangle,
  ArrowUpRight,
  RefreshCw,
  Info
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend
} from 'recharts';

export default function Dashboard({ onNavigateToResults, onNavigateToRules, onNavigateToTesting }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getDashboardStats();
      setStats(data);
    } catch (err) {
      setError(err.message || 'Failed to load dashboard metrics.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3 text-cyan-400">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="text-xs font-mono tracking-wider uppercase text-slate-400">Loading Telemetry...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="p-4 bg-red-950/40 border border-red-800 rounded-xl text-red-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadStats}
            className="px-3 py-1 bg-red-900/60 hover:bg-red-800 rounded text-white text-xs font-semibold"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const pieData = stats && stats.total_records > 0
    ? [
        { name: 'Allowed', value: stats.allowed_records, color: '#10b981' },
        { name: 'Denied', value: stats.denied_records, color: '#ef4444' },
      ]
    : [];

  const barData = stats && stats.rule_match_stats
    ? stats.rule_match_stats.map((r) => ({
        name: r.rule_name.length > 20 ? r.rule_name.substring(0, 18) + '...' : r.rule_name,
        fullName: r.rule_name,
        matches: r.match_count,
        action: r.action,
        color: r.action === 'ALLOW' ? '#10b981' : '#ef4444',
      }))
    : [];

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      {/* Notice Banner */}
      <div className="p-4 rounded-xl bg-cyan-950/30 border border-cyan-800/40 flex items-start space-x-3.5 text-xs text-cyan-200">
        <Info className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <span className="font-semibold text-cyan-300 uppercase tracking-wider text-[11px]">
            Simulation Environment Notice
          </span>
          <p className="text-slate-300 leading-relaxed text-xs">
            All statistics below reflect offline simulated firewall decisions. The host operating system's kernel, iptables, and live network interfaces are completely untouched.
          </p>
        </div>
      </div>

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* Total Simulations */}
        <div className="p-5 rounded-xl bg-[#111726] border border-slate-800 shadow-lg relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Total Simulations</span>
            <Activity className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-slate-100">{stats?.total_simulations || 0}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Test sessions recorded</p>
        </div>

        {/* Total Records */}
        <div className="p-5 rounded-xl bg-[#111726] border border-slate-800 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-slate-400">Records Evaluated</span>
            <Layers className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-slate-100">{stats?.total_records || 0}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Packet traffic rows processed</p>
        </div>

        {/* Allowed Records */}
        <div className="p-5 rounded-xl bg-[#111726] border border-emerald-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-emerald-400">Allowed Traffic</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-emerald-400">{stats?.allowed_records || 0}</span>
            <span className="text-xs font-mono text-emerald-500 font-bold">({stats?.allowed_percentage || 0}%)</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Permitted by policies</p>
        </div>

        {/* Denied Records */}
        <div className="p-5 rounded-xl bg-[#111726] border border-red-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-red-400">Denied Traffic</span>
            <ShieldAlert className="w-4 h-4 text-red-400" />
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold font-mono text-red-400">{stats?.denied_records || 0}</span>
            <span className="text-xs font-mono text-red-500 font-bold">({stats?.denied_percentage || 0}%)</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Blocked by rules or default</p>
        </div>

        {/* Invalid Records */}
        <div className="p-5 rounded-xl bg-[#111726] border border-amber-900/40 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-amber-400">Invalid Records</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold font-mono text-amber-400">{stats?.invalid_records || 0}</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Malformed packet data</p>
        </div>
      </div>

      {/* Visual Charts */}
      {stats && stats.total_records > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pie Chart: Allowed vs Denied */}
          <div className="p-6 rounded-xl bg-[#111726] border border-slate-800 shadow-lg">
            <h3 className="text-sm font-semibold text-slate-200 mb-1">Decisions Distribution</h3>
            <p className="text-xs text-slate-400 mb-4">Proportion of allowed vs denied traffic</p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    itemStyle={{ color: '#f1f5f9', fontSize: '12px' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Bar Chart: Matches by Rule */}
          <div className="p-6 rounded-xl bg-[#111726] border border-slate-800 shadow-lg lg:col-span-2">
            <h3 className="text-sm font-semibold text-slate-200 mb-1">Top Matched Rules & Policies</h3>
            <p className="text-xs text-slate-400 mb-4">Traffic evaluation count per rule</p>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barData} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis
                    dataKey="name"
                    stroke="#64748b"
                    fontSize={10}
                    angle={-20}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis stroke="#64748b" fontSize={11} allowDecimals={false} />
                  <RechartsTooltip
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-slate-900 border border-slate-700 p-2.5 rounded-lg shadow-xl text-xs">
                            <p className="font-semibold text-slate-100">{data.fullName}</p>
                            <p className="text-slate-400 mt-1">
                              Action: <span className={data.action === 'ALLOW' ? 'text-emerald-400 font-bold' : 'text-red-400 font-bold'}>{data.action}</span>
                            </p>
                            <p className="text-cyan-400 font-mono mt-0.5">Matched Records: {data.matches}</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="matches" fill="#06b6d4" radius={[4, 4, 0, 0]}>
                    {barData.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.color} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="p-10 rounded-2xl bg-[#111726] border border-slate-800 text-center space-y-4">
          <div className="w-14 h-14 rounded-full bg-cyan-950/60 border border-cyan-800/40 text-cyan-400 mx-auto flex items-center justify-center">
            <Activity className="w-7 h-7" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-100">No Simulations Performed Yet</h3>
            <p className="text-xs text-slate-400 max-w-md mx-auto mt-1">
              Configure your firewall rules and upload a network traffic dataset to simulate packet decisions.
            </p>
          </div>
          <div className="flex justify-center space-x-3 pt-2">
            <button
              onClick={onNavigateToRules}
              className="px-4 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700"
            >
              Configure Rules
            </button>
            <button
              onClick={onNavigateToTesting}
              className="px-4 py-2 text-xs font-bold text-slate-950 bg-cyan-400 hover:bg-cyan-300 rounded-lg shadow-[0_0_15px_rgba(6,182,212,0.25)]"
            >
              Upload & Test Dataset
            </button>
          </div>
        </div>
      )}

      {/* Recent Simulation History Table */}
      {stats && stats.recent_simulations && stats.recent_simulations.length > 0 && (
        <div className="p-6 rounded-xl bg-[#111726] border border-slate-800 shadow-lg space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-200">Recent Simulation Activity</h3>
              <p className="text-xs text-slate-400">Latest policy simulation runs</p>
            </div>
          </div>

          <div className="border border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4 font-semibold">Simulation Name</th>
                  <th className="py-2.5 px-4 font-semibold">Timestamp</th>
                  <th className="py-2.5 px-4 font-semibold">Records</th>
                  <th className="py-2.5 px-4 font-semibold">Allowed</th>
                  <th className="py-2.5 px-4 font-semibold">Denied</th>
                  <th className="py-2.5 px-4 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {stats.recent_simulations.map((sim) => (
                  <tr key={sim.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="py-3 px-4 font-sans font-medium text-slate-200">{sim.name}</td>
                    <td className="py-3 px-4 text-slate-400 text-[11px]">
                      {new Date(sim.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-4 text-slate-300">{sim.total_records}</td>
                    <td className="py-3 px-4">
                      <span className="text-emerald-400 font-bold">{sim.allowed_records}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="text-red-400 font-bold">{sim.denied_records}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onNavigateToResults(sim.id)}
                        className="inline-flex items-center space-x-1 text-xs text-cyan-400 hover:text-cyan-300 font-semibold"
                      >
                        <span>View Results</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
