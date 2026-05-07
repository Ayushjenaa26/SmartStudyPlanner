/**
 * Google Calendar Integration Module
 * Provides UI controls and functionality for syncing to Google Calendar
 */

class GoogleCalendarIntegration {
    constructor(containerId = null) {
        this.container = containerId ? document.getElementById(containerId) : null;
        this.isConnected = false;
        this.init();
    }

    async init() {
        // Check connection status on page load
        await this.checkConnectionStatus();
        if (this.container) {
            this.renderUI();
        }
    }

    /**
     * Check if user has already authorized Google Calendar
     */
    async checkConnectionStatus() {
        try {
            const response = await authFetch('/api/calendar/events?days=1');
            const data = await response.json();
            this.isConnected = response.ok && data.status === 'success';
        } catch (error) {
            this.isConnected = false;
        }
    }

    /**
     * Start Google Calendar authorization flow
     */
    async authorize() {
        try {
            const response = await authFetch('/api/calendar/auth');
            const data = await response.json();

            if (data.auth_url) {
                window.location.href = data.auth_url;
            } else {
                this.showError(data.message || 'Failed to get authorization URL');
            }
        } catch (error) {
            this.showError(`Authorization failed: ${error.message}`);
        }
    }

    /**
     * Sync all pending tasks to Google Calendar
     */
    async syncTasks(filters = {}) {
        try {
            const button = document.getElementById('syncToCalendarBtn');
            if (button) {
                button.disabled = true;
                button.textContent = 'Syncing...';
            }

            const response = await authFetch('/api/calendar/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(filters)
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.showSuccess(data.message);
                const result = data.sync_result;
                console.log(`Synced ${result.synced_count} tasks, ${result.failed_count} failed`);
            } else {
                this.showError(data.message || 'Sync failed');
            }

            if (button) {
                button.disabled = false;
                button.textContent = '⬆️ Sync Tasks to Calendar';
            }
        } catch (error) {
            this.showError(`Sync failed: ${error.message}`);
        }
    }

    /**
     * List upcoming calendar events
     */
    async listEvents(days = 30) {
        try {
            const response = await authFetch(`/api/calendar/events?days=${days}`);
            const data = await response.json();

            if (data.status === 'success') {
                return data.events || [];
            } else {
                this.showError(data.message || 'Failed to fetch events');
                return [];
            }
        } catch (error) {
            this.showError(`Failed to fetch events: ${error.message}`);
            return [];
        }
    }

    /**
     * Revoke Google Calendar access
     */
    async revoke() {
        if (!confirm('Are you sure you want to revoke Google Calendar access?')) {
            return;
        }

        try {
            const response = await authFetch('/api/calendar/revoke', {
                method: 'POST'
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.isConnected = false;
                this.showSuccess(data.message);
                this.renderUI();
            } else {
                this.showError(data.message || 'Failed to revoke access');
            }
        } catch (error) {
            this.showError(`Revoke failed: ${error.message}`);
        }
    }

    /**
     * Render UI controls
     */
    renderUI() {
        if (!this.container) return;

        this.container.innerHTML = '';

        if (this.isConnected) {
            // Show connected state
            const card = document.createElement('div');
            card.style.cssText = `
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 16px;
            `;
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0 0 8px; font-size: 16px; font-weight: 600;">
                            📅 Google Calendar Connected
                        </h3>
                        <p style="margin: 0; font-size: 14px; opacity: 0.9;">
                            Your study tasks can be synced to Google Calendar
                        </p>
                    </div>
                </div>
            `;
            this.container.appendChild(card);

            // Sync button
            const syncBtn = document.createElement('button');
            syncBtn.id = 'syncToCalendarBtn';
            syncBtn.className = 'btn-primary';
            syncBtn.textContent = '⬆️ Sync Tasks to Calendar';
            syncBtn.style.cssText = `
                width: 100%;
                padding: 12px;
                margin-bottom: 8px;
                background: var(--primary);
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: opacity 0.2s;
            `;
            syncBtn.addEventListener('click', () => this.syncTasks());
            syncBtn.addEventListener('mouseenter', (e) => e.target.style.opacity = '0.9');
            syncBtn.addEventListener('mouseleave', (e) => e.target.style.opacity = '1');
            this.container.appendChild(syncBtn);

            // Revoke button
            const revokeBtn = document.createElement('button');
            revokeBtn.textContent = '🔓 Disconnect Calendar';
            revokeBtn.style.cssText = `
                width: 100%;
                padding: 10px;
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                cursor: pointer;
                transition: opacity 0.2s;
            `;
            revokeBtn.addEventListener('click', () => this.revoke());
            revokeBtn.addEventListener('mouseenter', (e) => e.target.style.opacity = '0.9');
            revokeBtn.addEventListener('mouseleave', (e) => e.target.style.opacity = '1');
            this.container.appendChild(revokeBtn);
        } else {
            // Show disconnected state
            const card = document.createElement('div');
            card.style.cssText = `
                background: #f0f9ff;
                border: 1px solid #bfdbfe;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 16px;
            `;
            card.innerHTML = `
                <h3 style="margin: 0 0 8px; color: #1e40af; font-size: 16px; font-weight: 600;">
                    📅 Connect Google Calendar
                </h3>
                <p style="margin: 0 0 16px; color: #1e3a8a; font-size: 14px;">
                    Sync your study tasks directly to Google Calendar to stay organized
                </p>
            `;
            this.container.appendChild(card);

            const authorizeBtn = document.createElement('button');
            authorizeBtn.id = 'connectGoogleCalendarBtn';
            authorizeBtn.className = 'btn-primary';
            authorizeBtn.textContent = '🔗 Connect Google Calendar';
            authorizeBtn.style.cssText = `
                width: 100%;
                padding: 12px;
                background: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
                transition: opacity 0.2s;
            `;
            authorizeBtn.addEventListener('click', () => this.authorize());
            authorizeBtn.addEventListener('mouseenter', (e) => e.target.style.opacity = '0.9');
            authorizeBtn.addEventListener('mouseleave', (e) => e.target.style.opacity = '1');
            this.container.appendChild(authorizeBtn);
        }
    }

    /**
     * Show success message
     */
    showSuccess(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 400px;
            animation: slideIn 0.3s ease-in-out;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in-out';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    /**
     * Show error message
     */
    showError(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #ef4444;
            color: white;
            padding: 16px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 400px;
            animation: slideIn 0.3s ease-in-out;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in-out';
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }
}

// Auto-initialize if element exists
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('googleCalendarWidget')) {
        window.googleCalendarIntegration = new GoogleCalendarIntegration('googleCalendarWidget');
    }
});
