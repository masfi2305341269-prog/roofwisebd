import React, { useState } from 'react';
import { User as UserIcon, Mail, Phone, MapPin, Lock, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const UserProfilePage: React.FC = () => {
  const { user, updateProfile, refreshUser } = useAuth();

  // Profile Edit State
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [phone, setPhone] = useState(user?.phone || '');
  const [address, setAddress] = useState(user?.address || '');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileMsg, setProfileMsg] = useState<string | null>(null);
  const [profileErr, setProfileErr] = useState<string | null>(null);

  // Change Password State
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [pwLoading, setPwLoading] = useState(false);
  const [pwMsg, setPwMsg] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);

  if (!user) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <p className="text-slate-500">Please sign in to view your profile.</p>
      </div>
    );
  }

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileErr(null);
    setProfileMsg(null);
    setProfileLoading(true);

    try {
      await updateProfile({
        full_name: fullName,
        phone: phone || undefined,
        address: address || undefined,
      });
      setProfileMsg('Profile information updated successfully.');
      await refreshUser();
    } catch (err: any) {
      setProfileErr(err.message || 'Failed to update profile.');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwErr(null);
    setPwMsg(null);

    if (!currentPassword) {
      setPwErr('Current password is required.');
      return;
    }
    if (newPassword.length < 8) {
      setPwErr('New password must be at least 8 characters long.');
      return;
    }
    if (!/[A-Za-z]/.test(newPassword) || !/\d/.test(newPassword)) {
      setPwErr('New password must contain at least one letter and one number.');
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwErr('New passwords do not match.');
      return;
    }

    setPwLoading(true);
    try {
      const res = await api.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMsg(res.message || 'Password updated successfully.');
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err: any) {
      setPwErr(err.message || 'Unable to update password.');
    } finally {
      setPwLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 rounded-2xl bg-forest-900 text-solar-400 flex items-center justify-center text-2xl font-black shadow-md">
            {user.full_name.charAt(0).toUpperCase()}
          </div>
          <div>
            <h1 className="text-2xl font-black text-forest-950 tracking-tight">{user.full_name}</h1>
            <p className="text-sm text-slate-500">{user.email}</p>
            <div className="mt-2 flex items-center space-x-2">
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                user.role === 'admin' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
              }`}>
                <ShieldCheck className="w-3.5 h-3.5 mr-1" />
                {user.role}
              </span>
              <span className="text-xs text-slate-400">
                Member since {new Date(user.created_at).toLocaleDateString()}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Profile Info Form */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-lg font-bold text-forest-950 mb-1 flex items-center">
            <UserIcon className="w-5 h-5 mr-2 text-forest-800" />
            <span>Personal Information</span>
          </h2>
          <p className="text-xs text-slate-500 mb-6">Manage your contact details and location.</p>

          {profileMsg && (
            <div className="mb-4 rounded-xl bg-emerald-50 border border-emerald-200 p-3 flex items-center space-x-2 text-emerald-800 text-xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{profileMsg}</span>
            </div>
          )}

          {profileErr && (
            <div className="mb-4 rounded-xl bg-rose-50 border border-rose-200 p-3 flex items-center space-x-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
              <span>{profileErr}</span>
            </div>
          )}

          <form onSubmit={handleUpdateProfile} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="block w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Email Address (Read-only)
              </label>
              <div className="flex items-center px-3 py-2 bg-slate-100 border border-slate-200 rounded-xl text-slate-500 text-sm">
                <Mail className="w-4 h-4 mr-2 text-slate-400" />
                <span>{user.email}</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Phone Number
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Phone className="w-4 h-4" />
                </div>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="01712345678"
                  className="block w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Address / Area
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <MapPin className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g. Dhanmondi, Dhaka"
                  className="block w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={profileLoading}
              className="w-full mt-2 py-2.5 px-4 rounded-xl font-bold text-sm text-white bg-forest-900 hover:bg-forest-800 disabled:opacity-50 transition-all cursor-pointer"
            >
              {profileLoading ? 'Saving...' : 'Update Information'}
            </button>
          </form>
        </div>

        {/* Change Password Form */}
        <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200">
          <h2 className="text-lg font-bold text-forest-950 mb-1 flex items-center">
            <Lock className="w-5 h-5 mr-2 text-forest-800" />
            <span>Security & Password</span>
          </h2>
          <p className="text-xs text-slate-500 mb-6">
            Updating your password secures your account across all active sessions.
          </p>

          {pwMsg && (
            <div className="mb-4 rounded-xl bg-emerald-50 border border-emerald-200 p-3 flex items-center space-x-2 text-emerald-800 text-xs">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <span>{pwMsg}</span>
            </div>
          )}

          {pwErr && (
            <div className="mb-4 rounded-xl bg-rose-50 border border-rose-200 p-3 flex items-center space-x-2 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0" />
              <span>{pwErr}</span>
            </div>
          )}

          <form onSubmit={handleChangePassword} className="space-y-4">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                New Password
              </label>
              <input
                type="password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Min 8 chars, letter & number"
                className="block w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700"
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Confirm New Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter new password"
                className="block w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-xl text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-forest-700"
              />
            </div>

            <button
              type="submit"
              disabled={pwLoading}
              className="w-full mt-2 py-2.5 px-4 rounded-xl font-bold text-sm text-white bg-slate-800 hover:bg-slate-900 disabled:opacity-50 transition-all cursor-pointer"
            >
              {pwLoading ? 'Updating Password...' : 'Change Password'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
