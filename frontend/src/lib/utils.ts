/**
 * VibeSec Frontend - Utility Functions
 */

import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
    });
}

export function formatDateTime(dateString: string): string {
    return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
}

export function getScoreColor(score: number | null): string {
    if (score === null) return 'text-gray-400';
    if (score >= 85) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
}

export function getScoreBgColor(score: number | null): string {
    if (score === null) return 'bg-gray-100';
    if (score >= 85) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
}

export function getScoreLabel(score: number | null): string {
    if (score === null) return 'Not Scanned';
    if (score >= 85) return 'Ready';
    if (score >= 60) return 'Needs Work';
    return 'Not Ready';
}

export function getSeverityColor(severity: string): string {
    switch (severity) {
        case 'critical':
            return 'text-red-700 bg-red-100';
        case 'high':
            return 'text-orange-700 bg-orange-100';
        case 'medium':
            return 'text-yellow-700 bg-yellow-100';
        case 'low':
            return 'text-blue-700 bg-blue-100';
        default:
            return 'text-gray-700 bg-gray-100';
    }
}

export function getStackIcon(stack: string): string {
    switch (stack) {
        case 'nextjs':
            return '⚛️';
        case 'express':
            return '🟢';
        case 'django':
            return '🐍';
        case 'fastapi':
            return '⚡';
        default:
            return '📁';
    }
}
