import React, { useState, useEffect } from 'react';
import {
  Cpu,
  Database,
  CheckCircle2,
  AlertTriangle,
  FolderOpen,
  Layers,
  FileText,
  ShieldCheck,
  RefreshCw,
  Info,
  Server
} from 'lucide-react';
import { api } from '../services/api';
import { SystemStatusResponse } from '../types';
import { ModelStatusBadge } from '../components/common/ModelStatusBadge';

export const SystemStatusPage: React.FC = () => {
  const [status, setStatus] = useState<SystemStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchStatus = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await api.getSystemStatus();
      setStatus(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Unable to connect to backend status API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-2">
              <Server className="w-4 h-4 text-solar-500" />
              <span>Academic Transparency & Model Registry</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              System Architecture & Model Registry
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Live inspection of machine learning models, raw dataset storage directories, and regulatory standards.
            </p>
          </div>

          <button
            onClick={fetchStatus}
            disabled={loading}
            className="inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-300 text-slate-700 hover:bg-slate-50 shadow-xs"
          >
            <RefreshCw className={`w-4 h-4 mr-2 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Registry</span>
          </button>
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm">
            {errorMsg}
          </div>
        )}

        {status && (
          <div className="space-y-8">
            {/* System Overview Bar */}
            <div className="bg-forest-950 text-white p-6 rounded-2xl shadow-md grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <span className="text-xs text-slate-400">Application</span>
                <p className="text-lg font-bold text-white mt-0.5">{status.app_name} v{status.version}</p>
                <span className="text-[11px] text-solar-400 font-mono">{status.python_runtime}</span>
              </div>

              <div>
                <span className="text-xs text-slate-400">Electricity Tariff</span>
                <p className="text-sm font-bold text-white mt-1">{status.berc_tariff_schedule}</p>
                <span className="text-[11px] text-emerald-400">Active Multi-Slab</span>
              </div>

              <div>
                <span className="text-xs text-slate-400">Grid Policy</span>
                <p className="text-sm font-bold text-white mt-1">{status.sreda_guideline_active}</p>
                <span className="text-[11px] text-emerald-400">Inverter AC ≤ Sanctioned</span>
              </div>

              <div>
                <span className="text-xs text-slate-400">Readiness Status</span>
                <p className="text-sm font-bold text-solar-300 mt-1">Operational</p>
                <span className="text-[11px] text-slate-300">Ready for weights</span>
              </div>
            </div>

            {/* Section 1: Machine Learning Models */}
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-forest-700" />
                <span>Machine Learning Subsystems Status</span>
              </h2>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {status.models.map((m) => (
                  <div
                    key={m.id}
                    className="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs space-y-4"
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <span className="text-xs font-mono font-bold text-slate-500 uppercase">
                          {m.id}
                        </span>
                        <h3 className="text-lg font-bold text-slate-900 mt-0.5">{m.name}</h3>
                      </div>
                      <ModelStatusBadge status={m.status} isTrained={m.model_file_found} />
                    </div>

                    <div className="space-y-2 text-xs divide-y divide-slate-100">
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-500">Algorithm</span>
                        <span className="font-bold text-slate-800">{m.algorithm}</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-500">Framework</span>
                        <span className="font-mono text-slate-700">{m.framework}</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-500">Expected File</span>
                        <span className="font-mono text-slate-700">{m.model_file_expected}</span>
                      </div>
                      <div className="flex justify-between py-1.5">
                        <span className="text-slate-500">Weights Detected</span>
                        <span
                          className={`font-bold ${
                            m.model_file_found ? 'text-emerald-600' : 'text-slate-500'
                          }`}
                        >
                          {m.model_file_found ? 'Yes (Loaded)' : 'No (Heuristic / Baseline Active)'}
                        </span>
                      </div>
                    </div>

                    <div>
                      <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block mb-1">
                        Planned Input Features:
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {m.input_features_planned.map((feat, i) => (
                          <span
                            key={i}
                            className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-md font-mono text-[10px]"
                          >
                            {feat}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="p-3 bg-slate-50 rounded-xl text-xs text-slate-600 border border-slate-100 space-y-1">
                      <p>
                        <strong>Scope:</strong> {m.academic_scope}
                      </p>
                      <p className="text-amber-800">
                        <strong>Limitations:</strong> {m.limitations}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Section 2: Datasets Directory Audit */}
            <div>
              <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center space-x-2">
                <Database className="w-5 h-5 text-forest-700" />
                <span>Planned Datasets Storage Structure (data/raw/)</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                {status.datasets.map((d) => (
                  <div
                    key={d.id}
                    className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs space-y-3"
                  >
                    <div className="flex justify-between items-start">
                      <div className="w-10 h-10 rounded-xl bg-forest-50 text-forest-800 flex items-center justify-center">
                        <FolderOpen className="w-5 h-5 text-forest-700" />
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          d.file_count > 0
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {d.file_count > 0 ? `${d.file_count} Files` : 'Empty Dir'}
                      </span>
                    </div>

                    <div>
                      <h4 className="font-bold text-sm text-slate-900">{d.name}</h4>
                      <p className="text-[11px] font-mono text-slate-500 mt-0.5">{d.folder_path}</p>
                    </div>

                    <p className="text-xs text-slate-600 leading-relaxed">{d.description}</p>

                    <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500 flex justify-between">
                      <span>Total Size:</span>
                      <span className="font-mono font-bold text-slate-700">{d.total_size_mb} MB</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Dataset Audit CLI Guide */}
            <div className="p-6 rounded-2xl bg-slate-900 text-white space-y-3">
              <div className="flex items-center space-x-2 text-sm font-bold text-solar-400">
                <ShieldCheck className="w-4 h-4" />
                <span>Dataset Integrity Audit Tool (CLI)</span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Before model training, execute the dataset audit tool to inspect CSV schemas, row counts, missing values, image dimensions, and corrupted files:
              </p>
              <pre className="p-3 bg-slate-950 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto">
                python scripts/audit_datasets.py
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
