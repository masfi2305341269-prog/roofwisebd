import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate, useLocation, useSearchParams } from 'react-router-dom';
import { Mail, CheckCircle2, AlertCircle, RefreshCw, ArrowRight, ShieldCheck, Sun, Edit3 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const VerifyEmailPage: React.FC = () => {
  const { verifyEmail, resendVerification } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();

  // Extract email from location state or URL search parameters
  const initialEmail = (location.state as any)?.email || searchParams.get('email') || '';
  const initialMessage = (location.state as any)?.message || null;

  const [email, setEmail] = useState<string>(initialEmail);
  const [isEditingEmail, setIsEditingEmail] = useState<boolean>(!initialEmail);
  const [digits, setDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [loading, setLoading] = useState<boolean>(false);
  const [resending, setResending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(initialMessage);
  const [isVerified, setIsVerified] = useState<boolean>(false);
  const [countdown, setCountdown] = useState<number>(60);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  // Timer countdown effect for Resend cooldown
  useEffect(() => {
    if (countdown <= 0) return;
    const interval = setInterval(() => {
      setCountdown((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [countdown]);

  // Focus the first empty digit box when page loads
  useEffect(() => {
    if (!isEditingEmail && inputRefs.current[0]) {
      inputRefs.current[0]?.focus();
    }
  }, [isEditingEmail]);

  // Handle individual digit change
  const handleDigitChange = (index: number, value: string) => {
    // Only accept numeric digits
    const cleaned = value.replace(/\D/g, '');
    if (!cleaned) {
      const nextDigits = [...digits];
      nextDigits[index] = '';
      setDigits(nextDigits);
      return;
    }

    // If pasted or multi-char typed into this slot
    if (cleaned.length > 1) {
      handlePastedCode(cleaned);
      return;
    }

    const nextDigits = [...digits];
    nextDigits[index] = cleaned[0];
    setDigits(nextDigits);

    // Auto-advance to next box if available
    if (index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text/plain').replace(/\D/g, '').trim();
    if (pastedData) {
      handlePastedCode(pastedData);
    }
  };

  const handlePastedCode = (code: string) => {
    const chars = code.slice(0, 6).split('');
    const nextDigits = ['', '', '', '', '', ''];
    chars.forEach((char, idx) => {
      nextDigits[idx] = char;
    });
    setDigits(nextDigits);

    const targetFocus = Math.min(chars.length, 5);
    inputRefs.current[targetFocus]?.focus();
  };

  const currentOtp = digits.join('');

  const handleVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setError('Please provide your registered email address.');
      setIsEditingEmail(true);
      return;
    }

    if (currentOtp.length !== 6 || !/^\d{6}$/.test(currentOtp)) {
      setError('Please enter the full 6-digit verification code.');
      return;
    }

    setLoading(true);
    try {
      const res = await verifyEmail({ email: trimmedEmail, otp: currentOtp });
      setIsVerified(true);
      setSuccessMsg(res.message || 'Email verified successfully! You can now sign in.');
      setTimeout(() => {
        navigate('/login', { state: { email: trimmedEmail, verified: true } });
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Verification failed. Please check the code and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (countdown > 0 || resending) return;
    setError(null);

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail) {
      setError('Please enter your email address to resend the code.');
      setIsEditingEmail(true);
      return;
    }

    setResending(true);
    try {
      const res = await resendVerification({ email: trimmedEmail });
      setSuccessMsg(res.message || 'A new verification code has been sent to your email.');
      setCountdown(res.cooldown_seconds || 60);
      setDigits(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code. Please try again later.');
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="min-h-[85vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-6 bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-forest-900 text-solar-400 mb-4 shadow-md">
            {isVerified ? (
              <CheckCircle2 className="w-8 h-8 text-emerald-400" />
            ) : (
              <ShieldCheck className="w-8 h-8 text-solar-400" />
            )}
          </div>
          <h2 className="text-2xl font-black text-forest-950 tracking-tight">
            {isVerified ? 'Email Verified!' : 'Verify Your Email'}
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            {isVerified
              ? 'Your email has been successfully verified. Redirecting to sign in...'
              : 'Enter the 6-digit verification code sent to your email address.'}
          </p>
        </div>

        {/* Email Address Indicator & Quick Edit */}
        {!isVerified && (
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 flex flex-col space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-500 uppercase tracking-wider">
                Target Email Address
              </span>
              <button
                type="button"
                onClick={() => setIsEditingEmail(!isEditingEmail)}
                className="text-forest-700 hover:text-forest-900 font-semibold inline-flex items-center space-x-1 cursor-pointer"
              >
                <Edit3 className="w-3.5 h-3.5" />
                <span>{isEditingEmail ? 'Done' : 'Change'}</span>
              </button>
            </div>
            {isEditingEmail ? (
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full px-3 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 focus:outline-none focus:ring-2 focus:ring-forest-700"
                />
              </div>
            ) : (
              <p className="text-sm font-semibold text-slate-800 break-all flex items-center space-x-1.5">
                <Mail className="w-4 h-4 text-slate-400 flex-shrink-0" />
                <span>{email || 'No email provided'}</span>
              </p>
            )}
          </div>
        )}

        {/* Success Alert */}
        {successMsg && !error && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-start space-x-3 text-emerald-800 text-sm animate-fade-in">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
            <div>
              <p className="font-semibold">{isVerified ? 'Verification Complete' : 'Verification Code Sent'}</p>
              <p className="mt-0.5 text-xs text-emerald-700">{successMsg}</p>
            </div>
          </div>
        )}

        {/* Error Alert */}
        {error && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-start space-x-3 text-rose-700 text-sm animate-fade-in">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
            <div>
              <p className="font-semibold">Verification Problem</p>
              <p className="mt-0.5 text-xs text-rose-600">{error}</p>
            </div>
          </div>
        )}

        {!isVerified ? (
          <form className="mt-6 space-y-6" onSubmit={handleVerify}>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2 text-center">
                6-Digit Security Code
              </label>

              {/* 6 Individual Digit Slots */}
              <div className="flex justify-center items-center space-x-2 sm:space-x-3">
                {digits.map((digit, idx) => (
                  <input
                    key={idx}
                    ref={(el) => (inputRefs.current[idx] = el)}
                    type="text"
                    inputMode="numeric"
                    pattern="\d*"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleDigitChange(idx, e.target.value)}
                    onKeyDown={(e) => handleKeyDown(idx, e)}
                    onPaste={handlePaste}
                    className="w-11 h-13 sm:w-12 sm:h-14 text-center text-xl sm:text-2xl font-bold bg-slate-50 border-2 border-slate-200 rounded-xl text-forest-950 focus:bg-white focus:border-forest-700 focus:outline-none focus:ring-2 focus:ring-forest-700/20 transition-all shadow-xs"
                  />
                ))}
              </div>
              <p className="text-center text-xs text-slate-400 mt-2">
                Code expires in 10 minutes. Check your inbox and spam folder.
              </p>
            </div>

            <button
              type="submit"
              disabled={loading || currentOtp.length !== 6}
              className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-forest-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 mr-2" />
                  <span>Verify Email</span>
                </>
              )}
            </button>

            {/* Resend Action */}
            <div className="pt-2 text-center">
              <p className="text-xs text-slate-500 mb-1.5">Didn't receive the email code?</p>
              <button
                type="button"
                onClick={handleResend}
                disabled={countdown > 0 || resending}
                className="inline-flex items-center text-xs font-bold text-forest-800 hover:text-forest-950 disabled:text-slate-400 disabled:cursor-not-allowed transition-colors cursor-pointer"
              >
                {resending ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 mr-1 animate-spin" />
                    <span>Resending code...</span>
                  </>
                ) : countdown > 0 ? (
                  <span>Resend code in {countdown}s</span>
                ) : (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 mr-1" />
                    <span className="underline">Resend verification code</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <div className="mt-6 text-center space-y-4">
            <button
              type="button"
              onClick={() => navigate('/login', { state: { email: email.trim().toLowerCase(), verified: true } })}
              className="w-full flex items-center justify-center py-3 px-4 rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 transition-all cursor-pointer"
            >
              <span>Sign In to Your Account</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </button>
          </div>
        )}

        <div className="pt-4 border-t border-slate-100 text-center">
          <Link
            to="/login"
            className="text-xs font-semibold text-slate-500 hover:text-forest-800 transition-colors"
          >
            ← Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
