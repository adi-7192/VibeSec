'use client';

/**
 * VibeSec Frontend - Dashboard Layout
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { logout } from '@/lib/firebase';
import {
    LayoutDashboard,
    Settings,
    LogOut,
    User,
    Shield,
    Menu,
    X,
} from 'lucide-react';
import { useState } from 'react';
import { cn } from '@/lib/utils';

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const { user, loading, isAuthenticated } = useAuth();
    const router = useRouter();
    const [sidebarOpen, setSidebarOpen] = useState(false);

    useEffect(() => {
        if (!loading && !isAuthenticated) {
            router.push('/login');
        }
    }, [loading, isAuthenticated, router]);

    const handleLogout = async () => {
        await logout();
        router.push('/login');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (!isAuthenticated) {
        return null;
    }

    const navigation = [
        { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
        { name: 'Settings', href: '/settings', icon: Settings },
    ];

    return (
        <div className="min-h-screen bg-slate-900">
            {/* Mobile sidebar backdrop */}
            {sidebarOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 lg:hidden"
                    onClick={() => setSidebarOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    'fixed top-0 left-0 z-50 h-full w-64 bg-slate-800 border-r border-slate-700 transform transition-transform lg:translate-x-0',
                    sidebarOpen ? 'translate-x-0' : '-translate-x-full'
                )}
            >
                {/* Logo */}
                <div className="h-16 flex items-center justify-between px-6 border-b border-slate-700">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <Shield className="h-8 w-8 text-purple-500" />
                        <span className="text-xl font-bold text-white">
                            <span className="text-purple-400">Vibe</span>Sec
                        </span>
                    </Link>
                    <button
                        onClick={() => setSidebarOpen(false)}
                        className="lg:hidden text-gray-400 hover:text-white"
                    >
                        <X className="h-6 w-6" />
                    </button>
                </div>

                {/* Navigation */}
                <nav className="flex-1 px-4 py-6 space-y-1">
                    {navigation.map((item) => (
                        <Link
                            key={item.name}
                            href={item.href}
                            className="flex items-center gap-3 px-3 py-2 text-gray-300 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                        >
                            <item.icon className="h-5 w-5" />
                            {item.name}
                        </Link>
                    ))}
                </nav>

                {/* User section */}
                <div className="p-4 border-t border-slate-700">
                    <div className="flex items-center gap-3 px-3 py-2">
                        <div className="h-8 w-8 bg-purple-600 rounded-full flex items-center justify-center">
                            {user?.picture ? (
                                <img
                                    src={user.picture}
                                    alt=""
                                    className="h-8 w-8 rounded-full"
                                />
                            ) : (
                                <User className="h-4 w-4 text-white" />
                            )}
                        </div>
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-white truncate">
                                {user?.name || user?.email}
                            </p>
                            <p className="text-xs text-gray-400 truncate">{user?.email}</p>
                        </div>
                    </div>
                    <button
                        onClick={handleLogout}
                        className="mt-2 w-full flex items-center gap-3 px-3 py-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        <LogOut className="h-5 w-5" />
                        Sign out
                    </button>
                </div>
            </aside>

            {/* Main content */}
            <div className="lg:pl-64">
                {/* Top bar */}
                <header className="h-16 bg-slate-800/50 border-b border-slate-700 flex items-center px-6 sticky top-0 z-30 backdrop-blur-sm">
                    <button
                        onClick={() => setSidebarOpen(true)}
                        className="lg:hidden text-gray-400 hover:text-white mr-4"
                    >
                        <Menu className="h-6 w-6" />
                    </button>
                    <div className="flex-1" />
                </header>

                {/* Page content */}
                <main className="p-6">{children}</main>
            </div>
        </div>
    );
}
