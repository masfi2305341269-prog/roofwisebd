import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Sun, Link as LinkIcon } from 'lucide-react';
import { supabase } from '../services/supabase';
import { api } from '../services/api';

type CallbackState =
  | 'loading'
  | 'provisioning'
  | 'needs_linking'
  | 'password_recovery'
  | 'success'
  | 'error';

export const AuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const hashParams = new URLSearchParams(window.location.hash.replace(/^#/, ''));
  const callbackType = searchParams.get('type') || hashParams.get('type');

  const [state, setState] = useState<CallbackState>('loading');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [legacyPassword, setLegacyPassword] = useState('');
  const [linking, setLinking] = useState(false);
  const [linkError, setLinkError] = useState<string | null>(null);

  // New password fields (password recovery flow)
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Check for error parameters in query string or URL hash fragment
        const errorDesc = searchParams.get('error_description') || hashParams.get('error_description');
        if (errorDesc) {
          throw new Error(errorDesc);
        }

        // Supabase places the session tokens in the URL hash/query params after redirect.
        // getSession() reads those params and exchanges them for a valid session.
        const { data: { session }, error: sessionErr } = await supabase.auth.getSession();

        if (sessionErr) throw new Error(sessionErr.message);

        if (!session) {
          // Try to get the session from URL params (PKCE flow)
          const { data, error } = await supabase.auth.exchangeCodeForSession(
            window.location.href
          );
          if (error || !data.session) {
            throw new Error(error?.message || 'No session found. The confirmation link may have expired.');
          }
        }

        // Password recovery: redirect to a form for the user to set new password
        if (callbackType === 'recovery') {
          setState('password_recovery');
          return;
        }

        // Attempt to provision / fetch the FastAPI public.users profile
        try {
          await api.provisionProfile();
          setState('success');
          setTimeout(() => navigate('/dashboard', { replace: true }), 1500);
        } catch (provErr: any) {
          if (provErr.message?.includes('already exists') || provErr.message?.includes('409')) {
            // Existing account: user must link legacy password
            setState('needs_linking');
          } else {
            throw provErr;
          }
        }
      } catch (err: any) {
        setErrorMsg(err.message || 'Email confirmation failed.');
        setState('error');
      }
    };

    handleCallback();
  }, [navigate, callbackType]);

  const handleLinkAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    setLinkError(null);
    setLinking(true);
    try {
      await api.linkLegacyAccount(legacyPassword);
      setState('success');
      setTimeout(() => navigate('/dashboard', { replace: true }), 1500);
    } catch (err: any) {
      setLinkError(err.message || 'Account linking failed.');
    } finally {
      setLinking(false);
    }
  };

  const handleSetNewPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword.length < 8) {
      setLinkError('Password must be at least 8 characters.');
      return;
    }
    if (!/[A-Za-z]/.test(newPassword) || !/\d/.test(newPassword)) {
      setLinkError('Password must contain at least one letter and one number.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setLinkError('Passwords do not match.');
      return;
    }
    setLinkError(null);
    setSavingPassword(true);
    try {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw new Error(error.message);
      // After password update, provision the profile and redirect
      try {
        await api.provisionProfile();
      } catch {
        // Profile may already exist — that's OK
      }
      setState('success');
      setTimeout(() => navigate('/dashboard', { replace: true }), 1500);
    } catch (err: any) {
      setLinkError(err.message || 'Password update failed.');
    } finally {
      setSavingPassword(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12 px-4">
      <div className="max-w-md w-full bg-white p-8 rounded-2xl shadow-xl border border-slate-100 space-y-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-forest-900 text-solar-400 mb-4 shadow-md">
            <Sun className="w-8 h-8 animate-[spin_12s_linear_infinite]" />
          </div>
          <h2 className="text-xl font-black text-forest-950 tracking-tight">
            {state === 'loading' && 'Verifying your account…'}
            {state === 'provisioning' && 'Setting up your profile…'}
            {state === 'needs_linking' && 'Link Your Existing Account'}
            {state === 'password_recovery' && 'Set a New Password'}
            {state === 'success' && 'You\'re all set!'}
            {state === 'error' && 'Verification Failed'}
          </h2>
        </div>

        {/* Loading / Provisioning spinner */}
        {(state === 'loading' || state === 'provisioning') && (
          <div className="flex justify-center py-6">
            <div className="w-10 h-10 border-3 border-forest-900 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {/* Success */}
        {state === 'success' && (
          <div className="text-center space-y-3">
            <CheckCircle2 className="w-16 h-16 text-emerald-500 mx-auto" />
            <p className="text-slate-600 text-sm">Redirecting to your dashboard…</p>
          </div>
        )}

        {/* Error */}
        {state === 'error' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-rose-50 border border-rose-200 p-4 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-rose-700">Verification failed</p>
                <p className="text-xs text-rose-600 mt-0.5">{errorMsg}</p>
              </div>
            </div>
            <div className="text-center">
              <button
                onClick={() => navigate('/register')}
                className="text-sm font-bold text-forest-700 hover:underline"
              >
                Back to Register
              </button>
            </div>
          </div>
        )}

        {/* Needs Legacy Account Linking */}
        {state === 'needs_linking' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
              <p className="font-semibold">Existing Account Detected</p>
              <p className="mt-1 text-xs text-amber-700">
                An account with this email already exists. Enter your old password to securely
                link your account to Supabase Auth. You won't need this password again after linking.
              </p>
            </div>
            <form onSubmit={handleLinkAccount} className="space-y-4">
              {linkError && (
                <p className="text-xs text-rose-600 flex items-center space-x-1">
                  <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                  <span>{linkError}</span>
                </p>
              )}
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                  Existing Password
                </label>
                <input
                  type="password"
                  required
                  value={legacyPassword}
                  onChange={(e) => setLegacyPassword(e.target.value)}
                  placeholder="Your old RoofwiseBD password"
                  className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
                />
              </div>
              <button
                type="submit"
                disabled={linking}
                className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 transition-all cursor-pointer"
              >
                {linking ? (
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <span>Link My Account</span>
                )}
              </button>
            </form>
          </div>
        )}

        {/* Password Recovery: set new password */}
        {state === 'password_recovery' && (
          <form onSubmit={handleSetNewPassword} className="space-y-4">
            {linkError && (
              <p className="text-xs text-rose-600 flex items-center space-x-1">
                <AlertCircle className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{linkError}</span>
              </p>
            )}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min 8 chars, include a letter and a number"
                className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
              />
            </div>
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter your new password"
                className="block w-full px-3 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700 focus:bg-white transition-all"
              />
            </div>
            <button
              type="submit"
              disabled={savingPassword}
              className="w-full flex items-center justify-center py-3 px-4 border border-transparent rounded-xl shadow-md text-sm font-bold text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 transition-all cursor-pointer"
            >
              {savingPassword ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span>Set New Password</span>
              )}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default AuthCallbackPage;
