'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowRight, BarChart3, BookOpenText, FileStack, MessagesSquare, ScanSearch, ShieldCheck } from 'lucide-react';
import { authUtils } from '@/lib/auth';

const featureCards = [
  {
    icon: ScanSearch,
    title: 'Answer against source material',
    copy: 'Turn dense PDFs into a searchable knowledge layer instead of manually skimming sections for every question.',
  },
  {
    icon: MessagesSquare,
    title: 'Keep session context intact',
    copy: 'Organize each document review as a live conversation instead of isolated one-off prompts.',
  },
  {
    icon: ShieldCheck,
    title: 'Built like a product, not a demo',
    copy: 'Authentication, document ownership, API boundaries, and structured pages make the experience feel deployable.',
  },
];

const workflow = [
  'Upload policy manuals, investor decks, due diligence packets, or internal reports.',
  'Ask targeted questions and follow up naturally without losing the thread.',
  'Use the workspace to review faster, brief teammates, and reduce repeated reading.',
];

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    if (authUtils.isAuthenticated()) {
      router.push('/chat');
    }
  }, [router]);

  return (
    <main className="overflow-hidden">
      <section className="relative px-4 pb-16 pt-6 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <header className="flex flex-col gap-5 pb-10 sm:flex-row sm:items-center sm:justify-between">
            <Link href="/" className="flex items-center gap-3 text-[var(--forest)]">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--forest)] text-[#fff8ef] shadow-lg shadow-emerald-950/10">
                <BookOpenText className="h-5 w-5" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.28em] text-[var(--muted)]">VexaAI</div>
                <div className="text-sm font-medium">Document Intelligence Workspace</div>
              </div>
            </Link>

            <div className="flex flex-wrap items-center gap-3">
              <Link href="/auth/login" className="secondary-button">
                Sign in
              </Link>
              <Link href="/auth/register" className="primary-button">
                Create account
              </Link>
            </div>
          </header>

          <div className="grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:items-center">
            <div className="max-w-3xl">
              <span className="hero-chip">For researchers, operators, analysts, and legal teams</span>
              <h1 className="mt-8 max-w-4xl text-6xl leading-[0.95] text-[var(--forest)] sm:text-7xl">
                Your PDFs deserve a real workspace, not a toy chatbot.
              </h1>
              <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)] sm:text-xl">
                VexaAI turns static files into a product-grade review flow. Upload documents, question them in plain language, and keep every answer tied to a usable session.
              </p>

              <div className="mt-10 flex flex-wrap gap-4">
                <Link href="/auth/register" className="primary-button">
                  Start with a workspace
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
                <Link href="/auth/login" className="secondary-button">
                  Continue to dashboard
                </Link>
              </div>

              <div className="mt-12 grid gap-4 sm:grid-cols-3">
                <div className="glass-card p-5">
                  <div className="text-3xl text-[var(--forest)]">50MB</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Upload capacity</div>
                </div>
                <div className="glass-card p-5">
                  <div className="text-3xl text-[var(--forest)]">Multi-session</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Conversation history</div>
                </div>
                <div className="glass-card p-5">
                  <div className="text-3xl text-[var(--forest)]">AI-ready</div>
                  <div className="mt-2 text-xs uppercase tracking-[0.2em] text-[var(--muted)]">Question answering</div>
                </div>
              </div>
            </div>

            <div className="glass-card relative overflow-hidden p-6 sm:p-8">
              <div className="absolute right-0 top-0 h-36 w-36 rounded-full bg-[rgba(195,91,51,0.16)] blur-3xl" />
              <div className="relative">
                <div className="flex items-center justify-between border-b border-[var(--line)] pb-5">
                  <div>
                    <div className="text-xs uppercase tracking-[0.22em] text-[var(--accent-deep)]">Active review</div>
                    <h2 className="mt-2 text-4xl text-[var(--forest)]">Board meeting packet</h2>
                  </div>
                  <div className="rounded-full bg-[rgba(36,70,61,0.1)] px-3 py-1 text-xs font-medium text-[var(--forest)]">
                    Context indexed
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  <div className="rounded-[24px] bg-[rgba(36,70,61,0.92)] p-5 text-[#f7efdf]">
                    <div className="text-xs uppercase tracking-[0.18em] text-[#d8c9aa]">Question</div>
                    <p className="mt-2 text-sm leading-6">
                      Which operating risks were called out most frequently across the Q3 board report?
                    </p>
                  </div>
                  <div className="rounded-[24px] border border-[var(--line)] bg-[rgba(255,250,240,0.82)] p-5">
                    <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-[var(--accent-deep)]">
                      <BarChart3 className="h-4 w-4" />
                      Response summary
                    </div>
                    <p className="mt-3 text-sm leading-7 text-[var(--muted)]">
                      Vendor concentration, delayed enterprise renewals, and cloud infrastructure spend appeared repeatedly. The most explicit discussion is concentrated in the operating review and finance appendix.
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-[var(--forest)]">
                      <span className="rounded-full bg-[rgba(36,70,61,0.08)] px-3 py-1">Ops review · page 8</span>
                      <span className="rounded-full bg-[rgba(36,70,61,0.08)] px-3 py-1">Finance appendix · page 21</span>
                    </div>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-[22px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-4">
                      <FileStack className="h-5 w-5 text-[var(--accent)]" />
                      <div className="mt-3 text-sm font-medium text-[var(--forest)]">Upload and organize</div>
                      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Keep documents, chats, and users inside one product surface.</p>
                    </div>
                    <div className="rounded-[22px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-4">
                      <MessagesSquare className="h-5 w-5 text-[var(--accent)]" />
                      <div className="mt-3 text-sm font-medium text-[var(--forest)]">Question with context</div>
                      <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Follow the thread instead of re-explaining the document every time.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 py-10 sm:px-6 lg:px-10">
        <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-3">
          {featureCards.map(({ icon: Icon, title, copy }) => (
            <article key={title} className="glass-card p-6 sm:p-7">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--forest)] text-[#fff8ef]">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="mt-5 text-3xl text-[var(--forest)]">{title}</h3>
              <p className="mt-3 text-sm leading-7 text-[var(--muted)]">{copy}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="px-4 py-12 sm:px-6 lg:px-10">
        <div className="mx-auto grid max-w-7xl gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="glass-card p-7 sm:p-9">
            <span className="hero-chip">How teams actually use it</span>
            <h2 className="mt-7 text-5xl leading-none text-[var(--forest)]">From upload to insight, without dead-end UX.</h2>
            <p className="mt-5 text-base leading-7 text-[var(--muted)]">
              The product is structured like a real internal tool: account entry, controlled upload flow, session management, and an interface that can plausibly support repeat usage.
            </p>
          </div>

          <div className="glass-card p-7 sm:p-9">
            <div className="space-y-5">
              {workflow.map((item, index) => (
                <div key={item} className="flex gap-4 rounded-[22px] border border-[var(--line)] bg-[rgba(255,250,240,0.72)] p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[var(--accent)] text-sm font-semibold text-[#fff8ef]">
                    0{index + 1}
                  </div>
                  <p className="pt-1 text-sm leading-7 text-[var(--muted)]">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="px-4 pb-16 pt-6 sm:px-6 lg:px-10">
        <div className="mx-auto max-w-7xl rounded-[36px] bg-[var(--forest)] px-8 py-10 text-[#f7efdf] shadow-2xl shadow-emerald-950/10 sm:px-10 sm:py-12">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-2xl">
              <div className="text-xs uppercase tracking-[0.26em] text-[#d9c9a7]">Ready to use</div>
              <h2 className="mt-4 text-5xl leading-none">Make the first impression feel like a product team built it.</h2>
              <p className="mt-4 text-base leading-7 text-[#e7dcc4]">
                Create an account, upload a real file, and move straight into a document conversation flow that feels deployable.
              </p>
            </div>

            <div className="flex flex-wrap gap-3">
              <Link href="/auth/register" className="rounded-full bg-[#f7efdf] px-6 py-3 text-sm font-semibold text-[var(--forest)] transition-colors hover:bg-white">
                Create account
              </Link>
              <Link href="/auth/login" className="rounded-full border border-[rgba(247,239,223,0.28)] px-6 py-3 text-sm font-semibold text-[#f7efdf] transition-colors hover:bg-[rgba(247,239,223,0.08)]">
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
