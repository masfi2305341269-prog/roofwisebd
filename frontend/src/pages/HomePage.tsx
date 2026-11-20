import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Sun,
  Zap,
  ShieldCheck,
  BatteryCharging,
  Layers,
  ArrowRight,
  FileCheck2,
  Cpu,
  BarChart3,
  HelpCircle,
  ChevronDown,
  Building2,
  DollarSign,
  AlertCircle
} from 'lucide-react';
import { DemoBadge } from '../components/common/DemoBadge';

export const HomePage: React.FC = () => {
  const [activeFaq, setActiveFaq] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setActiveFaq(activeFaq === index ? null : index);
  };

  const faqs = [
    {
      q: 'How does RoofwiseBD calculate my rooftop solar potential?',
      a: 'RoofwiseBD evaluates your usable rooftop area (excluding parapet setbacks, staircase headrooms, and water tanks) along with location-specific multi-year NASA POWER solar irradiance data for your Bangladesh administrative division. It factors in modern monocrystalline panel dimensions (550Wp), system losses (PR ~ 0.78), and orientation to predict monthly energy yield in kWh.'
    },
    {
      q: 'What is the SREDA Net Metering Guideline 2025 rule?',
      a: 'Under the Bangladesh Net Metering Guideline 2025, the renewable energy converter\'s (inverter\'s) AC output capacity must not exceed the customer\'s sanctioned electrical load from the distribution utility. Systems above 10 kW typically require a three-phase connection. RoofwiseBD verifies compliance and notifies you if a utility sanction enhancement is needed.'
    },
    {
      q: 'How are electricity bill savings computed?',
      a: 'Savings are computed using the latest verified BERC 2026 residential tariff schedule (including the June 4, 2026 revision restoring the initial tiers). When your solar system offsets grid electricity, it first eliminates units billed in your highest tariff slab (up to Tk 17.03/kWh for consumption above 600 units), delivering significant bill reductions.'
    },
    {
      q: 'Can I use RoofwiseBD if I live outside Dhaka?',
      a: 'Yes. RoofwiseBD incorporates solar irradiance baseline data for all 8 administrative divisions of Bangladesh (Dhaka, Chattogram, Rajshahi, Khulna, Barishal, Sylhet, Rangpur, and Mymensingh) and supports residential addresses in all 64 districts.'
    },
    {
      q: 'Is a physical roof inspection still required?',
      a: 'Yes. While RoofwiseBD provides precise spatial sizing and electrical forecasts, a physical civil structural load-bearing audit by a certified engineer and utility approval (DESCO, DPDC, BPDB, NESCO, or BREB) are mandatory before installation.'
    }
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 1. Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-forest-50/70 via-white to-slate-50 pt-16 pb-20 lg:pt-24 lg:pb-32 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <div className="text-center max-w-3xl mx-auto space-y-6">
            <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-forest-100 border border-forest-300 text-forest-900 text-xs font-semibold shadow-xs">
              <Sun className="w-4 h-4 text-solar-500" />
              <span>Tailored for Bangladesh Residential Solar</span>
              <span className="text-forest-400">•</span>
              <span className="text-forest-800">BERC 2026 & SREDA 2025 Ready</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-forest-950 tracking-tight leading-tight">
              Make Your Rooftop <br className="hidden sm:inline" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-forest-800 via-forest-700 to-solar-600">
                Solar Ready
              </span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-600 leading-relaxed max-w-2xl mx-auto">
              Discover your rooftop solar potential, estimate electricity generation,
              and find the right solar system for your home in Bangladesh.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/assessment"
                className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-xl text-base font-bold bg-forest-900 text-white hover:bg-forest-800 transition-all shadow-md hover:shadow-lg"
              >
                <span>Calculate Solar Potential</span>
                <ArrowRight className="w-5 h-5 ml-2 text-solar-400" />
              </Link>
              <a
                href="#features"
                className="w-full sm:w-auto inline-flex items-center justify-center px-7 py-3.5 rounded-xl text-base font-semibold bg-white text-forest-900 border border-slate-300 hover:bg-slate-50 transition-all shadow-xs"
              >
                <span>Explore Features</span>
              </a>
            </div>

            {/* Quick Context Highlights */}
            <div className="pt-10 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Solar Resource</span>
                <p className="text-sm font-bold text-slate-800 mt-1">NASA POWER Multi-Year</p>
                <p className="text-[11px] text-slate-500">8 BD Divisions Mapped</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Electricity Tariff</span>
                <p className="text-sm font-bold text-slate-800 mt-1">BERC 2026 Schedule</p>
                <p className="text-[11px] text-slate-500">June 4 Tier Correction</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Net Metering</span>
                <p className="text-sm font-bold text-slate-800 mt-1">SREDA 2025 Rules</p>
                <p className="text-[11px] text-slate-500">AC Output ≤ Sanctioned Load</p>
              </div>
              <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs">
                <span className="text-xs text-slate-500 font-medium">Solar Hardware</span>
                <p className="text-sm font-bold text-slate-800 mt-1">550Wp Mono PERC</p>
                <p className="text-[11px] text-slate-500">Configurable Specifications</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 2. How RoofwiseBD Works */}
      <section className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-forest-700 mb-2">
              Simple 4-Step Process
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
              How RoofwiseBD Works
            </p>
            <p className="text-slate-600 mt-3 text-sm sm:text-base">
              A transparent, engineering-backed pathway from your electricity bill to clean solar generation.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            {/* Step 1 */}
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 relative group hover:border-forest-400 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-forest-900 text-solar-400 font-bold flex items-center justify-center text-lg shadow-sm mb-4">
                1
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Upload Electricity Bill</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Upload your DESCO, DPDC, BPDB, NESCO, or BREB monthly electricity bill or enter your monthly kWh consumption.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 relative group hover:border-forest-400 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-forest-900 text-solar-400 font-bold flex items-center justify-center text-lg shadow-sm mb-4">
                2
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Enter Rooftop Info</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Provide your gross roof area, roof type (flat RCC or tin shed), and shading condition for setback calculation.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 relative group hover:border-forest-400 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-forest-900 text-solar-400 font-bold flex items-center justify-center text-lg shadow-sm mb-4">
                3
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Analyze Solar Potential</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Our engine computes generation forecasts, required panel layouts, and checks SREDA net metering sanction constraints.
              </p>
            </div>

            {/* Step 4 */}
            <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 relative group hover:border-forest-400 transition-colors">
              <div className="w-12 h-12 rounded-xl bg-forest-900 text-solar-400 font-bold flex items-center justify-center text-lg shadow-sm mb-4">
                4
              </div>
              <h3 className="font-bold text-lg text-slate-900 mb-2">Get Recommendation</h3>
              <p className="text-slate-600 text-sm leading-relaxed">
                Receive 3 customized system tiers with BERC 2026 tariff savings, panel counts, inverter ratings, and printable report.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3. Main Features */}
      <section id="features" className="py-20 bg-slate-50 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-xs font-bold uppercase tracking-widest text-forest-700 mb-2">
              Advanced Tool Suite
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
              RoofwiseBD Core Features
            </p>
            <p className="text-slate-600 mt-3 text-sm sm:text-base">
              Explore intelligent tools designed around residential clean energy and power reliability.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-forest-50 text-forest-800 flex items-center justify-center mb-5">
                <Sun className="w-6 h-6 text-forest-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">Solar Generation Prediction</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Forecast hourly and monthly photovoltaic electricity generation in kWh based on NASA POWER irradiance data and XGBoost model architecture.
              </p>
              <Link to="/generation" className="inline-flex items-center text-sm font-semibold text-forest-800 hover:text-forest-950">
                <span>Simulate Generation</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>

            {/* Feature 2 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-800 flex items-center justify-center mb-5">
                <Cpu className="w-6 h-6 text-amber-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">AI Dust & Soiling Detection</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Upload photos of your solar panels to detect dust and particulate accumulation using MobileNetV2 architecture and receive scheduled cleaning advice.
              </p>
              <Link to="/dust" className="inline-flex items-center text-sm font-semibold text-amber-800 hover:text-amber-950">
                <span>Check Panel Cleanliness</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>

            {/* Feature 3 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-800 flex items-center justify-center mb-5">
                <Layers className="w-6 h-6 text-emerald-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">Rooftop Spatial Sizing</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Accurately estimates usable rooftop area by deducting parapet setbacks, staircase headrooms, and water tanks across RCC flat and tin roofs.
              </p>
              <Link to="/assessment" className="inline-flex items-center text-sm font-semibold text-emerald-800 hover:text-emerald-950">
                <span>Assess Rooftop Area</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>

            {/* Feature 4 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-800 flex items-center justify-center mb-5">
                <FileCheck2 className="w-6 h-6 text-blue-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">Electricity Bill Analysis</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Prioritizes actual kWh unit consumption over BDT currency amounts. Prepares OCR bill parsing with immediate manual confirmation fallback.
              </p>
              <Link to="/assessment" className="inline-flex items-center text-sm font-semibold text-blue-800 hover:text-blue-950">
                <span>Analyze Bill</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>

            {/* Feature 5 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-800 flex items-center justify-center mb-5">
                <Zap className="w-6 h-6 text-purple-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">Solar System Recommendation</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Generates 3 customized system options (Economical, Balanced, Maximum Capacity) strictly observing SREDA 2025 net metering inverter limits.
              </p>
              <Link to="/assessment" className="inline-flex items-center text-sm font-semibold text-purple-800 hover:text-purple-950">
                <span>View Recommendations</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>

            {/* Feature 6 */}
            <div className="bg-white p-7 rounded-2xl border border-slate-200 shadow-xs hover:shadow-md transition-shadow">
              <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-800 flex items-center justify-center mb-5">
                <BatteryCharging className="w-6 h-6 text-teal-700" />
              </div>
              <h3 className="font-bold text-xl text-slate-900 mb-3">Battery Backup Optimizer</h3>
              <p className="text-slate-600 text-sm leading-relaxed mb-4">
                Calculate critical load during load shedding using real appliance inventories, configurable Depth of Discharge (DoD), and preliminary dispatch schedules.
              </p>
              <Link to="/battery" className="inline-flex items-center text-sm font-semibold text-teal-800 hover:text-teal-950">
                <span>Optimize Backup</span>
                <ArrowRight className="w-4 h-4 ml-1" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 4. Why Rooftop Solar in Bangladesh */}
      <section className="py-20 bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-6">
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold">
                <span>Local Context</span>
              </div>
              <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
                Why Rooftop Solar Makes Sense in Bangladesh
              </h2>
              <p className="text-slate-600 leading-relaxed">
                With rising residential electricity tariffs under BERC 2026 revisions and seasonal grid stress,
                rooftop solar provides predictable cost hedging and critical appliance resilience.
              </p>

              <div className="space-y-4 pt-2">
                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-forest-100 text-forest-800 flex items-center justify-center shrink-0 mt-0.5">
                    <DollarSign className="w-5 h-5 text-forest-700" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900">Highest Tier Tariff Relief</h4>
                    <p className="text-sm text-slate-600">
                      Units above 600 kWh are billed at Tk 17.03/kWh (plus VAT and demand fees). Solar energy offsets these peak slab charges first.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-forest-100 text-forest-800 flex items-center justify-center shrink-0 mt-0.5">
                    <ShieldCheck className="w-5 h-5 text-forest-700" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900">SREDA Net Metering 2025</h4>
                    <p className="text-sm text-slate-600">
                      Surplus daytime generation can be credited against night-time grid usage through bi-directional net meters.
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <div className="w-8 h-8 rounded-lg bg-forest-100 text-forest-800 flex items-center justify-center shrink-0 mt-0.5">
                    <BatteryCharging className="w-5 h-5 text-forest-700" />
                  </div>
                  <div>
                    <h4 className="font-bold text-slate-900">Load Shedding Protection</h4>
                    <p className="text-sm text-slate-600">
                      Hybrid battery storage maintains critical lights, fans, refrigerators, and internet routers during power outages.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Visual Card */}
            <div className="bg-forest-950 text-white p-8 sm:p-10 rounded-3xl shadow-xl space-y-6 relative overflow-hidden">
              <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-forest-800/30 rounded-full blur-3xl"></div>
              <div className="relative z-10 space-y-6">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-xs uppercase tracking-widest text-solar-400 font-bold">
                      Bangladesh Tariff Reference
                    </span>
                    <h3 className="text-2xl font-bold text-white mt-1">BERC 2026 Schedule</h3>
                  </div>
                  <span className="px-2.5 py-1 rounded-md text-xs font-semibold bg-forest-900 text-forest-200 border border-forest-800">
                    Official Rates
                  </span>
                </div>

                <div className="space-y-2 text-sm divide-y divide-forest-900">
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Lifeline (0–50 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 4.63 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Step 1 (0–75 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 5.26 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Slab 2 (76–200 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 8.50 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Slab 3 (201–300 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 9.10 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Slab 4 (301–400 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 9.62 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Slab 5 (401–600 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 15.01 / kWh</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-300">Slab 6 (Above 600 kWh)</span>
                    <span className="font-mono font-bold text-solar-400">Tk 17.03 / kWh</span>
                  </div>
                </div>

                <div className="p-3 bg-forest-900/80 rounded-xl text-xs text-forest-200 border border-forest-800">
                  Includes June 4, 2026 correction restoring the initial two tiers. Demand charges and utility VAT apply separately.
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 5. FAQs */}
      <section className="py-20 bg-slate-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-xs font-bold uppercase tracking-widest text-forest-700 mb-2">
              Questions & Answers
            </h2>
            <p className="text-3xl font-extrabold text-slate-900 tracking-tight">
              Frequently Asked Questions
            </p>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-xs"
              >
                <button
                  onClick={() => toggleFaq(idx)}
                  className="w-full px-6 py-4 text-left flex justify-between items-center hover:bg-slate-50 transition-colors"
                >
                  <span className="font-bold text-slate-900 text-base">{faq.q}</span>
                  <ChevronDown
                    className={`w-5 h-5 text-slate-500 transition-transform ${
                      activeFaq === idx ? 'rotate-180 text-forest-800' : ''
                    }`}
                  />
                </button>
                {activeFaq === idx && (
                  <div className="px-6 pb-5 text-sm text-slate-600 leading-relaxed border-t border-slate-100 pt-3">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="mt-12 text-center">
            <Link
              to="/assessment"
              className="inline-flex items-center px-6 py-3 rounded-xl text-sm font-bold bg-forest-900 text-white hover:bg-forest-800 shadow-sm"
            >
              <span>Ready to start? Assess your rooftop now</span>
              <ArrowRight className="w-4 h-4 ml-2 text-solar-400" />
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
};
