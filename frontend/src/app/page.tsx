'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';
import { Shield, ArrowRight, CheckCircle, Zap, Lock, Code } from 'lucide-react';

export default function HomePage() {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push('/dashboard');
    }
  }, [loading, isAuthenticated, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900">
      {/* Header */}
      <header className="container mx-auto px-6 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="h-8 w-8 text-purple-500" />
            <span className="text-2xl font-bold text-white">
              <span className="text-purple-400">Vibe</span>Sec
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-gray-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/login"
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <main className="container mx-auto px-6 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-purple-500/20 rounded-full text-purple-300 text-sm mb-8">
            <Zap className="h-4 w-4" />
            Built for vibe-coded applications
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Test your{' '}
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
              vibe-coded
            </span>{' '}
            apps before launch
          </h1>

          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Security and testing platform designed for AI-generated web applications.
            Get production-ready with automated SAST, SCA, and LLM-assisted remediation.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/login"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg shadow-purple-500/25"
            >
              Start Free Analysis
              <ArrowRight className="h-5 w-5" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center justify-center gap-2 px-8 py-4 bg-white/10 text-white font-semibold rounded-xl hover:bg-white/20 transition-all border border-white/20"
            >
              See How It Works
            </a>
          </div>
        </div>

        {/* Features */}
        <div id="features" className="mt-32 grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon={Lock}
            title="Security Analysis"
            description="SAST and SCA scanning to detect vulnerabilities, hardcoded secrets, and dependency issues in your AI-generated code."
          />
          <FeatureCard
            icon={CheckCircle}
            title="Production Readiness"
            description="Get a comprehensive readiness score across security, testing, reliability, observability, and infrastructure."
          />
          <FeatureCard
            icon={Code}
            title="AI-Powered Fixes"
            description="LLM-generated code fixes and test cases. Create PRs automatically or copy patches directly."
          />
        </div>

        {/* Supported Stacks */}
        <div className="mt-32 text-center">
          <p className="text-gray-400 mb-8">Supported frameworks</p>
          <div className="flex flex-wrap justify-center gap-8">
            <StackBadge emoji="⚛️" name="Next.js" />
            <StackBadge emoji="🟢" name="Express" />
            <StackBadge emoji="🐍" name="Django" />
            <StackBadge emoji="⚡" name="FastAPI" />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-6 py-12 mt-20 border-t border-slate-800">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-purple-500" />
            <span className="text-lg font-bold text-white">
              <span className="text-purple-400">Vibe</span>Sec
            </span>
          </div>
          <p className="text-gray-500 text-sm">
            © 2026 VibeSec. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  description,
}: {
  icon: any;
  title: string;
  description: string;
}) {
  return (
    <div className="p-8 bg-slate-800/50 rounded-2xl border border-slate-700 hover:border-purple-500/50 transition-all">
      <div className="w-12 h-12 bg-purple-500/20 rounded-xl flex items-center justify-center mb-4">
        <Icon className="h-6 w-6 text-purple-400" />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </div>
  );
}

function StackBadge({ emoji, name }: { emoji: string; name: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg border border-slate-700">
      <span className="text-2xl">{emoji}</span>
      <span className="text-white font-medium">{name}</span>
    </div>
  );
}
