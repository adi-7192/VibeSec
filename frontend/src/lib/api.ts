/**
 * VibeSec Frontend - API Client
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { getIdToken } from './firebase';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
    baseURL: `${API_URL}/api/v1`,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth interceptor
apiClient.interceptors.request.use(async (config) => {
    const token = await getIdToken();
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Types
export interface User {
    id: number;
    email: string;
    name: string | null;
    picture: string | null;
    llm_provider: 'gemini' | 'openai' | null;
    has_llm_key: boolean;
    github_connected: boolean;
    github_username: string | null;
    created_at: string;
}

export interface Project {
    id: number;
    name: string;
    description: string | null;
    source_type: 'github' | 'zip' | 'demo';
    repo_url: string | null;
    repo_full_name: string | null;
    stack: 'nextjs' | 'express' | 'django' | 'fastapi' | 'unknown';
    latest_score: number | null;
    latest_scan_id: number | null;
    created_at: string;
    updated_at: string;
}

export interface ProjectWithStats extends Project {
    total_scans: number;
    critical_findings: number;
    high_findings: number;
}

export interface Scan {
    id: number;
    project_id: number;
    status: 'pending' | 'cloning' | 'detecting' | 'scanning_sast' | 'scanning_sca' | 'scoring' | 'completed' | 'failed';
    status_message: string | null;
    progress: number;
    commit_sha: string | null;
    overall_score: number | null;
    domain_scores: Record<string, { score: number; issues: number }> | null;
    total_findings: number;
    critical_count: number;
    high_count: number;
    medium_count: number;
    low_count: number;
    created_at: string;
    completed_at: string | null;
    duration_seconds: number | null;
}

export interface Finding {
    id: number;
    scan_id: number;
    finding_type: 'sast' | 'sca';
    severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
    category: string;
    title: string;
    description: string;
    file_path: string | null;
    line_start: number | null;
    package_name: string | null;
    package_version: string | null;
    cwe_id: string | null;
    cve_id: string | null;
    has_fix_suggestion: boolean;
    has_test_suggestion: boolean;
}

// API Functions

// Auth
export const verifyToken = async (token: string) => {
    const response = await apiClient.post('/auth/verify', { token });
    return response.data;
};

export const getMe = async (): Promise<User> => {
    const response = await apiClient.get('/auth/me');
    return response.data;
};

// Projects
export const getProjects = async (): Promise<{ projects: Project[]; total: number }> => {
    const response = await apiClient.get('/projects');
    return response.data;
};

export const getProject = async (id: number): Promise<ProjectWithStats> => {
    const response = await apiClient.get(`/projects/${id}`);
    return response.data;
};

export const createProjectFromGitHub = async (data: {
    name: string;
    description?: string;
    repo_url: string;
    repo_full_name: string;
    default_branch?: string;
}): Promise<Project> => {
    const response = await apiClient.post('/projects/github', data);
    return response.data;
};

export const deleteProject = async (id: number): Promise<void> => {
    await apiClient.delete(`/projects/${id}`);
};

// Scans
export const getScans = async (projectId: number): Promise<{ scans: Scan[]; total: number }> => {
    const response = await apiClient.get(`/projects/${projectId}/scans`);
    return response.data;
};

export const triggerScan = async (projectId: number): Promise<Scan> => {
    const response = await apiClient.post(`/projects/${projectId}/scans`, {});
    return response.data;
};

export const getScan = async (scanId: number): Promise<Scan> => {
    const response = await apiClient.get(`/scans/${scanId}`);
    return response.data;
};

// Findings
export const getFindings = async (
    scanId: number,
    filters?: { severity?: string[]; category?: string[] }
): Promise<{ findings: Finding[]; total: number }> => {
    const response = await apiClient.get(`/scans/${scanId}/findings`, { params: filters });
    return response.data;
};

export default apiClient;
