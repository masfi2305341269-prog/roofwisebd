import {
  SolarRecommendationResponse,
  GenerationPredictionResponse,
  DustPredictionResponse,
  BatteryOptimizationResponse,
  SystemStatusResponse,
  User,
  AdminUserItem,
  AdminStats,
  SavedAssessmentRecord,
} from '../types';
import { getAccessToken } from './supabase';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';
const IS_SUPABASE_MODE = (import.meta.env.VITE_AUTH_MODE || 'legacy') === 'supabase';

function getCsrfTokenFromCookie(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(new RegExp('(^|;\\s*)roofwise_csrf_token=([^;]+)'));
  return match ? decodeURIComponent(match[2]) : null;
}

async function secureFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  const method = (options.method || 'GET').toUpperCase();

  // In Supabase mode, inject Supabase JWT as Bearer token for all requests
  // (admin routes use legacy cookie auth and don't need this)
  if (IS_SUPABASE_MODE && !headers.has('Authorization')) {
    const token = await getAccessToken();
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
  }

  // State-changing requests require CSRF token for cookie-based (legacy/admin) auth
  // Bearer-authenticated requests are inherently CSRF-safe (browser can't send custom
  // Authorization headers cross-origin without explicit CORS permission).
  if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method) && !headers.has('X-CSRF-Token')) {
    // Skip CSRF for Supabase-mode Bearer requests (backend verify_csrf also skips these)
    const hasBearer = headers.has('Authorization') && headers.get('Authorization')!.startsWith('Bearer ');
    if (!hasBearer) {
      let csrf = getCsrfTokenFromCookie();
      if (!csrf && !url.includes('/auth/csrf')) {
        try {
          const csrfRes = await fetch(`${API_BASE}/auth/csrf`, { credentials: 'include' });
          if (csrfRes.ok) {
            const data = await csrfRes.json();
            csrf = data.csrf_token;
          }
        } catch {
          // Fallback to cookie or proceeding
        }
      }
      if (csrf) {
        headers.set('X-CSRF-Token', csrf);
      }
    }
  }

  return fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await res.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // CSRF Bootstrap
  async getCsrfToken(): Promise<{ csrf_token: string }> {
    const res = await secureFetch(`${API_BASE}/auth/csrf`);
    return handleResponse<{ csrf_token: string }>(res);
  },

  // Authentication & Session
  async register(data: { email: string; password: string; full_name: string; phone?: string; address?: string }): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<User>(res);
  },

  async verifyEmail(data: { email: string; otp: string }): Promise<{ message: string; email: string; email_verified: boolean }> {
    const res = await secureFetch(`${API_BASE}/auth/verify-email`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<{ message: string; email: string; email_verified: boolean }>(res);
  },

  async resendVerification(data: { email: string }): Promise<{ message: string; email: string; cooldown_seconds: number }> {
    const res = await secureFetch(`${API_BASE}/auth/resend-verification`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<{ message: string; email: string; cooldown_seconds: number }>(res);
  },

  async login(data: { email: string; password: string }): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<User>(res);
  },

  async adminLogin(data: { email: string; password: string }): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/admin/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<User>(res);
  },

  async logout(): Promise<{ message: string }> {
    const res = await secureFetch(`${API_BASE}/auth/logout`, {
      method: 'POST',
    });
    return handleResponse<{ message: string }>(res);
  },

  async getMe(): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/me`);
    return handleResponse<User>(res);
  },

  async provisionProfile(): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/provision-profile`, {
      method: 'POST',
    });
    return handleResponse<User>(res);
  },

  async linkLegacyAccount(legacyPassword: string): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/link-legacy-account`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ legacy_password: legacyPassword }),
    });
    return handleResponse<User>(res);
  },

  async updateProfile(data: { full_name?: string; phone?: string; address?: string }): Promise<User> {
    const res = await secureFetch(`${API_BASE}/auth/me`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<User>(res);
  },

  async changePassword(data: { current_password: string; new_password: string }): Promise<{ message: string }> {
    const res = await secureFetch(`${API_BASE}/auth/change-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<{ message: string }>(res);
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const res = await secureFetch(`${API_BASE}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async resetPassword(token: string, new_password: string): Promise<{ message: string }> {
    const res = await secureFetch(`${API_BASE}/auth/reset-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async getDevLastResetToken(email: string): Promise<{ email: string; token: string }> {
    const res = await secureFetch(`${API_BASE}/auth/dev/last-reset-token?email=${encodeURIComponent(email)}`);
    return handleResponse<{ email: string; token: string }>(res);
  },

  // User Assessments History & Claiming
  async getUserAssessments(): Promise<SavedAssessmentRecord[]> {
    const res = await secureFetch(`${API_BASE}/solar/user/assessments`);
    return handleResponse<SavedAssessmentRecord[]>(res);
  },

  async getSingleAssessment(id: number, claimToken?: string): Promise<SavedAssessmentRecord> {
    const headers: Record<string, string> = {};
    if (claimToken) {
      headers['X-Claim-Token'] = claimToken;
    }
    const res = await secureFetch(`${API_BASE}/solar/assessment/${id}`, { headers });
    return handleResponse<SavedAssessmentRecord>(res);
  },

  async claimAssessment(assessmentId: number, claimToken: string): Promise<{ message: string; assessment_id: number }> {
    const res = await secureFetch(`${API_BASE}/solar/assessment/${assessmentId}/claim`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ claim_token: claimToken }),
    });
    return handleResponse<{ message: string; assessment_id: number }>(res);
  },

  // Admin Endpoints
  async getAdminStats(): Promise<AdminStats> {
    const res = await secureFetch(`${API_BASE}/admin/stats`);
    return handleResponse<AdminStats>(res);
  },

  async getAdminUsers(): Promise<AdminUserItem[]> {
    const res = await secureFetch(`${API_BASE}/admin/users`);
    return handleResponse<AdminUserItem[]>(res);
  },

  async toggleUserStatus(userId: number, isActive: boolean): Promise<{ message: string }> {
    const res = await secureFetch(`${API_BASE}/admin/users/${userId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ is_active: isActive }),
    });
    return handleResponse<{ message: string }>(res);
  },

  async getAdminAssessments(limit: number = 50): Promise<any[]> {
    const res = await secureFetch(`${API_BASE}/admin/assessments?limit=${limit}`);
    return handleResponse<any[]>(res);
  },

  // Health & Status
  async getHealth() {
    const res = await secureFetch(`${API_BASE}/health`);
    return handleResponse<{ status: string; service: string; version: string }>(res);
  },

  async getSystemStatus(): Promise<SystemStatusResponse> {
    const res = await secureFetch(`${API_BASE}/system/status`);
    return handleResponse<SystemStatusResponse>(res);
  },

  async getModelsStatus() {
    const res = await secureFetch(`${API_BASE}/models/status`);
    return handleResponse<{ status: string; models: any[] }>(res);
  },

  async getDatasetsStatus() {
    const res = await secureFetch(`${API_BASE}/datasets/status`);
    return handleResponse<{ status: string; datasets: any[] }>(res);
  },

  // Rooftop Analysis
  async analyzeRooftop(data: {
    total_area_sqft: number;
    roof_type: string;
    shading_condition: string;
    manual_usable_area_sqft?: number;
    panel_wattage_wp?: number;
  }) {
    const res = await secureFetch(`${API_BASE}/rooftop/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<any>(res);
  },

  async uploadRooftopImage(file: File): Promise<{ filename: string; image_url: string; file_size_kb: number; message: string }> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await secureFetch(`${API_BASE}/rooftop/upload-image`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<{ filename: string; image_url: string; file_size_kb: number; message: string }>(res);
  },

  // Solar Recommendation
  async getSolarRecommendation(data: {
    monthly_units_kwh: number;
    total_roof_area_sqft: number;
    sanctioned_load_kw: number;
    division: string;
    roof_type?: string;
    shading_condition?: string;
    usable_roof_area_sqft?: number;
  }): Promise<SolarRecommendationResponse> {
    const res = await secureFetch(`${API_BASE}/solar/recommendation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<SolarRecommendationResponse>(res);
  },

  // Full Assessment Submission
  async submitAssessment(data: any) {
    const res = await secureFetch(`${API_BASE}/solar/assessment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<any>(res);
  },

  // Generation Prediction (ML 1)
  async predictGeneration(data: {
    system_capacity_kwp: number;
    division: string;
    tilt_degrees?: number;
    shading_factor?: number;
  }): Promise<GenerationPredictionResponse> {
    const res = await secureFetch(`${API_BASE}/generation/predict`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<GenerationPredictionResponse>(res);
  },

  // Dust Detection (ML 2)
  async predictDust(file: File): Promise<DustPredictionResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await secureFetch(`${API_BASE}/dust/predict`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<DustPredictionResponse>(res);
  },

  // Bill Analysis
  async analyzeBill(file: File, manualUnits?: number, manualBill?: number) {
    const formData = new FormData();
    formData.append('file', file);
    if (manualUnits) formData.append('manual_units_kwh', manualUnits.toString());
    if (manualBill) formData.append('manual_bill_bdt', manualBill.toString());
    const res = await secureFetch(`${API_BASE}/bill/analyze`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<any>(res);
  },

  // Battery Optimization
  async getBatteryRecommendation(data: {
    appliances: Array<{
      name: string;
      wattage: number;
      quantity: number;
      daily_usage_hours: number;
      is_critical: boolean;
    }>;
    required_backup_hours: number;
    battery_chemistry: string;
    custom_dod?: number;
    custom_inverter_eff?: number;
  }): Promise<BatteryOptimizationResponse> {
    const res = await secureFetch(`${API_BASE}/battery/recommendation`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<BatteryOptimizationResponse>(res);
  },
};
