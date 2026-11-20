import React, { useState, useEffect } from 'react';
import {
  BatteryCharging,
  Zap,
  Plus,
  Trash2,
  Info,
  AlertTriangle,
  Clock,
  ShieldCheck,
  TrendingDown,
  DollarSign
} from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import { api } from '../services/api';
import { ApplianceItem, BatteryOptimizationResponse } from '../types';

const INITIAL_APPLIANCES: ApplianceItem[] = [
  { name: 'Ceiling Fan', wattage: 75, quantity: 3, daily_usage_hours: 8, is_critical: true },
  { name: 'LED Light Bulb', wattage: 15, quantity: 5, daily_usage_hours: 6, is_critical: true },
  { name: 'WiFi Router', wattage: 12, quantity: 1, daily_usage_hours: 24, is_critical: true },
  { name: 'Refrigerator', wattage: 150, quantity: 1, daily_usage_hours: 12, is_critical: true },
  { name: 'Television', wattage: 80, quantity: 1, daily_usage_hours: 4, is_critical: false },
];

export const BatteryOptimizerPage: React.FC = () => {
  const [appliances, setAppliances] = useState<ApplianceItem[]>(INITIAL_APPLIANCES);
  const [backupHours, setBackupHours] = useState<number>(4.0);
  const [chemistry, setChemistry] = useState<string>('lifepo4');
  const [customDod, setCustomDod] = useState<number>(0.85);
  const [inverterEff, setInverterEff] = useState<number>(0.90);
  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<BatteryOptimizationResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // New appliance input state
  const [newName, setNewName] = useState('');
  const [newWatts, setNewWatts] = useState(60);
  const [newQty, setNewQty] = useState(1);

  const handleAddAppliance = () => {
    if (!newName.trim()) return;
    setAppliances([
      ...appliances,
      {
        name: newName.trim(),
        wattage: Number(newWatts),
        quantity: Number(newQty),
        daily_usage_hours: 6,
        is_critical: true,
      },
    ]);
    setNewName('');
    setNewWatts(60);
    setNewQty(1);
  };

  const handleRemoveAppliance = (idx: number) => {
    setAppliances(appliances.filter((_, i) => i !== idx));
  };

  const toggleCritical = (idx: number) => {
    const updated = [...appliances];
    updated[idx].is_critical = !updated[idx].is_critical;
    setAppliances(updated);
  };

  const handleChemistryChange = (chem: string) => {
    setChemistry(chem);
    if (chem === 'lifepo4') {
      setCustomDod(0.85);
    } else {
      setCustomDod(0.50);
    }
  };

  const fetchOptimization = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await api.getBatteryRecommendation({
        appliances,
        required_backup_hours: Number(backupHours),
        battery_chemistry: chemistry,
        custom_dod: Number(customDod),
        custom_inverter_eff: Number(inverterEff),
      });
      setResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Battery calculation failed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOptimization();
  }, [appliances, backupHours, chemistry, customDod, inverterEff]);

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-2">
            <BatteryCharging className="w-4 h-4 text-solar-500" />
            <span>Engineering Calculation Engine</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Battery Capacity & Backup Optimizer
          </h1>
          <p className="text-slate-600 text-sm mt-1">
            Determine exact battery storage for load shedding and peak shaving using your home appliance inventory.
          </p>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm">
            {errorMsg}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Appliance Inventory (2 cols) */}
          <div className="lg:col-span-2 space-y-6">
            {/* Inventory Card */}
            <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    Household Appliance Inventory
                  </h2>
                  <p className="text-xs text-slate-500">
                    Mark appliances as "Critical" to include them in outage backup calculations.
                  </p>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-lg">
                  {appliances.length} Items
                </span>
              </div>

              {/* Table */}
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Appliance</th>
                      <th className="px-4 py-3">Power (Watts)</th>
                      <th className="px-4 py-3">Quantity</th>
                      <th className="px-4 py-3">Total Watts</th>
                      <th className="px-4 py-3">Critical Backup</th>
                      <th className="px-4 py-3 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {appliances.map((app, idx) => {
                      const totalWatts = app.wattage * app.quantity;
                      return (
                        <tr key={idx} className="hover:bg-slate-50/60">
                          <td className="px-4 py-3 font-semibold text-slate-900">{app.name}</td>
                          <td className="px-4 py-3 text-slate-600">{app.wattage} W</td>
                          <td className="px-4 py-3 text-slate-600">{app.quantity}</td>
                          <td className="px-4 py-3 font-mono font-bold text-slate-900">{totalWatts} W</td>
                          <td className="px-4 py-3">
                            <button
                              type="button"
                              onClick={() => toggleCritical(idx)}
                              className={`px-2.5 py-1 rounded-md text-[11px] font-bold transition-colors ${
                                app.is_critical
                                  ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                                  : 'bg-slate-100 text-slate-500 border border-slate-200'
                              }`}
                            >
                              {app.is_critical ? '✓ Critical' : 'Non-Critical'}
                            </button>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={() => handleRemoveAppliance(idx)}
                              className="text-slate-400 hover:text-red-600 p-1 rounded"
                              title="Delete"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {/* Add Custom Appliance */}
              <div className="mt-6 pt-5 border-t border-slate-100 grid grid-cols-1 sm:grid-cols-4 gap-3 items-end">
                <div className="sm:col-span-2">
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                    Add Appliance
                  </label>
                  <input
                    type="text"
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    placeholder="e.g. Water Pump, Desktop PC..."
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-bold text-slate-600 uppercase mb-1">
                    Watts
                  </label>
                  <input
                    type="number"
                    value={newWatts}
                    onChange={(e) => setNewWatts(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600"
                  />
                </div>
                <div>
                  <button
                    type="button"
                    onClick={handleAddAppliance}
                    className="w-full inline-flex items-center justify-center px-4 py-2 rounded-xl text-xs font-bold bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-xs"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    <span>Add Item</span>
                  </button>
                </div>
              </div>
            </div>

            {/* 24-Hour Schedule Profile Chart */}
            {result && (
              <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs">
                <div className="flex justify-between items-center mb-4">
                  <div>
                    <h3 className="font-bold text-slate-900 text-base">
                      24-Hour Battery Dispatch Schedule (Planning Model)
                    </h3>
                    <p className="text-xs text-slate-500">
                      Simulated State of Charge (SOC%) across daytime solar charging and evening backup
                    </p>
                  </div>
                  <span className="text-xs font-semibold px-2 py-1 rounded bg-forest-100 text-forest-800">
                    SOC Profile
                  </span>
                </div>
                <div className="h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart
                      data={result.schedule_profile}
                      margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis
                        dataKey="hour"
                        tickFormatter={(h) => `${h}:00`}
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        domain={[0, 100]}
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        formatter={(val: number) => [`${val}%`, 'Battery SOC']}
                        contentStyle={{
                          backgroundColor: '#0f172a',
                          borderRadius: '8px',
                          color: '#fff',
                          fontSize: '12px',
                        }}
                      />
                      <Line
                        type="monotone"
                        dataKey="battery_soc_pct"
                        stroke="#16a34a"
                        strokeWidth={2.5}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>

                <div className="mt-4 p-3 bg-slate-50 rounded-xl text-xs text-slate-500 border border-slate-200">
                  {result.preliminary_notice}
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Parameters & Results (1 col) */}
          <div className="space-y-6">
            {/* Parameters Configuration Card */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-5">
              <h3 className="font-bold text-slate-900 text-base border-b border-slate-100 pb-3">
                Backup Requirements
              </h3>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                  Outage Duration Required (Hours)
                </label>
                <div className="flex items-center space-x-2">
                  {[2, 4, 6, 8, 12].map((hrs) => (
                    <button
                      key={hrs}
                      type="button"
                      onClick={() => setBackupHours(hrs)}
                      className={`flex-1 py-2 text-xs font-bold rounded-xl border transition-all ${
                        backupHours === hrs
                          ? 'bg-forest-900 text-white border-forest-900 shadow-xs'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {hrs}h
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                  Battery Chemistry
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => handleChemistryChange('lifepo4')}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      chemistry === 'lifepo4'
                        ? 'bg-forest-50 border-forest-600 text-forest-950 font-bold ring-1 ring-forest-600'
                        : 'bg-slate-50 border-slate-200 text-slate-600'
                    }`}
                  >
                    <p className="font-bold">LiFePO4</p>
                    <span className="text-[10px] text-slate-500">85% DoD • 4000+ Cycles</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => handleChemistryChange('lead_acid')}
                    className={`p-3 rounded-xl border text-left text-xs transition-all ${
                      chemistry === 'lead_acid'
                        ? 'bg-forest-50 border-forest-600 text-forest-950 font-bold ring-1 ring-forest-600'
                        : 'bg-slate-50 border-slate-200 text-slate-600'
                    }`}
                  >
                    <p className="font-bold">Tubular Lead-Acid</p>
                    <span className="text-[10px] text-slate-500">50% DoD • Lower Cost</span>
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Depth of Discharge</label>
                  <input
                    type="number"
                    step="0.05"
                    min="0.3"
                    max="0.95"
                    value={customDod}
                    onChange={(e) => setCustomDod(parseFloat(e.target.value) || 0.85)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-bold text-slate-600 mb-1">Inverter Efficiency</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.7"
                    max="0.98"
                    value={inverterEff}
                    onChange={(e) => setInverterEff(parseFloat(e.target.value) || 0.90)}
                    className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl"
                  />
                </div>
              </div>
            </div>

            {/* Sizing Results Card */}
            {result && (
              <div className="bg-forest-950 text-white p-6 rounded-2xl shadow-md space-y-5">
                <div className="border-b border-forest-900 pb-3">
                  <span className="text-xs font-bold uppercase tracking-widest text-solar-400">
                    Storage Recommendation
                  </span>
                  <h3 className="text-xl font-extrabold text-white mt-1">Recommended Capacity</h3>
                </div>

                <div className="p-4 rounded-xl bg-forest-900/80 border border-forest-800">
                  <span className="text-xs text-slate-400">Nominal Battery Bank</span>
                  <p className="text-3xl font-extrabold text-solar-400 mt-1">
                    {result.recommended_nominal_capacity_kwh}{' '}
                    <span className="text-base font-normal text-white">kWh</span>
                  </p>
                  <p className="text-[11px] text-slate-300 mt-1">
                    Delivers {result.usable_capacity_required_kwh} kWh usable energy at {intDod(result.dod_used)}% DoD
                  </p>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-forest-900">
                    <span className="text-slate-400">Critical Load</span>
                    <span className="font-mono font-bold text-white">
                      {result.total_critical_load_watts} Watts
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-forest-900">
                    <span className="text-slate-400">Backup Energy Required</span>
                    <span className="font-mono font-bold text-white">
                      {(result.required_backup_energy_wh / 1000).toFixed(2)} kWh
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-forest-900">
                    <span className="text-slate-400">Est. Battery Cost (Min)</span>
                    <span className="font-mono font-bold text-solar-300">
                      ৳ {result.est_battery_cost_bdt_min.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-forest-900">
                    <span className="text-slate-400">Est. Battery Cost (Max)</span>
                    <span className="font-mono font-bold text-solar-300">
                      ৳ {result.est_battery_cost_bdt_max.toLocaleString()}
                    </span>
                  </div>
                </div>

                <div className="p-3 bg-forest-900/40 rounded-xl text-[11px] text-slate-300 border border-forest-800">
                  {result.optimization_explanation}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

function intDod(val: number) {
  return Math.round(val * 100);
}
