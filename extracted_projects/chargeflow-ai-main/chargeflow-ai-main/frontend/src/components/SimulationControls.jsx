import { Play, RotateCcw, Zap, AlertTriangle, Shield } from 'lucide-react';

export default function SimulationControls({ scenario, isPeak, isOptimised, onSimulate, onOptimize, onReset, simLoading }) {
  return (
    <div className="rounded-xl border border-[#2a3050] p-5" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center">
            <Play size={16} className="text-purple-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Simulation Controls</h3>
            <p className="text-xs text-gray-500">
              Current: <span className={`font-medium ${scenario === 'normal' ? 'text-green-400' : scenario === 'peak' ? 'text-red-400' : 'text-yellow-400'}`}>
                {scenario === 'normal' ? 'Normal State' : scenario === 'peak' ? 'Peak Demand' : 'Grid Constraint'}
              </span>
              {isOptimised && <span className="text-blue-400 ml-2">• Optimised</span>}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <button
            onClick={() => onSimulate('peak')}
            disabled={!!simLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-red-600 to-orange-600 hover:from-red-500 hover:to-orange-500 text-white text-sm font-medium transition-all duration-200 disabled:opacity-50 shadow-lg shadow-red-500/20 hover:shadow-red-500/30"
          >
            {simLoading === 'peak' ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Zap size={16} />
            )}
            Simulate Peak Demand
          </button>

          <button
            onClick={() => onSimulate('grid')}
            disabled={!!simLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-gradient-to-r from-yellow-600 to-amber-600 hover:from-yellow-500 hover:to-amber-500 text-white text-sm font-medium transition-all duration-200 disabled:opacity-50 shadow-lg shadow-yellow-500/20"
          >
            {simLoading === 'grid' ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <AlertTriangle size={16} />
            )}
            Grid Constraint
          </button>

          {isPeak && !isOptimised && (
            <button
              onClick={onOptimize}
              disabled={!!simLoading}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white text-sm font-semibold transition-all duration-200 disabled:opacity-50 shadow-lg shadow-blue-500/25 hover:shadow-blue-500/40 animate-slide-up"
            >
              {simLoading === 'optimize' ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Shield size={16} />
              )}
              Run ChargeFlow Optimisation
            </button>
          )}

          <button
            onClick={onReset}
            disabled={!!simLoading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[#2a3050] hover:bg-white/5 text-gray-400 hover:text-white text-sm font-medium transition-all duration-200 disabled:opacity-50"
          >
            {simLoading === 'reset' ? (
              <div className="w-4 h-4 border-2 border-gray-500/30 border-t-gray-400 rounded-full animate-spin" />
            ) : (
              <RotateCcw size={16} />
            )}
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
