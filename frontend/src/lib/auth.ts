"use client";

const TOKEN_KEY = "kineia_token";

export interface User {
  sub: string;
  email: string;
  name: string;
  role: "admin" | "user";
  exp: number;
  iat: number;
}

function base64UrlDecode(str: string): string {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  while (str.length % 4) str += "=";
  return atob(str);
}

function decodeJWT(token: string): User | null {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const payload = JSON.parse(base64UrlDecode(parts[1]));
    if (!payload.sub || !payload.role || !payload.exp) return null;
    return payload as User;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  const token = getToken();
  if (!token) return false;
  const user = decodeJWT(token);
  if (!user) return false;
  // Check if token is expired
  return user.exp * 1000 > Date.now();
}

export function isAdmin(): boolean {
  const token = getToken();
  if (!token) return false;
  const user = decodeJWT(token);
  if (!user) return false;
  return user.role === "admin" && user.exp * 1000 > Date.now();
}

export function getUser(): User | null {
  const token = getToken();
  if (!token) return null;
  return decodeJWT(token);
}
