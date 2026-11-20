import React from 'react';
import { CheckCircle2, AlertTriangle, Cpu } from 'lucide-react';

interface ModelStatusBadgeProps {
  status: string;
  isTrained?: boolean;
}

export const ModelStatusBadge: React.FC<ModelStatusBadgeProps> = ({ status, isTrained }) => {
  const isTrainedActive = isTrained || status.toLowerCase().includes('trained active');
  const isPhysics = status.toLowerCase().includes('physics');

  if (isTrainedActive) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
        <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-emerald-600" />
        Trained Model Active
      </span>
    );
  }

  if (isPhysics) {
    return (
      <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-blue-100 text-blue-800 border border-blue-300">
        <Cpu className="w-3.5 h-3.5 mr-1.5 text-blue-600" />
        NASA POWER Physics Engine
      </span>
    );
  }

  return (
    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-300">
      <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-amber-500" />
      Model Weights Pending
    </span>
  );
};
