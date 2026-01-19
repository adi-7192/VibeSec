'use client';

/**
 * VibeSec Frontend - Dashboard Page
 */

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import apiClient, { getProjects, Project } from '@/lib/api';
import { getIdToken } from '@/lib/firebase';
import {
    formatDate,
    getScoreColor,
    getScoreLabel,
    getStackIcon,
    cn
} from '@/lib/utils';
import {
    Plus,
    Github,
    Upload,
    TrendingUp,
    AlertTriangle,
    CheckCircle,
    XCircle,
    FolderOpen,
} from 'lucide-react';

export default function DashboardPage() {
    const [showNewProjectModal, setShowNewProjectModal] = useState(false);

    const { data, isLoading, error } = useQuery({
        queryKey: ['projects'],
        queryFn: getProjects,
    });

    const projects = data?.projects || [];

    // Calculate aggregate stats
    const totalProjects = projects.length;
    const avgScore =
        projects.length > 0
            ? projects.reduce((sum, p) => sum + (p.latest_score || 0), 0) /
            projects.filter((p) => p.latest_score !== null).length
            : 0;
    const readyCount = projects.filter(
        (p) => p.latest_score !== null && p.latest_score >= 85
    ).length;
    const needsWorkCount = projects.filter(
        (p) => p.latest_score !== null && p.latest_score >= 60 && p.latest_score < 85
    ).length;
    const notReadyCount = projects.filter(
        (p) => p.latest_score !== null && p.latest_score < 60
    ).length;

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white">Projects</h1>
                    <p className="text-gray-400 mt-1">
                        Manage and monitor your vibe-coded applications
                    </p>
                </div>
                <button
                    onClick={() => setShowNewProjectModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
                >
                    <Plus className="h-5 w-5" />
                    New Project
                </button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatsCard
                    title="Total Projects"
                    value={totalProjects}
                    icon={FolderOpen}
                    color="purple"
                />
                <StatsCard
                    title="Ready"
                    value={readyCount}
                    icon={CheckCircle}
                    color="green"
                />
                <StatsCard
                    title="Needs Work"
                    value={needsWorkCount}
                    icon={AlertTriangle}
                    color="yellow"
                />
                <StatsCard
                    title="Not Ready"
                    value={notReadyCount}
                    icon={XCircle}
                    color="red"
                />
            </div>

            {/* Project List */}
            {isLoading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
                </div>
            ) : error ? (
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6 text-center">
                    <p className="text-red-400">Failed to load projects</p>
                </div>
            ) : projects.length === 0 ? (
                <EmptyState onCreateProject={() => setShowNewProjectModal(true)} />
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {projects.map((project) => (
                        <ProjectCard key={project.id} project={project} />
                    ))}
                </div>
            )}

            {/* New Project Modal */}
            {showNewProjectModal && (
                <NewProjectModal onClose={() => setShowNewProjectModal(false)} />
            )}
        </div>
    );
}

function StatsCard({
    title,
    value,
    icon: Icon,
    color,
}: {
    title: string;
    value: number;
    icon: any;
    color: 'purple' | 'green' | 'yellow' | 'red';
}) {
    const colors = {
        purple: 'bg-purple-500/20 text-purple-400',
        green: 'bg-green-500/20 text-green-400',
        yellow: 'bg-yellow-500/20 text-yellow-400',
        red: 'bg-red-500/20 text-red-400',
    };

    return (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg', colors[color])}>
                    <Icon className="h-5 w-5" />
                </div>
                <div>
                    <p className="text-gray-400 text-sm">{title}</p>
                    <p className="text-2xl font-bold text-white">{value}</p>
                </div>
            </div>
        </div>
    );
}

function ProjectCard({ project }: { project: Project }) {
    const scoreColor = getScoreColor(project.latest_score);
    const scoreLabel = getScoreLabel(project.latest_score);

    return (
        <Link href={`/projects/${project.id}`}>
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-purple-500/50 transition-all cursor-pointer group">
                <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                        <span className="text-2xl">{getStackIcon(project.stack)}</span>
                        <div>
                            <h3 className="font-semibold text-white group-hover:text-purple-400 transition-colors">
                                {project.name}
                            </h3>
                            <p className="text-sm text-gray-500">
                                {project.source_type === 'github' ? (
                                    <span className="flex items-center gap-1">
                                        <Github className="h-3 w-3" />
                                        {project.repo_full_name}
                                    </span>
                                ) : (
                                    <span className="flex items-center gap-1">
                                        <Upload className="h-3 w-3" />
                                        ZIP Upload
                                    </span>
                                )}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Score */}
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-sm text-gray-400">Readiness Score</p>
                        <div className="flex items-baseline gap-2">
                            <span className={cn('text-3xl font-bold', scoreColor)}>
                                {project.latest_score !== null
                                    ? Math.round(project.latest_score)
                                    : '—'}
                            </span>
                            <span className={cn('text-sm', scoreColor)}>{scoreLabel}</span>
                        </div>
                    </div>
                    <div className="text-right">
                        <p className="text-xs text-gray-500">Last updated</p>
                        <p className="text-sm text-gray-400">
                            {formatDate(project.updated_at)}
                        </p>
                    </div>
                </div>
            </div>
        </Link>
    );
}

function EmptyState({ onCreateProject }: { onCreateProject: () => void }) {
    return (
        <div className="bg-slate-800/50 rounded-2xl border border-dashed border-slate-600 p-12 text-center">
            <div className="mx-auto w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mb-4">
                <FolderOpen className="h-8 w-8 text-purple-400" />
            </div>
            <h3 className="text-xl font-semibold text-white mb-2">No projects yet</h3>
            <p className="text-gray-400 mb-6 max-w-sm mx-auto">
                Connect a GitHub repository or upload a ZIP file to analyze your
                vibe-coded application.
            </p>
            <button
                onClick={onCreateProject}
                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
                <Plus className="h-5 w-5" />
                Create Your First Project
            </button>
        </div>
    );
}

function NewProjectModal({ onClose }: { onClose: () => void }) {
    const router = useRouter();
    const [loading, setLoading] = useState<'github' | 'zip' | null>(null);

    const handleGitHubConnect = async () => {
        setLoading('github');
        try {
            // First check if user already has GitHub connected
            const meResponse = await apiClient.get('/auth/me');
            if (meResponse.data.github_connected) {
                // Already connected, go directly to repo selection
                router.push('/projects/new/github');
                return;
            }

            // Not connected, start OAuth flow
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/github/auth`, {
                headers: {
                    'Authorization': `Bearer ${await getIdToken()}`,
                },
            });
            const data = await response.json();

            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else if (data.detail) {
                alert(data.detail);
                setLoading(null);
            }
        } catch (error) {
            console.error('GitHub auth error:', error);
            alert('GitHub integration is not configured. Please set up GitHub OAuth in your environment.');
            setLoading(null);
        }
    };

    const handleZipUpload = () => {
        setLoading('zip');
        router.push('/projects/new?type=zip');
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div
                className="absolute inset-0 bg-black/50 backdrop-blur-sm"
                onClick={onClose}
            />
            <div className="relative bg-slate-800 rounded-2xl p-8 w-full max-w-lg border border-slate-700 shadow-2xl">
                <h2 className="text-2xl font-bold text-white mb-6">New Project</h2>

                <div className="space-y-4">
                    <button
                        onClick={handleGitHubConnect}
                        disabled={loading !== null}
                        className="w-full flex items-center gap-4 p-4 bg-slate-700/50 hover:bg-slate-700 rounded-xl border border-slate-600 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <div className="p-3 bg-purple-500/20 rounded-lg group-hover:bg-purple-500/30">
                            {loading === 'github' ? (
                                <div className="h-6 w-6 animate-spin rounded-full border-2 border-purple-400 border-t-transparent" />
                            ) : (
                                <Github className="h-6 w-6 text-purple-400" />
                            )}
                        </div>
                        <div className="text-left">
                            <h3 className="font-semibold text-white">Connect GitHub</h3>
                            <p className="text-sm text-gray-400">
                                Import a repository from your GitHub account
                            </p>
                        </div>
                    </button>

                    <button
                        onClick={handleZipUpload}
                        disabled={loading !== null}
                        className="w-full flex items-center gap-4 p-4 bg-slate-700/50 hover:bg-slate-700 rounded-xl border border-slate-600 transition-colors group disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        <div className="p-3 bg-blue-500/20 rounded-lg group-hover:bg-blue-500/30">
                            {loading === 'zip' ? (
                                <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-400 border-t-transparent" />
                            ) : (
                                <Upload className="h-6 w-6 text-blue-400" />
                            )}
                        </div>
                        <div className="text-left">
                            <h3 className="font-semibold text-white">Upload ZIP</h3>
                            <p className="text-sm text-gray-400">
                                Upload your source code as a ZIP file
                            </p>
                        </div>
                    </button>
                </div>

                <button
                    onClick={onClose}
                    className="mt-6 w-full py-2 text-gray-400 hover:text-white transition-colors"
                >
                    Cancel
                </button>
            </div>
        </div>
    );
}
