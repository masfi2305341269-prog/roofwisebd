import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User } from '../types';
import { api } from '../services/api';
import { supabase } from '../services/supabase';

const IS_SUPABASE_MODE = (import.meta.env.VITE_AUTH_MODE || 'legacy') === 'supabase';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isLoading: boolean;
  authMode: 'legacy' | 'supabase';
  login: (credentials: { email: string; password: string }) => Promise<User>;
  adminLogin: (credentials: { email: string; password: string }) => Promise<User>;
  register: (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
    address?: string;
  }) => Promise<{ message: string; email: string; requiresEmailConfirmation?: boolean }>;
  verifyEmail: (data: { email: string; otp: string }) => Promise<{ message: string; email: string; email_verified: boolean }>;
  resendVerification: (data: { email: string }) => Promise<{ message: string; email: string; cooldown_seconds: number }>;
  logout: () => Promise<void>;
  updateProfile: (data: { full_name?: string; phone?: string; address?: string }) => Promise<User>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  /**
   * Load profile from FastAPI using the current Supabase session token.
   * Returns null if the profile isn't provisioned yet (409/404).
   */
  const loadSupabaseProfile = useCallback(async (): Promise<User | null> => {
    try {
      return await api.getMe();
    } catch {
      return null;
    }
  }, []);

  useEffect(() => {
    if (!IS_SUPABASE_MODE) {
      // ── LEGACY MODE bootstrap ──────────────────────────────────────────
      let isMounted = true;
      const initLegacy = async () => {
        try {
          await api.getCsrfToken().catch(() => {});
          const currentUser = await api.getMe();
          if (isMounted) setUser(currentUser);
        } catch {
          if (isMounted) setUser(null);
        } finally {
          if (isMounted) setIsLoading(false);
        }
      };
      initLegacy();
      return () => { isMounted = false; };
    } else {
      // ── SUPABASE MODE bootstrap ────────────────────────────────────────
      let isMounted = true;

      const initSupabase = async () => {
        // Check for an existing Supabase session on page load
        const { data: { session } } = await supabase.auth.getSession();
        if (session && isMounted) {
          const profile = await loadSupabaseProfile();
          if (isMounted) setUser(profile);
        }
        if (isMounted) setIsLoading(false);
      };

      initSupabase();

      // Listen for Supabase auth state changes (sign-in, sign-out, token refresh)
      const { data: { subscription } } = supabase.auth.onAuthStateChange(
        async (event, session) => {
          if (!isMounted) return;
          if (event === 'SIGNED_IN' && session) {
            const profile = await loadSupabaseProfile();
            if (isMounted) setUser(profile);
          } else if (event === 'SIGNED_OUT') {
            if (isMounted) setUser(null);
          } else if (event === 'TOKEN_REFRESHED' && session) {
            // Re-fetch profile on token refresh to pick up any changes
            const profile = await loadSupabaseProfile();
            if (isMounted) setUser(profile);
          }
        }
      );

      return () => {
        isMounted = false;
        subscription.unsubscribe();
      };
    }
  }, [loadSupabaseProfile]);

  const refreshUser = async () => {
    try {
      const currentUser = await api.getMe();
      setUser(currentUser);
    } catch {
      setUser(null);
    }
  };

  // ── LOGIN ──────────────────────────────────────────────────────────────
  const login = async (credentials: { email: string; password: string }): Promise<User> => {
    if (!IS_SUPABASE_MODE) {
      await api.getCsrfToken().catch(() => {});
      const loggedInUser = await api.login(credentials);
      setUser(loggedInUser);
      return loggedInUser;
    }

    // Supabase mode: signInWithPassword → fetch FastAPI profile
    const { data, error } = await supabase.auth.signInWithPassword({
      email: credentials.email.trim().toLowerCase(),
      password: credentials.password,
    });
    if (error) {
      // Map Supabase error messages to user-friendly text
      if (error.message.includes('Email not confirmed')) {
        throw new Error('Your email address has not been confirmed yet. Please check your inbox and click the confirmation link.');
      }
      if (error.message.includes('Invalid login credentials')) {
        throw new Error('Invalid email or password. Please check your credentials.');
      }
      throw new Error(error.message);
    }
    if (!data.session) throw new Error('Login failed: no session returned.');

    // Provision or fetch the FastAPI public.users profile
    try {
      const profile = await api.getMe();
      setUser(profile);
      return profile;
    } catch {
      // Profile not yet provisioned — caller (e.g. AuthCallbackPage) will handle it
      setUser(null);
      throw new Error('PROFILE_NOT_PROVISIONED');
    }
  };

  // ── ADMIN LOGIN (always uses legacy FastAPI, regardless of AUTH_MODE) ──
  const adminLogin = async (credentials: { email: string; password: string }): Promise<User> => {
    await api.getCsrfToken().catch(() => {});
    const adminUser = await api.adminLogin(credentials);
    if (adminUser.role !== 'admin') {
      await api.logout().catch(() => {});
      setUser(null);
      throw new Error('Access restricted: This account does not have administrator privileges.');
    }
    setUser(adminUser);
    return adminUser;
  };

  // ── REGISTER ───────────────────────────────────────────────────────────
  const register = async (data: {
    email: string;
    password: string;
    full_name: string;
    phone?: string;
    address?: string;
  }): Promise<{ message: string; email: string; requiresEmailConfirmation?: boolean }> => {
    if (!IS_SUPABASE_MODE) {
      await api.getCsrfToken().catch(() => {});
      await api.register(data);
      return {
        message: 'Account created! Please enter the 6-digit verification code sent to your email.',
        email: data.email.trim().toLowerCase(),
        requiresEmailConfirmation: false,
      };
    }

    // Supabase mode: signUp with metadata for the profile provisioning step
    const { data: sbData, error } = await supabase.auth.signUp({
      email: data.email.trim().toLowerCase(),
      password: data.password,
      options: {
        data: {
          full_name: data.full_name.trim(),
          phone: data.phone || null,
          address: data.address || null,
        },
        // Supabase sends the confirmation email to this address automatically
      },
    });

    if (error) {
      if (error.message.includes('already registered') || error.message.includes('User already registered')) {
        throw new Error('An account with this email address already exists. Please sign in instead.');
      }
      throw new Error(error.message);
    }

    if (!sbData.user) throw new Error('Registration failed: no user returned.');

    return {
      message: 'Account created! We\'ve sent a confirmation link to your email. Click it to activate your account.',
      email: data.email.trim().toLowerCase(),
      requiresEmailConfirmation: true,
    };
  };

  // ── OTP VERIFY / RESEND (legacy mode only; no-ops in Supabase mode) ───
  const verifyEmail = async (data: { email: string; otp: string }) => {
    if (!IS_SUPABASE_MODE) {
      await api.getCsrfToken().catch(() => {});
      return api.verifyEmail(data);
    }
    // In Supabase mode verification is handled by the confirmation email link
    return { message: 'Email verification is handled via your confirmation email link.', email: data.email, email_verified: false };
  };

  const resendVerification = async (data: { email: string }) => {
    if (!IS_SUPABASE_MODE) {
      await api.getCsrfToken().catch(() => {});
      return api.resendVerification(data);
    }
    // Resend Supabase confirmation email
    const { error } = await supabase.auth.resend({ type: 'signup', email: data.email });
    if (error) throw new Error(error.message);
    return { message: 'Confirmation email resent. Please check your inbox.', email: data.email, cooldown_seconds: 60 };
  };

  // ── LOGOUT ─────────────────────────────────────────────────────────────
  const logout = async () => {
    try {
      if (IS_SUPABASE_MODE) {
        await supabase.auth.signOut();
      } else {
        await api.logout();
      }
    } catch {
      // Clear client state even if network fails
    } finally {
      setUser(null);
    }
  };

  // ── UPDATE PROFILE ─────────────────────────────────────────────────────
  const updateProfile = async (data: { full_name?: string; phone?: string; address?: string }): Promise<User> => {
    const updated = await api.updateProfile(data);
    setUser(updated);
    return updated;
  };

  const isAuthenticated = Boolean(user && user.is_active);
  const isAdmin = Boolean(user && user.is_active && user.role === 'admin');

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isAdmin,
        isLoading,
        authMode: IS_SUPABASE_MODE ? 'supabase' : 'legacy',
        login,
        adminLogin,
        register,
        verifyEmail,
        resendVerification,
        logout,
        updateProfile,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
