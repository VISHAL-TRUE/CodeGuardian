import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { TrendingUp } from 'lucide-react';

export default function DemandChart({ stations }) {
  if (!stations?.length) return null;

  const data = stations.map((s) => ({
    name: s.station_id,
    fullName: s.name,
    demand: s.prediction?.predicted_demand || 0,
    risk: s.prediction?.congestion_risk || 0,
    utilisation: s.utilisation_pct,
  }));

  const getColor = (risk) => {
    if (risk > 0.6) return '#ef4444';
    if (risk > 0.3) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="rounded-xl border border-[#2a3050] p-5" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="flex items-center gap-2 mb-4">
        <TrendingUp size={18} className="text-purple-400" />
        <h3 className="text-sm font-semibold text-white">Predicted Demand</h3>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} barCategoryGap="20%">
          <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ background: '#1a1f35', border: '1px solid #2a3050', borderRadius: '8px' }}
            labelStyle={{ color: '#e5e7eb' }}
          />
          <Bar dataKey="demand" name="Predicted Demand" radius={[6, 6, 0, 0]} maxBarSize={50}>
            {data.map((d, i) => (
              <Cell key={i} fill={getColor(d.risk)} fillOpacity={0.8} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
