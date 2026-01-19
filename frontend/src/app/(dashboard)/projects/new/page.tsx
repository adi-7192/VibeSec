'use client';

/**
 * VibeSec Frontend - New Project Page
 * 
 * Handles ZIP file upload for creating new projects.
 */

import { useState, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Upload, ArrowLeft, FolderArchive, Loader2, CheckCircle, XCircle } from 'lucide-react';
import Link from 'next/link';
import apiClient from '@/lib/api';

export default function NewProjectPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const queryClient = useQueryClient();
    const type = searchParams.get('type') || 'zip';

    const [file, setFile] = useState<File | null>(null);
    const [projectName, setProjectName] = useState('');
    const [description, setDescription] = useState('');
    const [dragActive, setDragActive] = useState(false);

    const uploadMutation = useMutation({
        mutationFn: async () => {
            if (!file) throw new Error('No file selected');

            const formData = new FormData();
            formData.append('file', file);
            formData.append('name', projectName || file.name.replace('.zip', ''));
            if (description) formData.append('description', description);

            const response = await apiClient.post('/projects/zip', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            router.push(`/projects/${data.id}`);
        },
    });

    const handleDrag = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            const droppedFile = e.dataTransfer.files[0];
            if (droppedFile.name.endsWith('.zip')) {
                setFile(droppedFile);
                if (!projectName) {
                    setProjectName(droppedFile.name.replace('.zip', ''));
                }
            }
        }
    }, [projectName]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            if (!projectName) {
                setProjectName(selectedFile.name.replace('.zip', ''));
            }
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        uploadMutation.mutate();
    };

    return (
        <div className="max-w-2xl mx-auto py-8">
            {/* Header */}
            <div className="mb-8">
                <Link
                    href="/dashboard"
                    className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-4 transition-colors"
                >
                    <ArrowLeft className="h-4 w-4" />
                    Back to Dashboard
                </Link>
                <h1 className="text-3xl font-bold text-white">Upload Project</h1>
                <p className="text-gray-400 mt-2">
                    Upload your source code as a ZIP file to analyze it for security issues.
                </p>
            </div>

            {/* Upload Form */}
            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Drag & Drop Zone */}
                <div
                    className={`
                        relative border-2 border-dashed rounded-xl p-8 text-center transition-all
                        ${dragActive
                            ? 'border-purple-500 bg-purple-500/10'
                            : file
                                ? 'border-green-500 bg-green-500/10'
                                : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
                        }
                    `}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <input
                        type="file"
                        accept=".zip"
                        onChange={handleFileChange}
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                    />

                    {file ? (
                        <div className="space-y-2">
                            <CheckCircle className="h-12 w-12 text-green-400 mx-auto" />
                            <p className="text-white font-medium">{file.name}</p>
                            <p className="text-gray-400 text-sm">
                                {(file.size / (1024 * 1024)).toFixed(2)} MB
                            </p>
                            <button
                                type="button"
                                onClick={(e) => {
                                    e.preventDefault();
                                    setFile(null);
                                }}
                                className="text-sm text-red-400 hover:text-red-300"
                            >
                                Remove file
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            <div className="mx-auto w-16 h-16 bg-slate-700 rounded-full flex items-center justify-center">
                                <FolderArchive className="h-8 w-8 text-gray-400" />
                            </div>
                            <div>
                                <p className="text-white font-medium">
                                    Drag and drop your ZIP file here
                                </p>
                                <p className="text-gray-400 text-sm mt-1">
                                    or click to browse
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Project Name */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Project Name
                    </label>
                    <input
                        type="text"
                        value={projectName}
                        onChange={(e) => setProjectName(e.target.value)}
                        placeholder="My Awesome Project"
                        className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500"
                    />
                </div>

                {/* Description */}
                <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                        Description (optional)
                    </label>
                    <textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="A brief description of your project..."
                        rows={3}
                        className="w-full px-4 py-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 resize-none"
                    />
                </div>

                {/* Error Display */}
                {uploadMutation.isError && (
                    <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
                        <XCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                        <div>
                            <p className="text-red-400 font-medium">Upload failed</p>
                            <p className="text-red-300 text-sm">
                                {(uploadMutation.error as Error)?.message || 'An error occurred'}
                            </p>
                        </div>
                    </div>
                )}

                {/* Submit Button */}
                <button
                    type="submit"
                    disabled={!file || uploadMutation.isPending}
                    className="w-full py-3 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                    {uploadMutation.isPending ? (
                        <>
                            <Loader2 className="h-5 w-5 animate-spin" />
                            Uploading...
                        </>
                    ) : (
                        <>
                            <Upload className="h-5 w-5" />
                            Upload and Analyze
                        </>
                    )}
                </button>
            </form>
        </div>
    );
}
