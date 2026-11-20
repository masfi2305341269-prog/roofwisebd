import React from 'react';
import { Link } from 'react-router-dom';
import { Sun, Shield, ExternalLink, FileText, CheckCircle2 } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-forest-950 text-slate-300 pt-16 pb-12 border-t border-forest-900 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-10 pb-12 border-b border-forest-900">
          {/* Brand Info */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-forest-900 flex items-center justify-center text-solar-400">
                <Sun className="w-5 h-5" />
              </div>
              <span className="font-extrabold text-xl tracking-tight text-white font-sans">
                Roofwise<span className="text-solar-400">BD</span>
              </span>
            </div>
            <p className="text-sm text-slate-400 leading-relaxed">
              University Software Engineering platform dedicated to residential rooftop solar
              potential estimation, dust detection, and SREDA 2025 net metering compliance in Bangladesh.
            </p>
            <div className="flex items-center space-x-2 text-xs text-forest-300 bg-forest-900/60 px-3 py-1.5 rounded-lg border border-forest-800">
              <Shield className="w-4 h-4 text-solar-400" />
              <span>BERC 2026 Tariff Sched. & SREDA 2025 Net Metering</span>
            </div>
          </div>

          {/* Core Tools */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Core Capabilities
            </h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li>
                <Link to="/assessment" className="hover:text-solar-300 transition-colors">
                  Rooftop Solar Wizard
                </Link>
              </li>
              <li>
                <Link to="/generation" className="hover:text-solar-300 transition-colors">
                  Solar Generation Forecasting
                </Link>
              </li>
              <li>
                <Link to="/dust" className="hover:text-solar-300 transition-colors">
                  Panel Dust Detection (AI)
                </Link>
              </li>
              <li>
                <Link to="/battery" className="hover:text-solar-300 transition-colors">
                  Battery Backup Optimizer
                </Link>
              </li>
              <li>
                <Link to="/status" className="hover:text-solar-300 transition-colors">
                  AI Model Registry & Status
                </Link>
              </li>
            </ul>
          </div>

          {/* Energy Policy & Standards */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Standards & Guidelines
            </h4>
            <ul className="space-y-2 text-sm text-slate-400">
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-forest-400" />
                <span>SREDA Net Metering Guideline 2025</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-forest-400" />
                <span>BERC 2026 Residential Tariff Schedule</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-forest-400" />
                <span>NASA POWER Solar Agroclimatology</span>
              </li>
              <li className="flex items-center space-x-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-forest-400" />
                <span>SolNet Dust Dataset Architecture</span>
              </li>
            </ul>
          </div>

          {/* Disclaimers & Notice */}
          <div>
            <h4 className="text-white font-semibold text-sm uppercase tracking-wider mb-4">
              Engineering Notice
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Calculations provide preliminary sizing, energy yield forecasts, and financial estimates.
              A professional civil structural engineering inspection and power utility (DESCO / DPDC / BPDB / NESCO / BREB)
              approval are mandatory before physical installation.
            </p>
          </div>
        </div>

        <div className="pt-8 flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500">
          <p>© {new Date().getFullYear()} RoofwiseBD. Academic Software Engineering Project.</p>
          <p className="mt-2 sm:mt-0 text-slate-400">
            Tailored for Bangladesh's residential clean energy transition.
          </p>
        </div>
      </div>
    </footer>
  );
};
