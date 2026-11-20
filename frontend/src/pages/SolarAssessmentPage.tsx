import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MapPin,
  Zap,
  UploadCloud,
  Home,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  AlertCircle,
  Info,
  FileText,
  Trash2,
  Eye,
  ShieldCheck,
  Compass
} from 'lucide-react';
import { api } from '../services/api';

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

const BD_DISTRICTS: Record<string, string[]> = {
  Dhaka: ['Dhaka', 'Gazipur', 'Narayanganj', 'Tangail', 'Faridpur', 'Narsingdi', 'Manikganj', 'Munshiganj'],
  Chattogram: ['Chattogram', "Cox's Bazar", 'Cumilla', 'Feni', 'Noakhali', 'Brahmanbaria', 'Chandpur', 'Rangamati'],
  Rajshahi: ['Rajshahi', 'Bogura', 'Pabna', 'Sirajganj', 'Naogaon', 'Natore', 'Chapai Nawabganj', 'Joypurhat'],
  Khulna: ['Khulna', 'Jashore', 'Kushtia', 'Satkhira', 'Jhenaidah', 'Bagerhat', 'Chuadanga', 'Magura'],
  Barishal: ['Barishal', 'Patuakhali', 'Bhola', 'Pirojpur', 'Jhalokati', 'Barguna'],
  Sylhet: ['Sylhet', 'Moulvibazar', 'Habiganj', 'Sunamganj'],
  Rangpur: ['Rangpur', 'Dinajpur', 'Kurigram', 'Gaibandha', 'Nilphamari', 'Lalmonirhat', 'Thakurgaon', 'Panchagarh'],
  Mymensingh: ['Mymensingh', 'Jamalpur', 'Netrokona', 'Sherpur'],
};

export const SolarAssessmentPage: React.FC = () => {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  // Step 1: Location
  const [division, setDivision] = useState('Dhaka');
  const [district, setDistrict] = useState('Dhaka');
  const [area, setArea] = useState('Mirpur');
  const [lat, setLat] = useState<number | undefined>(23.8103);
  const [lng, setLng] = useState<number | undefined>(90.4125);

  // Step 2: Consumption
  const [monthlyUnits, setMonthlyUnits] = useState<number>(350);
  const [billingPeriodDays, setBillingPeriodDays] = useState<number>(30);
  const [billAmountBdt, setBillAmountBdt] = useState<number | undefined>(3100);
  const [sanctionedLoad, setSanctionedLoad] = useState<number>(3.0);
  const [consumerCategory, setConsumerCategory] = useState('Residential');

  // Step 3: Bill Upload
  const [billFile, setBillFile] = useState<File | null>(null);
  const [billFilePreview, setBillFilePreview] = useState<string | null>(null);
  const [billUploadProgress, setBillUploadProgress] = useState(false);
  const [ocrStatusMessage, setOcrStatusMessage] = useState<string | null>(null);

  // Step 4: Rooftop Info
  const [totalRoofArea, setTotalRoofArea] = useState<number>(1200);
  const [customUsableArea, setCustomUsableArea] = useState<number | undefined>(undefined);
  const [roofType, setRoofType] = useState<'concrete_flat' | 'tin_shed' | 'tiled'>('concrete_flat');
  const [shadingCondition, setShadingCondition] = useState<'none' | 'low' | 'medium' | 'heavy'>('low');
  const [orientation, setOrientation] = useState('South');
  const [tiltDegrees, setTiltDegrees] = useState(23.0);
  const [roofPhoto, setRoofPhoto] = useState<File | null>(null);
  const [roofPhotoPreview, setRoofPhotoPreview] = useState<string | null>(null);
  const [roofImageUrl, setRoofImageUrl] = useState<string | null>(null);
  const [roofPhotoUploading, setRoofPhotoUploading] = useState(false);
  const [roofPhotoMessage, setRoofPhotoMessage] = useState<string | null>(null);

  const handleDivisionChange = (newDiv: string) => {
    setDivision(newDiv);
    const districts = BD_DISTRICTS[newDiv] || [];
    setDistrict(districts[0] || newDiv);
  };

  const handleBillFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setBillFile(file);
      if (file.type.startsWith('image/')) {
        setBillFilePreview(URL.createObjectURL(file));
      } else {
        setBillFilePreview(null);
      }
      setBillUploadProgress(true);
      try {
        const analysis = await api.analyzeBill(file, Number(monthlyUnits), billAmountBdt ? Number(billAmountBdt) : undefined);
        setOcrStatusMessage(
          `Analyzed "${file.name}" (${analysis.file_size_kb} KB): ${analysis.ocr_engine_message}`
        );
        if (analysis.extracted_units_kwh && !monthlyUnits) {
          setMonthlyUnits(analysis.extracted_units_kwh);
        }
      } catch {
        setOcrStatusMessage(
          `Uploaded "${file.name}" (${(file.size / 1024).toFixed(1)} KB). Please verify your monthly units below.`
        );
      } finally {
        setBillUploadProgress(false);
      }
    }
  };

  const removeBillFile = () => {
    setBillFile(null);
    setBillFilePreview(null);
    setOcrStatusMessage(null);
  };

  const handleRoofPhotoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setRoofPhoto(file);
      setRoofPhotoPreview(URL.createObjectURL(file));
      setRoofPhotoUploading(true);
      try {
        const res = await api.uploadRooftopImage(file);
        setRoofImageUrl(res.image_url);
        setRoofPhotoMessage(`Uploaded "${file.name}" (${res.file_size_kb} KB). Ready for spatial evaluation.`);
      } catch (err: any) {
        setRoofPhotoMessage(`Selected "${file.name}". Ready for spatial evaluation.`);
      } finally {
        setRoofPhotoUploading(false);
      }
    }
  };

  const removeRoofPhoto = () => {
    setRoofPhoto(null);
    setRoofPhotoPreview(null);
    setRoofImageUrl(null);
    setRoofPhotoMessage(null);
  };

  const calculateAutoUsableArea = () => {
    if (customUsableArea && customUsableArea > 0) return customUsableArea;
    const ratio = roofType === 'tin_shed' ? 0.78 : roofType === 'tiled' ? 0.65 : 0.70;
    return Math.round(totalRoofArea * ratio);
  };

  const handleSubmit = async () => {
    setErrorMsg(null);
    setSubmitting(true);
    try {
      const assessmentData = {
        location: {
          division,
          district,
          area,
          latitude: lat,
          longitude: lng,
        },
        consumption: {
          monthly_units_kwh: Number(monthlyUnits),
          billing_period_days: Number(billingPeriodDays),
          bill_amount_bdt: billAmountBdt ? Number(billAmountBdt) : undefined,
          sanctioned_load_kw: Number(sanctionedLoad),
          consumer_category: consumerCategory,
        },
        rooftop: {
          total_area_sqft: Number(totalRoofArea),
          usable_area_sqft: calculateAutoUsableArea(),
          roof_type: roofType,
          shading_condition: shadingCondition,
          orientation,
          tilt_degrees: Number(tiltDegrees),
          roof_image_url: roofImageUrl || undefined,
        },
      };

      // 1. Fetch live recommendation
      const recommendation = await api.getSolarRecommendation({
        monthly_units_kwh: Number(monthlyUnits),
        total_roof_area_sqft: Number(totalRoofArea),
        sanctioned_load_kw: Number(sanctionedLoad),
        division,
        roof_type: roofType,
        shading_condition: shadingCondition,
        usable_roof_area_sqft: calculateAutoUsableArea(),
      });

      // 2. Submit assessment to database
      const savedAssessment = await api.submitAssessment(assessmentData);

      // Navigate to recommendation dashboard passing state
      navigate('/recommendations', {
        state: {
          recommendation,
          assessment: assessmentData,
          savedAssessment,
        },
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate recommendations. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const steps = [
    { num: 1, title: 'Location', desc: 'Bangladesh District' },
    { num: 2, title: 'Consumption', desc: 'Monthly kWh Units' },
    { num: 3, title: 'Bill Upload', desc: 'Bill Verification' },
    { num: 4, title: 'Rooftop', desc: 'Area & Shading' },
    { num: 5, title: 'Review', desc: 'Calculate Solar' },
  ];

  return (
    <div className="min-h-screen bg-slate-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-forest-100 text-forest-900 text-xs font-semibold mb-3">
            <ShieldCheck className="w-4 h-4 text-solar-500" />
            <span>SREDA Net Metering 2025 & BERC 2026 Compliant</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            Solar Potential Assessment Wizard
          </h1>
          <p className="text-slate-600 mt-2 text-sm sm:text-base max-w-xl mx-auto">
            Answer a few quick questions about your home, location, and electricity consumption to calculate your tailored solar potential.
          </p>
        </div>

        {/* Multi-Step Stepper Header */}
        <div className="bg-white p-4 sm:p-6 rounded-2xl border border-slate-200 shadow-xs mb-8">
          <div className="flex items-center justify-between">
            {steps.map((s, idx) => {
              const isPassed = currentStep > s.num;
              const isCurrent = currentStep === s.num;
              return (
                <React.Fragment key={s.num}>
                  <div className="flex flex-col items-center text-center">
                    <button
                      onClick={() => currentStep > s.num && setCurrentStep(s.num)}
                      className={`w-10 h-10 rounded-xl flex items-center justify-center font-bold text-sm transition-all ${
                        isPassed
                          ? 'bg-forest-900 text-white shadow-xs'
                          : isCurrent
                          ? 'bg-forest-100 text-forest-900 border-2 border-forest-800 ring-2 ring-forest-100'
                          : 'bg-slate-100 text-slate-400'
                      }`}
                    >
                      {isPassed ? <CheckCircle2 className="w-5 h-5 text-solar-400" /> : s.num}
                    </button>
                    <span
                      className={`mt-2 text-xs font-semibold hidden sm:block ${
                        isCurrent ? 'text-forest-900' : 'text-slate-500'
                      }`}
                    >
                      {s.title}
                    </span>
                  </div>
                  {idx < steps.length - 1 && (
                    <div
                      className={`flex-1 h-1 mx-2 sm:mx-4 rounded-full transition-colors ${
                        currentStep > s.num ? 'bg-forest-800' : 'bg-slate-200'
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* Wizard Card Body */}
        <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm relative">
          {errorMsg && (
            <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-200 text-red-800 text-sm flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Assessment Error</p>
                <p>{errorMsg}</p>
              </div>
            </div>
          )}

          {/* STEP 1: LOCATION */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <MapPin className="w-5 h-5 text-forest-700" />
                  <span>Step 1: Your Location in Bangladesh</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Solar irradiance varies by division and season across Bangladesh.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Division *
                  </label>
                  <select
                    value={division}
                    onChange={(e) => handleDivisionChange(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
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
                    District *
                  </label>
                  <select
                    value={district}
                    onChange={(e) => setDistrict(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
                  >
                    {(BD_DISTRICTS[division] || [division]).map((dist) => (
                      <option key={dist} value={dist}>
                        {dist}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    City / Thana / Area
                  </label>
                  <input
                    type="text"
                    value={area}
                    onChange={(e) => setArea(e.target.value)}
                    placeholder="e.g. Mirpur, Gulshan, Nasirabad, Halishahar, Boalia..."
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Latitude (Optional)
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={lat || ''}
                    onChange={(e) => setLat(parseFloat(e.target.value) || undefined)}
                    placeholder="e.g. 23.8103"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white text-sm"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Longitude (Optional)
                  </label>
                  <input
                    type="number"
                    step="0.0001"
                    value={lng || ''}
                    onChange={(e) => setLng(parseFloat(e.target.value) || undefined)}
                    placeholder="e.g. 90.4125"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white text-sm"
                  />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-forest-50 border border-forest-200 text-xs text-forest-900 flex items-start space-x-3">
                <Info className="w-4 h-4 text-forest-700 shrink-0 mt-0.5" />
                <p>
                  RoofwiseBD automatically aligns your location with NASA POWER multi-year agroclimatology
                  records for <strong>{division}</strong> (monthly average irradiance ~4.1 to 5.8 kWh/m²/day).
                </p>
              </div>
            </div>
          )}

          {/* STEP 2: ELECTRICITY CONSUMPTION */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <Zap className="w-5 h-5 text-forest-700" />
                  <span>Step 2: Electricity Consumption & Utility Slabs</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Solar sizing prioritizes your actual kWh/unit consumption to offset high-tier utility slabs.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Monthly Electricity Units (kWh) *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      required
                      min={1}
                      max={10000}
                      value={monthlyUnits}
                      onChange={(e) => setMonthlyUnits(Math.max(1, parseFloat(e.target.value) || 0))}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white pr-14"
                    />
                    <span className="absolute right-4 top-2.5 text-xs font-bold text-slate-500">
                      kWh
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Check "Total Units Billed" on your monthly electricity receipt.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Sanctioned Load (kW) *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      required
                      step="0.5"
                      min={0.5}
                      max={50}
                      value={sanctionedLoad}
                      onChange={(e) => setSanctionedLoad(Math.max(0.5, parseFloat(e.target.value) || 0.5))}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white pr-12"
                    />
                    <span className="absolute right-4 top-2.5 text-xs font-bold text-slate-500">
                      kW
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Under SREDA 2025 rules, inverter AC output must not exceed sanctioned load.
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Monthly Bill Amount (BDT ৳) — Optional
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      min={0}
                      value={billAmountBdt || ''}
                      onChange={(e) => setBillAmountBdt(parseFloat(e.target.value) || undefined)}
                      placeholder="e.g. 3100"
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white pr-12"
                    />
                    <span className="absolute right-4 top-2.5 text-xs font-bold text-slate-500">
                      ৳ BDT
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Consumer Category
                  </label>
                  <select
                    value={consumerCategory}
                    onChange={(e) => setConsumerCategory(e.target.value)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
                  >
                    <option value="Residential">Residential (BERC LT-A)</option>
                    <option value="Commercial">Commercial (LT-E)</option>
                    <option value="Small Building">Small Building / Institution</option>
                  </select>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-900 flex items-start space-x-3">
                <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Tariff Slab Alert: </span>
                  Under BERC 2026 rates, units in the highest bracket (&gt;600 kWh) cost <strong>Tk 17.03/kWh</strong>,
                  while 401–600 units cost <strong>Tk 15.01/kWh</strong>. Your solar system eliminates high slabs first.
                </div>
              </div>
            </div>
          )}

          {/* STEP 3: BILL UPLOAD */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <UploadCloud className="w-5 h-5 text-forest-700" />
                  <span>Step 3: Electricity Bill Upload (Optional)</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Upload an image or PDF of your bill (DESCO, DPDC, BPDB, NESCO, BREB) or verify your manual entry.
                </p>
              </div>

              {!billFile ? (
                <div className="border-2 border-dashed border-slate-300 rounded-2xl p-8 text-center hover:border-forest-600 hover:bg-forest-50/40 transition-colors">
                  <input
                    type="file"
                    id="bill-file-input"
                    accept=".jpg,.jpeg,.png,.pdf"
                    onChange={handleBillFileUpload}
                    className="hidden"
                  />
                  <label htmlFor="bill-file-input" className="cursor-pointer block space-y-3">
                    <div className="w-14 h-14 mx-auto rounded-2xl bg-forest-50 text-forest-800 flex items-center justify-center shadow-xs">
                      <UploadCloud className="w-7 h-7 text-forest-700" />
                    </div>
                    <div>
                      <span className="font-bold text-slate-800 text-base">
                        Click to upload or drag & drop bill
                      </span>
                      <p className="text-xs text-slate-500 mt-1">
                        Supported formats: JPG, PNG, PDF (Up to 10 MB)
                      </p>
                    </div>
                  </label>
                </div>
              ) : (
                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 rounded-xl bg-forest-900 text-white flex items-center justify-center">
                        <FileText className="w-5 h-5 text-solar-400" />
                      </div>
                      <div>
                        <p className="text-sm font-bold text-slate-800">{billFile.name}</p>
                        <p className="text-xs text-slate-500">{(billFile.size / 1024).toFixed(1)} KB</p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={removeBillFile}
                      className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                      title="Remove file"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  {billFilePreview && (
                    <div className="mt-3 overflow-hidden rounded-xl border border-slate-200 max-h-48">
                      <img src={billFilePreview} alt="Bill Preview" className="w-full object-cover" />
                    </div>
                  )}

                  {ocrStatusMessage && (
                    <div className="p-3 bg-forest-100/70 border border-forest-300 rounded-xl text-xs text-forest-900">
                      {ocrStatusMessage}
                    </div>
                  )}
                </div>
              )}

              <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-600 space-y-2">
                <div className="flex items-center space-x-2 font-bold text-slate-800">
                  <Info className="w-4 h-4 text-forest-700" />
                  <span>Manual Verification Confirmed</span>
                </div>
                <p>
                  Currently configured consumption: <strong>{monthlyUnits} kWh</strong> / month
                  ({(monthlyUnits / 30).toFixed(1)} kWh/day). You can always override this value anytime.
                </p>
              </div>
            </div>
          )}

          {/* STEP 4: ROOFTOP INFORMATION */}
          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <Home className="w-5 h-5 text-forest-700" />
                  <span>Step 4: Rooftop Characteristics & Shading</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Assess available space, parapet setbacks, roof materials, and obstacle shading.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Gross Rooftop Area (sq ft) *
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      required
                      min={50}
                      max={100000}
                      value={totalRoofArea}
                      onChange={(e) => setTotalRoofArea(Math.max(50, parseFloat(e.target.value) || 0))}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 font-bold focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white pr-16"
                    />
                    <span className="absolute right-4 top-2.5 text-xs font-bold text-slate-500">
                      sq ft
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Calculated usable area: ~{calculateAutoUsableArea()} sq ft
                  </span>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Roof Construction Type *
                  </label>
                  <select
                    value={roofType}
                    onChange={(e) => setRoofType(e.target.value as any)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
                  >
                    <option value="concrete_flat">Flat RCC Concrete (Standard BD Apartment/House)</option>
                    <option value="tin_shed">Sloped Tin / Steel Shed (Residential / Semi-Urban)</option>
                    <option value="tiled">Clay / Concrete Tiled Roof</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Shading Condition *
                  </label>
                  <select
                    value={shadingCondition}
                    onChange={(e) => setShadingCondition(e.target.value as any)}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:bg-white"
                  >
                    <option value="none">None (Full Sun all day — 100% factor)</option>
                    <option value="low">Low (Occasional slight shadow — 95% factor)</option>
                    <option value="medium">Medium (Adjacent building / trees — 85% factor)</option>
                    <option value="heavy">Heavy (Dense urban surround — 70% factor)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Primary Orientation & Tilt
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={orientation}
                      onChange={(e) => setOrientation(e.target.value)}
                      className="px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-forest-600"
                    >
                      <option value="South">South (Optimal)</option>
                      <option value="South-East">South-East</option>
                      <option value="South-West">South-West</option>
                      <option value="East">East</option>
                      <option value="West">West</option>
                    </select>
                    <div className="relative">
                      <input
                        type="number"
                        value={tiltDegrees}
                        onChange={(e) => setTiltDegrees(parseFloat(e.target.value) || 23.0)}
                        className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 text-sm focus:outline-none focus:ring-2 focus:ring-forest-600 pr-8"
                      />
                      <span className="absolute right-3 top-2 text-xs text-slate-500">°</span>
                    </div>
                  </div>
                  <span className="text-[11px] text-slate-500 mt-1 block">
                    Configured reference: 22°–24° south-facing tilt for Bangladesh.
                  </span>
                </div>

                <div className="sm:col-span-2">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Manual Usable Space Override (sq ft) — Optional
                  </label>
                  <input
                    type="number"
                    value={customUsableArea || ''}
                    onChange={(e) => setCustomUsableArea(parseFloat(e.target.value) || undefined)}
                    placeholder="Leave empty to use automatic setback ratio"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-slate-800 focus:outline-none focus:ring-2 focus:ring-forest-600 text-sm"
                  />
                </div>

                {/* Rooftop Site / Drone Photo Upload */}
                <div className="sm:col-span-2 pt-3 border-t border-slate-100">
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                    Rooftop Site Photo or Satellite Image (Optional)
                  </label>
                  {!roofPhoto ? (
                    <div className="border-2 border-dashed border-slate-300 rounded-xl p-5 text-center hover:border-forest-600 hover:bg-forest-50/30 transition-colors">
                      <input
                        type="file"
                        id="roof-photo-upload"
                        accept=".jpg,.jpeg,.png,.webp"
                        onChange={handleRoofPhotoUpload}
                        className="hidden"
                      />
                      <label htmlFor="roof-photo-upload" className="cursor-pointer block space-y-1.5">
                        <UploadCloud className="w-8 h-8 mx-auto text-forest-700" />
                        <span className="text-xs font-bold text-slate-800 block">
                          Upload rooftop photo, drone capture, or site plan
                        </span>
                        <span className="text-[11px] text-slate-400 block">
                          Supported formats: JPG, PNG, WEBP (Up to 10 MB)
                        </span>
                      </label>
                    </div>
                  ) : (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        {roofPhotoPreview ? (
                          <img
                            src={roofPhotoPreview}
                            alt="Rooftop preview"
                            className="w-12 h-12 rounded-lg object-cover border border-slate-200"
                          />
                        ) : (
                          <div className="w-12 h-12 rounded-lg bg-forest-900 text-white flex items-center justify-center">
                            <Home className="w-6 h-6 text-solar-400" />
                          </div>
                        )}
                        <div>
                          <p className="text-xs font-bold text-slate-900">{roofPhoto.name}</p>
                          <p className="text-[11px] text-slate-500">
                            {roofPhotoUploading ? 'Uploading to server...' : (roofPhotoMessage || `${(roofPhoto.size / 1024).toFixed(1)} KB`)}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={removeRoofPhoto}
                        className="p-1.5 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer"
                        title="Remove photo"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Civil engineering warning */}
              <div className="p-4 rounded-xl bg-slate-100 border border-slate-200 text-xs text-slate-600 flex items-start space-x-3">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <p>
                  <strong>Structural Safety Notice:</strong> Rooftop spatial calculation estimates available
                  panel surface area. A formal on-site civil structural and electrical survey is mandatory prior to physical installation.
                </p>
              </div>
            </div>
          )}

          {/* STEP 5: REVIEW ALL INPUTS */}
          {currentStep === 5 && (
            <div className="space-y-6">
              <div className="border-b border-slate-100 pb-4">
                <h2 className="text-xl font-bold text-slate-900 flex items-center space-x-2">
                  <CheckCircle2 className="w-5 h-5 text-forest-700" />
                  <span>Step 5: Review Assessment Inputs</span>
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  Verify your inputs below. You can click "Edit" on any section to make adjustments.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                {/* Location Review Card */}
                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-forest-800 flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5" />
                      <span>Location</span>
                    </span>
                    <button
                      onClick={() => setCurrentStep(1)}
                      className="text-xs font-bold text-forest-700 hover:text-forest-900 underline"
                    >
                      Edit
                    </button>
                  </div>
                  <div className="text-sm text-slate-800 space-y-1">
                    <p>
                      <strong>Division:</strong> {division}
                    </p>
                    <p>
                      <strong>District:</strong> {district}
                    </p>
                    <p>
                      <strong>Area:</strong> {area || 'Not specified'}
                    </p>
                  </div>
                </div>

                {/* Consumption Review Card */}
                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-forest-800 flex items-center space-x-1.5">
                      <Zap className="w-3.5 h-3.5" />
                      <span>Electricity Consumption</span>
                    </span>
                    <button
                      onClick={() => setCurrentStep(2)}
                      className="text-xs font-bold text-forest-700 hover:text-forest-900 underline"
                    >
                      Edit
                    </button>
                  </div>
                  <div className="text-sm text-slate-800 space-y-1">
                    <p>
                      <strong>Monthly Units:</strong> {monthlyUnits} kWh
                    </p>
                    <p>
                      <strong>Sanctioned Load:</strong> {sanctionedLoad} kW
                    </p>
                    <p>
                      <strong>Approx. Bill:</strong> {billAmountBdt ? `৳ ${billAmountBdt}` : 'Auto-calculated'}
                    </p>
                    {billFile && (
                      <p className="text-xs text-forest-800 flex items-center pt-1 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600 flex-shrink-0" />
                        <span>Uploaded Bill: {billFile.name}</span>
                      </p>
                    )}
                  </div>
                </div>

                {/* Rooftop Review Card */}
                <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold uppercase tracking-wider text-forest-800 flex items-center space-x-1.5">
                      <Home className="w-3.5 h-3.5" />
                      <span>Rooftop Characteristics</span>
                    </span>
                    <button
                      onClick={() => setCurrentStep(4)}
                      className="text-xs font-bold text-forest-700 hover:text-forest-900 underline"
                    >
                      Edit
                    </button>
                  </div>
                  <div className="text-sm text-slate-800 space-y-1">
                    <p>
                      <strong>Gross Area:</strong> {totalRoofArea} sq ft
                    </p>
                    <p>
                      <strong>Estimated Usable:</strong> ~{calculateAutoUsableArea()} sq ft
                    </p>
                    <p>
                      <strong>Roof Type:</strong> {roofType.replace('_', ' ').toUpperCase()}
                    </p>
                    <p>
                      <strong>Shading:</strong> {shadingCondition.toUpperCase()}
                    </p>
                    {roofPhoto && (
                      <p className="text-xs text-forest-800 flex items-center pt-1 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-600 flex-shrink-0" />
                        <span>Rooftop Photo: {roofPhoto.name}</span>
                      </p>
                    )}
                  </div>
                </div>

                {/* SREDA Net Metering Pre-Check Card */}
                <div className="p-5 rounded-2xl bg-forest-50 border border-forest-200 space-y-3">
                  <span className="text-xs font-bold uppercase tracking-wider text-forest-900 flex items-center space-x-1.5">
                    <ShieldCheck className="w-4 h-4 text-forest-700" />
                    <span>SREDA 2025 Pre-Check</span>
                  </span>
                  <div className="text-xs text-forest-900 space-y-1.5 leading-relaxed">
                    <p>
                      Sanctioned Load is set to <strong>{sanctionedLoad} kW</strong>.
                    </p>
                    <p>
                      The recommendation engine will design an inverter AC output within this limit
                      and flag whether utility sanction upgrades are required.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Stepper Navigation Buttons */}
          <div className="pt-8 border-t border-slate-100 flex items-center justify-between">
            {currentStep > 1 ? (
              <button
                type="button"
                onClick={() => setCurrentStep(currentStep - 1)}
                className="inline-flex items-center px-5 py-2.5 rounded-xl text-sm font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                <span>Back</span>
              </button>
            ) : (
              <div />
            )}

            {currentStep < 5 ? (
              <button
                type="button"
                onClick={() => setCurrentStep(currentStep + 1)}
                className="inline-flex items-center px-6 py-2.5 rounded-xl text-sm font-bold bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-sm"
              >
                <span>Continue</span>
                <ArrowRight className="w-4 h-4 ml-2 text-solar-400" />
              </button>
            ) : (
              <button
                type="button"
                disabled={submitting}
                onClick={handleSubmit}
                className="inline-flex items-center px-7 py-3 rounded-xl text-sm font-bold bg-forest-900 text-white hover:bg-forest-800 transition-colors shadow-md disabled:opacity-50"
              >
                {submitting ? (
                  <span>Calculating Recommendations...</span>
                ) : (
                  <>
                    <span>Generate Solar Recommendation</span>
                    <ArrowRight className="w-4 h-4 ml-2 text-solar-400" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
