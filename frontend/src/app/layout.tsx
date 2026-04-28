import type { Metadata } from 'next';
import { Cormorant_Garamond, Space_Grotesk } from 'next/font/google';
import './globals.css';

const bodyFont = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-body',
});

const displayFont = Cormorant_Garamond({
  subsets: ['latin'],
  variable: '--font-display',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'VexaAI | Document Intelligence Workspace',
  description: 'Turn dense PDF reports, briefs, and manuals into a searchable AI workspace.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${bodyFont.variable} ${displayFont.variable} min-h-screen bg-[var(--surface)] text-[var(--ink)] antialiased`}>
        {children}
      </body>
    </html>
  );
}
