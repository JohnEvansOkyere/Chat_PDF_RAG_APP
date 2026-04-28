'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, Mail, ShieldCheck } from 'lucide-react';
import { authAPI } from '@/lib/api';
import { authUtils } from '@/lib/auth';
import toast from 'react-hot-toast';
import AuthShell from '@/components/auth/AuthShell';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await authAPI.login(email, password);
      authUtils.setAuth(response);
      toast.success('Login successful');
      router.push('/chat');
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      eyebrow="Sign In"
      title="Return to your document workspace."
      subtitle="Review evidence, cross-check sections, and continue active chats from one calm, focused workspace."
      alternateLabel="Create an account"
      alternateHref="/auth/register"
      alternateText="New here?"
    >
      <form className="space-y-5" onSubmit={handleSubmit}>
        <div className="rounded-[26px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-4 text-sm text-[var(--muted)]">
          <div className="flex items-center gap-2 text-[var(--forest)]">
            <ShieldCheck className="h-4 w-4" />
            Secure session
          </div>
          <p className="mt-2 leading-6">
            Sign in to access your uploaded documents, previous conversations, and active review sessions.
          </p>
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium text-[var(--forest)]">
            Work email
          </label>
          <div className="relative">
            <Mail className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#8b8f93]" />
            <input
              id="email"
              type="email"
              required
              className="auth-input pl-11"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="password" className="text-sm font-medium text-[var(--forest)]">
              Password
            </label>
            <Link href="/auth/register" className="text-xs font-medium uppercase tracking-[0.18em] text-[var(--accent-deep)]">
              Need access?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            required
            className="auth-input"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        <button type="submit" disabled={isLoading} className="primary-button w-full disabled:cursor-not-allowed disabled:opacity-60">
          {isLoading ? 'Signing in...' : 'Enter workspace'}
          {!isLoading && <ArrowRight className="ml-2 h-4 w-4" />}
        </button>
      </form>
    </AuthShell>
  );
}
