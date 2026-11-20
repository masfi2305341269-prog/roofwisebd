import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Sun,
  Zap,
  BarChart3,
  TrendingUp,
  Calendar,
  MapPin,
  ArrowRight,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Clock,
  Download
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { SavedAssessmentRecord } from '../types';

export const UserDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [assessments, setAssessments] = useState<SavedAssessmentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        const data = await api.getUserAssessments();
        setAssessments(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load your assessments.');
      } finally {
        setLoading(false);
      }
    };

    fetchAssessments();
  }, []);

  // Compute Aggregates
  const totalCapacityKWp = assessments.reduce((acc, curr) => acc + curr.recommended_capacity_kwp, 0);
  const totalAnnualGenKWh = assessments.reduce((acc, curr) => acc + curr.annual_generation_kwh, 0);
  const totalMonthlySavingsBDT = assessments.reduce((acc, curr) => acc + curr.monthly_savings_bdt, 0);

  const handleViewAssessment = async (record: SavedAssessmentRecord) => {
    // Generate recommendation parameters for this assessment and navigate to recommendations view
    try {
      const rec = await api.getSolarRecommendation({
        monthly_units_kwh: record.monthly_units_kwh,
        total_roof_area_sqft: record.total_area_sqft,
        sanctioned_load_kw: record.sanctioned_load_kw,
        division: record.division,
        roof_type: record.roof_type,
        shading_condition: record.shading_condition,
        usable_roof_area_sqft: record.usable_area_sqft,
      });

      navigate('/recommendations', {
        state: {
          recommendation: rec,
          recommendationData: rec,
          assessment: {
            location: { division: record.division, district: record.district, area: record.area },
            consumption: {
              monthly_units_kwh: record.monthly_units_kwh,
              billing_period_days: record.billing_period_days,
              bill_amount_bdt: record.bill_amount_bdt,
              sanctioned_load_kw: record.sanctioned_load_kw,
              consumer_category: record.consumer_category,
            },
            rooftop: {
              total_area_sqft: record.total_area_sqft,
              usable_area_sqft: record.usable_area_sqft,
              roof_type: record.roof_type,
              shading_condition: record.shading_condition,
              orientation: record.orientation,
              tilt_degrees: record.tilt_degrees,
            },
          },
          savedAssessment: record,
          assessmentResponse: {
            id: record.id,
            created_at: record.created_at,
            location: { division: record.division, district: record.district, area: record.area },
            consumption: {
              monthly_units_kwh: record.monthly_units_kwh,
              billing_period_days: record.billing_period_days,
              bill_amount_bdt: record.bill_amount_bdt,
              sanctioned_load_kw: record.sanctioned_load_kw,
              consumer_category: record.consumer_category,
            },
            rooftop: {
              total_area_sqft: record.total_area_sqft,
              usable_area_sqft: record.usable_area_sqft,
              roof_type: record.roof_type,
              shading_condition: record.shading_condition,
              orientation: record.orientation,
              tilt_degrees: record.tilt_degrees,
            },
            recommended_capacity_kwp: record.recommended_capacity_kwp,
            recommended_inverter_ac_kw: record.recommended_inverter_ac_kw,
            panel_count: record.panel_count,
            daily_generation_kwh: record.daily_generation_kwh,
            monthly_generation_kwh: record.monthly_generation_kwh,
            annual_generation_kwh: record.annual_generation_kwh,
            monthly_savings_bdt: record.monthly_savings_bdt,
            estimated_payback_years: record.estimated_payback_years,
            sreda_compliant: record.sreda_compliant,
            sreda_advisory: rec.sreda_compliance.advisory_text,
            structural_disclaimer: rec.disclaimer,
            is_guest: false,
          },
        },
      });
    } catch {
      // Fallback
      navigate('/assessment');
    }
  };

  const handleExportCSV = () => {
    if (assessments.length === 0) return;
    const headers = [
      'ID',
      'Date',
      'Division',
      'District',
      'Monthly_Units_kWh',
      'Sanctioned_Load_kW',
      'Capacity_kWp',
      'Inverter_AC_kW',
      'Panel_Count',
      'Monthly_Savings_BDT',
      'Annual_Generation_kWh',
      'SREDA_Compliant'
    ];
    const rows = assessments.map(a => [
      a.id,
      new Date(a.created_at).toISOString().split('T')[0],
      `"${a.division}"`,
      `"${a.district}"`,
      a.monthly_units_kwh,
      a.sanctioned_load_kw,
      a.recommended_capacity_kwp,
      a.recommended_inverter_ac_kw,
      a.panel_count,
      Math.round(a.monthly_savings_bdt),
      Math.round(a.annual_generation_kwh),
      a.sreda_compliant ? 'Yes' : 'No'
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `roofwise_assessments_${(user?.full_name || 'portfolio').replace(/\s+/g, '_').toLowerCase()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-forest-950 via-forest-900 to-forest-800 rounded-3xl p-6 sm:p-10 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-solar-500/20 text-solar-300 text-xs font-bold uppercase tracking-wider mb-3 border border-solar-500/30">
              <Sun className="w-3.5 h-3.5 mr-1.5" />
              <span>Residential Solar Dashboard</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight">
              Welcome back, {user?.full_name.split(' ')[0]}!
            </h1>
            <p className="mt-2 text-sm sm:text-base text-slate-300 max-w-2xl leading-relaxed">
              Track your evaluated rooftop solar projects, monitor estimated monthly utility savings
              under the BERC 2026 tariff, and verify SREDA 2025 net metering compliance.
            </p>
          </div>
          <Link
            to="/assessment"
            className="inline-flex items-center justify-center px-5 py-3 rounded-xl font-bold text-sm bg-solar-500 text-forest-950 hover:bg-solar-400 transition-all shadow-lg hover:shadow-solar-500/20 flex-shrink-0 cursor-pointer"
          >
            <span>New Solar Assessment</span>
            <ArrowRight className="w-4 h-4 ml-2" />
          </Link>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-forest-50 text-forest-800 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Assessments</p>
            <p className="text-2xl font-black text-forest-950 mt-0.5">{assessments.length}</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-solar-50 text-solar-700 flex items-center justify-center">
            <Zap className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Potential Capacity</p>
            <p className="text-2xl font-black text-forest-950 mt-0.5">{totalCapacityKWp.toFixed(2)} kWp</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Annual Generation</p>
            <p className="text-2xl font-black text-forest-950 mt-0.5">{Math.round(totalAnnualGenKWh).toLocaleString()} kWh</p>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Monthly Savings</p>
            <p className="text-2xl font-black text-emerald-700 mt-0.5">৳ {Math.round(totalMonthlySavingsBDT).toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Saved Assessments Table */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-forest-950">Your Saved Assessments</h2>
            <p className="text-xs text-slate-500">History of rooftop evaluations conducted on this account.</p>
          </div>
          <div className="flex items-center space-x-3">
            {assessments.length > 0 && (
              <button
                type="button"
                onClick={handleExportCSV}
                className="inline-flex items-center px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 mr-1 text-slate-500" />
                <span>Export CSV</span>
              </button>
            )}
            <span className="text-xs font-semibold text-slate-400">
              {assessments.length} {assessments.length === 1 ? 'record' : 'records'}
            </span>
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="inline-block w-8 h-8 border-3 border-forest-800 border-t-transparent rounded-full animate-spin" />
            <p className="mt-3 text-xs text-slate-500 font-medium">Loading saved assessments...</p>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-rose-600 text-sm">{error}</div>
        ) : assessments.length === 0 ? (
          <div className="p-12 text-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-slate-100 text-slate-400 flex items-center justify-center mx-auto">
              <FileText className="w-8 h-8" />
            </div>
            <div>
              <p className="font-bold text-slate-700">No assessments saved yet</p>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Run your first rooftop solar assessment to see tailored recommendations, cost estimates, and savings.
              </p>
            </div>
            <Link
              to="/assessment"
              className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-bold bg-forest-900 text-white hover:bg-forest-800 transition-all shadow-sm"
            >
              <span>Start Assessment</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1.5" />
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100">
                  <th className="py-3.5 px-6">Date</th>
                  <th className="py-3.5 px-6">Location</th>
                  <th className="py-3.5 px-6">Consumption</th>
                  <th className="py-3.5 px-6">Sized Capacity</th>
                  <th className="py-3.5 px-6">Monthly Savings</th>
                  <th className="py-3.5 px-6">SREDA Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6 text-slate-600 whitespace-nowrap">
                      <div className="flex items-center text-xs">
                        <Clock className="w-3.5 h-3.5 mr-1.5 text-slate-400" />
                        <span>{new Date(a.created_at).toLocaleDateString()}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 font-semibold text-slate-900 whitespace-nowrap">
                      <div className="flex items-center">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        <span>{a.district}, {a.division}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-slate-700 whitespace-nowrap">
                      <span className="font-bold">{a.monthly_units_kwh}</span> kWh
                      <span className="text-xs text-slate-400 ml-1.5">({a.sanctioned_load_kw} kW load)</span>
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      <span className="font-bold text-forest-900">{a.recommended_capacity_kwp} kWp</span>
                      <span className="text-xs text-slate-400 block">{a.panel_count} modules ({a.recommended_inverter_ac_kw} kW AC)</span>
                    </td>
                    <td className="py-4 px-6 font-bold text-emerald-700 whitespace-nowrap">
                      ৳ {Math.round(a.monthly_savings_bdt).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      {a.sreda_compliant ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                          Compliant
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                          <AlertTriangle className="w-3.5 h-3.5 mr-1" />
                          Exceeds Load
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right whitespace-nowrap">
                      <button
                        onClick={() => handleViewAssessment(a)}
                        className="inline-flex items-center text-xs font-bold text-forest-800 hover:text-forest-950 hover:underline cursor-pointer"
                      >
                        <span>View Report</span>
                        <ArrowRight className="w-3.5 h-3.5 ml-1" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
