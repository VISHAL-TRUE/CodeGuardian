import { useState } from 'react';
import { MapPin, Battery, Target, Clock, Search } from 'lucide-react';
import { api } from '../services/api';
import Recommendation from '../components/Recommendation';

export default function DriverPortal({ data }) {
  const [form, setForm] = useState({
    latitude: '13.060',
    longitude: '80.260',
    current_soc: '25',
    target_soc: '90',
    max_charge_rate_kw: '60',
    deadline: '',
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.allocate({
        ev_id: 'DRIVER01',
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        current_soc: parseInt(form.current_soc),
        target_soc: parseInt(form.target_soc),
        max_charge_rate_kw: parseInt(form.max_charge_rate_kw),
        deadline: form.deadline || null,
      });
      setResult(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full bg-[#0a0e1a] border border-[#2a3050] rounded-lg px-4 py-2.5 text-white text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all";

  return (
    <main className="max-w-[1200px] mx-auto px-6 py-8">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white mb-1">Driver Portal</h2>
        <p className="text-gray-500 text-sm">Find the optimal charging station based on your needs</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <div>
          <form onSubmit={handleSubmit} className="rounded-xl border border-[#2a3050] p-6 space-y-5" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
            <h3 className="text-sm font-semibold text-white mb-2">Your Details</h3>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><MapPin size={12} /> Latitude</label>
                <input type="text" value={form.latitude} onChange={e => setForm(f => ({ ...f, latitude: e.target.value }))} className={inputClass} />
              </div>
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><MapPin size={12} /> Longitude</label>
                <input type="text" value={form.longitude} onChange={e => setForm(f => ({ ...f, longitude: e.target.value }))} className={inputClass} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><Battery size={12} /> Current Battery %</label>
                <input type="number" min="0" max="100" value={form.current_soc} onChange={e => setForm(f => ({ ...f, current_soc: e.target.value }))} className={inputClass} />
              </div>
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><Target size={12} /> Target Battery %</label>
                <input type="number" min="0" max="100" value={form.target_soc} onChange={e => setForm(f => ({ ...f, target_soc: e.target.value }))} className={inputClass} />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><Zap size={12} /> Max Charge Rate (kW)</label>
                <select value={form.max_charge_rate_kw} onChange={e => setForm(f => ({ ...f, max_charge_rate_kw: e.target.value }))} className={inputClass}>
                  <option value="22">22 kW (AC)</option>
                  <option value="50">50 kW (DC)</option>
                  <option value="60">60 kW (DC)</option>
                  <option value="120">120 kW (DC Fast)</option>
                  <option value="150">150 kW (DC Ultra)</option>
                </select>
              </div>
              <div>
                <label className="flex items-center gap-1.5 text-xs text-gray-500 mb-1.5"><Clock size={12} /> Departure Time</label>
                <input type="time" value={form.deadline} onChange={e => setForm(f => ({ ...f, deadline: e.target.value }))} className={inputClass} />
              </div>
            </div>

            {error && (
              <div className="text-red-400 text-sm bg-red-500/10 border border-red-500/20 rounded-lg p-3">{error}</div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-semibold py-3 rounded-lg transition-all duration-200 shadow-lg shadow-blue-500/20 disabled:opacity-50"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <Search size={16} />
                  Find Best Station
                </>
              )}
            </button>
          </form>

          {/* Quick presets */}
          <div className="mt-4 flex gap-2 flex-wrap">
            <span className="text-xs text-gray-600">Quick presets:</span>
            <button onClick={() => setForm(f => ({ ...f, latitude: '13.083', longitude: '80.271', current_soc: '15' }))} className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 px-2 py-1 rounded">Near Central Chennai (Low SOC)</button>
            <button onClick={() => setForm(f => ({ ...f, latitude: '13.007', longitude: '80.257', current_soc: '40' }))} className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 px-2 py-1 rounded">Near Adyar</button>
            <button onClick={() => setForm(f => ({ ...f, latitude: '12.965', longitude: '80.246', current_soc: '10' }))} className="text-xs text-blue-400 hover:text-blue-300 bg-blue-500/10 px-2 py-1 rounded">Near OMR / Perungudi (Critical)</button>
          </div>
        </div>

        {/* Results */}
        <div>
          {result ? (
            <Recommendation result={result} />
          ) : (
            <div className="rounded-xl border border-[#2a3050] p-12 text-center" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
              <div className="w-16 h-16 rounded-full bg-blue-500/10 flex items-center justify-center mx-auto mb-4">
                <Search size={28} className="text-blue-400/50" />
              </div>
              <p className="text-gray-500 text-sm">Enter your details and click "Find Best Station"</p>
              <p className="text-gray-600 text-xs mt-2">ChargeFlow AI will recommend the optimal station with score breakdown</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}

function Zap({ size, className }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>
  );
}
