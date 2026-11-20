import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Mail, Lock, User as UserIcon, Phone, MapPin, UserPlus, AlertCircle, CheckCircle2, Sun } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const BANGLADESH_DISTRICTS = [
  'Bagerhat', 'Bandarban', 'Barguna', 'Barishal', 'Bhola',
  'Bogura', 'Brahmanbaria', 'Chandpur', 'Chapai Nawabganj', 'Chattogram',
  'Chuadanga', "Cox's Bazar", 'Cumilla', 'Dhaka', 'Dinajpur',
  'Faridpur', 'Feni', 'Gaibandha', 'Gazipur', 'Gopalganj',
  'Habiganj', 'Jamalpur', 'Jashore', 'Jhalokati', 'Jhenaidah',
  'Joypurhat', 'Khagrachhari', 'Khulna', 'Kishoreganj', 'Kurigram',
  'Kushtia', 'Lakshmipur', 'Lalmonirhat', 'Madaripur', 'Magura',
  'Manikganj', 'Meherpur', 'Moulvibazar', 'Munshiganj', 'Mymensingh',
  'Naogaon', 'Narail', 'Narayanganj', 'Narsingdi', 'Natore',
  'Netrokona', 'Nilphamari', 'Noakhali', 'Pabna', 'Panchagarh',
  'Patuakhali', 'Pirojpur', 'Rajbari', 'Rajshahi', 'Rangamati',
  'Rangpur', 'Satkhira', 'Shariatpur', 'Sherpur', 'Sirajganj',
  'Sunamganj', 'Sylhet', 'Tangail', 'Thakurgaon',
];

interface FieldErrors {
  fullName?: string;
  email?: string;
  phone?: string;
  password?: string;
  confirmPassword?: string;
}

export const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [district, setDistrict] = useState('');
  const [area, setArea] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const [errors, setErrors] = useState<FieldErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [successMsg, setSuccessMsg] = useState('Account created successfully! Redirecting to sign in...');
  const [loading, setLoading] = useState(false);

  const { register } = useAuth();
  const navigate = useNavigate();

  // Field validation helpers
  const validateFullName = (name: string): string | undefined => {
    const trimmed = name.trim();
    if (!trimmed) {
      return 'Full name is required.';
    }
    if (trimmed.length < 2) {
      return 'Full name must be at least 2 characters.';
    }
    if (trimmed.length > 100) {
      return 'Full name cannot exceed 100 characters.';
    }
    if (!/[a-zA-Z\u0980-\u09FF]/.test(trimmed)) {
      return 'Full name must contain at least one letter.';
    }
    if (!/^[a-zA-Z\u0980-\u09FF\s\-'.]+$/.test(trimmed)) {
      return 'Full name may only contain English/Bangla letters, spaces, hyphens, and apostrophes.';
    }
    return undefined;
  };

  const validateEmail = (emailStr: string): string | undefined => {
    const trimmed = emailStr.trim();
    if (!trimmed) return 'Email address is required.';
    if (/\s/.test(trimmed)) return 'Email address cannot contain spaces.';
    if (trimmed.length > 254) return 'Email address cannot exceed 254 characters.';
    const atCount = (trimmed.match(/@/g) || []).length;
    if (atCount === 0) return 'Email address must contain an @ symbol.';
    if (atCount > 1) return 'Email address must contain exactly one @ symbol.';
    const [local, domain] = trimmed.split('@');
    if (!local) return 'Email address is missing the local part before @ (e.g. \'@gmail.com\' is invalid).';
    if (local.length > 64) return 'Email local part cannot exceed 64 characters.';
    if (local.startsWith('.')) return 'Email local part cannot start with a period.';
    if (local.endsWith('.')) return 'Email local part cannot end with a period.';
    if (local.includes('..')) return 'Email local part cannot contain consecutive periods.';
    if (!/^[a-zA-Z0-9._%+\-]+$/.test(local)) return 'Email local part contains invalid characters.';
    if (!domain) return 'Email address is missing the domain after @.';
    if (domain.startsWith('.') || domain.startsWith('-')) return 'Email domain cannot start with a period or hyphen.';
    if (domain.endsWith('.') || domain.endsWith('-')) return 'Email domain cannot end with a period or hyphen.';
    if (domain.includes('..')) return 'Email domain cannot contain consecutive periods.';
    if (!domain.includes('.')) return 'Email domain must contain a valid top-level domain (e.g. \'.com\').';
    const domainParts = domain.split('.');
    if (domainParts.some((p) => p.length === 0)) return 'Email domain contains an empty label (e.g. double dot).';
    const tld = domainParts[domainParts.length - 1];
    if (tld.length < 2) return 'Email top-level domain must be at least 2 characters.';
    if (!/^[a-zA-Z]+$/.test(tld)) return 'Email top-level domain must contain only letters.';
    return undefined;
  };

  const validatePhone = (phoneStr: string): string | undefined => {
    const trimmed = phoneStr.trim();
    if (!trimmed) {
      return undefined; // Optional
    }
    if (/[a-zA-Z]/.test(trimmed)) {
      return 'Phone number cannot contain alphabetic characters.';
    }
    const clean = trimmed.replace(/[\s\-]/g, '');
    const bdPhoneRegex = /^(\+8801|01)[3-9]\d{8}$/;
    if (!bdPhoneRegex.test(clean)) {
      return 'Must be a valid Bangladesh phone (e.g. 01XXXXXXXXX or +8801XXXXXXXXX).';
    }
    return undefined;
  };

  const validatePassword = (pw: string): string | undefined => {
    if (!pw) {
      return 'Password is required.';
    }
    if (pw.length < 8) {
      return 'Password must be at least 8 characters long.';
    }
    if (pw.length > 128) {
      return 'Password cannot exceed 128 characters.';
    }
    if (!/[A-Za-z]/.test(pw)) {
      return 'Password must contain at least one letter.';
    }
    if (!/\d/.test(pw)) {
      return 'Password must contain at least one number.';
    }
    return undefined;
  };

  const validateConfirmPassword = (pw: string, confirmPw: string): string | undefined => {
    if (!confirmPw) {
      return 'Please confirm your password.';
    }
    if (pw !== confirmPw) {
      return 'Passwords do not match.';
    }
    return undefined;
  };

  // Blur handler to trigger inline validation
  const handleBlur = (field: keyof FieldErrors) => {
    setTouched((prev) => ({ ...prev, [field]: true }));
    let error: string | undefined;

    switch (field) {
      case 'fullName':
        error = validateFullName(fullName);
        break;
      case 'email':
        error = validateEmail(email);
        break;
      case 'phone':
        error = validatePhone(phone);
        break;
      case 'password':
        error = validatePassword(password);
        if (touched.confirmPassword) {
          setErrors((prev) => ({
            ...prev,
            confirmPassword: validateConfirmPassword(password, confirmPassword),
          }));
        }
        break;
      case 'confirmPassword':
        error = validateConfirmPassword(password, confirmPassword);
        break;
    }

    setErrors((prev) => ({ ...prev, [field]: error }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setServerError(null);

    // Prevent duplicate submission while already processing
    if (loading || success) return;

    // Validate all fields
    const nameErr = validateFullName(fullName);
    const emailErr = validateEmail(email);
    const phoneErr = validatePhone(phone);
    const pwErr = validatePassword(password);
    const confirmErr = validateConfirmPassword(password, confirmPassword);

    const validationErrors: FieldErrors = {
      fullName: nameErr,
      email: emailErr,
      phone: phoneErr,
      password: pwErr,
      confirmPassword: confirmErr,
    };

    setErrors(validationErrors);
    setTouched({
      fullName: true,
      email: true,
      phone: true,
      password: true,
      confirmPassword: true,
    });

    if (nameErr || emailErr || phoneErr || pwErr || confirmErr) {
      return;
    }

    // Format address from controlled dropdown and area
    let finalAddress: string | undefined = undefined;
    if (district) {
      finalAddress = area.trim() ? `${district}, ${area.trim()}` : district;
    } else if (area.trim()) {
      finalAddress = area.trim();
    }

    setLoading(true);
    try {
      const normalizedEmail = email.trim().toLowerCase();
      const res = await register({
        email: normalizedEmail,
        password,
        full_name: fullName.trim(),
        phone: phone.trim() ? phone.trim().replace(/[\s\-]/g, '') : undefined,
        address: finalAddress,
      });

      const msg = res?.message || 'Account created! Redirecting to email verification...';
      setSuccessMsg(msg);
      setSuccess(true);

      if (res?.requiresEmailConfirmation) {
        // Supabase mode: stay on page and show "check your email" message
        // No navigation — the user clicks the confirmation link in their email
      } else {
        // Legacy OTP mode: redirect to /verify-email after short delay
        setTimeout(() => {
          navigate('/verify-email', {
            state: {
              email: normalizedEmail,
              message: 'A 6-digit verification code has been sent to your email. Please enter it below to activate your account.',
            },
          });
        }, 1000);
      }
    } catch (err: any) {
      setServerError(err.message || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-forest-900 text-solar-400 mb-4 shadow-md">
            <Sun className="w-8 h-8 animate-[spin_12s_linear_infinite]" />
          </div>
          <h2 className="text-2xl font-black text-forest-950 tracking-tight">
            Create an Account
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Join RoofwiseBD to save assessments and monitor rooftop solar savings.
          </p>
        </div>

        {serverError && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-start space-x-3 text-rose-700 text-sm">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
            <div>
              <p className="font-semibold">Registration Issue</p>
              <p className="mt-0.5 text-xs text-rose-600">{serverError}</p>
            </div>
          </div>
        )}

        {success && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-start space-x-3 text-emerald-800 text-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold">Account Created!</p>
              <p className="mt-0.5 text-xs text-emerald-700">{successMsg}</p>
            </div>
          </div>
        )}

        <form className="mt-6 space-y-4" onSubmit={handleSubmit} noValidate>
          {/* Full Name */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Full Name *
            </label>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <UserIcon className="h-5 h-5" />
              </div>
              <input
                type="text"
                name="full_name"
                id="full_name"
                autoComplete="name"
                required
                disabled={loading || success}
                value={fullName}
                onChange={(e) => {
                  setFullName(e.target.value);
                  if (touched.fullName) {
                    setErrors((prev) => ({ ...prev, fullName: validateFullName(e.target.value) }));
                  }
                }}
                onBlur={() => handleBlur('fullName')}
                placeholder="e.g. Tanvir Ahmed"
                className={`block w-full pl-10 pr-3 py-2 bg-slate-50 border rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none transition-all ${
                  errors.fullName
                    ? 'border-rose-400 focus:ring-2 focus:ring-rose-500 bg-rose-50/20'
                    : 'border-slate-200 focus:ring-2 focus:ring-forest-700 focus:bg-white'
                }`}
              />
            </div>
            {errors.fullName && (
              <p className="mt-1 text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{errors.fullName}</span>
              </p>
            )}
          </div>

          {/* Email Address */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Email Address *
            </label>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Mail className="h-5 h-5" />
              </div>
              <input
                type="email"
                name="email"
                id="email"
                autoComplete="email"
                required
                disabled={loading || success}
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  if (touched.email) {
                    setErrors((prev) => ({ ...prev, email: validateEmail(e.target.value) }));
                  }
                }}
                onBlur={() => handleBlur('email')}
                placeholder="name@example.com"
                className={`block w-full pl-10 pr-3 py-2 bg-slate-50 border rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none transition-all ${
                  errors.email
                    ? 'border-rose-400 focus:ring-2 focus:ring-rose-500 bg-rose-50/20'
                    : 'border-slate-200 focus:ring-2 focus:ring-forest-700 focus:bg-white'
                }`}
              />
            </div>
            {errors.email && (
              <p className="mt-1 text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{errors.email}</span>
              </p>
            )}
          </div>

          {/* Phone Number & District */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Phone Number <span className="text-slate-400 font-normal lowercase">(optional)</span>
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Phone className="h-4 h-4" />
                </div>
                <input
                  type="tel"
                  name="phone"
                  id="phone"
                  autoComplete="tel"
                  disabled={loading || success}
                  value={phone}
                  onChange={(e) => {
                    setPhone(e.target.value);
                    if (touched.phone) {
                      setErrors((prev) => ({ ...prev, phone: validatePhone(e.target.value) }));
                    }
                  }}
                  onBlur={() => handleBlur('phone')}
                  placeholder="017XXXXXXXX"
                  className={`block w-full pl-9 pr-3 py-2 bg-slate-50 border rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none transition-all ${
                    errors.phone
                      ? 'border-rose-400 focus:ring-2 focus:ring-rose-500 bg-rose-50/20'
                      : 'border-slate-200 focus:ring-2 focus:ring-forest-700 focus:bg-white'
                  }`}
                />
              </div>
              {errors.phone && (
                <p className="mt-1 text-xs text-rose-600 flex items-center space-x-1">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{errors.phone}</span>
                </p>
              )}
            </div>

            {/* Controlled District Dropdown */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                District <span className="text-slate-400 font-normal lowercase">(optional)</span>
              </label>
              <div className="relative rounded-xl shadow-xs">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <MapPin className="h-4 h-4" />
                </div>
                <select
                  name="district"
                  id="district"
                  autoComplete="address-level2"
                  disabled={loading || success}
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  className="block w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all cursor-pointer"
                >
                  <option value="">Select District</option>
                  {BANGLADESH_DISTRICTS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* Area / Thana (Optional) */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Area / Thana <span className="text-slate-400 font-normal lowercase">(optional)</span>
            </label>
            <div className="relative rounded-xl shadow-xs">
              <input
                type="text"
                name="area"
                id="area"
                autoComplete="address-level3"
                disabled={loading || success}
                value={area}
                onChange={(e) => setArea(e.target.value)}
                placeholder="e.g. Mirpur, Uttara, Banani"
                className="block w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
              />
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Password *
            </label>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 h-5" />
              </div>
              <input
                type="password"
                name="password"
                id="password"
                autoComplete="new-password"
                required
                disabled={loading || success}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  if (touched.password) {
                    setErrors((prev) => ({
                      ...prev,
                      password: validatePassword(e.target.value),
                      ...(touched.confirmPassword
                        ? { confirmPassword: validateConfirmPassword(e.target.value, confirmPassword) }
                        : {}),
                    }));
                  }
                }}
                onBlur={() => handleBlur('password')}
                placeholder="Min 8 characters with letter & number"
                className={`block w-full pl-10 pr-3 py-2 bg-slate-50 border rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none transition-all ${
                  errors.password
                    ? 'border-rose-400 focus:ring-2 focus:ring-rose-500 bg-rose-50/20'
                    : 'border-slate-200 focus:ring-2 focus:ring-forest-700 focus:bg-white'
                }`}
              />
            </div>
            {errors.password && (
              <p className="mt-1 text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{errors.password}</span>
              </p>
            )}
          </div>

          {/* Confirm Password */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Confirm Password *
            </label>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 h-5" />
              </div>
              <input
                type="password"
                name="confirm_password"
                id="confirm_password"
                autoComplete="new-password"
                required
                disabled={loading || success}
                value={confirmPassword}
                onChange={(e) => {
                  setConfirmPassword(e.target.value);
                  if (touched.confirmPassword) {
                    setErrors((prev) => ({
                      ...prev,
                      confirmPassword: validateConfirmPassword(password, e.target.value),
                    }));
                  }
                }}
                onBlur={() => handleBlur('confirmPassword')}
                placeholder="Re-enter your password"
                className={`block w-full pl-10 pr-3 py-2 bg-slate-50 border rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none transition-all ${
                  errors.confirmPassword
                    ? 'border-rose-400 focus:ring-2 focus:ring-rose-500 bg-rose-50/20'
                    : 'border-slate-200 focus:ring-2 focus:ring-forest-700 focus:bg-white'
                }`}
              />
            </div>
            {errors.confirmPassword && (
              <p className="mt-1 text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{errors.confirmPassword}</span>
              </p>
            )}
          </div>

          {/* Submit Button with Duplicate Submission Prevention */}
          <button
            type="submit"
            disabled={loading || success}
            className="w-full mt-2 flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-forest-700 disabled:opacity-50 transition-all cursor-pointer"
          >
            {loading ? (
              <div className="flex items-center space-x-2">
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Creating Account...</span>
              </div>
            ) : (
              <>
                <UserPlus className="w-4 h-4 mr-2" />
                <span>Register Account</span>
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500">
            Already registered?{' '}
            <Link to="/login" className="font-bold text-forest-700 hover:text-forest-900 underline ml-1">
              Sign in to your account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};
