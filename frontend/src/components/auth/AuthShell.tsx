'use client';

import Link from 'next/link';
import { BookOpenText, Clock3, LockKeyhole, Sparkles } from 'lucide-react';
import { ReactNode } from 'react';

type AuthShellProps = {
  eyebrow: string;
  title: string;
  subtitle: string;
  alternateLabel: string;
  alternateHref: string;
  alternateText: string;
  children: ReactNode;
};

const highlights = [
  {
    icon: BookOpenText,
    title: 'Built for serious reading',
    copy: 'Analyze investor decks, legal clauses, research reports, and operating manuals in one workspace.',
  },
  {
    icon: Clock3,
    title: 'Responses with pace',
    copy: 'Turn multi-page PDFs into question-ready context without forcing users through a brittle workflow.',
  },
  {
    icon: LockKeyhole,
    title: 'Private by default',
    copy: 'Authentication, document ownership, and session history are kept behind your API boundary.',
  },
];

export default function AuthShell({
  eyebrow,
  title,
  subtitle,
  alternateLabel,
  alternateHref,
  alternateText,
  children,
}: AuthShellProps) {
  return (
    <main className="relative min-h-screen overflow-hidden px-4 py-6 sm:px-6 lg:px-10">
      <div className="mx-auto flex max-w-7xl items-center justify-between pb-8">
        <Link href="/" className="flex items-center gap-3 text-[var(--forest)]">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--forest)] text-[#fff8ef] shadow-lg shadow-emerald-950/10">
            <BookOpenText className="h-5 w-5" />
          </div>
          <div>
            <div className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">VexaAI</div>
            <div className="text-sm font-medium">Document Intelligence</div>
          </div>
        </Link>
        <Link href="/" className="secondary-button hidden sm:inline-flex">
          Back to overview
        </Link>
      </div>

      <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[1.15fr_0.85fr]">
        <section className="glass-card relative overflow-hidden px-7 py-8 sm:px-10 sm:py-10 lg:px-12 lg:py-12">
          <div className="absolute -right-14 top-8 h-40 w-40 rounded-full bg-[rgba(195,91,51,0.12)] blur-3xl" />
          <div className="absolute bottom-0 left-0 h-56 w-56 rounded-full bg-[rgba(36,70,61,0.1)] blur-3xl" />

          <div className="relative max-w-xl">
            <span className="hero-chip">
              <Sparkles className="h-3.5 w-3.5" />
              Trusted workflow for document-heavy teams
            </span>
            <h1 className="mt-8 text-5xl leading-none text-[var(--forest)] sm:text-6xl">{title}</h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-[var(--muted)] sm:text-lg">{subtitle}</p>
          </div>

          <div className="relative mt-10 grid gap-4">
            {highlights.map(({ icon: Icon, title: itemTitle, copy }) => (
              <div key={itemTitle} className="rounded-[24px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-5">
                <div className="flex items-start gap-4">
                  <div className="mt-1 flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--forest)] text-[#fff8ef]">
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h2 className="text-2xl text-[var(--forest)]">{itemTitle}</h2>
                    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">{copy}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="relative mt-10 grid gap-4 rounded-[28px] border border-[rgba(36,70,61,0.12)] bg-[rgba(36,70,61,0.95)] p-6 text-[#f7efdf] sm:grid-cols-3">
            <div>
              <div className="text-3xl">50MB</div>
              <div className="mt-2 text-xs uppercase tracking-[0.22em] text-[#dccdb3]">Document size</div>
            </div>
            <div>
              <div className="text-3xl">Multi-chat</div>
              <div className="mt-2 text-xs uppercase tracking-[0.22em] text-[#dccdb3]">Session history</div>
            </div>
            <div>
              <div className="text-3xl">Contextual</div>
              <div className="mt-2 text-xs uppercase tracking-[0.22em] text-[#dccdb3]">Answer generation</div>
            </div>
          </div>
        </section>

        <section className="glass-card px-6 py-7 sm:px-8 sm:py-8">
          <div className="mb-8 flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.26em] text-[var(--accent-deep)]">{eyebrow}</div>
              <div className="mt-2 text-sm text-[var(--muted)]">Use your workspace credentials to continue.</div>
            </div>
            <div className="hidden rounded-full border border-[var(--line)] bg-[rgba(255,250,240,0.8)] px-3 py-1 text-xs text-[var(--forest)] sm:block">
              Secure access
            </div>
          </div>

          {children}

          <div className="mt-7 border-t border-[var(--line)] pt-5 text-sm text-[var(--muted)]">
            {alternateText}{' '}
            <Link href={alternateHref} className="font-semibold text-[var(--accent-deep)] transition-colors hover:text-[var(--accent)]">
              {alternateLabel}
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
