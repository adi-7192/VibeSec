'use client';

/**
 * VibeSec Frontend - Fix Preview Modal
 */

import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import apiClient from '@/lib/api';
import {
    X,
    Sparkles,
    Copy,
    Check,
    GitPullRequest,
    Loader2,
    Code,
    TestTube,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface FixPreviewProps {
    findingId: number;
    title: string;
    onClose: () => void;
}

export default function FixPreview({ findingId, title, onClose }: FixPreviewProps) {
    const [activeTab, setActiveTab] = useState<'fix' | 'test'>('fix');
    const [copied, setCopied] = useState(false);

    const fixMutation = useMutation({
        mutationFn: () => apiClient.post(`/findings/${findingId}/fix`).then(r => r.data),
    });

    const testMutation = useMutation({
        mutationFn: () => apiClient.post(`/findings/${findingId}/test`).then(r => r.data),
    });

    const handleGenerate = () => {
        if (activeTab === 'fix') {
            fixMutation.mutate();
        } else {
            testMutation.mutate();
        }
    };

    const handleCopy = (text: string) => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const isLoading = fixMutation.isPending || testMutation.isPending;
    const fixData = fixMutation.data;
    const testData = testMutation.data;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            <div className="relative bg-slate-800 rounded-2xl w-full max-w-3xl border border-slate-700 shadow-2xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="p-6 border-b border-slate-700">
                    <div className="flex items-start justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white">AI-Generated Solution</h2>
                            <p className="text-sm text-gray-400 mt-1">{title}</p>
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-white">
                            <X className="h-6 w-6" />
                        </button>
                    </div>

                    {/* Tabs */}
                    <div className="flex gap-2 mt-4">
                        <button
                            onClick={() => setActiveTab('fix')}
                            className={cn(
                                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                                activeTab === 'fix'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-slate-700 text-gray-300 hover:text-white'
                            )}
                        >
                            <Code className="h-4 w-4" />
                            Code Fix
                        </button>
                        <button
                            onClick={() => setActiveTab('test')}
                            className={cn(
                                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                                activeTab === 'test'
                                    ? 'bg-purple-600 text-white'
                                    : 'bg-slate-700 text-gray-300 hover:text-white'
                            )}
                        >
                            <TestTube className="h-4 w-4" />
                            Test Case
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6">
                    {!fixData && !testData && !isLoading && (
                        <div className="text-center py-12">
                            <div className="w-16 h-16 bg-purple-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Sparkles className="h-8 w-8 text-purple-400" />
                            </div>
                            <h3 className="text-lg font-medium text-white mb-2">
                                Generate {activeTab === 'fix' ? 'Code Fix' : 'Test Case'}
                            </h3>
                            <p className="text-gray-400 mb-6 max-w-sm mx-auto">
                                {activeTab === 'fix'
                                    ? 'Our AI will analyze the vulnerability and generate a secure code fix.'
                                    : 'Generate a test case to verify the vulnerability is properly addressed.'}
                            </p>
                            <button
                                onClick={handleGenerate}
                                disabled={isLoading}
                                className="inline-flex items-center gap-2 px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                            >
                                {isLoading ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : (
                                    <Sparkles className="h-5 w-5" />
                                )}
                                Generate with AI
                            </button>
                        </div>
                    )}

                    {isLoading && (
                        <div className="text-center py-12">
                            <Loader2 className="h-8 w-8 animate-spin text-purple-400 mx-auto mb-4" />
                            <p className="text-gray-400">Generating {activeTab === 'fix' ? 'fix' : 'test'}...</p>
                        </div>
                    )}

                    {activeTab === 'fix' && fixData && (
                        <div className="space-y-6">
                            {/* Explanation */}
                            <div>
                                <h4 className="text-sm font-medium text-gray-300 mb-2">Explanation</h4>
                                <p className="text-gray-400">{fixData.explanation}</p>
                            </div>

                            {/* Fixed Code */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-sm font-medium text-gray-300">Fixed Code</h4>
                                    <button
                                        onClick={() => handleCopy(fixData.fixed_code)}
                                        className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
                                    >
                                        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                        {copied ? 'Copied!' : 'Copy'}
                                    </button>
                                </div>
                                <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm text-green-400">
                                    <code>{fixData.fixed_code}</code>
                                </pre>
                            </div>

                            {/* Diff */}
                            {fixData.diff && (
                                <div>
                                    <h4 className="text-sm font-medium text-gray-300 mb-2">Changes</h4>
                                    <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm">
                                        <code>
                                            {fixData.diff.split('\n').map((line: string, i: number) => (
                                                <div
                                                    key={i}
                                                    className={cn(
                                                        line.startsWith('+') && 'text-green-400',
                                                        line.startsWith('-') && 'text-red-400'
                                                    )}
                                                >
                                                    {line}
                                                </div>
                                            ))}
                                        </code>
                                    </pre>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'test' && testData && (
                        <div className="space-y-6">
                            {/* Explanation */}
                            <div>
                                <h4 className="text-sm font-medium text-gray-300 mb-2">What This Tests</h4>
                                <p className="text-gray-400">{testData.explanation}</p>
                            </div>

                            {/* Test Code */}
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <h4 className="text-sm font-medium text-gray-300">
                                        Test Code ({testData.test_framework})
                                    </h4>
                                    <button
                                        onClick={() => handleCopy(testData.test_code)}
                                        className="flex items-center gap-1 text-xs text-purple-400 hover:text-purple-300"
                                    >
                                        {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                        {copied ? 'Copied!' : 'Copy'}
                                    </button>
                                </div>
                                <pre className="bg-slate-900 rounded-lg p-4 overflow-x-auto text-sm text-blue-400">
                                    <code>{testData.test_code}</code>
                                </pre>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                {(fixData || testData) && (
                    <div className="p-6 border-t border-slate-700 flex justify-between">
                        <button
                            onClick={handleGenerate}
                            disabled={isLoading}
                            className="flex items-center gap-2 px-4 py-2 text-gray-400 hover:text-white transition-colors"
                        >
                            <Sparkles className="h-4 w-4" />
                            Regenerate
                        </button>
                        <div className="flex gap-3">
                            <button
                                onClick={() => handleCopy(activeTab === 'fix' ? fixData?.fixed_code : testData?.test_code)}
                                className="flex items-center gap-2 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                            >
                                <Copy className="h-4 w-4" />
                                Copy Code
                            </button>
                            {activeTab === 'fix' && (
                                <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                                    <GitPullRequest className="h-4 w-4" />
                                    Create PR
                                </button>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
