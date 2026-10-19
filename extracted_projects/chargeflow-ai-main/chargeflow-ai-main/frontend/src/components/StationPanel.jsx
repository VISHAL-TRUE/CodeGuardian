import { Battery, Users, Gauge, IndianRupee } from 'lucide-react';

function UtilBar({ pct, status }) {
  const colors = {
    green: 'bg-green-500',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
  };
  return (
    <div className="w-full h-2 bg-[#1a1f35] rounded-full overflow-hidden">
      <div
        className={`h-full rounded-full transition-all duration-700 ${colors[status] || 'bg-gray-500'}`}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  );
}

export default function StationPanel({ stations }) {
  if (!stations?.length) return null;

  return (
    <div className="space-y-3 max-h-[520px] overflow-y-auto pr-1">
      <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider px-1">Stations</h3>
      {stations.map((s) => {
        const statusBorder = s.status === 'red' ? 'border-red-500/30' : s.status === 'yellow' ? 'border-yellow-500/20' : 'border-[#2a3050]';
        const statusDot = s.status === 'red' ? 'bg-red-500' : s.status === 'yellow' ? 'bg-yellow-500' : 'bg-green-500';

        return (
          <div
            key={s.station_id}
            className={`rounded-xl border ${statusBorder} p-4 transition-all duration-300 hover:border-blue-500/30 ${s.status === 'red' ? 'pulse-red' : ''}`}
            style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className={`w-2.5 h-2.5 rounded-full ${statusDot}`} />
                <span className="text-sm font-semibold text-white">{s.name}</span>
              </div>
              <span className="text-[10px] text-gray-500 font-mono">{s.station_id}</span>
            </div>

            {/* Utilisation bar */}
            <div className="mb-3">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500">Utilisation</span>
                <span className={`font-semibold ${s.status === 'red' ? 'text-red-400' : s.status === 'yellow' ? 'text-yellow-400' : 'text-green-400'}`}>
                  {s.utilisation_pct}%
                </span>
              </div>
              <UtilBar pct={s.utilisation_pct} status={s.status} />
            </div>

            {/* Grid load */}
            <div className="mb-3">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500">Grid Load</span>
                <span className="text-gray-300">{s.current_load_kw} / {s.grid_limit_kw} kW</span>
              </div>
              <UtilBar pct={(s.current_load_kw / s.grid_limit_kw) * 100} status={s.current_load_kw / s.grid_limit_kw > 0.8 ? 'red' : s.current_load_kw / s.grid_limit_kw > 0.5 ? 'yellow' : 'green'} />
            </div>

            {/* Stats grid */}
            <div className="grid grid-cols-3 gap-2 text-xs">
              <div className="flex items-center gap-1.5 text-gray-400">
                <Battery size={12} />
                <span>{s.available_chargers}/{s.total_chargers}</span>
              </div>
              <div className="flex items-center gap-1.5 text-gray-400">
                <Users size={12} />
                <span>Q: {s.queue_length}</span>
              </div>
              {s.pricing && (
                <div className={`flex items-center gap-1.5 font-medium ${s.pricing.incentive === 'DISCOUNT' ? 'text-green-400' : s.pricing.incentive === 'SURCHARGE' ? 'text-red-400' : 'text-gray-400'}`}>
                  <IndianRupee size={12} />
                  <span>{s.pricing.final_price}/kWh</span>
                </div>
              )}
            </div>

            {/* Prediction */}
            {s.prediction?.congestion_risk > 0.3 && (
              <div className="mt-3 px-3 py-2 bg-yellow-500/10 border border-yellow-500/20 rounded-lg text-xs text-yellow-300">
                Predicted congestion risk: {(s.prediction.congestion_risk * 100).toFixed(0)}%
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
