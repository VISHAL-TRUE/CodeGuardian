import { useState, useEffect, useCallback } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Zap, LayoutDashboard, User, Activity } from 'lucide-react';
import { api } from './services/api';
import Dashboard from './pages/Dashboard';
import DriverPortal from './pages/DriverPortal';

function NavLink({ to, icon: Icon, label }) {
  const location = useLocation();
  const active = location.pathname === to;
  return (
    <Link
      to={to}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
        active
          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
          : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
      }`}
    >
      <Icon size={18} />
      {label}
    </Link>
  );
}

function AppContent() {
  const [data, setData] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [simLoading, setSimLoading] = useState('');
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    try {
      const [stationsData, metricsData] = await Promise.all([
        api.getStations(),
        api.getMetrics(),
      ]);
      setData(stationsData);
      setMetrics(metricsData);
      setError(null);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSimulate = async (action) => {
    setSimLoading(action);
    try {
      let result;
      if (action === 'peak') result = await api.simulatePeak();
      else if (action === 'grid') result = await api.simulateGridConstraint();
      else if (action === 'optimize') result = await api.simulateOptimize();
      else if (action === 'reset') result = await api.simulateReset();
      await refresh();
      return result;
    } catch (e) {
      setError(e.message);
    } finally {
      setSimLoading('');
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0e1a]">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-[#2a3050] bg-[#0a0e1a]/80 backdrop-blur-xl">
        <div className="max-w-[1600px] mx-auto px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-500 to-cyan-400 rounded-lg flex items-center justify-center">
              <Zap size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white tracking-tight">ChargeFlow AI</h1>
              <p className="text-[10px] text-gray-500 uppercase tracking-widest">Predictive EV Charging Optimisation</p>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <NavLink to="/" icon={LayoutDashboard} label="Dashboard" />
            <NavLink to="/driver" icon={User} label="Driver Portal" />
          </nav>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${error ? 'bg-red-500' : 'bg-green-500'}`} />
            <span className="text-xs text-gray-500">{error ? 'Error' : 'Connected'}</span>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-6 py-2 text-center">
          <span className="text-red-400 text-sm">{error}</span>
          <button onClick={() => { setError(null); refresh(); }} className="ml-4 text-red-300 underline text-sm">Retry</button>
        </div>
      )}

      {/* Routes */}
      <Routes>
        <Route
          path="/"
          element={
            <Dashboard
              data={data}
              metrics={metrics}
              onSimulate={handleSimulate}
              simLoading={simLoading}
              onRefresh={refresh}
            />
          }
        />
        <Route path="/driver" element={<DriverPortal data={data} />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}
