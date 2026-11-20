import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Mail, Lock, LogIn, AlertCircle, CheckCircle2, Sun, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const LoginPage: React.FC = () => {
  const location = useLocation();
  const initialEmail = (location.state as any)?.email || '';
  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const { login, authMode } = useAuth();
  const navigate = useNavigate();

  const isVerifiedBanner = (location.state as any)?.verified;

  // Redirect destination after login (e.g. back to assessment or dashboard)
  const from = (location.state as any)?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      await login({ email: email.trim().toLowerCase(), password });
      navigate(from, { replace: true });
    } catch (err: any) {
      if (err.message === 'PROFILE_NOT_PROVISIONED') {
        // Supabase user logged in but no FastAPI profile yet — send to callback to provision
        navigate('/auth/callback', { replace: true });
        return;
      }
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-forest-900 text-solar-400 mb-4 shadow-md">
            <Sun className="w-8 h-8 animate-[spin_12s_linear_infinite]" />
          </div>
          <h2 className="text-2xl font-black text-forest-950 tracking-tight">
            Sign In to Roofwise<span className="text-solar-500">BD</span>
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Access your saved solar assessments and tailored energy recommendations.
          </p>
        </div>

        {isVerifiedBanner && !error && (
          <div className="rounded-xl bg-emerald-50 border border-emerald-200 p-4 flex items-start space-x-3 text-emerald-800 text-sm animate-fade-in">
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-emerald-600" />
            <div>
              <p className="font-semibold">Email Verified!</p>
              <p className="mt-0.5 text-xs text-emerald-700">Your email has been verified. You can now sign in with your credentials.</p>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-start space-x-3 text-rose-700 text-sm animate-fade-in">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
            <div className="flex-1">
              <p className="font-semibold">Sign in unsuccessful</p>
              <p className="mt-0.5 text-xs text-rose-600">{error}</p>
              {/* Legacy OTP mode: link to /verify-email */}
              {error.toLowerCase().includes('verif') && authMode === 'legacy' && (
                <div className="mt-2 pt-2 border-t border-rose-200">
                  <Link
                    to={`/verify-email?email=${encodeURIComponent(email.trim().toLowerCase())}`}
                    state={{ email: email.trim().toLowerCase() }}
                    className="inline-flex items-center text-xs font-bold text-rose-800 hover:text-rose-950 underline"
                  >
                    <span>Enter verification code now</span>
                    <ArrowRight className="w-3.5 h-3.5 ml-1" />
                  </Link>
                </div>
              )}
              {/* Supabase mode: remind user to check their inbox */}
              {error.toLowerCase().includes('confirmed') && authMode === 'supabase' && (
                <div className="mt-2 pt-2 border-t border-rose-200">
                  <p className="text-xs text-rose-700">
                    Check your email inbox for the confirmation link, or{' '}
                    <Link
                      to="/register"
                      className="font-bold underline hover:text-rose-900"
                    >
                      register again
                    </Link>{' '}to resend it.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        <form className="mt-6 space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Email Address
            </label>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Mail className="h-5 h-5" />
              </div>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                Password
              </label>
              <Link
                to="/forgot-password"
                className="text-xs font-semibold text-forest-700 hover:text-forest-900 transition-colors"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative rounded-xl shadow-xs">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                <Lock className="h-5 h-5" />
              </div>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="block w-full pl-10 pr-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-forest-700 disabled:opacity-50 transition-all cursor-pointer"
          >
            {loading ? (
              <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <>
                <LogIn className="w-4 h-4 mr-2" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-slate-100 text-center">
          <p className="text-xs text-slate-500">
            Don't have a RoofwiseBD account?{' '}
            <Link to="/register" className="font-bold text-forest-700 hover:text-forest-900 underline ml-1">
              Create an account
            </Link>
          </p>
          <div className="mt-4 pt-3 border-t border-slate-50">
            <Link
              to="/assessment"
              className="inline-flex items-center text-xs font-semibold text-slate-500 hover:text-forest-800 transition-colors"
            >
              <span>Continue as guest to calculate solar potential</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
