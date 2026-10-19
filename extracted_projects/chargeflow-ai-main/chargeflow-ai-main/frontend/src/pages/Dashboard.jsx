import { useState } from 'react';
import { Activity, Zap, Clock, Gauge, AlertTriangle, TrendingDown, TrendingUp, BarChart3 } from 'lucide-react';
import SimulationControls from '../components/SimulationControls';
import MapView from '../components/MapView';
import StationPanel from '../components/StationPanel';
import DemandChart from '../components/DemandChart';
import GridLoadChart from '../components/GridLoadChart';
import QueuePanel from '../components/QueuePanel';

function KPICard({ icon: Icon, label, value, unit, color, glow }) {
  return (
    <div
      className={`relative rounded-xl border border-[#2a3050] p-4 transition-all duration-300 hover:border-${color}-500/40 overflow-hidden`}
      style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}
    >
      {glow && <div className={`absolute inset-0 bg-${color}-500/5 rounded-xl`} />}
      <div className="relative flex items-center gap-3">
        <div className={`w-10 h-10 rounded-lg bg-${color}-500/15 flex items-center justify-center`}>
          <Icon size={20} className={`text-${color}-400`} />
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wider">{label}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-white">{value}</span>
            {unit && <span className="text-xs text-gray-500">{unit}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

function ComparisonTable({ baseline, optimised }) {
  if (!baseline || !optimised) return null;

  const rows = [
    { label: 'Avg Wait Time', bVal: `${baseline.avg_wait_min} min`, oVal: `${optimised.avg_wait_min} min`, better: optimised.avg_wait_min < baseline.avg_wait_min },
    { label: 'Avg Queue Length', bVal: baseline.avg_queue_length, oVal: optimised.avg_queue_length, better: optimised.avg_queue_length < baseline.avg_queue_length },
    { label: 'Peak Grid Utilisation', bVal: `${baseline.peak_grid_utilisation}%`, oVal: `${optimised.peak_grid_utilisation}%`, better: optimised.peak_grid_utilisation < baseline.peak_grid_utilisation },
    { label: 'Grid Overload Events', bVal: baseline.grid_overload_events, oVal: optimised.grid_overload_events, better: optimised.grid_overload_events < baseline.grid_overload_events },
    { label: 'Load Imbalance', bVal: `${baseline.load_imbalance}%`, oVal: `${optimised.load_imbalance}%`, better: optimised.load_imbalance < baseline.load_imbalance },
  ];

  return (
    <div className="animate-slide-up rounded-xl border border-[#2a3050] overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="px-5 py-4 border-b border-[#2a3050] flex items-center gap-2">
        <BarChart3 size={18} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-white">Before vs After — Performance Comparison</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#2a3050]">
              <th className="text-left px-5 py-3 text-gray-500 font-medium">Metric</th>
              <th className="text-center px-5 py-3 text-red-400 font-medium">Uncoordinated Baseline</th>
              <th className="text-center px-5 py-3 text-green-400 font-medium">ChargeFlow AI</th>
              <th className="text-center px-5 py-3 text-gray-500 font-medium">Impact</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-[#2a3050]/50 hover:bg-white/[0.02]">
                <td className="px-5 py-3 text-gray-300">{row.label}</td>
                <td className="px-5 py-3 text-center text-red-300 font-mono">{row.bVal}</td>
                <td className="px-5 py-3 text-center text-green-300 font-mono">{row.oVal}</td>
                <td className="px-5 py-3 text-center">
                  {row.better ? (
                    <span className="inline-flex items-center gap-1 text-green-400 text-xs font-medium bg-green-500/10 px-2 py-0.5 rounded-full">
                      <TrendingDown size={12} /> Improved
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-gray-500 text-xs">—</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Dashboard({ data, metrics, onSimulate, simLoading, onRefresh }) {
  const [optimizeResult, setOptimizeResult] = useState(null);

  if (!data || !metrics) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-12 h-12 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading dashboard…</p>
        </div>
      </div>
    );
  }

  const kpis = metrics.kpis || {};
  const stations = data.stations || [];
  const alerts = [];
  stations.forEach(s => {
    if (s.status === 'red') alerts.push({ type: 'danger', msg: `${s.name}: Load at ${s.utilisation_pct}% — CONGESTED` });
    else if (s.status === 'yellow' && s.utilisation_pct > 65) alerts.push({ type: 'warn', msg: `${s.name}: Load at ${s.utilisation_pct}% — Elevated` });
  });

  const handleOptimize = async () => {
    const result = await onSimulate('optimize');
    if (result) setOptimizeResult(result);
  };

  const handleReset = async () => {
    await onSimulate('reset');
    setOptimizeResult(null);
  };

  return (
    <main className="max-w-[1600px] mx-auto px-6 py-6 space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 animate-fade-in">
        <KPICard icon={Activity} label="Active EVs" value={kpis.active_evs || 0} color="blue" />
        <KPICard icon={Zap} label="Charging" value={kpis.charging_evs || 0} color="green" />
        <KPICard icon={Clock} label="Avg Wait" value={kpis.avg_wait_min || 0} unit="min" color="yellow" />
        <KPICard icon={Gauge} label="Grid Load" value={`${kpis.avg_grid_load_pct || 0}`} unit="%" color="cyan" glow={kpis.avg_grid_load_pct > 70} />
        <KPICard icon={AlertTriangle} label="Congested" value={kpis.congested_stations || 0} unit={`/ ${kpis.total_stations || 5}`} color="red" glow={kpis.congested_stations > 0} />
      </div>

      {/* Simulation Controls */}
      <SimulationControls
        scenario={metrics.scenario}
        isPeak={metrics.is_peak}
        isOptimised={metrics.is_optimised}
        onSimulate={onSimulate}
        onOptimize={handleOptimize}
        onReset={handleReset}
        simLoading={simLoading}
      />

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="space-y-2 animate-slide-up">
          {alerts.map((a, i) => (
            <div
              key={i}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${
                a.type === 'danger'
                  ? 'bg-red-500/10 border-red-500/20 text-red-300'
                  : 'bg-yellow-500/10 border-yellow-500/20 text-yellow-300'
              }`}
            >
              <AlertTriangle size={16} />
              <span className="text-sm">{a.msg}</span>
            </div>
          ))}
        </div>
      )}

      {/* Map + Stations */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <MapView stations={stations} />
        </div>
        <div>
          <StationPanel stations={stations} />
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <GridLoadChart stations={stations} />
        <QueuePanel stations={stations} />
      </div>

      {/* Before vs After Comparison */}
      {metrics.baseline_metrics && metrics.optimised_metrics && (
        <ComparisonTable baseline={metrics.baseline_metrics} optimised={metrics.optimised_metrics} />
      )}
      {optimizeResult?.comparison && optimizeResult?.baseline_metrics && optimizeResult?.optimised_metrics && !metrics.optimised_metrics && (
        <ComparisonTable baseline={optimizeResult.baseline_metrics} optimised={optimizeResult.optimised_metrics} />
      )}
    </main>
  );
}
