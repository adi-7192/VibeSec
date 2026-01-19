'use client';

/**
 * VibeSec Frontend - GitHub Repository Selection Page
 * 
 * Displays user's GitHub repositories for project creation.
 */

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import Link from 'next/link';
import apiClient, { createProjectFromGitHub } from '@/lib/api';
import { formatDate, cn } from '@/lib/utils';
import {
    ArrowLeft,
    Github,
    Star,
    Lock,
    Globe,
    Loader2,
    Search,
    RefreshCw,
    AlertCircle,
} from 'lucide-react';

interface GitHubRepo {
    id: number;
    name: string;
    full_name: string;
    description: string | null;
    html_url: string;
    clone_url: string;
    default_branch: string;
    private: boolean;
    language: string | null;
    updated_at: string;
    stargazers_count: number;
}

export default function GitHubRepoSelectionPage() {
    const router = useRouter();
    const queryClient = useQueryClient();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedRepo, setSelectedRepo] = useState<GitHubRepo | null>(null);

    // Fetch repositories
    const { data, isLoading, error, refetch, isRefetching } = useQuery({
        queryKey: ['github-repos'],
        queryFn: async () => {
            const response = await apiClient.get('/github/repos', {
                params: { per_page: 100 }
            });
            return response.data as { repos: GitHubRepo[] };
        },
    });

    // Create project mutation
    const createProjectMutation = useMutation({
        mutationFn: async (repo: GitHubRepo) => {
            return createProjectFromGitHub({
                name: repo.name,
                description: repo.description || undefined,
                repo_url: repo.clone_url,
                repo_full_name: repo.full_name,
                default_branch: repo.default_branch,
            });
        },
        onSuccess: (project) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            router.push(`/projects/${project.id}`);
        },
    });

    const repos = data?.repos || [];
    const filteredRepos = repos.filter(repo =>
        repo.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        repo.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (repo.description?.toLowerCase().includes(searchQuery.toLowerCase()))
    );

    const handleSelectRepo = (repo: GitHubRepo) => {
        setSelectedRepo(repo);
        createProjectMutation.mutate(repo);
    };

    // Language colors (subset)
    const languageColors: Record<string, string> = {
        TypeScript: 'bg-blue-500',
        JavaScript: 'bg-yellow-400',
        Python: 'bg-green-500',
        Go: 'bg-cyan-400',
        Rust: 'bg-orange-500',
        Java: 'bg-red-500',
        Ruby: 'bg-red-400',
        PHP: 'bg-purple-500',
        Swift: 'bg-orange-400',
        Kotlin: 'bg-purple-400',
    };

    return (
        <div className="max-w-4xl mx-auto py-8">
            {/* Header */}
            <div className="mb-8">
                <Link
                    href="/dashboard"
                    className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Dashboard
                </Link>
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <Github className="h-8 w-8" />
                            Select Repository
                        </h1>
                        <p className="text-gray-400 mt-2">
                            Choose a repository to analyze for security vulnerabilities
                        </p>
                    </div>
                    <button
                        onClick={() => refetch()}
                        disabled={isRefetching}
                        className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50"
                    >
                        <RefreshCw className={cn("h-4 w-4", isRefetching && "animate-spin")} />
                        Refresh
                    </button>
                </div>
            </div>

            {/* Search */}
            <div className="relative mb-6">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search repositories..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-12 pr-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                />
            </div>

            {/* Error State */}
            {error && (
                <div className="p-6 bg-red-500/10 border border-red-500/30 rounded-xl mb-6">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-red-400 font-medium">Failed to load repositories</p>
                            <p className="text-red-300 text-sm mt-1">
                                {(error as Error)?.message || 'Please make sure your GitHub account is connected.'}
                            </p>
                            <Link
                                href="/settings"
                                className="inline-block mt-3 text-sm text-purple-400 hover:text-purple-300"
                            >
                                Go to Settings to connect GitHub →
                            </Link>
                        </div>
                    </div>
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="flex flex-col items-center justify-center py-16">
                    <Loader2 className="h-10 w-10 text-purple-500 animate-spin mb-4" />
                    <p className="text-gray-400">Loading your repositories...</p>
                </div>
            )}

            {/* Repository List */}
            {!isLoading && !error && (
                <>
                    <p className="text-gray-400 text-sm mb-4">
                        {filteredRepos.length} {filteredRepos.length === 1 ? 'repository' : 'repositories'} found
                    </p>

                    <div className="space-y-3">
                        {filteredRepos.map((repo) => (
                            <div
                                key={repo.id}
                                className={cn(
                                    "bg-slate-800 rounded-xl p-5 border transition-all",
                                    selectedRepo?.id === repo.id
                                        ? "border-purple-500 bg-purple-500/10"
                                        : "border-slate-700 hover:border-slate-500"
                                )}
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-2 mb-1">
                                            {repo.private ? (
                                                <Lock className="h-4 w-4 text-yellow-400" />
                                            ) : (
                                                <Globe className="h-4 w-4 text-gray-400" />
                                            )}
                                            <h3 className="font-semibold text-white truncate">
                                                {repo.full_name}
                                            </h3>
                                        </div>

                                        {repo.description && (
                                            <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                                                {repo.description}
                                            </p>
                                        )}

                                        <div className="flex items-center gap-4 text-sm">
                                            {repo.language && (
                                                <span className="flex items-center gap-1.5">
                                                    <span className={cn(
                                                        "w-3 h-3 rounded-full",
                                                        languageColors[repo.language] || "bg-gray-500"
                                                    )} />
                                                    <span className="text-gray-300">{repo.language}</span>
                                                </span>
                                            )}
                                            {repo.stargazers_count > 0 && (
                                                <span className="flex items-center gap-1 text-gray-400">
                                                    <Star className="h-4 w-4" />
                                                    {repo.stargazers_count}
                                                </span>
                                            )}
                                            <span className="text-gray-500">
                                                Updated {formatDate(repo.updated_at)}
                                            </span>
                                        </div>
                                    </div>

                                    <button
                                        onClick={() => handleSelectRepo(repo)}
                                        disabled={createProjectMutation.isPending}
                                        className={cn(
                                            "ml-4 px-4 py-2 rounded-lg font-medium transition-all flex items-center gap-2",
                                            selectedRepo?.id === repo.id && createProjectMutation.isPending
                                                ? "bg-purple-600 text-white"
                                                : "bg-slate-700 text-white hover:bg-purple-600"
                                        )}
                                    >
                                        {selectedRepo?.id === repo.id && createProjectMutation.isPending ? (
                                            <>
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                                Creating...
                                            </>
                                        ) : (
                                            'Select'
                                        )}
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>

                    {filteredRepos.length === 0 && repos.length > 0 && (
                        <div className="text-center py-12">
                            <p className="text-gray-400">No repositories match your search.</p>
                        </div>
                    )}

                    {repos.length === 0 && (
                        <div className="text-center py-12">
                            <Github className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400 mb-2">No repositories found</p>
                            <p className="text-gray-500 text-sm">
                                Make sure you have repositories in your GitHub account.
                            </p>
                        </div>
                    )}
                </>
            )}

            {/* Error from mutation */}
            {createProjectMutation.isError && (
                <div className="fixed bottom-6 right-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl max-w-md">
                    <div className="flex items-start gap-3">
                        <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
                        <div>
                            <p className="text-red-400 font-medium">Failed to create project</p>
                            <p className="text-red-300 text-sm">
                                {(createProjectMutation.error as Error)?.message || 'Please try again.'}
                            </p>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
