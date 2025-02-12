# Judge Voting System Implementation Plan

## Overview
Transform the current admin-based corruption marking system into a community-driven voting system where judges are categorized based on user votes into three sections: Corrupt, Undecided, and Not Corrupt.

## Version Tracking

Current Version: 1.0

### Updates
- [ ] Update 1.0: Initial voting system implementation
    - [x] Database schema changes
    - [x] Basic backend voting endpoints
    - [x] Basic frontend voting UI
    - [x] Rate limiting implementation

- [ ] Update 1.1: Anti-spam measures
    - [ ] Browser fingerprinting
    - [ ] Proof of work system
    - [ ] Honeypot fields
    - [ ] Geographic analysis
    - [ ] Trusted user system

- [ ] Update 1.2: Appeal system
    - [ ] Appeals database schema
    - [ ] Appeal button and modal UI
    - [ ] Backend appeal handling
    - [ ] Admin appeal review interface

- [ ] Update 1.3: Admin monitoring
    - [ ] Suspicious voting patterns page
    - [ ] Geographic vote distribution
    - [ ] Automated alerts system
    - [ ] Enhanced admin dashboard

Each update will be marked complete when all its sub-tasks are implemented and tested. The current working update is always the first unchecked update in the list.

## Database Changes

1. Create new `votes` table:
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

## Frontend Changes

1. Update `index.html`:
   - Add new "Not Corrupt" section below undecided
   - Add voting buttons to each judge card
   - Add vote counts and ratio display
   - Add tooltips for voting rules
   - Add floating appeal button (bottom left corner)
   - Add appeal submission modal

2. Update `static/styles.css`:
   - Style new "Not Corrupt" section (matching existing sections)
   - Style voting buttons and counters
   - Add voting feedback animations
   - Style appeal button and modal
   - Add vote ratio visualizations

3. Update `static/script.js`:
   - Add vote submission functionality
   - Add vote count updates
   - Implement rate limiting feedback
   - Add section reordering based on vote status
   - Add appeal submission handling
   - Implement browser fingerprinting
   - Add rate limiting for submit/appeal buttons

## Backend Changes

1. New API Endpoints:
   - POST `/vote/<judge_id>` - Submit a vote
   - GET `/judges` - Update to include vote counts and status
   - POST `/appeal/<judge_id>` - Submit an appeal
   - GET `/admin/suspicious` - List suspicious voting patterns

2. Vote Processing Logic:
   - Implement 5:1 ratio checking
   - Status updates based on vote ratios
   - Rate limiting enforcement
   - IP whitelist checking
   - Browser fingerprint validation

3. Background Tasks:
   - Periodic vote ratio calculation
   - Clean up expired votes (older than 24 hours for non-whitelisted IPs)
   - Monitor geographic voting patterns
   - Generate automated alerts for suspicious patterns

4. Admin Interface Updates:
   - Add suspicious voting patterns page (similar to submissions page)
   - Add appeal review interface
   - Add geographic vote distribution visualization
   - Add automated alert notifications

## Anti-Spam Measures

### Current Implementation
1. Rate Limiting:
   - 1 vote per judge per day (non-whitelisted IPs)
   - 1 vote per minute across all judges
   - 1 submission/appeal per minute per IP + fingerprint
   - Utilize existing IP whitelist system

### Additional Anti-Spam Measures

1. Browser Fingerprinting:
   - Implement lightweight browser fingerprinting
   - Store hashed fingerprints with votes
   - Use combination of IP + fingerprint for rate limiting

2. Proof of Work:
   - Implement client-side proof of work before vote submission
   - Require small computational task completion
   - Adjustable difficulty based on server load

3. Honeypot Fields:
   - Add hidden form fields
   - Monitor submission patterns
   - Auto-blacklist IPs that fill honeypot fields

4. Geographic Analysis:
   - Utilize existing IP geolocation data
   - Flag suspicious voting patterns from same regions
   - Implement regional vote weighting

5. Trusted User System:
   - Track user reliability over time
   - Award "trusted" status based on voting history
   - Give slightly more weight to trusted user votes

## Implementation Order

1. Database Setup:
   - Create votes table ✓
   - Add necessary indexes ✓

2. Backend Implementation:
   - Basic vote submission endpoint
   - Rate limiting logic
   - Vote counting and status updates
   - Geographic monitoring system

3. Frontend Updates:
   - New section UI
   - Voting buttons and counters
   - Basic feedback system

4. Anti-Spam Measures:
   - Implement all anti-spam measures
   - Add browser fingerprinting
   - Deploy honeypot fields
   - Set up geographic analysis

5. Enhanced Features:
   - Trusted user system
   - Geographic analysis
   - Automated alert system

6. Testing & Monitoring:
   - Load testing
   - Spam prevention testing
   - Vote manipulation testing
   - Geographic pattern testing

## Implementation Decisions

1. Anti-spam measures: All suggested measures will be implemented as part of the initial release.

2. Vote display: Both exact counts and ratios will be shown to users.

3. Manual review system: Implemented in admin interface, following the style of the submissions page.

4. Rate limiting: Submit new judge and appeal judge buttons use the same rate limiting (once per minute per IP + fingerprint).