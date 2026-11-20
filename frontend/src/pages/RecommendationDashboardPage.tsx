import React, { useState } from 'react';
import { useLocation, Link } from 'react-router-dom';
import {
  Sun,
  Zap,
  ShieldCheck,
  Layers,
  ArrowRight,
  Printer,
  Download,
  AlertTriangle,
  Info,
  DollarSign,
  Calendar,
  BatteryCharging,
  TrendingUp,
  Cpu,
  CheckCircle2,
  Share2,
  BookmarkPlus,
  LayoutDashboard
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line
} from 'recharts';
import { SolarRecommendationResponse, SystemTier } from '../types';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const RecommendationDashboardPage: React.FC = () => {
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();
  const [claimed, setClaimed] = useState(false);
  const [claimMsg, setClaimMsg] = useState<string | null>(null);
  const [claimLoading, setClaimLoading] = useState(false);

  const stateData = location.state as {
    recommendation?: SolarRecommendationResponse;
    recommendationData?: SolarRecommendationResponse;
    assessment?: any;
    assessmentResponse?: any;
    savedAssessment?: any;
  } | undefined;


  // Fallback demo data if user accessed URL directly without assessment
  const fallbackRec: SolarRecommendationResponse = {
    recommended_system: {
      tier_name: 'Balanced (SREDA Compliant Target)',
      dc_capacity_kwp: 3.3,
      inverter_ac_kw: 2.75,
      panel_count: 6,
      panel_wattage_wp: 550,
      required_usable_area_sqft: 220.3,
      daily_generation_kwh: 12.0,
      monthly_generation_kwh: 360.0,
      annual_generation_kwh: 4380.0,
      consumption_offset_pct: 100.0,
      est_turnkey_cost_bdt_min: 224400,
      est_turnkey_cost_bdt_max: 280500,
      est_monthly_savings_bdt: 2950.0,
      est_annual_savings_bdt: 35400.0,
      est_payback_years_min: 6.3,
      est_payback_years_max: 7.9,
      sreda_ac_compliant: true,
      sreda_note: 'Compliant: Inverter AC (2.75 kW) is within sanctioned load (3.0 kW).'
    },
    alternative_options: [
      {
        tier_name: 'Economical (Quick Payback & Low Investment)',
        dc_capacity_kwp: 2.2,
        inverter_ac_kw: 1.83,
        panel_count: 4,
        panel_wattage_wp: 550,
        required_usable_area_sqft: 146.9,
        daily_generation_kwh: 8.0,
        monthly_generation_kwh: 240.0,
        annual_generation_kwh: 2920.0,
        consumption_offset_pct: 68.6,
        est_turnkey_cost_bdt_min: 149600,
        est_turnkey_cost_bdt_max: 187000,
        est_monthly_savings_bdt: 2250.0,
        est_annual_savings_bdt: 27000.0,
        est_payback_years_min: 5.5,
        est_payback_years_max: 6.9,
        sreda_ac_compliant: true,
        sreda_note: 'Compliant: Inverter AC (1.83 kW) is within sanctioned load (3.0 kW).'
      },
      {
        tier_name: 'Maximum Roof Capacity',
        dc_capacity_kwp: 6.6,
        inverter_ac_kw: 5.5,
        panel_count: 12,
        panel_wattage_wp: 550,
        required_usable_area_sqft: 440.6,
        daily_generation_kwh: 23.9,
        monthly_generation_kwh: 717.0,
        annual_generation_kwh: 8724.0,
        consumption_offset_pct: 100.0,
        est_turnkey_cost_bdt_min: 448800,
        est_turnkey_cost_bdt_max: 561000,
        est_monthly_savings_bdt: 3103.9,
        est_annual_savings_bdt: 37246.8,
        est_payback_years_min: 12.0,
        est_payback_years_max: 15.1,
        sreda_ac_compliant: false,
        sreda_note: 'Utility Sanction Required: Inverter AC (5.5 kW) exceeds current sanctioned load (3.0 kW).'
      }
    ],
    sreda_compliance: {
      is_compliant: true,
      sanctioned_load_kw: 3.0,
      recommended_inverter_ac_kw: 2.75,
      ac_to_sanctioned_ratio: 0.92,
      requires_three_phase: false,
      utility_approval_required: false,
      rule_summary: 'Inverter AC: 2.75 kW vs Sanctioned Load: 3.0 kW (Ratio: 0.92). Grid Phase: Standard Single/Three-Phase Compatible.',
      advisory_text: 'In accordance with Bangladesh Net Metering Guideline 2025, inverter AC output must not exceed sanctioned load.'
    },
    tariff_breakdown: {
      schedule_version: 'BERC 2026 (June 4 Revision)',
      units_kwh: 350.0,
      energy_charge_bdt: 2848.0,
      demand_charge_bdt: 70.0,
      meter_rent_bdt: 40.0,
      vat_bdt: 145.9,
      total_bill_bdt: 3103.9,
      slab_breakdown: [
        { slab: '0-75', units: 75, rate: 5.26, cost_bdt: 394.5 },
        { slab: '76-200', units: 125, rate: 8.50, cost_bdt: 1062.5 },
        { slab: '201-300', units: 100, rate: 9.10, cost_bdt: 910.0 },
        { slab: '301-400', units: 50, rate: 9.62, cost_bdt: 481.0 }
      ]
    },
    division: 'Dhaka',
    monthly_psh_avg: 4.65,
    disclaimer: 'Advisory Notice: Turnkey prices, electricity tariffs, and payback periods are engineering planning estimates based on prevailing Bangladesh market averages.'
  };

  const rec = stateData?.recommendation || stateData?.recommendationData || fallbackRec;
  const assessment = stateData?.assessment || stateData?.assessmentResponse;
  const savedAssessment = stateData?.savedAssessment || (stateData?.assessmentResponse?.id ? stateData.assessmentResponse : undefined);
  const [selectedTier, setSelectedTier] = useState<SystemTier>(rec.recommended_system);

  // Generate monthly generation data for chart based on selected tier
  const monthlyData = [
    { month: 'Jan', gen: Math.round(selectedTier.dc_capacity_kwp * 4.15 * 0.78 * 31) },
    { month: 'Feb', gen: Math.round(selectedTier.dc_capacity_kwp * 4.85 * 0.78 * 28) },
    { month: 'Mar', gen: Math.round(selectedTier.dc_capacity_kwp * 5.50 * 0.78 * 31) },
    { month: 'Apr', gen: Math.round(selectedTier.dc_capacity_kwp * 5.80 * 0.78 * 30) },
    { month: 'May', gen: Math.round(selectedTier.dc_capacity_kwp * 5.40 * 0.78 * 31) },
    { month: 'Jun', gen: Math.round(selectedTier.dc_capacity_kwp * 4.30 * 0.78 * 30) },
    { month: 'Jul', gen: Math.round(selectedTier.dc_capacity_kwp * 4.10 * 0.78 * 31) },
    { month: 'Aug', gen: Math.round(selectedTier.dc_capacity_kwp * 4.20 * 0.78 * 31) },
    { month: 'Sep', gen: Math.round(selectedTier.dc_capacity_kwp * 4.35 * 0.78 * 30) },
    { month: 'Oct', gen: Math.round(selectedTier.dc_capacity_kwp * 4.70 * 0.78 * 31) },
    { month: 'Nov', gen: Math.round(selectedTier.dc_capacity_kwp * 4.40 * 0.78 * 30) },
    { month: 'Dec', gen: Math.round(selectedTier.dc_capacity_kwp * 4.05 * 0.78 * 31) },
  ];

  const handlePrint = () => {
    window.print();
  };

  const handleDownloadReport = () => {
    const reportLines = [
      '=================================================================',
      '        ROOFWISEBD - RESIDENTIAL SOLAR ENGINEERING REPORT        ',
      '        Compliant with SREDA Net Metering 2025 & BERC 2026       ',
      '=================================================================',
      `Generated: ${new Date().toLocaleString()}`,
      `Location: ${rec.division} Division (PSH: ${rec.monthly_psh_avg} kWh/m²/day)`,
      savedAssessment?.id ? `Assessment ID: #${savedAssessment.id}` : 'Assessment ID: Unsaved (Interactive Estimate)',
      '',
      '-----------------------------------------------------------------',
      'SELECTED SOLAR SYSTEM SPECIFICATIONS',
      '-----------------------------------------------------------------',
      `Configuration Tier: ${selectedTier.tier_name}`,
      `Solar PV DC Capacity: ${selectedTier.dc_capacity_kwp} kWp`,
      `Inverter AC Grid Output: ${selectedTier.inverter_ac_kw} kW`,
      `Solar Modules Count: ${selectedTier.panel_count} units (${selectedTier.panel_wattage_wp}Wp Mono PERC)`,
      `Usable Rooftop Area Required: ${selectedTier.required_usable_area_sqft} sq ft`,
      `Estimated Daily Generation: ${selectedTier.daily_generation_kwh} kWh/day`,
      `Estimated Monthly Generation: ${selectedTier.monthly_generation_kwh} kWh/month`,
      `Estimated Annual Generation: ${selectedTier.annual_generation_kwh} kWh/year`,
      `Consumption Offset Target: ${selectedTier.consumption_offset_pct}%`,
      '',
      '-----------------------------------------------------------------',
      'FINANCIAL & TARIFF ECONOMICS (BERC 2026 TARIFF SCHEDULE)',
      '-----------------------------------------------------------------',
      `Estimated Turnkey Project Cost: Tk ${selectedTier.est_turnkey_cost_bdt_min.toLocaleString()} - Tk ${selectedTier.est_turnkey_cost_bdt_max.toLocaleString()}`,
      `Estimated Monthly Utility Bill Savings: Tk ${selectedTier.est_monthly_savings_bdt.toLocaleString()}`,
      `Estimated Annual Utility Bill Savings: Tk ${selectedTier.est_annual_savings_bdt.toLocaleString()}`,
      `Estimated Simple Payback Period: ${selectedTier.est_payback_years_min} - ${selectedTier.est_payback_years_max} Years`,
      'System Lifetime: 25 Years (PV Modules Warranted)',
      '',
      '-----------------------------------------------------------------',
      'SREDA 2025 NET METERING COMPLIANCE AUDIT',
      '-----------------------------------------------------------------',
      `Compliance Status: ${selectedTier.sreda_ac_compliant ? 'COMPLIANT' : 'SANCTION UPGRADE REQUIRED'}`,
      `Advisory Note: ${selectedTier.sreda_note}`,
      `Rule Reference: Inverter AC output must not exceed customer utility sanctioned load.`,
      '',
      '-----------------------------------------------------------------',
      'ESTIMATED 12-MONTH GENERATION PROFILE',
      '-----------------------------------------------------------------',
      ...monthlyData.map(m => `  ${m.month.padEnd(6)}: ${m.gen.toString().padStart(6)} kWh`),
      '',
      '-----------------------------------------------------------------',
      'DISCLAIMER & ENGINEERING NOTICE',
      '-----------------------------------------------------------------',
      rec.disclaimer,
      'A physical structural and electrical civil survey is required prior to hardware procurement.'
    ];

    const blob = new Blob([reportLines.join('\n')], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `RoofwiseBD_Solar_Report_${rec.division}_${selectedTier.dc_capacity_kwp}kWp.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleClaim = async () => {
    if (!savedAssessment?.id || !savedAssessment?.claim_token) return;
    setClaimLoading(true);
    setClaimMsg(null);
    try {
      const res = await api.claimAssessment(savedAssessment.id, savedAssessment.claim_token);
      setClaimed(true);
      setClaimMsg(res.message);
    } catch (err: any) {
      setClaimMsg(err.message || 'Unable to claim assessment.');
    } finally {
      setClaimLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 print:py-0 print:bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Action Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-2">
              <ShieldCheck className="w-4 h-4 text-solar-500" />
              <span>SREDA Net Metering 2025 & BERC 2026 Analysis</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Solar Recommendation Dashboard
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Location: <strong>{rec.division} Division</strong> • Baseline Irradiance:{' '}
              <strong>{rec.monthly_psh_avg} PSH/day</strong>
            </p>
          </div>

          <div className="flex items-center space-x-3 no-print">
            <button
              onClick={handleDownloadReport}
              className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-forest-900 text-white hover:bg-forest-800 shadow-sm cursor-pointer transition-colors"
              title="Download text engineering report"
            >
              <Download className="w-4 h-4 mr-2 text-solar-400" />
              <span>Download Report</span>
            </button>
            <button
              onClick={handlePrint}
              className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-xs cursor-pointer"
            >
              <Printer className="w-4 h-4 mr-2 text-slate-500" />
              <span>Print / Save PDF</span>
            </button>
            <Link
              to="/battery"
              className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-solar-500 text-forest-950 hover:bg-solar-400 shadow-sm transition-colors"
            >
              <BatteryCharging className="w-4 h-4 mr-2" />
              <span>Add Battery Backup</span>
            </Link>
          </div>
        </div>

        {/* Auth / Saved Assessment Status Banner */}
        {isAuthenticated ? (
          <div className="mb-6 p-4 rounded-2xl bg-forest-50 border border-forest-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-sm no-print">
            <div className="flex items-center space-x-3">
              <CheckCircle2 className="w-5 h-5 text-forest-800 flex-shrink-0" />
              <div>
                <p className="font-bold text-forest-950">
                  {claimed ? 'Assessment Claimed!' : 'Saved to your RoofwiseBD Account'}
                </p>
                <p className="text-xs text-forest-700">
                  {claimMsg || `This assessment is safely linked to ${user?.email}.`}
                </p>
              </div>
            </div>
            {savedAssessment?.claim_token && !claimed && (
              <button
                onClick={handleClaim}
                disabled={claimLoading}
                className="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-xs cursor-pointer"
              >
                {claimLoading ? 'Linking...' : 'Link to Account'}
              </button>
            )}
            <Link
              to="/dashboard"
              className="inline-flex items-center text-xs font-bold text-forest-900 hover:underline"
            >
              <LayoutDashboard className="w-3.5 h-3.5 mr-1" />
              <span>View Dashboard</span>
            </Link>
          </div>
        ) : (
          <div className="mb-6 p-4 rounded-2xl bg-amber-50 border border-amber-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-sm no-print">
            <div className="flex items-center space-x-3">
              <BookmarkPlus className="w-5 h-5 text-amber-700 flex-shrink-0" />
              <div>
                <p className="font-bold text-amber-950">Guest Solar Assessment</p>
                <p className="text-xs text-amber-800">
                  Sign in or create a free RoofwiseBD account to save this assessment and track your utility savings over time.
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Link
                to="/register"
                className="px-3.5 py-1.5 rounded-xl font-bold text-xs bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-xs"
              >
                Save to My Account
              </Link>
            </div>
          </div>
        )}

        {/* System Tiers Selector */}
        <div className="mb-8">
          <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">
            Choose System Configuration Option:
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[rec.recommended_system, ...rec.alternative_options].map((tier, idx) => {
              const isSelected = selectedTier.tier_name === tier.tier_name;
              return (
                <button
                  key={idx}
                  onClick={() => setSelectedTier(tier)}
                  className={`p-5 rounded-2xl text-left border transition-all ${
                    isSelected
                      ? 'bg-forest-950 text-white border-forest-900 ring-2 ring-forest-700 shadow-md'
                      : 'bg-white text-slate-800 border-slate-200 hover:border-slate-300 shadow-xs'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span
                      className={`text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full ${
                        isSelected
                          ? 'bg-forest-800 text-solar-300'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      {tier.tier_name.split('(')[0].trim()}
                    </span>
                    {tier.sreda_ac_compliant ? (
                      <span className="text-[10px] font-bold text-emerald-400 flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5 inline" />
                        <span>SREDA AC Compliant</span>
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold text-amber-400 flex items-center space-x-1">
                        <AlertTriangle className="w-3.5 h-3.5 inline" />
                        <span>Sanction Upgrade Req.</span>
                      </span>
                    )}
                  </div>

                  <p className="text-2xl font-extrabold tracking-tight mt-2">
                    {tier.dc_capacity_kwp} <span className="text-sm font-normal">kWp DC</span>
                  </p>
                  <p className={`text-xs mt-1 ${isSelected ? 'text-slate-300' : 'text-slate-500'}`}>
                    Inverter: {tier.inverter_ac_kw} kW AC • {tier.panel_count} Panels (550Wp)
                  </p>
                  <div className="mt-4 pt-3 border-t border-slate-200/20 flex justify-between text-xs">
                    <span className={isSelected ? 'text-slate-300' : 'text-slate-500'}>
                      Est. Savings:
                    </span>
                    <span className="font-bold text-solar-400">
                      ৳ {tier.est_monthly_savings_bdt.toLocaleString()} / mo
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Key Specs Card (2 cols) */}
          <div className="lg:col-span-2 bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {selectedTier.tier_name}
                </h2>
                <p className="text-xs text-slate-500 mt-1">
                  Engineered for Bangladesh residential rooftop conditions
                </p>
              </div>
              <span className="px-3 py-1 rounded-full text-xs font-bold bg-forest-100 text-forest-900">
                {selectedTier.consumption_offset_pct}% Bill Offset Target
              </span>
            </div>

            {/* Metric Boxes */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Solar PV Capacity</span>
                <p className="text-2xl font-extrabold text-forest-900 mt-1">
                  {selectedTier.dc_capacity_kwp}{' '}
                  <span className="text-xs font-normal text-slate-600">kWp</span>
                </p>
                <span className="text-[11px] text-slate-500 mt-0.5 block">DC Peak Power</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Inverter Capacity</span>
                <p className="text-2xl font-extrabold text-slate-900 mt-1">
                  {selectedTier.inverter_ac_kw}{' '}
                  <span className="text-xs font-normal text-slate-600">kW</span>
                </p>
                <span className="text-[11px] text-slate-500 mt-0.5 block">AC Grid Output</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Solar Panels</span>
                <p className="text-2xl font-extrabold text-slate-900 mt-1">
                  {selectedTier.panel_count}{' '}
                  <span className="text-xs font-normal text-slate-600">Units</span>
                </p>
                <span className="text-[11px] text-slate-500 mt-0.5 block">550Wp Mono PERC</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Roof Usable Space</span>
                <p className="text-2xl font-extrabold text-slate-900 mt-1">
                  {selectedTier.required_usable_area_sqft}{' '}
                  <span className="text-xs font-normal text-slate-600">sq ft</span>
                </p>
                <span className="text-[11px] text-slate-500 mt-0.5 block">Includes spacing</span>
              </div>
            </div>

            {/* SREDA 2025 Advisory Banner */}
            <div
              className={`p-4 rounded-xl border text-xs leading-relaxed flex items-start space-x-3 ${
                selectedTier.sreda_ac_compliant
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-900'
                  : 'bg-amber-50 border-amber-200 text-amber-900'
              }`}
            >
              {selectedTier.sreda_ac_compliant ? (
                <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              )}
              <div>
                <p className="font-bold">
                  SREDA Net Metering Guideline 2025: {selectedTier.sreda_ac_compliant ? 'Compliant' : 'Sanction Enhancement Needed'}
                </p>
                <p className="mt-0.5">{selectedTier.sreda_note}</p>
              </div>
            </div>

            {/* Monthly Generation Bar Chart */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-700">
                  Estimated 12-Month Generation Profile (kWh)
                </span>
                <span className="text-xs text-slate-500">
                  Annual Total: <strong>{selectedTier.annual_generation_kwh.toLocaleString()} kWh</strong>
                </span>
              </div>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={monthlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                    <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fontSize: 11, fill: '#64748b' }} axisLine={false} tickLine={false} />
                    <Tooltip
                      formatter={(val: number) => [`${val} kWh`, 'Estimated Yield']}
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                    />
                    <Bar dataKey="gen" fill="#166534" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Financial Breakdown Card (1 col) */}
          <div className="bg-forest-950 text-white p-6 sm:p-8 rounded-2xl shadow-md space-y-6 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex justify-between items-start border-b border-forest-900 pb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-widest text-solar-400">
                    Financial Economics
                  </span>
                  <h3 className="text-xl font-extrabold text-white mt-1">BERC 2026 Savings</h3>
                </div>
                <span className="text-xs bg-forest-900 text-forest-200 px-2.5 py-1 rounded-md border border-forest-800">
                  June 4 Slabs
                </span>
              </div>

              {/* Monthly Savings */}
              <div className="p-4 rounded-xl bg-forest-900/70 border border-forest-800">
                <span className="text-xs text-slate-400">Estimated Monthly Savings</span>
                <p className="text-3xl font-extrabold text-solar-400 mt-1">
                  ৳ {selectedTier.est_monthly_savings_bdt.toLocaleString()}
                </p>
                <p className="text-[11px] text-slate-400 mt-1">
                  Annual: ৳ {selectedTier.est_annual_savings_bdt.toLocaleString()} / year
                </p>
              </div>

              {/* Estimated Installation Cost Range */}
              <div className="space-y-2 text-xs">
                <div className="flex justify-between py-1.5 border-b border-forest-900">
                  <span className="text-slate-400">Turnkey Cost (Min)</span>
                  <span className="font-mono font-bold text-white">
                    ৳ {selectedTier.est_turnkey_cost_bdt_min.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-forest-900">
                  <span className="text-slate-400">Turnkey Cost (Max)</span>
                  <span className="font-mono font-bold text-white">
                    ৳ {selectedTier.est_turnkey_cost_bdt_max.toLocaleString()}
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-forest-900">
                  <span className="text-slate-400">Estimated Payback</span>
                  <span className="font-bold text-solar-400">
                    {selectedTier.est_payback_years_min} – {selectedTier.est_payback_years_max} Years
                  </span>
                </div>
                <div className="flex justify-between py-1.5 border-b border-forest-900">
                  <span className="text-slate-400">System Lifetime</span>
                  <span className="font-bold text-white">25 Years (Panels)</span>
                </div>
              </div>

              <div className="p-3 bg-forest-900/50 rounded-xl text-[11px] text-forest-300 border border-forest-800 leading-relaxed">
                Turnkey price range covers tier-1 on-grid components, aluminium mounting structures, AC/DC distribution boxes, and installation labor.
              </div>
            </div>

            <div className="space-y-3 pt-4">
              <Link
                to="/battery"
                className="w-full flex items-center justify-center px-4 py-3 rounded-xl text-sm font-bold bg-solar-500 text-forest-950 hover:bg-solar-400 transition-colors shadow-sm"
              >
                <BatteryCharging className="w-4 h-4 mr-2" />
                <span>Calculate Battery Addon</span>
              </Link>

              <Link
                to="/dust"
                className="w-full flex items-center justify-center px-4 py-2.5 rounded-xl text-xs font-semibold bg-forest-900 text-white hover:bg-forest-800 transition-colors border border-forest-800"
              >
                <Cpu className="w-4 h-4 mr-1.5 text-solar-400" />
                <span>AI Panel Dust Detector</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Current Tariff Breakdown Summary */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs mb-8">
          <h3 className="text-lg font-bold text-slate-900 mb-2">
            Your Monthly Utility Tariff Structure (BERC 2026 Schedule)
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Official residential tariff slabs with the June 4, 2026 tier restoration applied to your consumption.
          </p>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-200">
                <tr>
                  <th className="px-4 py-2.5">Tariff Slab</th>
                  <th className="px-4 py-2.5">Slab Rate (Tk/kWh)</th>
                  <th className="px-4 py-2.5">Units Billed</th>
                  <th className="px-4 py-2.5">Cost in Slab (BDT ৳)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {rec.tariff_breakdown.slab_breakdown.map((s, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/60">
                    <td className="px-4 py-2.5 font-bold text-slate-800">{s.slab}</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">Tk {s.rate.toFixed(2)}</td>
                    <td className="px-4 py-2.5 text-slate-800">{s.units.toFixed(1)} kWh</td>
                    <td className="px-4 py-2.5 font-bold text-slate-900 font-mono">
                      ৳ {s.cost_bdt.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot className="bg-slate-50/80 font-bold border-t border-slate-200 text-slate-900">
                <tr>
                  <td colSpan={3} className="px-4 py-2.5 text-right">
                    Total Estimated Bill (incl. demand charge, meter rent & VAT):
                  </td>
                  <td className="px-4 py-2.5 font-mono text-forest-900">
                    ৳ {rec.tariff_breakdown.total_bill_bdt.toFixed(2)}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Legal & Engineering Disclaimers */}
        <div className="p-6 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-600 space-y-2">
          <div className="flex items-center space-x-2 font-bold text-slate-800">
            <Info className="w-4 h-4 text-forest-700" />
            <span>Important Engineering & Regulatory Disclaimers</span>
          </div>
          <p>{rec.disclaimer}</p>
          <p>
            <strong>Structural Safety Notice:</strong> Rooftop area analysis provides spatial layout sizing.
            A formal civil structural load-bearing audit by a licensed engineer is required before physical installation.
          </p>
        </div>
      </div>
    </div>
  );
};
