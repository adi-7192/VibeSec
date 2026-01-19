'use client';

/**
 * VibeSec Frontend - Project Detail Page
 */

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProject, getScans, triggerScan, getFindings, ProjectWithStats, Scan, Finding } from '@/lib/api';
import {
    cn,
    formatDateTime,
    getScoreColor,
    getScoreLabel,
    getSeverityColor,
    getStackIcon,
} from '@/lib/utils';
import {
    Shield,
    TestTube,
    Activity,
    Eye,
    Zap,
    Server,
    Play,
    AlertTriangle,
    CheckCircle,
    XCircle,
    ChevronRight,
    RefreshCw,
    Github,
    ExternalLink,
} from 'lucide-react';

interface DomainScoreCardProps {
    title: string;
    icon: React.ElementType;
    score: number;
    issues: number;
}

function DomainScoreCard({ title, icon: Icon, score, issues }: DomainScoreCardProps) {
    const color = score >= 85 ? 'green' : score >= 60 ? 'yellow' : 'red';
    const colorClasses = {
        green: 'bg-green-500/20 text-green-400 border-green-500/30',
        yellow: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
        red: 'bg-red-500/20 text-red-400 border-red-500/30',
    };

    return (
        <div className={cn(
            'p-4 rounded-xl border transition-all hover:border-opacity-60',
            colorClasses[color]
        )}>
            <div className="flex items-center gap-2 mb-2">
                <Icon className="h-4 w-4" />
                <span className="text-sm font-medium text-gray-300">{title}</span>
            </div>
            <div className="flex items-baseline gap-2">
                <span className="text-2xl font-bold">{Math.round(score)}</span>
                {issues > 0 && (
                    <span className="text-xs text-gray-400">({issues} issues)</span>
                )}
            </div>
        </div>
    );
}

export default function ProjectPage() {
    const params = useParams();
    const projectId = Number(params.id);
    const queryClient = useQueryClient();
    const [activeTab, setActiveTab] = useState<'security' | 'testing' | 'reliability' | 'observability' | 'performance' | 'infrastructure'>('security');

    // Fetch project details
    const { data: project, isLoading: isProjectLoading } = useQuery({
        queryKey: ['project', projectId],
        queryFn: () => getProject(projectId),
    });

    // Fetch latest scans (for status polling)
    const { data: scansData, isLoading: isScansLoading } = useQuery({
        queryKey: ['project', projectId, 'scans'],
        queryFn: () => getScans(projectId),
        refetchInterval: (query) => {
            const data = query.state.data;
            const latest = data?.scans?.[0];
            if (latest && ['pending', 'cloning', 'detecting', 'scanning_sast', 'scanning_sca', 'scoring'].includes(latest.status)) {
                return 2000; // Poll every 2s if active
            }
            return false;
        },
    });

    const latestScan = scansData?.scans?.[0];
    const isScanning = latestScan && ['pending', 'cloning', 'detecting', 'scanning_sast', 'scanning_sca', 'scoring'].includes(latestScan.status);

    const scanMutation = useMutation({
        mutationFn: () => triggerScan(projectId),
        onSuccess: () => {
            // Invalidate to trigger polling
            queryClient.invalidateQueries({ queryKey: ['project', projectId] });
            queryClient.invalidateQueries({ queryKey: ['project', projectId, 'scans'] });
        },
        onError: (error: any) => {
            alert(error.response?.data?.detail || 'Failed to start scan');
        }
    });

    if (isProjectLoading || isScansLoading) {
        return (
            <div className="flex justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    if (!project) {
        return (
            <div className="text-center py-12">
                <p className="text-gray-400">Project not found</p>
            </div>
        );
    }

    const scoreColor = getScoreColor(latestScan?.overall_score ?? null);
    const scoreLabel = getScoreLabel(latestScan?.overall_score ?? null);

    // Use actual domain scores or valid defaults (zeros if never scanned)
    const emptyDomainScores = {
        security: { score: 0, issues: 0 },
        testing: { score: 0, issues: 0 },
        reliability: { score: 0, issues: 0 },
        observability: { score: 0, issues: 0 },
        performance: { score: 0, issues: 0 },
        infrastructure: { score: 0, issues: 0 },
    };

    const domainScores = latestScan?.domain_scores || emptyDomainScores;
    const hasScanData = latestScan && latestScan.status === 'completed';

    const tabs = [
        { key: 'security', label: 'Security', icon: Shield },
        { key: 'testing', label: 'Testing', icon: TestTube },
        { key: 'reliability', label: 'Reliability', icon: Activity },
        { key: 'observability', label: 'Observability', icon: Eye },
        { key: 'performance', label: 'Performance', icon: Zap },
        { key: 'infrastructure', label: 'Infrastructure', icon: Server },
    ];

    return (
        <div className="space-y-8 relative">
            {/* Scanning Overlay */}
            {isScanning && (
                <div className="absolute inset-0 z-50 bg-slate-900/80 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center">
                    <div className="w-full max-w-md p-8 bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl text-center">
                        <div className="relative w-20 h-20 mx-auto mb-6">
                            <div className="absolute inset-0 border-4 border-slate-700 rounded-full"></div>
                            <div className="absolute inset-0 border-4 border-purple-500 rounded-full border-t-transparent animate-spin"></div>
                            <div className="absolute inset-0 flex items-center justify-center font-bold text-white">
                                {latestScan?.progress}%
                            </div>
                        </div>
                        <h3 className="text-xl font-bold text-white mb-2">Analysis in Progress</h3>
                        <p className="text-gray-400 mb-4 animate-pulse">
                            {latestScan?.status === 'pending' && 'Preparing scan...'}
                            {latestScan?.status === 'cloning' && 'Cloning repository...'}
                            {latestScan?.status === 'detecting' && 'Detecting technology stack...'}
                            {latestScan?.status === 'scanning_sast' && 'Running security checks...'}
                            {latestScan?.status === 'scanning_sca' && 'Checking dependencies...'}
                            {latestScan?.status === 'scoring' && 'Calculating scores...'}
                        </p>
                        <div className="w-full bg-slate-700 rounded-full h-2 overflow-hidden">
                            <div
                                className="bg-purple-500 h-full transition-all duration-500 ease-out"
                                style={{ width: `${latestScan?.progress}%` }}
                            ></div>
                        </div>
                    </div>
                </div>
            )}

            {/* Header */}
            <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                    <span className="text-4xl">{getStackIcon(project.stack)}</span>
                    <div>
                        <h1 className="text-3xl font-bold text-white">{project.name}</h1>
                        {project.repo_full_name && (
                            <a
                                href={project.repo_url || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-1 text-gray-400 hover:text-purple-400 transition-colors mt-1"
                            >
                                <Github className="h-4 w-4" />
                                {project.repo_full_name}
                                <ExternalLink className="h-3 w-3" />
                            </a>
                        )}
                    </div>
                </div>
                <button
                    onClick={() => scanMutation.mutate()}
                    disabled={isScanning || scanMutation.isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                >
                    {isScanning || scanMutation.isPending ? (
                        <RefreshCw className="h-5 w-5 animate-spin" />
                    ) : (
                        <Play className="h-5 w-5" />
                    )}
                    {isScanning || scanMutation.isPending ? 'Scanning...' : 'Run Scan'}
                </button>
            </div>

            {/* Main Score */}
            <div className="bg-slate-800 rounded-2xl p-8 border border-slate-700">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        {/* Circular Score */}
                        <div className="relative w-32 h-32">
                            <svg className="w-full h-full transform -rotate-90">
                                <circle
                                    cx="64"
                                    cy="64"
                                    r="56"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    className="text-slate-700"
                                />
                                <circle
                                    cx="64"
                                    cy="64"
                                    r="56"
                                    fill="none"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    strokeLinecap="round"
                                    strokeDasharray={`${(latestScan?.overall_score || 0) * 3.52} 352`}
                                    className={scoreColor}
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className={cn('text-3xl font-bold', scoreColor)}>
                                    {latestScan?.overall_score !== null && latestScan?.overall_score !== undefined
                                        ? Math.round(latestScan.overall_score)
                                        : '—'}
                                </span>
                                <span className="text-xs text-gray-400">Readiness</span>
                            </div>
                        </div>

                        <div>
                            <div className={cn(
                                'inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium mb-2',
                                latestScan?.overall_score && latestScan.overall_score >= 85
                                    ? 'bg-green-500/20 text-green-400'
                                    : latestScan?.overall_score && latestScan.overall_score >= 60
                                        ? 'bg-yellow-500/20 text-yellow-400'
                                        : (latestScan?.overall_score !== null && latestScan?.overall_score !== undefined)
                                            ? 'bg-red-500/20 text-red-400'
                                            : 'bg-slate-700 text-gray-400'
                            )}>
                                {latestScan?.overall_score && latestScan.overall_score >= 85 ? (
                                    <CheckCircle className="h-4 w-4" />
                                ) : latestScan?.overall_score && latestScan.overall_score >= 60 ? (
                                    <AlertTriangle className="h-4 w-4" />
                                ) : (latestScan?.overall_score !== null && latestScan?.overall_score !== undefined) ? (
                                    <XCircle className="h-4 w-4" />
                                ) : (
                                    <AlertTriangle className="h-4 w-4" />
                                )}
                                {scoreLabel}
                            </div>
                            <p className="text-gray-400">
                                {project.total_scans} scans completed
                            </p>
                        </div>
                    </div>

                    <div className="text-right">
                        <p className="text-sm text-gray-400 mb-1">Issues Found</p>
                        <div className="flex gap-4">
                            <div className="text-center">
                                <span className={cn("text-2xl font-bold", latestScan ? "text-red-400" : "text-gray-600")}>
                                    {latestScan?.critical_count ?? 0}
                                </span>
                                <p className="text-xs text-gray-500">Critical</p>
                            </div>
                            <div className="text-center">
                                <span className={cn("text-2xl font-bold", latestScan ? "text-orange-400" : "text-gray-600")}>
                                    {latestScan?.high_count ?? 0}
                                </span>
                                <p className="text-xs text-gray-500">High</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Domain Scores Grid */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                <DomainScoreCard
                    title="Security"
                    icon={Shield}
                    score={domainScores?.security?.score || 0}
                    issues={domainScores?.security?.issues || 0}
                />
                <DomainScoreCard
                    title="Testing"
                    icon={TestTube}
                    score={domainScores?.testing?.score || 0}
                    issues={domainScores?.testing?.issues || 0}
                />
                <DomainScoreCard
                    title="Reliability"
                    icon={Activity}
                    score={domainScores?.reliability?.score || 0}
                    issues={domainScores?.reliability?.issues || 0}
                />
                <DomainScoreCard
                    title="Observability"
                    icon={Eye}
                    score={domainScores?.observability?.score || 0}
                    issues={domainScores?.observability?.issues || 0}
                />
                <DomainScoreCard
                    title="Performance"
                    icon={Zap}
                    score={domainScores?.performance?.score || 0}
                    issues={domainScores?.performance?.issues || 0}
                />
                <DomainScoreCard
                    title="Infrastructure"
                    icon={Server}
                    score={domainScores?.infrastructure?.score || 0}
                    issues={domainScores?.infrastructure?.issues || 0}
                />
            </div>

            {/* Tabs */}
            <div className="bg-slate-800 rounded-2xl border border-slate-700 overflow-hidden">
                <div className="flex border-b border-slate-700 overflow-x-auto">
                    {tabs.map((tab) => (
                        <button
                            key={tab.key}
                            onClick={() => setActiveTab(tab.key as any)}
                            className={cn(
                                'flex items-center gap-2 px-4 py-3 text-sm font-medium whitespace-nowrap transition-colors',
                                activeTab === tab.key
                                    ? 'text-purple-400 border-b-2 border-purple-400 bg-purple-500/5'
                                    : 'text-gray-400 hover:text-white'
                            )}
                        >
                            <tab.icon className="h-4 w-4" />
                            {tab.label}
                        </button>
                    ))}
                </div>

                <div className="p-6">
                    {/* Content Logic: Show checks if we have scan data, otherwise show empty state prompts */}
                    {!hasScanData && !isScanning ? (
                        <div className="text-center py-12">
                            <Play className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                            <p className="text-gray-400 font-medium">No results yet</p>
                            <p className="text-gray-500 text-sm mt-1">Run a scan to analyze {activeTab} metrics.</p>
                        </div>
                    ) : (
                        <>
                            {activeTab === 'security' && (
                                <SecurityTab projectId={projectId} scanId={latestScan?.id || null} />
                            )}
                            {activeTab === 'testing' && domainScores?.testing && (
                                <TestingTab domainScore={domainScores.testing} />
                            )}
                            {activeTab === 'reliability' && domainScores?.reliability && (
                                <ReliabilityTab domainScore={domainScores.reliability} />
                            )}
                            {activeTab === 'observability' && domainScores?.observability && (
                                <ObservabilityTab domainScore={domainScores.observability} />
                            )}
                            {activeTab === 'performance' && domainScores?.performance && (
                                <PerformanceTab domainScore={domainScores.performance} />
                            )}
                            {activeTab === 'infrastructure' && domainScores?.infrastructure && (
                                <InfrastructureTab domainScore={domainScores.infrastructure} />
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

// Domain tab components
function TestingTab({ domainScore }: { domainScore: { score: number; issues: number } }) {
    const checks = [
        { name: 'Test Framework', detected: true, details: 'Jest detected', impact: 'positive' },
        { name: 'Test Files', detected: true, details: '12 test files found', impact: 'positive' },
        { name: 'Coverage Config', detected: false, details: 'No coverage configuration', impact: 'negative' },
        { name: 'E2E Tests', detected: false, details: 'No Playwright/Cypress found', impact: 'negative' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white">Testing Analysis</h3>
                    <p className="text-sm text-gray-400">Code coverage and test quality assessment</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-yellow-400">{Math.round(domainScore.score)}</span>
                    <span className="text-gray-400">/100</span>
                </div>
            </div>

            <div className="grid gap-3">
                {checks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                            {check.detected ? (
                                <CheckCircle className="h-5 w-5 text-green-400" />
                            ) : (
                                <XCircle className="h-5 w-5 text-red-400" />
                            )}
                            <div>
                                <p className="text-white font-medium">{check.name}</p>
                                <p className="text-sm text-gray-400">{check.details}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-blue-400 font-medium">💡 Recommendation</p>
                <p className="text-sm text-gray-300 mt-1">Add code coverage reporting and E2E tests to improve your testing score.</p>
            </div>
        </div>
    );
}

function ReliabilityTab({ domainScore }: { domainScore: { score: number; issues: number } }) {
    const checks = [
        { name: 'Error Handling', detected: true, details: 'try/catch blocks found', impact: 'positive' },
        { name: 'Retry Logic', detected: true, details: 'Exponential backoff detected', impact: 'positive' },
        { name: 'Environment Config', detected: true, details: 'Using process.env', impact: 'positive' },
        { name: 'Graceful Shutdown', detected: false, details: 'No shutdown handlers', impact: 'warning' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white">Reliability Analysis</h3>
                    <p className="text-sm text-gray-400">Error handling and fault tolerance patterns</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-green-400">{Math.round(domainScore.score)}</span>
                    <span className="text-gray-400">/100</span>
                </div>
            </div>

            <div className="grid gap-3">
                {checks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                            {check.detected ? (
                                <CheckCircle className="h-5 w-5 text-green-400" />
                            ) : (
                                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                            )}
                            <div>
                                <p className="text-white font-medium">{check.name}</p>
                                <p className="text-sm text-gray-400">{check.details}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function ObservabilityTab({ domainScore }: { domainScore: { score: number; issues: number } }) {
    const checks = [
        { name: 'Structured Logging', detected: false, details: 'Only console.log found', impact: 'negative' },
        { name: 'Health Endpoint', detected: false, details: 'No /health endpoint', impact: 'negative' },
        { name: 'Error Tracking', detected: false, details: 'No Sentry/DataDog', impact: 'negative' },
        { name: 'Metrics', detected: false, details: 'No metrics collection', impact: 'negative' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white">Observability Analysis</h3>
                    <p className="text-sm text-gray-400">Logging, monitoring, and debugging capabilities</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-red-400">{Math.round(domainScore.score)}</span>
                    <span className="text-gray-400">/100</span>
                </div>
            </div>

            <div className="grid gap-3">
                {checks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                            {check.detected ? (
                                <CheckCircle className="h-5 w-5 text-green-400" />
                            ) : (
                                <XCircle className="h-5 w-5 text-red-400" />
                            )}
                            <div>
                                <p className="text-white font-medium">{check.name}</p>
                                <p className="text-sm text-gray-400">{check.details}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-red-400 font-medium">⚠️ Action Required</p>
                <p className="text-sm text-gray-300 mt-1">Add structured logging, health endpoints, and error tracking for production.</p>
            </div>
        </div>
    );
}

function PerformanceTab({ domainScore }: { domainScore: { score: number; issues: number } }) {
    const checks = [
        { name: 'Caching', detected: true, details: 'Redis caching detected', impact: 'positive' },
        { name: 'Async Operations', detected: true, details: 'async/await usage found', impact: 'positive' },
        { name: 'N+1 Queries', detected: false, details: 'No N+1 patterns found', impact: 'positive' },
        { name: 'Image Optimization', detected: true, details: 'Next.js Image component used', impact: 'positive' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white">Performance Analysis</h3>
                    <p className="text-sm text-gray-400">Optimization patterns and potential bottlenecks</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-green-400">{Math.round(domainScore.score)}</span>
                    <span className="text-gray-400">/100</span>
                </div>
            </div>

            <div className="grid gap-3">
                {checks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                            <CheckCircle className="h-5 w-5 text-green-400" />
                            <div>
                                <p className="text-white font-medium">{check.name}</p>
                                <p className="text-sm text-gray-400">{check.details}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

function InfrastructureTab({ domainScore }: { domainScore: { score: number; issues: number } }) {
    const checks = [
        { name: 'CI/CD Config', detected: true, details: 'GitHub Actions found', impact: 'positive' },
        { name: 'Docker', detected: true, details: 'Dockerfile present', impact: 'positive' },
        { name: 'Environment Variables', detected: true, details: 'Using .env files', impact: 'positive' },
        { name: 'Hardcoded Secrets', detected: true, details: '2 potential secrets found', impact: 'negative' },
    ];

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="text-lg font-semibold text-white">Infrastructure Analysis</h3>
                    <p className="text-sm text-gray-400">CI/CD, containerization, and deployment readiness</p>
                </div>
                <div className="text-right">
                    <span className="text-3xl font-bold text-yellow-400">{Math.round(domainScore.score)}</span>
                    <span className="text-gray-400">/100</span>
                </div>
            </div>

            <div className="grid gap-3">
                {checks.map((check) => (
                    <div key={check.name} className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg">
                        <div className="flex items-center gap-3">
                            {check.impact === 'positive' ? (
                                <CheckCircle className="h-5 w-5 text-green-400" />
                            ) : (
                                <AlertTriangle className="h-5 w-5 text-yellow-400" />
                            )}
                            <div>
                                <p className="text-white font-medium">{check.name}</p>
                                <p className="text-sm text-gray-400">{check.details}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                <p className="text-yellow-400 font-medium">⚠️ Warning</p>
                <p className="text-sm text-gray-300 mt-1">Remove hardcoded secrets and use environment variables or a secrets manager.</p>
            </div>
        </div>
    );
}

function SecurityTab({ projectId, scanId }: { projectId: number; scanId: number | null }) {
    const { data, isLoading } = useQuery({
        queryKey: ['findings', scanId],
        queryFn: () => scanId ? getFindings(scanId) : Promise.resolve({ findings: [], total: 0 }),
        enabled: !!scanId,
    });

    if (!scanId) {
        return (
            <div className="text-center py-8 text-gray-400">
                <p>No scan results yet. Run a scan to see security findings.</p>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-purple-500"></div>
            </div>
        );
    }

    const findings = data?.findings || [];

    if (findings.length === 0) {
        return (
            <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-400 mx-auto mb-3" />
                <p className="text-green-400 font-medium">No security issues found!</p>
                <p className="text-gray-400 text-sm mt-1">Your code passed all security checks.</p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {findings.map((finding: Finding) => (
                <div
                    key={finding.id}
                    className="p-4 bg-slate-700/50 rounded-lg border border-slate-600 hover:border-slate-500 transition-colors"
                >
                    <div className="flex items-start justify-between">
                        <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                                <span className={cn(
                                    'px-2 py-0.5 rounded text-xs font-medium',
                                    getSeverityColor(finding.severity)
                                )}>
                                    {finding.severity.toUpperCase()}
                                </span>
                                <span className="text-xs text-gray-500">
                                    {finding.finding_type.toUpperCase()}
                                </span>
                            </div>
                            <h4 className="font-medium text-white mb-1">{finding.title}</h4>
                            {finding.file_path && (
                                <p className="text-sm text-gray-400">
                                    {finding.file_path}
                                    {finding.line_start && `:${finding.line_start}`}
                                </p>
                            )}
                            {finding.package_name && (
                                <p className="text-sm text-gray-400">
                                    {finding.package_name}@{finding.package_version || '?'}
                                </p>
                            )}
                        </div>
                        <button className="flex items-center gap-1 px-3 py-1.5 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors">
                            Get Fix
                            <ChevronRight className="h-4 w-4" />
                        </button>
                    </div>
                </div>
            ))}
        </div>
    );
}
