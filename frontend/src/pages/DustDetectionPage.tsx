import React, { useState } from 'react';
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Info,
  Sparkles,
  Droplets,
  Calendar,
  Layers,
  Trash2
} from 'lucide-react';
import { api } from '../services/api';
import { DustPredictionResponse } from '../types';
import { ModelStatusBadge } from '../components/common/ModelStatusBadge';
import { DemoBadge } from '../components/common/DemoBadge';

export const DustDetectionPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState<boolean>(false);
  const [result, setResult] = useState<DustPredictionResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
      setErrorMsg(null);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setResult(null);
    setErrorMsg(null);
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setAnalyzing(true);
    setErrorMsg(null);
    try {
      const res = await api.predictDust(selectedFile);
      setResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Image analysis failed. Please check image file.');
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-8">
          <div>
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-2">
              <Cpu className="w-4 h-4 text-solar-500" />
              <span>Machine Learning 2 — MobileNetV2 Architecture</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Solar Panel Dust Detection AI
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Classify panel cleanliness (Clean vs Dusty) to prevent energy harvest loss from atmospheric dust in Bangladesh.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            {result && <ModelStatusBadge status={result.model_status} />}
          </div>
        </div>

        {/* Upload Card */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-xs mb-8">
          {!previewUrl ? (
            <div className="border-2 border-dashed border-slate-300 rounded-2xl p-10 text-center hover:border-forest-600 hover:bg-forest-50/30 transition-colors">
              <input
                type="file"
                id="dust-panel-upload"
                accept=".jpg,.jpeg,.png,.webp"
                onChange={handleFileChange}
                className="hidden"
              />
              <label htmlFor="dust-panel-upload" className="cursor-pointer block space-y-3">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-forest-50 text-forest-800 flex items-center justify-center shadow-xs">
                  <UploadCloud className="w-8 h-8 text-forest-700" />
                </div>
                <div>
                  <span className="font-bold text-slate-900 text-base">
                    Upload Solar Panel Photo
                  </span>
                  <p className="text-xs text-slate-500 mt-1">
                    Drag and drop or click to browse (JPG, PNG, WEBP)
                  </p>
                </div>
              </label>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="relative rounded-2xl overflow-hidden border border-slate-200 bg-slate-950 max-h-96 flex items-center justify-center">
                <img
                  src={previewUrl}
                  alt="Solar Panel Upload"
                  className="max-h-96 w-auto object-contain"
                />
                <button
                  onClick={handleClear}
                  className="absolute top-3 right-3 p-2 bg-slate-900/80 hover:bg-slate-900 text-white rounded-xl backdrop-blur-sm transition-colors shadow-md"
                  title="Remove image"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
                <div className="text-xs text-slate-500">
                  File: <strong>{selectedFile?.name}</strong> • Size:{' '}
                  <strong>{((selectedFile?.size || 0) / 1024).toFixed(1)} KB</strong>
                </div>

                <button
                  type="button"
                  disabled={analyzing}
                  onClick={handleAnalyze}
                  className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3 rounded-xl text-sm font-bold bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-sm disabled:opacity-50"
                >
                  {analyzing ? (
                    <span>Analyzing Image...</span>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2 text-solar-400" />
                      <span>Analyze Panel Cleanliness</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          )}
        </div>

        {errorMsg && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm">
            {errorMsg}
          </div>
        )}

        {/* Prediction Result Card */}
        {result && (
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm space-y-6 mb-8">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-100 pb-5">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Classification Result
                </span>
                <h3 className="text-2xl font-extrabold text-slate-900 mt-1 flex items-center space-x-3">
                  <span>Surface Status:</span>
                  <span
                    className={
                      result.classification === 'Dusty'
                        ? 'text-amber-600'
                        : 'text-emerald-700'
                    }
                  >
                    {result.classification}
                  </span>
                </h3>
              </div>

              <div className="flex items-center space-x-2">
                {result.is_demo && <DemoBadge label="HEURISTIC PREVIEW" />}
                <ModelStatusBadge status={result.model_status} />
              </div>
            </div>

            {/* Score & Dimensions */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Model Confidence</span>
                <p className="text-2xl font-extrabold text-slate-900 mt-1">
                  {result.model_score ? `${(result.model_score * 100).toFixed(1)}%` : 'N/A'}
                </p>
                <span className="text-[11px] text-slate-500">
                  {result.is_demo ? 'Preliminary heuristic' : 'Softmax probability'}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                <span className="text-xs text-slate-500 font-medium">Image Resolution</span>
                <p className="text-2xl font-extrabold text-slate-900 mt-1">
                  {result.image_width} × {result.image_height}
                </p>
                <span className="text-[11px] text-slate-500">Resampled to 224×224</span>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 col-span-2 sm:col-span-1">
                <span className="text-xs text-slate-500 font-medium">Architecture</span>
                <p className="text-sm font-bold text-forest-900 mt-2">MobileNetV2</p>
                <span className="text-[11px] text-slate-500">SolNet Classification</span>
              </div>
            </div>

            {/* Cleaning Advisory Box */}
            <div
              className={`p-5 rounded-xl border text-sm leading-relaxed space-y-2 ${
                result.classification === 'Dusty'
                  ? 'bg-amber-50 border-amber-200 text-amber-950'
                  : 'bg-emerald-50 border-emerald-200 text-emerald-950'
              }`}
            >
              <div className="flex items-center space-x-2 font-bold">
                <Droplets className="w-5 h-5 text-forest-700" />
                <span>Maintenance Recommendation</span>
              </div>
              <p>{result.cleaning_recommendation}</p>
              <p className="text-xs opacity-90 border-t border-slate-200/40 pt-2">
                <strong>Cleaning Protocol:</strong> {result.maintenance_tip}
              </p>
            </div>
          </div>
        )}

        {/* Academic Scope Notice */}
        <div className="p-6 rounded-2xl bg-slate-100 border border-slate-200 text-xs text-slate-600 space-y-2">
          <div className="flex items-center space-x-2 font-bold text-slate-900 text-sm">
            <Info className="w-4 h-4 text-forest-700" />
            <span>Academic Specification & Technical Scope</span>
          </div>
          <p className="leading-relaxed">
            RoofwiseBD's dust detection subsystem utilizes a <strong>MobileNetV2</strong> transfer learning
            pipeline designed for binary classification (Clean vs Dusty). It classifies overall module surface
            cleanliness from uploaded field photos and does not perform pixel-level semantic segmentation.
          </p>
          <p>
            When trained model weights (<code>mobilenetv2_dust.keras</code>) are absent from <code>models/dust/</code>,
            the service operates in transparent heuristic mode, clearly identified by the DEMO badge.
          </p>
        </div>
      </div>
    </div>
  );
};
