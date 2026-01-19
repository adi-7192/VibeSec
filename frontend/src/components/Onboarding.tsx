'use client';

/**
 * VibeSec Frontend - Onboarding Component
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import {
    Rocket,
    Github,
    Upload,
    Play,
    ChevronRight,
    Sparkles,
    X,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface OnboardingProps {
    onClose: () => void;
    onGitHubConnect: () => void;
}

export default function Onboarding({ onClose, onGitHubConnect }: OnboardingProps) {
    const router = useRouter();
    const queryClient = useQueryClient();
    const [creating, setCreating] = useState(false);

    const createDemoMutation = useMutation({
        mutationFn: () => apiClient.post('/demo/project').then(r => r.data),
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            router.push(`/projects/${data.project_id}`);
        },
    });

    const handleCreateDemo = async () => {
        setCreating(true);
        await createDemoMutation.mutateAsync();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            <div className="relative bg-gradient-to-br from-slate-800 to-slate-900 rounded-3xl w-full max-w-2xl border border-slate-700 shadow-2xl overflow-hidden">
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-400 hover:text-white z-10"
                >
                    <X className="h-6 w-6" />
                </button>

                {/* Header */}
                <div className="p-8 pb-4 text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-500/20 rounded-2xl mb-4">
                        <Rocket className="h-8 w-8 text-purple-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Welcome to VibeSec!</h2>
                    <p className="text-gray-400">
                        Let&apos;s get your first project set up for security scanning.
                    </p>
                </div>

                {/* Options */}
                <div className="p-8 pt-4 space-y-4">
                    {/* Demo Project */}
                    <button
                        onClick={handleCreateDemo}
                        disabled={creating}
                        className={cn(
                            "w-full flex items-center gap-4 p-5 rounded-2xl border-2 transition-all text-left group",
                            "bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-purple-500/30",
                            "hover:from-purple-500/20 hover:to-pink-500/20 hover:border-purple-500/50",
                            creating && "opacity-50 cursor-not-allowed"
                        )}
                    >
                        <div className="p-3 bg-purple-500/20 rounded-xl">
                            <Sparkles className="h-6 w-6 text-purple-400" />
                        </div>
                        <div className="flex-1">
                            <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-white">Try Demo Project</h3>
                                <span className="px-2 py-0.5 bg-purple-500/30 text-purple-300 text-xs rounded-full">
                                    Recommended
                                </span>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">
                                Explore VibeSec with a pre-configured sample project with real security findings
                            </p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-purple-400 transition-colors" />
                    </button>

                    {/* GitHub */}
                    <button
                        onClick={onGitHubConnect}
                        className="w-full flex items-center gap-4 p-5 rounded-2xl border-2 border-slate-600 hover:border-slate-500 bg-slate-700/30 hover:bg-slate-700/50 transition-all text-left group"
                    >
                        <div className="p-3 bg-slate-600/50 rounded-xl">
                            <Github className="h-6 w-6 text-white" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-white">Connect GitHub</h3>
                            <p className="text-sm text-gray-400 mt-1">
                                Import a repository directly from your GitHub account
                            </p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-white transition-colors" />
                    </button>

                    {/* Upload ZIP */}
                    <button className="w-full flex items-center gap-4 p-5 rounded-2xl border-2 border-slate-600 hover:border-slate-500 bg-slate-700/30 hover:bg-slate-700/50 transition-all text-left group">
                        <div className="p-3 bg-slate-600/50 rounded-xl">
                            <Upload className="h-6 w-6 text-blue-400" />
                        </div>
                        <div className="flex-1">
                            <h3 className="font-semibold text-white">Upload ZIP File</h3>
                            <p className="text-sm text-gray-400 mt-1">
                                Upload your project source code as a ZIP archive
                            </p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 group-hover:text-white transition-colors" />
                    </button>
                </div>

                {/* Footer */}
                <div className="px-8 pb-6 text-center">
                    <button
                        onClick={onClose}
                        className="text-sm text-gray-500 hover:text-gray-300 transition-colors"
                    >
                        Skip for now
                    </button>
                </div>
            </div>
        </div>
    );
}
