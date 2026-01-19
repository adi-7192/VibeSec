'use client';

/**
 * VibeSec Frontend - Login Page
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { signInWithEmail, signUpWithEmail, signInWithGoogle, resetPassword } from '@/lib/firebase';
import { cn } from '@/lib/utils';

type AuthMode = 'signin' | 'signup' | 'reset';

export default function LoginPage() {
    const router = useRouter();
    const [mode, setMode] = useState<AuthMode>('signin');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setMessage('');
        setLoading(true);

        try {
            if (mode === 'reset') {
                await resetPassword(email);
                setMessage('Password reset email sent! Check your inbox.');
                setMode('signin');
            } else if (mode === 'signup') {
                if (password !== confirmPassword) {
                    setError('Passwords do not match');
                    setLoading(false);
                    return;
                }
                if (password.length < 6) {
                    setError('Password must be at least 6 characters');
                    setLoading(false);
                    return;
                }
                await signUpWithEmail(email, password);
                router.push('/dashboard');
            } else {
                await signInWithEmail(email, password);
                router.push('/dashboard');
            }
        } catch (err: any) {
            const errorMessage = err.code === 'auth/user-not-found'
                ? 'No account found with this email'
                : err.code === 'auth/wrong-password'
                    ? 'Incorrect password'
                    : err.code === 'auth/email-already-in-use'
                        ? 'An account with this email already exists'
                        : err.code === 'auth/invalid-email'
                            ? 'Invalid email address'
                            : err.message || 'An error occurred';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    const handleGoogleSignIn = async () => {
        setError('');
        setLoading(true);
        try {
            await signInWithGoogle();
            router.push('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Failed to sign in with Google');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-white mb-2">
                        <span className="text-purple-400">Vibe</span>Sec
                    </h1>
                    <p className="text-gray-400">Test your vibe-coded apps before launch</p>
                </div>

                {/* Card */}
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
                    {/* Tabs */}
                    <div className="flex mb-6 bg-white/5 rounded-lg p-1">
                        <button
                            onClick={() => { setMode('signin'); setError(''); }}
                            className={cn(
                                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
                                mode === 'signin'
                                    ? 'bg-purple-600 text-white'
                                    : 'text-gray-300 hover:text-white'
                            )}
                        >
                            Sign In
                        </button>
                        <button
                            onClick={() => { setMode('signup'); setError(''); }}
                            className={cn(
                                'flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all',
                                mode === 'signup'
                                    ? 'bg-purple-600 text-white'
                                    : 'text-gray-300 hover:text-white'
                            )}
                        >
                            Create Account
                        </button>
                    </div>

                    {/* Error/Message */}
                    {error && (
                        <div className="bg-red-500/20 border border-red-500/50 text-red-200 px-4 py-3 rounded-lg mb-4 text-sm">
                            {error}
                        </div>
                    )}
                    {message && (
                        <div className="bg-green-500/20 border border-green-500/50 text-green-200 px-4 py-3 rounded-lg mb-4 text-sm">
                            {message}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-300 mb-1">
                                Email
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                placeholder="you@example.com"
                                required
                            />
                        </div>

                        {mode !== 'reset' && (
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Password
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        )}

                        {mode === 'signup' && (
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">
                                    Confirm Password
                                </label>
                                <input
                                    type="password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                                    placeholder="••••••••"
                                    required
                                />
                            </div>
                        )}

                        {mode === 'signin' && (
                            <div className="text-right">
                                <button
                                    type="button"
                                    onClick={() => setMode('reset')}
                                    className="text-sm text-purple-400 hover:text-purple-300"
                                >
                                    Forgot password?
                                </button>
                            </div>
                        )}

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full py-3 px-4 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading
                                ? 'Please wait...'
                                : mode === 'signin'
                                    ? 'Sign In'
                                    : mode === 'signup'
                                        ? 'Create Account'
                                        : 'Send Reset Email'}
                        </button>
                    </form>

                    {mode !== 'reset' && (
                        <>
                            {/* Divider */}
                            <div className="flex items-center my-6">
                                <div className="flex-1 border-t border-white/10"></div>
                                <span className="px-4 text-sm text-gray-400">or</span>
                                <div className="flex-1 border-t border-white/10"></div>
                            </div>

                            {/* Google Sign In */}
                            <button
                                onClick={handleGoogleSignIn}
                                disabled={loading}
                                className="w-full py-3 px-4 bg-white/10 border border-white/20 text-white font-medium rounded-lg hover:bg-white/20 focus:outline-none focus:ring-2 focus:ring-white/50 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                            >
                                <svg className="w-5 h-5" viewBox="0 0 24 24">
                                    <path
                                        fill="currentColor"
                                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                                    />
                                    <path
                                        fill="currentColor"
                                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                                    />
                                </svg>
                                Continue with Google
                            </button>
                        </>
                    )}

                    {mode === 'reset' && (
                        <button
                            onClick={() => setMode('signin')}
                            className="w-full mt-4 text-sm text-gray-400 hover:text-white"
                        >
                            ← Back to sign in
                        </button>
                    )}
                </div>

                {/* Footer */}
                <p className="text-center text-gray-500 text-sm mt-6">
                    By continuing, you agree to our Terms of Service and Privacy Policy.
                </p>
            </div>
        </div>
    );
}
