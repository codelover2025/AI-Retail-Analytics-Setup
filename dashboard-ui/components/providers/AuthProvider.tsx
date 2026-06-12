"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import {
  type AuthUser,
  type LoginCredentials,
  clearToken,
  getCurrentUser,
  loginWithCredentials,
  logout,
} from "@/lib/auth";

/** Sets a lightweight presence cookie readable by Next.js middleware. */
function setAuthCookie() {
  if (typeof document !== "undefined") {
    document.cookie = "orzen_auth=1; path=/; max-age=86400; SameSite=Lax";
  }
}

/** Clears the presence cookie. */
function clearAuthCookie() {
  if (typeof document !== "undefined") {
    document.cookie = "orzen_auth=; path=/; max-age=0";
  }
}

// ---------------------------------------------------------------------------
// Context shape
// ---------------------------------------------------------------------------

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  hasRole: (requiredRole: string) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Hydrate from localStorage on mount
  useEffect(() => {
    const currentUser = getCurrentUser();
    setUser(currentUser);
    setIsLoading(false);
  }, []);

  const handleLogin = useCallback(async (credentials: LoginCredentials) => {
    const loggedInUser = await loginWithCredentials(credentials);
    setAuthCookie();
    setUser(loggedInUser);
  }, []);

  const handleLogout = useCallback(() => {
    clearAuthCookie();
    logout();
    setUser(null);
  }, []);

  const hasRoleCheck = useCallback(
    (requiredRole: string): boolean => {
      if (!user) return false;
      const ROLE_HIERARCHY = [
        "staff_viewer",
        "store_manager",
        "brand_admin",
        "super_admin",
      ];
      return (
        ROLE_HIERARCHY.indexOf(user.role) >= ROLE_HIERARCHY.indexOf(requiredRole)
      );
    },
    [user]
  );

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login: handleLogin,
        logout: handleLogout,
        hasRole: hasRoleCheck,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
