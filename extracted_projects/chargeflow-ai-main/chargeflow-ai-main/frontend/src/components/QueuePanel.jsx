import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Users } from 'lucide-react';

export default function QueuePanel({ stations }) {
  if (!stations?.length) return null;

  const data = stations.map((s) => ({
    name: s.station_id,
    fullName: s.name,
    queue: s.queue_length,
    chargers: s.total_chargers,
    available: s.available_chargers,
    waitMin: s.pricing?.estimated_wait_min || 0,
  }));

  const getColor = (q, total) => {
    const ratio = q / total;
    if (ratio > 1) return '#ef4444';
    if (ratio > 0.5) return '#f59e0b';
    return '#10b981';
  };

  const CustomTooltip = ({ active, payload }) => {
    if (!active || !payload?.length) return null;
    const d = payload[0].payload;
    return (
      <div className="bg-[#1a1f35] border border-[#2a3050] rounded-lg p-3 shadow-xl text-xs">
        <p className="font-semibold text-white mb-1">{d.fullName}</p>
        <p className="text-gray-400">Queue: <span className="text-white font-mono">{d.queue} EVs</span></p>
        <p className="text-gray-400">Chargers: <span className="text-white font-mono">{d.available}/{d.chargers}</span></p>
        <p className="text-gray-400">Est. Wait: <span className="text-yellow-400 font-mono">{d.waitMin} min</span></p>
      </div>
    );
  };

  return (
    <div className="rounded-xl border border-[#2a3050] p-5" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="flex items-center gap-2 mb-4">
        <Users size={18} className="text-yellow-400" />
        <h3 className="text-sm font-semibold text-white">Queue Length & Wait Times</h3>
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Bar dataKey="queue" name="Queue" radius={[6, 6, 0, 0]} maxBarSize={50}>
            {data.map((d, i) => (
              <Cell key={i} fill={getColor(d.queue, d.chargers)} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Wait time badges */}
      <div className="flex gap-3 mt-3 flex-wrap">
        {data.map((d) => (
          <div key={d.name} className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full bg-white/5 border border-[#2a3050]">
            <span className="text-gray-500">{d.name}</span>
            <span className={`font-mono font-medium ${d.waitMin > 30 ? 'text-red-400' : d.waitMin > 10 ? 'text-yellow-400' : 'text-green-400'}`}>
              {d.waitMin} min
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
