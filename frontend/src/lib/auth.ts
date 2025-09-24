// frontend/src/lib/auth.ts
import { User, AuthResponse } from '@/types';

export const authUtils = {
  setAuth: (authData: AuthResponse) => {
    localStorage.setItem('access_token', authData.access_token); // Match api.ts
    localStorage.setItem('user', JSON.stringify(authData.user)); // Match api.ts
  },

  getAuth: () => {
    if (typeof window === 'undefined') return { user: null, token: null };
    
    const token = localStorage.getItem('access_token'); // Match api.ts
    const user = localStorage.getItem('user'); // Match api.ts
    
    return {
      user: user ? JSON.parse(user) : null,
      token
    };
  },

  clearAuth: async () => {
    localStorage.removeItem('access_token'); // Match api.ts
    localStorage.removeItem('user'); // Match api.ts
  },

  isAuthenticated: (): boolean => {
    if (typeof window === 'undefined') return false;
    const token = localStorage.getItem('access_token'); // Match api.ts
    return !!token;
  },
};