"use client";

const AUTH_COOKIE = "legalos_token";

function shouldUseSecureCookie() {
  if (typeof window === "undefined") {
    return false;
  }

  return window.location.protocol === "https:";
}

export function setAuthToken(token: string) {
  if (typeof window === "undefined") {
    return;
  }

  const secureFlag = shouldUseSecureCookie() ? "; Secure" : "";
  document.cookie = `${AUTH_COOKIE}=${token}; path=/; samesite=lax; max-age=86400${secureFlag}`;
}

export function clearAuthToken() {
  if (typeof window === "undefined") {
    return;
  }

  document.cookie = `${AUTH_COOKIE}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT`;
  if (shouldUseSecureCookie()) {
    document.cookie = `${AUTH_COOKIE}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; Secure`;
  }
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

  return cookieToken ?? null;
}
