'use client';

/**
 * VibeSec Frontend - Auth Context Provider
 */

import React, { createContext, useContext, useEffect, useState } from 'react';
import { User as FirebaseUser } from 'firebase/auth';
import { onAuthChange, getIdToken } from '@/lib/firebase';
import { verifyToken, User } from '@/lib/api';

interface AuthContextType {
    firebaseUser: FirebaseUser | null;
    user: User | null;
    loading: boolean;
    isAuthenticated: boolean;
    refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
    firebaseUser: null,
    user: null,
    loading: true,
    isAuthenticated: false,
    refreshUser: async () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    const refreshUser = async () => {
        const token = await getIdToken();
        if (token) {
            try {
                const data = await verifyToken(token);
                setUser(data.user);
            } catch (error) {
                console.error('Failed to refresh user:', error);
            }
        }
    };

    useEffect(() => {
        const unsubscribe = onAuthChange(async (fbUser) => {
            setFirebaseUser(fbUser);

            if (fbUser) {
                try {
                    const token = await fbUser.getIdToken();
                    const data = await verifyToken(token);
                    setUser(data.user);
                } catch (error) {
                    console.error('Failed to verify token:', error);
                    setUser(null);
                }
            } else {
                setUser(null);
            }

            setLoading(false);
        });

        return () => unsubscribe();
    }, []);

    return (
        <AuthContext.Provider
            value={{
                firebaseUser,
                user,
                loading,
                isAuthenticated: !!user,
                refreshUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
