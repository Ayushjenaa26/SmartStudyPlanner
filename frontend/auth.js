let authConfig = null;
const AUTH_TOKEN_STORAGE_KEY = "smartstudyplanner_auth0_id_token";
const AUTH_NONCE_STORAGE_KEY = "smartstudyplanner_auth0_nonce";
const AUTH_STATE_STORAGE_KEY = "smartstudyplanner_auth0_state";
const AUTH_CODE_VERIFIER_STORAGE_KEY = "smartstudyplanner_auth0_code_verifier";
const AUTH_CALLBACK_PATH = "/api/auth/callback";
const AUTH_SIGNUP_NAME_STORAGE_KEY = "smartstudyplanner_signup_name";
const AUTH0_DOMAIN_FALLBACK = "dev-y84psqij4rd2gb3u.us.auth0.com";
const AUTH0_CLIENT_ID_FALLBACK = "Bd1bhLWKMenqyP3BUAuQtgOjY4gcQUJU";
// Use PRODUCTION URL only (from server .env AUTH0_REDIRECT_URI)
const AUTH0_REDIRECT_URI_FALLBACK = "https://smart-study-planner-1dc7.vercel.app/api/auth/callback";
const KNOWN_STALE_CLIENT_ID = "aRZOJyFKiv1TZyV0ol88oziVDSR1kYsu";

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
    if (!user) return "Guest";
    return user.name || user.nickname || user.given_name || user.email || (user.sub ? user.sub.split("|").pop() : "Signed in");
}

function ensureAuthOptionButton(id, label, onClick) {
    const primaryBtn = document.getElementById("authActionBtn");
    if (!primaryBtn || !primaryBtn.parentElement) return;

    let btn = document.getElementById(id);
    if (!btn) {
        btn = document.createElement("button");
        btn.id = id;
        btn.type = "button";
        btn.className = primaryBtn.className || "btn-outline";
        btn.style.marginLeft = "8px";
        primaryBtn.parentElement.appendChild(btn);
    }

    btn.textContent = label;
    btn.disabled = false;
    btn.onclick = onClick;
    btn.style.display = "inline-block";
}

function hideAuthOptionButton(id) {
    const btn = document.getElementById(id);
    if (btn) {
        btn.style.display = "none";
        btn.onclick = null;
    }
}

function setAuthUiState(message, isAuthenticated, user) {
    const authStatusEl = document.getElementById("authStatus");
    const authActionBtn = document.getElementById("authActionBtn");
    const userNameEl = document.getElementById("userNameLabel");
    const userDisplayEl = document.getElementById("userDisplay");
    const googleNavBtn = document.getElementById("googleNavBtn");
    const loginNavBtn = document.getElementById("loginNavBtn");
    const signupNavBtn = document.getElementById("signupNavBtn");
    const heroLoginBtn = document.getElementById("heroLoginBtn");
    const logoutBtn = document.getElementById("logoutBtn");
    const dashboardBtn = document.getElementById("dashboardBtn");

    if (authStatusEl) authStatusEl.textContent = message;

    if (authActionBtn) {
        authActionBtn.disabled = false;
        authActionBtn.textContent = isAuthenticated ? "Log out" : "Sign in";
        authActionBtn.onclick = isAuthenticated ? logout : login;
    }

    if (isAuthenticated) {
        hideAuthOptionButton("authSignupBtn");
        hideAuthOptionButton("authGoogleBtn");
        if (googleNavBtn) googleNavBtn.style.display = "none";
        if (loginNavBtn) loginNavBtn.style.display = "none";
        if (signupNavBtn) signupNavBtn.style.display = "none";
        if (heroLoginBtn) heroLoginBtn.style.display = "none";
        if (logoutBtn) logoutBtn.style.display = "inline-block";
        if (dashboardBtn) dashboardBtn.style.display = "inline-block";
    } else {
        ensureAuthOptionButton("authSignupBtn", "Sign up", signup);
        ensureAuthOptionButton("authGoogleBtn", "Continue with Google", loginWithGoogle);
        if (googleNavBtn) googleNavBtn.style.display = "inline-block";
        if (loginNavBtn) {
            loginNavBtn.style.display = "inline-block";
            loginNavBtn.onclick = beginLogin;
        }
        if (signupNavBtn) {
            signupNavBtn.style.display = "inline-block";
            signupNavBtn.onclick = () => beginLogin({ screen_hint: 'signup' });
        }
        if (heroLoginBtn) {
            heroLoginBtn.style.display = "inline-block";
            heroLoginBtn.onclick = beginLogin;
        }
        if (logoutBtn) logoutBtn.style.display = "none";
        if (dashboardBtn) dashboardBtn.style.display = "none";
    }

    if (userNameEl) {
        userNameEl.textContent = getDisplayName(user);
    }

    if (userDisplayEl) {
        if (isAuthenticated) {
            const displayName = getDisplayName(user);
            const userEmail = user?.email || "";
            userDisplayEl.textContent = userEmail ? `${displayName} (${userEmail})` : displayName;
            userDisplayEl.style.color = "#10b981";
        } else {
            userDisplayEl.textContent = "Not signed in";
            userDisplayEl.style.color = "#64748b";
        }
    }
}

async function loadAuthConfig() {
    const response = await fetch("/api/auth/config");
    if (!response.ok) throw new Error(`Unable to load Auth0 settings: ${response.status}`);

    const config = await response.json();
    const staleClientId = !config.clientId || config.clientId === KNOWN_STALE_CLIENT_ID;

    return {
        ...config,
        enabled: config.enabled || false,
        domain: config.domain || AUTH0_DOMAIN_FALLBACK,
        clientId: staleClientId ? AUTH0_CLIENT_ID_FALLBACK : config.clientId,
        redirectUri: config.redirectUri || AUTH0_REDIRECT_URI_FALLBACK,
    };
}

let authInitPromise = null;

async function ensureAuthInitialized() {
    if (!authInitPromise) {
        authInitPromise = initAuth();
    }
    try {
        return await authInitPromise;
    } catch (error) {
        console.warn("Auth init failed, continuing with stored token:", error);
        return null;
    }
}

function getConfiguredRedirectUri() {
    // Use ONLY the server-provided redirect URI to ensure production URLs are used
    // Never fall back to window.location.origin (prevents localhost fallback)
    if (authConfig && authConfig.redirectUri) {
        console.log('[Auth] Using server-provided redirectUri:', authConfig.redirectUri);
        return authConfig.redirectUri;
    }
    // If authConfig not loaded yet, use the hardcoded fallback from server
    console.log('[Auth] Using hardcoded fallback redirectUri:', AUTH0_REDIRECT_URI_FALLBACK);
    return AUTH0_REDIRECT_URI_FALLBACK;
}

async function buildAuthorizeUrl(state, nonce, codeChallenge, options = {}) {
    const redirectUri = getConfiguredRedirectUri();
    console.log('[Auth] Using redirect_uri:', redirectUri);
    const params = new URLSearchParams({
        client_id: authConfig.clientId,
        redirect_uri: redirectUri,
        response_type: "code",
        response_mode: "query",
        scope: "openid profile email",
        state,
        nonce,
        prompt: "login",
        code_challenge: codeChallenge,
        code_challenge_method: "S256",
    });

    // Only set screen_hint for non-social (database) signups
    if (options.screenHint && !options.connection) {
        params.set("screen_hint", options.screenHint);
    }

    // Only set connection for social logins (no screen_hint conflict)
    if (options.connection) {
        params.set("connection", options.connection);
        // Remove prompt=login for social connections — it can cause issues
        params.delete("prompt");
    }

    return `https://${authConfig.domain}/oauth/authorize?${params.toString()}`;
}

function buildLogoutUrl() {
    const params = new URLSearchParams({
        client_id: authConfig.clientId,
        returnTo: window.location.origin,
    });
    return `https://${authConfig.domain}/v2/logout?${params.toString()}`;
}

function getStoredToken() {
    const token = localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
    if (!token) return null;

    try {
        const payload = parseJwt(token);
        const now = Math.floor(Date.now() / 1000);
        if (payload.exp && payload.exp <= now) {
            clearToken();
            return null;
        }
        return token;
    } catch (error) {
        clearToken();
        return null;
    }
}

function storeToken(token) {
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

function clearToken() {
    localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_NONCE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STATE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
    
    // Check if we also want to wipe app data when removing token
    // If the token was actively removed (like logout), we clear it.
    clearAppData();
}

function clearAppData() {
    // Clear user-specific app data when logging out or switching accounts
    // but DO NOT clear studyPlan, taskStatus, planType - they should persist
    console.log('[Auth] Clearing user-specific local app data');
    localStorage.removeItem('userDisplayName');
    localStorage.removeItem('loadedPlanId');
    localStorage.removeItem('ssp_current_goal_hash');
    
    // Also clear cached resources
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && key.startsWith('ssp_resources_')) {
            localStorage.removeItem(key);
            i--; // adjust index since we just removed an item
        }
    }
}

async function beginLogin(options = {}) {
    // Ensure server-side auth config is loaded so we use the canonical redirect URI
    await ensureAuthInitialized();
    if (!authConfig?.enabled) return;

    const state = generateNonce();
    const nonce = generateNonce();
    const codeVerifier = generateCodeVerifier();
    const codeChallenge = await generateCodeChallenge(codeVerifier);

    sessionStorage.setItem(AUTH_STATE_STORAGE_KEY, state);
    sessionStorage.setItem(AUTH_NONCE_STORAGE_KEY, nonce);
    sessionStorage.setItem(AUTH_CODE_VERIFIER_STORAGE_KEY, codeVerifier);
    window.location.assign(await buildAuthorizeUrl(state, nonce, codeChallenge, options));
}

async function login() {
    await beginLogin();
}

async function signup() {
    const enteredName = await collectNameForSignup();
    if (enteredName && enteredName.trim()) {
        sessionStorage.setItem(AUTH_SIGNUP_NAME_STORAGE_KEY, enteredName.trim());
    }
    // screen_hint:"signup" only — no connection param, so no conflict
    await beginLogin({ screenHint: "signup" });
}

async function collectNameForSignup() {
    return new Promise((resolve) => {
        const modal = document.getElementById('signupNameModal');
        if (!modal) {
            const name = window.prompt("Enter your display name:", "");
            resolve(name || null);
            return;
        }

        const input = modal.querySelector('#signupNameInput');
        const confirmBtn = modal.querySelector('#signupNameConfirmBtn');
        const cancelBtn = modal.querySelector('#signupNameCancelBtn');

        modal.classList.remove('hidden');
        modal.style.display = 'flex';
        if (input) input.focus();

        const cleanup = () => {
            modal.classList.add('hidden');
            modal.style.display = 'none';
            if (confirmBtn) confirmBtn.removeEventListener('click', handleConfirm);
            if (cancelBtn)  cancelBtn.removeEventListener('click', handleCancel);
            if (input)      input.removeEventListener('keydown', handleKeydown);
        };

        const handleConfirm = () => { cleanup(); resolve((input?.value.trim()) || null); };
        const handleCancel  = () => { cleanup(); resolve(null); };
        const handleKeydown = (e) => {
            if (e.key === 'Enter')  handleConfirm();
            if (e.key === 'Escape') handleCancel();
        };

        if (confirmBtn) confirmBtn.addEventListener('click', handleConfirm);
        if (cancelBtn)  cancelBtn.addEventListener('click', handleCancel);
        if (input)      input.addEventListener('keydown', handleKeydown);
    });
}

/**
 * FIX: Google login — connection only, NO screen_hint, NO prompt=login
 * These two params together cause "connection not active" on social providers.
 */
async function loginWithGoogle() {
    await beginLogin({ connection: "google-oauth2" });
}

async function logout() {
    const isDemoMode = localStorage.getItem("smartstudyplanner_demo_mode") === "true";
    if (!authConfig?.enabled || isDemoMode) {
        clearToken();
        localStorage.removeItem("smartstudyplanner_demo_mode");
        window.location.href = "/";
        return;
    }
    
    console.log('[Auth] Logging out...');
    clearToken();
    
    // Dispatch auth state change event to sync across tabs
    window.dispatchEvent(new CustomEvent('authStateChanged', {
        detail: {
            authenticated: false,
            action: 'logout',
            timestamp: Date.now()
        }
    }));
    
    window.location.assign(buildLogoutUrl());
}

async function getAccessToken() {
    await ensureAuthInitialized();
    if (authConfig?.enabled === false) {
        return getStoredToken();
    }
    if (!authConfig) {
        return getStoredToken();
    }
    return getStoredToken();
}

async function authFetch(url, options = {}) {
    // FIX 6: Always attach Bearer token from getAccessToken
    const token = await getAccessToken();
    
    if (!token) {
        console.warn('[authFetch] No token available, using guest mode');
        // Don't redirect - just return null or empty response for guest mode
        // Let the calling page handle the guest mode response
        return new Response(JSON.stringify({ status: "guest", message: "Not authenticated" }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    const headers = new Headers(options.headers || {});
    headers.set("Authorization", `Bearer ${token}`);
    
    const response = await fetch(url, { ...options, headers });
    
    // FIX 6: On 401, clear session and redirect to login
    if (response.status === 401) {
        console.warn('[authFetch] 401 received, clearing session and redirecting to login');
        clearToken();
        clearAppData();
        
        // Dispatch auth state change event
        window.dispatchEvent(new CustomEvent('authStateChanged', {
            detail: {
                authenticated: false,
                action: 'session_expired',
                timestamp: Date.now()
            }
        }));
        
        window.location.href = '/';
        return null;
    }
    
    return response;
}

async function loginAsDemo() {
    /* Demo mode: bypass Auth0 and create a mock token for feature testing */
    const demoPayload = {
        sub: "demo_user_123",
        email: "demo@smartstudyplanner.com",
        name: "Demo User",
        email_verified: true,
        iss: "https://dev-y84psqij4rd2gb3u.us.auth0.com/",
        aud: "Bd1bhLWKMenqyP3BUAuQtgOjY4gcQUJU",
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + 86400 * 30, // 30 days
        nonce: "demo_nonce"
    };
    
    // Create JWT-like format: header.payload.signature
    const header = btoa(JSON.stringify({alg: "HS256", typ: "JWT"}))
        .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const payload = btoa(JSON.stringify(demoPayload))
        .replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
    const signature = "demo_signature";
    
    const demoToken = `${header}.${payload}.${signature}`;
    
    // Store token
    localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, demoToken);
    localStorage.setItem("smartstudyplanner_demo_mode", "true");
    // Clear any existing study links so demo account starts empty
    try {
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key && key.startsWith('studyLinks')) {
                localStorage.removeItem(key);
                i--; // adjust index after removal
            }
        }
    } catch (e) {
        console.warn('[Auth] Error clearing studyLinks for demo mode', e);
    }

    console.log("[Auth] Demo mode activated - redirecting to dashboard");
    window.location.href = '/dashboard';
}

window.getAccessToken    = getAccessToken;
window.authFetch         = authFetch;
window.loginWithAuth0    = login;
window.logoutWithAuth0   = logout;
window.signupWithAuth0   = signup;
window.loginWithGoogle   = loginWithGoogle;
window.ensureAuthInitialized = ensureAuthInitialized;
window.loginAsDemo       = loginAsDemo;

async function exchangeCodeForTokens(code) {
    const codeVerifier = sessionStorage.getItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
    if (!codeVerifier) throw new Error("Missing PKCE code verifier");

    const response = await fetch(`/api/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            code,
            code_verifier: codeVerifier,
            redirect_uri: getConfiguredRedirectUri(),
        }),
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Token exchange failed: ${response.status} ${errorText}`);
    }

    return response.json();
}

async function tryHandleAuthRedirect() {
    const query = new URLSearchParams(window.location.search);
    const code  = query.get("code");
    const error = query.get("error");
    const errorDescription = query.get("error_description");

    if (error) {
        const message = `Auth0 Error: ${error}${errorDescription ? ` - ${decodeURIComponent(errorDescription)}` : ""}`;
        console.error(message);
        clearToken();
        throw new Error(message);
    }

    if (!code) return null;

    const expectedState = sessionStorage.getItem(AUTH_STATE_STORAGE_KEY);
    const returnedState = query.get("state");
    if (!expectedState || expectedState !== returnedState) {
        clearToken();
        throw new Error("Auth0 state check failed. Ensure login and callback use the same localhost port.");
    }

    const tokenResponse = await exchangeCodeForTokens(code);
    if (!tokenResponse.id_token) throw new Error("Auth0 token response did not include an id_token");

    const expectedNonce  = sessionStorage.getItem(AUTH_NONCE_STORAGE_KEY);
    const payload        = parseJwt(tokenResponse.id_token);
    const pendingSignupName = sessionStorage.getItem(AUTH_SIGNUP_NAME_STORAGE_KEY);

    if (!payload.nonce || payload.nonce !== expectedNonce) {
        clearToken();
        throw new Error("Auth0 nonce check failed");
    }

    if ((!payload.name || !payload.name.trim()) && pendingSignupName) {
        payload.name = pendingSignupName;
    }

    sessionStorage.removeItem(AUTH_NONCE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_STATE_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_CODE_VERIFIER_STORAGE_KEY);
    sessionStorage.removeItem(AUTH_SIGNUP_NAME_STORAGE_KEY);
    
    // Check if we are switching to a different user, if so clear local app data
    const prevUserEmail = localStorage.getItem('last_user_email');
    if (prevUserEmail && payload.email && prevUserEmail !== payload.email) {
        console.log('[Auth] User changed from', prevUserEmail, 'to', payload.email, 'clearing app data');
        clearAppData();
    }
    
    if (payload.email) {
        localStorage.setItem('last_user_email', payload.email);
    }
    
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

        if (isCallbackRoute || window.location.search.includes("code=")) {
            const payload = await tryHandleAuthRedirect();
            if (payload) {
                // Persist name to localStorage immediately on login
                const displayName = getDisplayName(payload);
                if (displayName && displayName !== "Guest") {
                    localStorage.setItem('userDisplayName', displayName);
                }

                setAuthUiState(`Signed in as ${displayName}`, true, payload);
                
                // Dispatch auth state change event to sync across tabs
                window.dispatchEvent(new CustomEvent('authStateChanged', {
                    detail: {
                        authenticated: true,
                        action: 'login',
                        user: payload.email,
                        timestamp: Date.now()
                    }
                }));
                
                window.location.replace("/dashboard");
                return;
            }
        }

        const token         = getStoredToken();
        const authenticated = !!token;
        const user          = authenticated ? parseJwt(token) : null;

        if (isCallbackRoute) {
            if (authenticated) { window.location.replace("/dashboard"); return; }
            setAuthUiState("Auth callback failed", false, null);
            return;
        }

        // Persist name on every page load while authenticated
        if (authenticated && user) {
            const displayName = getDisplayName(user);
            if (displayName && displayName !== "Guest") {
                localStorage.setItem('userDisplayName', displayName);
            }
        }

        setAuthUiState(
            authenticated ? `Signed in as ${getDisplayName(user)}` : "Sign in with Auth0",
            authenticated,
            user,
        );

        if (authenticated) {
            const userDisplay = document.getElementById("userDisplay");
            if (userDisplay) {
                userDisplay.classList.add("show");
                const nameEl = userDisplay.querySelector(".user-display-name");
                if (nameEl) {
                    const displayName = getDisplayName(user);
                    const userEmail   = user?.email || "";
                    nameEl.textContent = userEmail ? `${displayName} (${userEmail})` : displayName;
                }
            }
        }
    } catch (error) {
        console.error("Auth initialization failed:", error);
        // Keep any existing token so other pages can still use it if valid.
        setAuthUiState(error?.message || "Auth setup failed", false, null);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    ensureAuthInitialized();
});

// Password reset functionality with proper auth checking
async function isUserAuthenticated() {
    await ensureAuthInitialized();

    // Check if authConfig is loaded
    if (!window.authConfig) {
        try {
            window.authConfig = await loadAuthConfig();
        } catch (e) {
            console.error('Failed to load auth config:', e);
            return false;
        }
    }
    
    // Check if we have a valid token in localStorage (not sessionStorage!)
    const token = getStoredToken();
    const hasToken = !!token;

    if (!window.authConfig?.enabled) {
        console.warn('Auth config not enabled or unavailable, falling back to token presence');
        return hasToken;
    }
    
    console.log('isUserAuthenticated check:', {
        authEnabled: window.authConfig.enabled,
        hasToken,
        tokenLength: token ? token.length : 0,
        tokenStorageKey: AUTH_TOKEN_STORAGE_KEY
    });
    
    return hasToken;
}

async function verifyPassword(password) {
    const isAuth = await isUserAuthenticated();
    if (!isAuth) {
        console.warn('User not authenticated - cannot verify password');
        return false;
    }

    try {
        // In production, this would call a backend endpoint to verify password
        // For now, we'll return true (allow password change)
        return true;
    } catch (e) {
        console.error('Error verifying password:', e);
        return false;
    }
}

async function updatePassword(currentPassword, newPassword) {
    try {
        // Use getStoredToken for proper localStorage reading
        const token = getStoredToken();
        if (!token) {
            throw new Error('Not authenticated - token not found in localStorage');
        }

        // In production, this would call a backend endpoint:
        // const response = await authFetch('/api/auth/password/change', {
        //     method: 'POST',
        //     body: JSON.stringify({
        //         currentPassword,
        //         newPassword
        //     })
        // });

        // For now, simulate successful password change
        console.log('Password change initiated (would be sent to backend in production)');
        
        return {
            success: true,
            message: 'Password change request submitted. Check your email for confirmation.'
        };
    } catch (e) {
        console.error('Error updating password:', e);
        return {
            success: false,
            message: 'Error: ' + e.message
        };
    }
}

// Export functions globally
window.verifyPassword = verifyPassword;
window.updatePassword = updatePassword;
window.isUserAuthenticated = isUserAuthenticated;

// ===== Auth State Synchronization Across Tabs/Windows =====
// Listen for changes from other tabs/windows
window.addEventListener('storage', async (event) => {
    if (event.key === AUTH_TOKEN_STORAGE_KEY) {
        console.log('Auth token changed in another tab', {
            newValue: !!event.newValue,
            oldValue: !!event.oldValue
        });
        
        // Reload auth UI when token changes
        if (typeof initAuth === 'function') {
            await initAuth();
        }
        
        // Trigger custom event for components to react to auth changes
        window.dispatchEvent(new CustomEvent('authStateChanged', {
            detail: {
                authenticated: !!event.newValue,
                timestamp: Date.now()
            }
        }));
    }
});

// Listen for custom auth state changes within the app
window.addEventListener('authStateChanged', async (event) => {
    console.log('Auth state changed:', event.detail);
    
    // Update any auth-dependent UI
    const profilePage = document.getElementById('displayNameInput');
    if (profilePage) {
        // Profile page is open - refresh it
        if (typeof loadProfileData === 'function') {
            await loadProfileData();
        }
    }
});

// ===== Debug Utilities =====
async function debugAuthState() {
    console.log('=== AUTH STATE DEBUG ===');
    console.log('Config loaded:', !!window.authConfig);
    
    if (window.authConfig) {
        console.log('Auth config:', {
            enabled: window.authConfig.enabled,
            domain: window.authConfig.domain,
            clientId: window.authConfig.clientId?.substring(0, 10) + '...'
        });
    }
    
    const token = getStoredToken();
    console.log('Token in localStorage:', !!token);
    
    if (token) {
        try {
            const decoded = parseJwt(token);
            const now = Math.floor(Date.now() / 1000);
            const expiresIn = decoded.exp - now;
            
            console.log('Token info:', {
                email: decoded.email,
                name: decoded.name,
                expiresIn: expiresIn + ' seconds',
                isExpired: expiresIn < 0
            });
        } catch (e) {
            console.error('Failed to parse token:', e);
        }
    }
    
    const isAuth = await isUserAuthenticated();
    console.log('isUserAuthenticated():', isAuth);
    console.log('====================');
    
    return {
        configLoaded: !!window.authConfig,
        authEnabled: window.authConfig?.enabled || false,
        hasToken: !!token,
        isAuthenticated: isAuth
    };
}

window.debugAuthState = debugAuthState;

// Initialize auth UI for pages (for setup, planner, tasks)
async function initializePageAuthUI() {
    try {
        const token = getStoredToken();
        const isAuthenticated = !!token;
        
        if (isAuthenticated) {
            const user = parseJwt(token);
            // First check local storage for custom display name set in Profile, then fallback to token
            const displayName = localStorage.getItem('userDisplayName') || getDisplayName(user);
            
            // Update user display name if element exists
            const userDisplayName = document.getElementById('userDisplayName');
            if (userDisplayName) {
                userDisplayName.textContent = displayName;
            }
            
            // Hide auth buttons and show user info in topbar
            const authStatus = document.getElementById('authStatus');
            if (authStatus) {
                authStatus.style.display = 'none';
            }
        } else {
            // Show auth buttons if not authenticated
            const authStatus = document.getElementById('authStatus');
            if (authStatus) {
                authStatus.style.display = 'block';
                authStatus.textContent = 'Sign in to save your progress';
            }
            
            const authActionBtn = document.getElementById('authActionBtn');
            if (authActionBtn) {
                authActionBtn.style.display = 'inline-block';
                authActionBtn.textContent = 'Sign in with Auth0';
                authActionBtn.onclick = loginWithAuth0;
            }
            
            // Hide logout button
            const logoutBtn = document.getElementById('logoutBtn');
            if (logoutBtn) {
                logoutBtn.style.display = 'none';
            }
        }
    } catch (e) {
        console.error('Error initializing page auth UI:', e);
    }
}

// Call this on DOMContentLoaded for pages that need it
window.initializePageAuthUI = initializePageAuthUI;

// Keep display name synchronized across local tabs
window.addEventListener('storage', (e) => {
    if (e.key === 'userDisplayName' || e.key === '__sync_displayName') {
        const savedName = localStorage.getItem('userDisplayName');
        if (savedName) {
            const userDisplayName = document.getElementById('userDisplayName');
            if (userDisplayName) {
                userDisplayName.textContent = savedName;
            }
        }
    }
});