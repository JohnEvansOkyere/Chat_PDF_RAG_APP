'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, CheckCircle2, UserRound } from 'lucide-react';
import toast from 'react-hot-toast';
import { authAPI } from '@/lib/api';
import AuthShell from '@/components/auth/AuthShell';

export default function RegisterForm() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    displayName: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const router = useRouter();

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.displayName.trim()) {
      newErrors.displayName = 'Display name is required';
    } else if (formData.displayName.trim().length < 2) {
      newErrors.displayName = 'Display name must be at least 2 characters';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsLoading(true);

    try {
      await authAPI.register(formData.email, formData.password, formData.displayName);
      toast.success('Registration successful. Please sign in.');
      router.push('/auth/login');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || error.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Create Account"
      title="Open a workspace for serious document review."
      subtitle="Set up your account to manage uploads, organize sessions, and collaborate with an AI assistant trained on your PDFs."
      alternateLabel="Sign in"
      alternateHref="/auth/login"
      alternateText="Already have an account?"
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="grid gap-3 rounded-[26px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-4 text-sm text-[var(--muted)]">
          <div className="flex items-center gap-2 text-[var(--forest)]">
            <CheckCircle2 className="h-4 w-4" />
            Workspace includes
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <div>Document uploads and processing</div>
            <div>Session-based chat history</div>
            <div>Private account access</div>
            <div>Structured AI retrieval flow</div>
          </div>
        </div>

        <div className="space-y-2">
          <label htmlFor="displayName" className="text-sm font-medium text-[var(--forest)]">
            Full name
          </label>
          <div className="relative">
            <UserRound className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b8f93]" />
            <input
              id="displayName"
              name="displayName"
              type="text"
              required
              placeholder="Your full name"
              className={`auth-input pl-11 ${errors.displayName ? 'border-red-400' : ''}`}
              value={formData.displayName}
              onChange={handleInputChange}
            />
          </div>
          {errors.displayName && <p className="text-sm text-red-600">{errors.displayName}</p>}
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium text-[var(--forest)]">
            Email address
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            placeholder="you@company.com"
            className={`auth-input ${errors.email ? 'border-red-400' : ''}`}
            value={formData.email}
            onChange={handleInputChange}
          />
          {errors.email && <p className="text-sm text-red-600">{errors.email}</p>}
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium text-[var(--forest)]">
              Password
            </label>
            <input
              id="password"
              name="password"
              type="password"
              required
              placeholder="At least 6 characters"
              className={`auth-input ${errors.password ? 'border-red-400' : ''}`}
              value={formData.password}
              onChange={handleInputChange}
            />
            {errors.password && <p className="text-sm text-red-600">{errors.password}</p>}
          </div>

          <div className="space-y-2">
            <label htmlFor="confirmPassword" className="text-sm font-medium text-[var(--forest)]">
              Confirm password
            </label>
            <input
              id="confirmPassword"
              name="confirmPassword"
              type="password"
              required
              placeholder="Repeat your password"
              className={`auth-input ${errors.confirmPassword ? 'border-red-400' : ''}`}
              value={formData.confirmPassword}
              onChange={handleInputChange}
            />
            {errors.confirmPassword && <p className="text-sm text-red-600">{errors.confirmPassword}</p>}
          </div>
        </div>

        <button type="submit" disabled={isLoading} className="primary-button w-full disabled:cursor-not-allowed disabled:opacity-60">
          {isLoading ? 'Creating account...' : 'Create workspace'}
          {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
        </button>
      </form>
    </AuthShell>
  );
}
