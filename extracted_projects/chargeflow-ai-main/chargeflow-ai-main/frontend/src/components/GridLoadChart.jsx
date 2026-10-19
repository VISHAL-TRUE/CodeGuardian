import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts';
import { Gauge } from 'lucide-react';

export default function GridLoadChart({ stations }) {
  if (!stations?.length) return null;

  const data = stations.map((s) => ({
    name: s.station_id,
    fullName: s.name,
    load: s.current_load_kw,
    limit: s.grid_limit_kw,
    pct: Math.round((s.current_load_kw / s.grid_limit_kw) * 100),
    headroom: Math.max(0, s.grid_limit_kw - s.current_load_kw),
    status: s.status,
  }));

  const getColor = (status) => {
    if (status === 'red') return '#ef4444';
    if (status === 'yellow') return '#f59e0b';
    return '#10b981';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-[#1a1f35] border border-[#2a3050] rounded-lg p-3 shadow-xl text-xs">
        <p className="font-semibold text-white mb-1">{d.fullName}</p>
        <p className="text-gray-400">Load: <span className="text-white font-mono">{d.load} kW</span></p>
        <p className="text-gray-400">Limit: <span className="text-white font-mono">{d.limit} kW</span></p>
        <p className="text-gray-400">Headroom: <span className="text-green-400 font-mono">{d.headroom} kW</span></p>
        <p className="text-gray-400">Utilisation: <span style={{ color: getColor(d.status) }} className="font-mono font-semibold">{d.pct}%</span></p>
      </div>
    );
  };

  return (
    <div className="rounded-xl border border-[#2a3050] p-5" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="flex items-center gap-2 mb-4">
        <Gauge size={18} className="text-cyan-400" />
        <h3 className="text-sm font-semibold text-white">Grid Load vs Limit</h3>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} unit=" kW" />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Bar dataKey="load" radius={[6, 6, 0, 0]} maxBarSize={50}>
            {data.map((d, i) => (
              <Cell key={i} fill={getColor(d.status)} fillOpacity={0.8} />
            ))}
          </Bar>
          <Bar dataKey="limit" radius={[6, 6, 0, 0]} maxBarSize={50} fillOpacity={0.15} fill="#6b7280" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
