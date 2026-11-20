import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users,
  ShieldCheck,
  Zap,
  BarChart3,
  FileText,
  UserCheck,
  UserX,
  TrendingUp,
  Clock,
  MapPin,
  AlertCircle,
  CheckCircle2,
  Lock,
  Download,
  ArrowRight
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { AdminStats, AdminUserItem } from '../types';

export const AdminDashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [assessments, setAssessments] = useState<any[]>([]);
  const [activeTab, setActiveTab] = useState<'users' | 'assessments'>('users');
  const [loading, setLoading] = useState(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [actionErr, setActionErr] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsData, usersData, assessmentsData] = await Promise.all([
        api.getAdminStats(),
        api.getAdminUsers(),
        api.getAdminAssessments(50),
      ]);
      setStats(statsData);
      setUsers(usersData);
      setAssessments(assessmentsData);
    } catch (err: any) {
      setActionErr(err.message || 'Failed to fetch administrator data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleStatus = async (targetUser: AdminUserItem) => {
    setActionMsg(null);
    setActionErr(null);
    try {
      const res = await api.toggleUserStatus(targetUser.id, !targetUser.is_active);
      setActionMsg(res.message);
      // Refresh user list
      const updatedUsers = await api.getAdminUsers();
      setUsers(updatedUsers);
    } catch (err: any) {
      setActionErr(err.message || 'Status toggle failed.');
    }
  };

  const handleExportAssessmentsCSV = () => {
    if (assessments.length === 0) return;
    const headers = [
      'ID',
      'Date',
      'Type',
      'User_Email',
      'Division',
      'District',
      'Monthly_Units_kWh',
      'Capacity_kWp',
      'Inverter_AC_kW',
      'Panel_Count',
      'Monthly_Savings_BDT',
      'SREDA_Compliant'
    ];
    const rows = assessments.map(a => [
      a.id,
      new Date(a.created_at).toISOString().split('T')[0],
      a.is_guest ? 'Guest' : 'Registered',
      `"${a.user?.email || 'N/A'}"`,
      `"${a.division}"`,
      `"${a.district}"`,
      a.monthly_units_kwh,
      a.recommended_capacity_kwp,
      a.recommended_inverter_ac_kw,
      a.panel_count,
      Math.round(a.monthly_savings_bdt),
      a.sreda_compliant ? 'Yes' : 'No'
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `roofwise_admin_assessments_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleViewAssessment = async (record: any) => {
    try {
      const rec = await api.getSolarRecommendation({
        monthly_units_kwh: record.monthly_units_kwh,
        total_roof_area_sqft: 1200,
        sanctioned_load_kw: 3.0,
        division: record.division,
      });
      navigate('/recommendations', {
        state: {
          recommendation: rec,
          savedAssessment: record,
        },
      });
    } catch {
      navigate('/recommendations');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header Banner */}
      <div className="bg-slate-900 rounded-3xl p-6 sm:p-10 text-white shadow-xl border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <div className="inline-flex items-center px-3 py-1 rounded-full bg-amber-500/20 text-amber-400 text-xs font-bold uppercase tracking-wider mb-3 border border-amber-500/30">
            <ShieldCheck className="w-3.5 h-3.5 mr-1.5" />
            <span>Administrative Control Center</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-black tracking-tight">System Administration</h1>
          <p className="mt-2 text-sm text-slate-400 max-w-2xl">
            Live overview of registered users, solar assessments, role assignments, and system-wide energy metrics.
          </p>
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-800/80 px-4 py-2 rounded-xl border border-slate-700">
          <Lock className="w-4 h-4 text-amber-400" />
          <span>Logged in as: <strong className="text-white">{user?.email}</strong></span>
        </div>
      </div>

      {actionMsg && (
        <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-center space-x-2 text-emerald-800 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {actionErr && (
        <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-center space-x-2 text-rose-700 text-sm">
          <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />
          <span>{actionErr}</span>
        </div>
      )}

      {/* KPI Summary Cards */}
      {stats && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-700 flex items-center justify-center">
              <Users className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Users</p>
              <p className="text-2xl font-black text-slate-900 mt-0.5">
                {stats.total_users} <span className="text-xs font-normal text-slate-400">({stats.active_users} active)</span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-forest-50 text-forest-800 flex items-center justify-center">
              <FileText className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Assessments</p>
              <p className="text-2xl font-black text-slate-900 mt-0.5">
                {stats.total_assessments} <span className="text-xs font-normal text-slate-400">({stats.guest_assessments} guest)</span>
              </p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-solar-50 text-solar-700 flex items-center justify-center">
              <Zap className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Sized</p>
              <p className="text-2xl font-black text-slate-900 mt-0.5">{stats.total_capacity_kwp} kWp</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex items-center space-x-4">
            <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
              <TrendingUp className="w-6 h-6" />
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Est. Savings</p>
              <p className="text-2xl font-black text-emerald-700 mt-0.5">৳ {Math.round(stats.total_monthly_savings_bdt).toLocaleString()}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Control */}
      <div className="flex border-b border-slate-200 space-x-6">
        <button
          onClick={() => setActiveTab('users')}
          className={`pb-3 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'users'
              ? 'border-forest-900 text-forest-950'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          User Accounts ({users.length})
        </button>
        <button
          onClick={() => setActiveTab('assessments')}
          className={`pb-3 font-bold text-sm border-b-2 transition-all cursor-pointer ${
            activeTab === 'assessments'
              ? 'border-forest-900 text-forest-950'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          All Solar Assessments ({assessments.length})
        </button>
      </div>

      {/* Tab 1: User Management Table */}
      {activeTab === 'users' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100">
                  <th className="py-3.5 px-6">User</th>
                  <th className="py-3.5 px-6">Role</th>
                  <th className="py-3.5 px-6">Contact</th>
                  <th className="py-3.5 px-6">Assessments</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6">Joined</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6 font-semibold text-slate-900 whitespace-nowrap">
                      <div>
                        <span>{u.full_name}</span>
                        <span className="text-xs text-slate-400 block">{u.email}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                        u.role === 'admin' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-700'
                      }`}>
                        {u.role}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-slate-600 text-xs whitespace-nowrap">
                      <div>{u.phone || '—'}</div>
                      <div className="text-slate-400">{u.address || '—'}</div>
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap font-bold text-slate-700">
                      {u.assessment_count}
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      {u.is_active ? (
                        <span className="inline-flex items-center text-xs font-semibold text-emerald-700">
                          <UserCheck className="w-3.5 h-3.5 mr-1" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center text-xs font-semibold text-rose-600">
                          <UserX className="w-3.5 h-3.5 mr-1" />
                          Deactivated
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-slate-400 text-xs whitespace-nowrap">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6 text-right whitespace-nowrap">
                      {u.id === user?.id ? (
                        <span className="text-xs text-slate-400 italic">Current Session</span>
                      ) : (
                        <button
                          onClick={() => handleToggleStatus(u)}
                          className={`text-xs font-bold px-3 py-1.5 rounded-lg transition-colors cursor-pointer ${
                            u.is_active
                              ? 'text-rose-700 bg-rose-50 hover:bg-rose-100'
                              : 'text-emerald-700 bg-emerald-50 hover:bg-emerald-100'
                          }`}
                        >
                          {u.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: System Assessments Table */}
      {activeTab === 'assessments' && (
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
          <div className="p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">Platform Solar Assessments</h2>
              <p className="text-xs text-slate-500">All assessments recorded across residential users and guest evaluations.</p>
            </div>
            {assessments.length > 0 && (
              <button
                type="button"
                onClick={handleExportAssessmentsCSV}
                className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-bold bg-slate-100 text-slate-700 hover:bg-slate-200 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5 mr-1.5 text-slate-500" />
                <span>Export CSV ({assessments.length})</span>
              </button>
            )}
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-100">
                  <th className="py-3.5 px-6">ID & Date</th>
                  <th className="py-3.5 px-6">Account</th>
                  <th className="py-3.5 px-6">Location</th>
                  <th className="py-3.5 px-6">Consumption</th>
                  <th className="py-3.5 px-6">Capacity</th>
                  <th className="py-3.5 px-6">Monthly Savings</th>
                  <th className="py-3.5 px-6">SREDA Status</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {assessments.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-4 px-6 text-slate-600 whitespace-nowrap">
                      <div className="font-bold text-slate-900">#{a.id}</div>
                      <div className="text-xs text-slate-400">{new Date(a.created_at).toLocaleDateString()}</div>
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      {a.is_guest ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                          Guest Assessment
                        </span>
                      ) : (
                        <div>
                          <span className="font-semibold text-slate-900">{a.user?.full_name}</span>
                          <span className="text-xs text-slate-400 block">{a.user?.email}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-4 px-6 text-slate-800 whitespace-nowrap">
                      <div className="flex items-center text-xs">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400" />
                        <span>{a.district}, {a.division}</span>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-slate-700 whitespace-nowrap">
                      <span className="font-bold">{a.monthly_units_kwh}</span> kWh
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap font-bold text-forest-900">
                      {a.recommended_capacity_kwp} kWp
                      <span className="text-xs text-slate-400 block font-normal">{a.panel_count} panels ({a.recommended_inverter_ac_kw} kW AC)</span>
                    </td>
                    <td className="py-4 px-6 font-bold text-emerald-700 whitespace-nowrap">
                      ৳ {Math.round(a.monthly_savings_bdt).toLocaleString()}
                    </td>
                    <td className="py-4 px-6 whitespace-nowrap">
                      {a.sreda_compliant ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                          Compliant
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
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
        </div>
      )}
    </div>
  );
};
