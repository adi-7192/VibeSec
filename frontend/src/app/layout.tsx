import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';
import { QueryProvider } from '@/contexts/QueryProvider';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'VibeSec - Test your vibe-coded apps before launch',
  description:
    'Security and testing platform for AI-generated web applications. Get production-ready with SAST, SCA, and LLM-assisted fixes.',
  keywords: ['security', 'testing', 'AI', 'code analysis', 'SAST', 'SCA'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={inter.className}>
        <QueryProvider>
          <AuthProvider>{children}</AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
