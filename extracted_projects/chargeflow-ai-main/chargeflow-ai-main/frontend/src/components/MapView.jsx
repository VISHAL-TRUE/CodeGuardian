import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import { MapPin } from 'lucide-react';

const STATUS_COLORS = {
  green: '#10b981',
  yellow: '#f59e0b',
  red: '#ef4444',
};

const CENTER = [13.05, 80.25];

export default function MapView({ stations }) {
  if (!stations?.length) return null;

  return (
    <div className="rounded-xl border border-[#2a3050] overflow-hidden" style={{ background: 'linear-gradient(135deg, #1a1f35 0%, #111827 100%)' }}>
      <div className="px-5 py-4 border-b border-[#2a3050] flex items-center gap-2">
        <MapPin size={18} className="text-blue-400" />
        <h3 className="text-sm font-semibold text-white">Station Network</h3>
        <div className="ml-auto flex items-center gap-4 text-xs text-gray-500">
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-green-500" /> Low</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-yellow-500" /> Moderate</span>
          <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Congested</span>
        </div>
      </div>
      <div style={{ height: '420px' }}>
        <MapContainer center={CENTER} zoom={12} style={{ height: '100%', width: '100%' }} zoomControl={false}>
          <TileLayer
            attribution='&copy; OpenStreetMap'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          {stations.map((s) => {
            const color = STATUS_COLORS[s.status] || '#6b7280';
            const radius = Math.max(12, s.queue_length * 2 + 8);
            return (
              <CircleMarker
                key={s.station_id}
                center={[s.latitude, s.longitude]}
                radius={radius}
                pathOptions={{
                  color,
                  fillColor: color,
                  fillOpacity: 0.3,
                  weight: 2,
                  opacity: 0.8,
                }}
              >
                <Popup>
                  <div style={{ minWidth: '180px', fontFamily: 'Inter, sans-serif' }}>
                    <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '8px', color: '#e5e7eb' }}>{s.name}</h4>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px', fontSize: '12px' }}>
                      <span style={{ color: '#9ca3af' }}>Utilisation</span>
                      <span style={{ color, fontWeight: 600, textAlign: 'right' }}>{s.utilisation_pct}%</span>
                      <span style={{ color: '#9ca3af' }}>Load</span>
                      <span style={{ color: '#e5e7eb', textAlign: 'right' }}>{s.current_load_kw} kW</span>
                      <span style={{ color: '#9ca3af' }}>Grid Limit</span>
                      <span style={{ color: '#e5e7eb', textAlign: 'right' }}>{s.grid_limit_kw} kW</span>
                      <span style={{ color: '#9ca3af' }}>Queue</span>
                      <span style={{ color: '#e5e7eb', textAlign: 'right' }}>{s.queue_length}</span>
                      <span style={{ color: '#9ca3af' }}>Available</span>
                      <span style={{ color: '#e5e7eb', textAlign: 'right' }}>{s.available_chargers}/{s.total_chargers}</span>
                      {s.pricing && (
                        <>
                          <span style={{ color: '#9ca3af' }}>Price</span>
                          <span style={{ color: s.pricing.incentive === 'DISCOUNT' ? '#10b981' : s.pricing.incentive === 'SURCHARGE' ? '#ef4444' : '#e5e7eb', fontWeight: 600, textAlign: 'right' }}>
                            ₹{s.pricing.final_price}/kWh
                          </span>
                        </>
                      )}
                    </div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      </div>
    </div>
  );
}
