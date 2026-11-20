import React, { useState, useEffect } from 'react';
import {
  Sun,
  Zap,
  TrendingUp,
  Cpu,
  Compass,
  Layers,
  Info,
  AlertTriangle,
  RefreshCw,
  BarChart3,
  Calendar
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
  AreaChart
} from 'recharts';
import { api } from '../services/api';
import { GenerationPredictionResponse } from '../types';
import { ModelStatusBadge } from '../components/common/ModelStatusBadge';
import { DemoBadge } from '../components/common/DemoBadge';

const BD_DIVISIONS = [
  'Dhaka',
  'Chattogram',
  'Rajshahi',
  'Khulna',
  'Barishal',
  'Sylhet',
  'Rangpur',
  'Mymensingh',
];

export const GenerationPredictionPage: React.FC = () => {
  const [capacity, setCapacity] = useState<number>(3.5);
  const [division, setDivision] = useState<string>('Dhaka');
  const [tilt, setTilt] = useState<number>(23.0);
  const [shading, setShading] = useState<number>(0.95);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<GenerationPredictionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchPrediction = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.predictGeneration({
        system_capacity_kwp: Number(capacity),
        division,
        tilt_degrees: Number(tilt),
        shading_factor: Number(shading),
      });
      setResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to simulate solar generation.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrediction();
  }, [capacity, division, shading]);

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-2">
              <Cpu className="w-4 h-4 text-solar-500" />
              <span>Machine Learning 1 — XGBoost PV Architecture</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Solar Electricity Generation Prediction
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Simulate daily and monthly solar energy harvest across Bangladesh divisions using NASA POWER irradiance records.
            </p>
          </div>

          <div className="flex items-center space-x-3">
            {result && <ModelStatusBadge status={result.model_status} />}
          </div>
        </div>

        {/* Input Parameters Controls */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs mb-8">
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-5">
            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                System Capacity (kWp)
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="100"
                  value={capacity}
                  onChange={(e) => setCapacity(Math.max(0.5, parseFloat(e.target.value) || 0.5))}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-forest-600 pr-14"
                />
                <span className="absolute right-4 top-2.5 text-xs font-bold text-slate-500">kWp</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Bangladesh Division
              </label>
              <select
                value={division}
                onChange={(e) => setDivision(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600"
              >
                {BD_DIVISIONS.map((d) => (
                  <option key={d} value={d}>
                    {d} Division
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Panel Tilt Angle
              </label>
              <div className="relative">
                <input
                  type="number"
                  step="1"
                  min="10"
                  max="45"
                  value={tilt}
                  onChange={(e) => setTilt(parseFloat(e.target.value) || 23)}
                  className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 pr-10"
                />
                <span className="absolute right-4 top-2.5 text-xs text-slate-500">° S</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Shading Factor
              </label>
              <select
                value={shading}
                onChange={(e) => setShading(parseFloat(e.target.value))}
                className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600"
              >
                <option value={1.0}>1.00 — Zero Shading</option>
                <option value={0.95}>0.95 — Low / Occasional</option>
                <option value={0.85}>0.85 — Medium Shading</option>
                <option value={0.70}>0.70 — Heavy Shading</option>
              </select>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm">
            {errorMsg}
          </div>
        )}

        {result && (
          <>
            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Daily Average
                  </span>
                  <Sun className="w-5 h-5 text-solar-500" />
                </div>
                <p className="text-3xl font-extrabold text-slate-900">
                  {result.average_daily_generation_kwh}{' '}
                  <span className="text-base font-normal text-slate-500">kWh/day</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">Across 365 calendar days</p>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Annual Total
                  </span>
                  <Zap className="w-5 h-5 text-forest-700" />
                </div>
                <p className="text-3xl font-extrabold text-forest-900">
                  {result.annual_generation_kwh.toLocaleString()}{' '}
                  <span className="text-base font-normal text-slate-500">kWh/yr</span>
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  ~{(result.annual_generation_kwh / 12).toFixed(0)} kWh monthly average
                </p>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Model Engine
                  </span>
                  <Cpu className="w-5 h-5 text-blue-600" />
                </div>
                <p className="text-sm font-bold text-slate-900">{result.model_status}</p>
                <p className="text-xs text-slate-500 mt-1">{result.data_source}</p>
              </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              {/* Diurnal 24-hour curve */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">
                      24-Hour Diurnal Solar Profile
                    </h3>
                    <p className="text-xs text-slate-500">Estimated kW power curve throughout the day</p>
                  </div>
                  <span className="text-xs font-semibold px-2 py-1 rounded bg-slate-100 text-slate-600">
                    Sunny Day Profile
                  </span>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart
                      data={result.hourly_sample_profile}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <defs>
                        <linearGradient id="solarYield" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="time_label" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(val: number) => [`${val} kW`, 'Power Output']}
                        contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                      />
                      <Area type="monotone" dataKey="generation_kw" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#solarYield)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Monthly breakdown */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">
                      Monthly Generation in {division}
                    </h3>
                    <p className="text-xs text-slate-500">Seasonal variation based on multi-year NASA POWER PSH</p>
                  </div>
                  <span className="text-xs font-semibold px-2 py-1 rounded bg-forest-100 text-forest-800">
                    Monthly kWh
                  </span>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                      data={result.monthly_breakdown}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="month_name" tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 10, fill: '#64748b' }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(val: number) => [`${val} kWh`, 'Monthly Yield']}
                        contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                      />
                      <Bar dataKey="generation_kwh" fill="#15803d" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* Academic Notice & Limitations */}
            <div className="p-6 rounded-2xl bg-slate-100 border border-slate-200 space-y-3 text-xs text-slate-700">
              <div className="flex items-center space-x-2 font-bold text-slate-900 text-sm">
                <Info className="w-4 h-4 text-forest-700" />
                <span>Prediction Explanation & Dataset Scope</span>
              </div>
              <p className="leading-relaxed">{result.prediction_explanation}</p>
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-900 flex items-start space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <p>{result.limitations_notice}</p>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
