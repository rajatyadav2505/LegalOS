"use client";

const AUTH_COOKIE = "legalos_token";

export function setAuthToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(AUTH_COOKIE, token);
  document.cookie = `${AUTH_COOKIE}=${token}; path=/; samesite=lax; max-age=86400`;
}

export function clearAuthToken() {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.removeItem(AUTH_COOKIE);
  document.cookie = `${AUTH_COOKIE}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
}

export function getBrowserAuthToken() {
  if (typeof window === "undefined") {
    return null;
  }

  const cookieToken = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${AUTH_COOKIE}=`))
    ?.split("=")[1];

  return cookieToken ?? window.localStorage.getItem(AUTH_COOKIE);
}
