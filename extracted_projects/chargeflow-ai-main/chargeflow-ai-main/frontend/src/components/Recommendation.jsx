import { CheckCircle, Star } from 'lucide-react';

export default function Recommendation({ result }) {
  if (!result) return null;

  const rec = result.recommended;
  const alts = result.alternatives || [];

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Recommended */}
      {rec && (
        <div className="rounded-xl border-2 border-green-500/30 p-5 relative overflow-hidden" style={{ background: 'linear-gradient(135deg, rgba(16,185,129,0.08) 0%, #111827 100%)' }}>
          <div className="absolute top-3 right-3 flex items-center gap-1 bg-green-500/20 text-green-400 text-xs font-semibold px-2 py-1 rounded-full">
            <Star size={12} /> RECOMMENDED
          </div>
          <div className="flex items-center gap-2 mb-3">
            <CheckCircle size={20} className="text-green-400" />
            <h4 className="text-lg font-bold text-white">{rec.station_name}</h4>
            <span className="text-xs text-gray-500 font-mono">{rec.station_id}</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
            <div>
              <p className="text-xs text-gray-500">Distance</p>
              <p className="text-sm font-semibold text-white">{rec.distance_km} km</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Wait</p>
              <p className="text-sm font-semibold text-white">{rec.pricing?.estimated_wait_min || 0} min</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Price</p>
              <p className={`text-sm font-semibold ${rec.pricing?.incentive === 'DISCOUNT' ? 'text-green-400' : 'text-white'}`}>
                ₹{rec.pricing?.final_price || 16}/kWh
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Score</p>
              <p className="text-sm font-bold text-blue-400">{rec.final_score}</p>
            </div>
          </div>

          {/* Score breakdown */}
          <div className="bg-black/20 rounded-lg p-3">
            <p className="text-xs text-gray-500 mb-2 font-medium">Score Breakdown</p>
            <div className="space-y-2">
              {Object.entries(rec.scores || {}).map(([key, val]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-gray-400 w-28 capitalize">{key.replace('_', ' ')}</span>
                  <div className="flex-1 h-2 bg-[#1a1f35] rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-700"
                      style={{ width: `${val * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-white font-mono w-10 text-right">{val.toFixed(2)}</span>
                </div>
              ))}
            </div>
          </div>

          {rec.pricing?.incentive === 'DISCOUNT' && (
            <div className="mt-3 flex items-center gap-2 text-green-400 text-sm">
              <span>💰</span> Save ₹{rec.pricing.savings_vs_base}/kWh — Incentive active!
            </div>
          )}
        </div>
      )}

      {/* Alternatives */}
      {alts.length > 0 && (
        <div>
          <h4 className="text-xs text-gray-500 uppercase tracking-wider mb-2 px-1">Alternatives</h4>
          <div className="space-y-2">
            {alts.map((a) => (
              <div key={a.station_id} className="rounded-lg border border-[#2a3050] p-3 flex items-center justify-between" style={{ background: '#1a1f35' }}>
                <div>
                  <span className="text-sm text-gray-300 font-medium">{a.station_name}</span>
                  <div className="flex gap-3 text-xs text-gray-500 mt-1">
                    <span>{a.distance_km} km</span>
                    <span>₹{a.pricing?.final_price || 16}/kWh</span>
                    <span>{a.pricing?.estimated_wait_min || 0} min wait</span>
                  </div>
                </div>
                <div className="text-right">
                  <span className="text-sm font-mono text-gray-400">{a.final_score}</span>
                  <p className="text-[10px] text-gray-600">score</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
