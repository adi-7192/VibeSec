'use client';

/**
 * VibeSec Frontend - Settings Page
 */

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import {
    Settings,
    Key,
    Github,
    User,
    Check,
    X,
    Loader2,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function SettingsPage() {
    const { user } = useAuth();
    const [llmProvider, setLlmProvider] = useState<'gemini' | 'openai'>(
        user?.llm_provider || 'gemini'
    );
    const [apiKey, setApiKey] = useState('');
    const [saving, setSaving] = useState(false);
    const [testingConnection, setTestingConnection] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<
        'idle' | 'success' | 'error'
    >('idle');

    const handleSaveApiKey = async () => {
        setSaving(true);
        // TODO: Implement API call
        await new Promise((resolve) => setTimeout(resolve, 1000));
        setSaving(false);
    };

    const handleTestConnection = async () => {
        setTestingConnection(true);
        setConnectionStatus('idle');
        // TODO: Implement API call
        await new Promise((resolve) => setTimeout(resolve, 1500));
        setConnectionStatus('success');
        setTestingConnection(false);
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-white">Settings</h1>
                <p className="text-gray-400 mt-1">
                    Configure your VibeSec account and integrations
                </p>
            </div>

            {/* Profile Section */}
            <section className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <User className="h-5 w-5 text-purple-400" />
                        Profile
                    </h2>
                </div>
                <div className="p-6">
                    <div className="flex items-center gap-4">
                        <div className="h-16 w-16 bg-purple-600 rounded-full flex items-center justify-center">
                            {user?.picture ? (
                                <img
                                    src={user.picture}
                                    alt=""
                                    className="h-16 w-16 rounded-full"
                                />
                            ) : (
                                <User className="h-8 w-8 text-white" />
                            )}
                        </div>
                        <div>
                            <p className="text-xl font-semibold text-white">
                                {user?.name || 'User'}
                            </p>
                            <p className="text-gray-400">{user?.email}</p>
                        </div>
                    </div>
                </div>
            </section>

            {/* LLM Configuration */}
            <section className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Key className="h-5 w-5 text-purple-400" />
                        AI & LLM Configuration
                    </h2>
                    <p className="text-sm text-gray-400 mt-1">
                        Configure your LLM provider for generating fixes and tests
                    </p>
                </div>
                <div className="p-6 space-y-6">
                    {/* Provider Selection */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-3">
                            Provider
                        </label>
                        <div className="flex gap-4">
                            <button
                                onClick={() => setLlmProvider('gemini')}
                                className={cn(
                                    'flex-1 p-4 rounded-lg border-2 transition-all',
                                    llmProvider === 'gemini'
                                        ? 'border-purple-500 bg-purple-500/10'
                                        : 'border-slate-600 hover:border-slate-500'
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="text-2xl">✨</div>
                                    <div className="text-left">
                                        <p className="font-semibold text-white">Gemini</p>
                                        <p className="text-sm text-gray-400">Google AI</p>
                                    </div>
                                </div>
                            </button>
                            <button
                                onClick={() => setLlmProvider('openai')}
                                className={cn(
                                    'flex-1 p-4 rounded-lg border-2 transition-all',
                                    llmProvider === 'openai'
                                        ? 'border-purple-500 bg-purple-500/10'
                                        : 'border-slate-600 hover:border-slate-500'
                                )}
                            >
                                <div className="flex items-center gap-3">
                                    <div className="text-2xl">🤖</div>
                                    <div className="text-left">
                                        <p className="font-semibold text-white">OpenAI</p>
                                        <p className="text-sm text-gray-400">GPT-4</p>
                                    </div>
                                </div>
                            </button>
                        </div>
                    </div>

                    {/* API Key */}
                    <div>
                        <label className="block text-sm font-medium text-gray-300 mb-2">
                            API Key
                        </label>
                        <div className="flex gap-3">
                            <input
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder={
                                    llmProvider === 'gemini'
                                        ? 'Enter your Gemini API key'
                                        : 'Enter your OpenAI API key'
                                }
                                className="flex-1 px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                            <button
                                onClick={handleTestConnection}
                                disabled={!apiKey || testingConnection}
                                className="px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-gray-300 hover:text-white hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                {testingConnection ? (
                                    <Loader2 className="h-5 w-5 animate-spin" />
                                ) : connectionStatus === 'success' ? (
                                    <Check className="h-5 w-5 text-green-400" />
                                ) : connectionStatus === 'error' ? (
                                    <X className="h-5 w-5 text-red-400" />
                                ) : (
                                    'Test'
                                )}
                            </button>
                        </div>
                        {user?.has_llm_key && (
                            <p className="mt-2 text-sm text-green-400 flex items-center gap-1">
                                <Check className="h-4 w-4" />
                                API key is configured
                            </p>
                        )}
                    </div>

                    {/* Save Button */}
                    <button
                        onClick={handleSaveApiKey}
                        disabled={!apiKey || saving}
                        className="px-6 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                    >
                        {saving && <Loader2 className="h-4 w-4 animate-spin" />}
                        Save Configuration
                    </button>
                </div>
            </section>

            {/* GitHub Integration */}
            <section className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Github className="h-5 w-5 text-purple-400" />
                        GitHub Integration
                    </h2>
                </div>
                <div className="p-6">
                    {user?.github_connected ? (
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="h-10 w-10 bg-slate-700 rounded-full flex items-center justify-center">
                                    <Github className="h-5 w-5 text-white" />
                                </div>
                                <div>
                                    <p className="font-medium text-white">
                                        @{user.github_username}
                                    </p>
                                    <p className="text-sm text-green-400 flex items-center gap-1">
                                        <Check className="h-3 w-3" />
                                        Connected
                                    </p>
                                </div>
                            </div>
                            <button className="px-4 py-2 text-red-400 hover:text-red-300 transition-colors">
                                Disconnect
                            </button>
                        </div>
                    ) : (
                        <button className="flex items-center gap-2 px-6 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors">
                            <Github className="h-5 w-5" />
                            Connect GitHub Account
                        </button>
                    )}
                </div>
            </section>
        </div>
    );
}
