# Judge Voting System Implementation Plan

## Overview

Transform the current admin-based corruption marking system into a community-driven voting system where judges are categorized based on user votes into three sections: Corrupt, Undecided, and Not Corrupt. The system will be designed for high scalability and security, leveraging Oracle Cloud's Always Free Tier and Cloudflare.

## Version Tracking

Current Version: 0.5.0

## Roadmap

- [x] **Update 0.5.0:** Initial voting system implementation (Current Version)
    - [x] Database schema changes (initial SQLite version)
    - [x] Basic backend voting endpoints
    - [x] Basic frontend voting UI
    - [x] Rate limiting implementation (basic)
    - [x] Basic anti-spam measures (honeypot)

- [ ] **Update 0.6.0:** Enhanced Security and Scalability
    - [x] Separate Admin Interface into its own Flask application
    - [x] Implement HMAC Authentication
    - [x] Implement Browser Fingerprinting
    - [x] Implement Client-Side Proof of Work
    - [x] Enhance Rate Limiting (leverage Cloudflare and use CF-Connecting-IP)
    - [x] Implement Server-Side Caching (Flask-Caching with Redis/Memcached in mind)
    - [x] Investigate Asynchronous Tasks with Celery (for IP geolocation)


- [ ] **Update 0.7.0:**  Admin Monitoring and Geographic Analysis
    - [ ] Suspicious voting patterns page (admin interface)
    - [ ] Geographic vote distribution visualization (admin interface)
    - [ ] Automated alerts system (for suspicious activity)
    - [ ] Enhanced admin dashboard
    - [x] Toggle on frontpage floating bottom left - show all votes or just votes from USA
    - [ ] Separate data analysis page in the dashboard for votes and submissions

- [ ] **Update 0.8.0:** Database Migration
    - [ ] Migrate from SQLite to PostgreSQL

- [ ] **Update 0.9.0:** Unit Testing & CloudFlare
    - [ ] Implement comprehensive unit tests for backend (Flask) and frontend (JavaScript) code.
    - [ ] Update documentation and configuration for Cloudflare setup (rate limiting, caching, firewall rules)

- [ ] **Update 1.0.0:** Release

## Hosting Environment

This application will be hosted on Oracle Cloud's Always Free Tier, utilizing Cloudflare for CDN, DDoS protection, caching, and other security features. See `@/hosting.md` for detailed information.  Key aspects:

*   **Frontend:** Static files (HTML, CSS, JS) served from Oracle Object Storage and cached by Cloudflare.
*   **Backend:** Flask API running on Oracle Ampere A1 instances, behind Gunicorn/Nginx (or Traefik).
*   **Database:** Initially SQLite for development, migrating to PostgreSQL for production.
*   **Cloudflare:** Provides a crucial layer of security and performance optimization.

## Implementation Details

### Database Changes (Initial SQLite Schema)

1.  Create new `votes` table:

```sql
CREATE TABLE votes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    judge_id INTEGER NOT NULL,
    ip_address TEXT NOT NULL,
    vote_type TEXT NOT NULL CHECK (vote_type IN ('corrupt', 'not_corrupt')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    browser_fingerprint TEXT NOT NULL,
    FOREIGN KEY (judge_id) REFERENCES judges(id)
);

-- Index for efficient vote counting and rate limiting
CREATE INDEX idx_votes_ip_judge ON votes(ip_address, judge_id);
CREATE INDEX idx_votes_created_at ON votes(created_at);
CREATE INDEX idx_votes_fingerprint ON votes(browser_fingerprint);
```

### Frontend Changes

1.  Update `index.html`:
    *   Add new "Not Corrupt" section below undecided
    *   Add voting buttons to each judge card
    *   Add vote counts and ratio display
    *   Add tooltips for voting rules

2.  Update `static/styles.css`:
    *   Style new "Not Corrupt" section (matching existing sections)
    *   Style voting buttons and counters
    *   Add voting feedback animations
    *   Add vote ratio visualizations
    * Style notification

3.  Update `static/script.js`:
    *   Add vote submission functionality (with HMAC, fingerprinting, and proof-of-work)
    *   Add vote count updates
    *   Implement rate limiting feedback
    *   Add section reordering based on vote status
    * Implement browser fingerprinting using fingerprintjs2
    * Implement client-side proof-of-work

### Backend Changes (Main App - `app.py`)

1.  New API Endpoints:
    *   POST `/vote/<judge_id>` - Submit a vote (protected by HMAC, rate limiting, fingerprinting, and proof-of-work)
    *   GET `/judges` - Update to include vote counts and status

2.  Vote Processing Logic:
    *   Implement 5:1 ratio checking
    *   Status updates based on vote ratios
    *   Rate limiting enforcement (using `CF-Connecting-IP`)
    *   IP whitelist checking (stored in database)
    *   Browser fingerprint validation
    *   Proof-of-work verification

### Backend Changes (Admin App - `admin_app/app.py`)

1.  Separate admin routes from main `app.py`.
2.  Implement login functionality.
3.  Implement admin-specific functionality (viewing submissions, approving/rejecting, managing judges, viewing logs).

### Anti-Spam Measures

1.  **Rate Limiting:**
    *   Limit votes per judge per IP address per day.
    *   Limit submissions per IP address and fingerprint per minute.
    *   Leverage Cloudflare's rate limiting capabilities.
    *   Use `CF-Connecting-IP` header to get the real client IP.

2.  **Browser Fingerprinting:**
    *   Use `fingerprintjs2` to generate browser fingerprints.
    *   Store hashed fingerprints with votes and submissions.
    *   Use fingerprint (along with IP) for rate limiting.

3.  **Proof of Work:**
    *   Require client-side proof-of-work for votes and submissions.
    *   Adjust difficulty dynamically based on server load.

4.  **Honeypot Fields:**
    *   Include hidden form fields to detect bots.

5.  **HMAC Authentication:**
    *   Protect API endpoints with HMAC signatures.

6.  **Geographic Analysis:**
    *   Utilize IP geolocation data (fetched asynchronously).
    *   Flag suspicious voting patterns from specific regions.

7. **Cloudflare Security Features:**
    * Utilize Cloudflare's built in bot protection, DDoS protection, and firewall rules.