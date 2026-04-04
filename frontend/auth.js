let authConfig = null;
const AUTH_TOKEN_STORAGE_KEY = "smartstudyplanner_auth0_id_token";
const AUTH_NONCE_STORAGE_KEY = "smartstudyplanner_auth0_nonce";
const AUTH_STATE_STORAGE_KEY = "smartstudyplanner_auth0_state";
const AUTH_CODE_VERIFIER_STORAGE_KEY = "smartstudyplanner_auth0_code_verifier";
const AUTH_CALLBACK_PATH = "/api/auth/callback";

function base64UrlDecode(value) {
    const padding = "===".slice((value.length + 3) % 4);
    return atob(value.replace(/-/g, "+").replace(/_/g, "/") + padding);
}

function generateNonce() {
    const randomBytes = new Uint8Array(16);
    crypto.getRandomValues(randomBytes);
    return Array.from(randomBytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function base64UrlEncode(bytes) {
    const binary = String.fromCharCode(...bytes);
    return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/g, "");
}

async function sha256(value) {
    const encoded = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest("SHA-256", encoded);
    return new Uint8Array(digest);
}

function generateCodeVerifier() {
    const randomBytes = new Uint8Array(32);
    crypto.getRandomValues(randomBytes);
    return base64UrlEncode(randomBytes);
}

async function generateCodeChallenge(verifier) {
    const digest = await sha256(verifier);
    return base64UrlEncode(digest);
}

function parseJwt(token) {
    const parts = token.split(".");
    if (parts.length < 2) {
        throw new Error("Invalid token format");
    }

    return JSON.parse(base64UrlDecode(parts[1]));
}

function getDisplayName(user) {
    if (!user) {
        return "Guest";
    }

    return user.name || user.email || (user.sub ? user.sub.split("|").pop() : "Signed in");
}

function setAuthUiState(message, isAuthenticated, user) {
    const authStatusEl = document.getElementById("authStatus");
    const authActionBtn = document.getElementById("authActionBtn");
    const userNameEl = document.getElementById("userNameLabel");

    if (authStatusEl) {
        authStatusEl.textContent = message;
    }

    if (authActionBtn) {
        authActionBtn.disabled = false;
        authActionBtn.textContent = isAuthenticated ? "Log out" : "Sign in";
        authActionBtn.onclick = isAuthenticated ? logout : login;
    }

    if (userNameEl) {
        userNameEl.textContent = getDisplayName(user);
    }
}

async function loadAuthConfig() {
    const response = await fetch("/api/auth/config");
    if (!response.ok) {
        throw new Error(`Unable to load Auth0 settings: ${response.status}`);
    }

    return response.json();
}

function getConfiguredRedirectUri() {
    return authConfig?.redirectUri || `${window.location.origin}${AUTH_CALLBACK_PATH}`;
}

function buildAuthorizeUrl(nonce) {
    throw new Error("buildAuthorizeUrl requires PKCE parameters");
}

async function buildAuthorizeUrl(state, nonce, codeChallenge) {
    const params = new URLSearchParams({
        client_id: authConfig.clientId,
        redirect_uri: getConfiguredRedirectUri(),
        response_type: "code",
        response_mode: "query",
        scope: "openid profile email",
        state,
        nonce,
        prompt: "login",
        code_challenge: codeChallenge,
        code_challenge_method: "S256",
    });

    return `https://${authConfig.domain}/oauth/authorize?${params.toString()}`;
}

function buildLogoutUrl() {
    const params = new URLSearchParams({
        client_id: authConfig.clientId,
        returnTo: getConfiguredRedirectUri(),
    });

    return `https://${authConfig.domain}/v2/logout?${params.toString()}`;
}

function getStoredToken() {
    const token = sessionStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (!token) {
        return null;
    }

    try {
        const payload = parseJwt(token);
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp <= now) {
            sessionStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
            return null;
        }
        return token;
    } catch (error) {
        sessionStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
        return null;
    }
}

function storeToken(token) {
    sessionStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

function clearToken() {
    sessionStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_NONCE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STATE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
}

async function login() {
    if (!authConfig?.enabled) {
        return;
    }

    const state = generateNonce();
    const nonce = generateNonce();
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);

    sessionStorage.setItem(AUTH_STATE_STORAGE_KEY, state);
    sessionStorage.setItem(AUTH_NONCE_STORAGE_KEY, nonce);
    sessionStorage.setItem(AUTH_CODE_VERIFIER_STORAGE_KEY, codeVerifier);
    window.location.assign(await buildAuthorizeUrl(state, nonce, codeChallenge));
}

async function logout() {
    if (!authConfig?.enabled) {
        return;
    }

    clearToken();
    window.location.assign(buildLogoutUrl());
}

async function getAccessToken() {
    if (!authConfig?.enabled) {
        return null;
    }

    return getStoredToken();
}

async function authFetch(url, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = await getAccessToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    return fetch(url, {
        ...options,
        headers,
    });
}

window.getAccessToken = getAccessToken;
window.authFetch = authFetch;
window.loginWithAuth0 = login;
window.logoutWithAuth0 = logout;

async function exchangeCodeForTokens(code) {
    const codeVerifier = sessionStorage.getItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
    if (!codeVerifier) {
        throw new Error("Missing PKCE code verifier");
    }

    const response = await fetch(`https://${authConfig.domain}/oauth/token`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            grant_type: "authorization_code",
            client_id: authConfig.clientId,
            code,
            redirect_uri: getConfiguredRedirectUri(),
            code_verifier: codeVerifier,
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Auth0 token exchange failed: ${response.status} ${errorText}`);
    }

    return response.json();
}

async function tryHandleAuthRedirect() {
    const query = new URLSearchParams(window.location.search);
    const code = query.get("code");
    const error = query.get("error");
    const errorDescription = query.get("error_description");

    if (error) {
        const message = `Auth0 Error: ${error}${errorDescription ? ` - ${decodeURIComponent(errorDescription)}` : ""}`;
        console.error(message);
        clearToken();
        throw new Error(message);
    }

    if (!code) {
        return null;
    }

    const expectedState = sessionStorage.getItem(AUTH_STATE_STORAGE_KEY);
    const returnedState = query.get("state");
    if (!expectedState || expectedState !== returnedState) {
        clearToken();
        throw new Error("Auth0 state check failed");
    }

    const tokenResponse = await exchangeCodeForTokens(code);
    if (!tokenResponse.id_token) {
        throw new Error("Auth0 token response did not include an id_token");
    }

    const expectedNonce = sessionStorage.getItem(AUTH_NONCE_STORAGE_KEY);
    const payload = parseJwt(tokenResponse.id_token);

    if (!payload.nonce || payload.nonce !== expectedNonce) {
        clearToken();
        throw new Error("Auth0 nonce check failed");
    }

    sessionStorage.removeItem(AUTH_NONCE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STATE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
    storeToken(tokenResponse.id_token);
    window.history.replaceState({}, document.title, window.location.pathname);
    return payload;
}

async function initAuth() {
    try {
        authConfig = await loadAuthConfig();
        const isCallbackRoute = window.location.pathname === AUTH_CALLBACK_PATH;

        if (!authConfig.enabled) {
            setAuthUiState("Auth0 not configured", false, null);
            const authActionBtn = document.getElementById("authActionBtn");
            if (authActionBtn) {
                authActionBtn.disabled = true;
                authActionBtn.textContent = "Auth setup required";
                authActionBtn.onclick = null;
            }
            return;
        }

        if (window.location.pathname === AUTH_CALLBACK_PATH || window.location.search.includes("code=")) {
            const payload = await tryHandleAuthRedirect();
            if (payload) {
                setAuthUiState(`Signed in as ${getDisplayName(payload)}`, true, payload);
                window.location.replace("/");
                return;
            }
        }

        const token = getStoredToken();
        const authenticated = !!token;
        const user = authenticated ? parseJwt(token) : null;

        if (isCallbackRoute) {
            if (authenticated) {
                window.location.replace("/");
                return;
            }

            setAuthUiState("Auth callback failed", false, null);
            return;
        }

        setAuthUiState(
            authenticated ? `Signed in as ${getDisplayName(user)}` : "Sign in with Auth0",
            authenticated,
            user,
        );
    } catch (error) {
        console.error("Auth initialization failed:", error);
        clearToken();
        const errorMsg = error?.message || "Auth setup failed";
        setAuthUiState(errorMsg, false, null);
    }
}

document.addEventListener("DOMContentLoaded", initAuth);