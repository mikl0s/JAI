# Judicial Accountability Initiative Codebase Overview

## Project Structure

```
/
├── app.py                      # Main Flask application
├── static/                     # Static assets
│   ├── admin_style.css        # Admin interface styling
│   ├── styles.css             # Main site styling
│   ├── script.js              # Frontend JavaScript
│   ├── Gotham-Black.otf       # Font files
│   └── old_stamper.ttf
├── templates/                  # HTML templates
│   ├── admin_header.html      # Admin navigation header
│   ├── admin_logs.html        # Admin logs page
│   ├── admin_pending.html     # Pending submissions review
│   ├── admin.html             # Main admin dashboard
│   ├── index.html             # Public frontend
│   └── login.html             # Admin login page
├── create_tables.py           # Database initialization
├── create_submissions_table.py # Submissions table setup
├── initialize_db.py           # Database seeding
├── ip_geolocation.py          # IP geolocation handling
└── populate_ip_geolocation.py # Geolocation data population
```

## Database Schema

### Current Tables

1. `judges`
```sql
CREATE TABLE judges (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    job_position TEXT NOT NULL,
    ruling TEXT NOT NULL,
    link TEXT NOT NULL,
    x_link TEXT,
    confirmed INTEGER DEFAULT 0,
    displayed INTEGER DEFAULT 1
);
```

2. `submissions`
```sql
CREATE TABLE submissions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    ruling TEXT NOT NULL,
    link TEXT NOT NULL,
    x_link TEXT,
    status TEXT DEFAULT 'pending',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT NOT NULL
);
```

3. `admin_logs`
```sql
CREATE TABLE admin_logs (
    id INTEGER PRIMARY KEY,
    admin_username TEXT NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

4. `ip_whitelist`
```sql
CREATE TABLE ip_whitelist (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL,
    reason TEXT NOT NULL,
    expiry TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ip_address)
);
```

5. `ip_geolocation`
```sql
CREATE TABLE ip_geolocation (
    id INTEGER PRIMARY KEY,
    ip_address TEXT NOT NULL UNIQUE,
    hostname TEXT,
    continent_code TEXT,
    continent_name TEXT,
    country_code2 TEXT,
    country_code3 TEXT,
    country_name TEXT,
    country_capital TEXT,
    state_prov TEXT,
    state_code TEXT,
    city TEXT,
    zipcode TEXT,
    latitude TEXT,
    longitude TEXT,
    is_eu BOOLEAN,
    country_flag TEXT,
    country_emoji TEXT,
    isp TEXT,
    organization TEXT,
    timezone_name TEXT,
    timezone_offset INTEGER,
    currency_code TEXT,
    currency_symbol TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ip_geolocation_ip ON ip_geolocation(ip_address);
```

## Key Components

### Backend (Flask)

1. **Authentication System**
   - Simple admin login system (username/password)
   - Session-based authentication
   - IP whitelisting for admin actions

2. **Rate Limiting**
   - IP-based submission limiting (10-minute cooldown)
   - Whitelist system for trusted IPs
   - Automatic admin IP whitelisting on login

3. **Judge Management**
   - Public submission of judges
   - Admin review system
   - Status tracking (confirmed/unconfirmed)
   - Display toggle functionality

4. **IP Geolocation**
   - Automatic IP geolocation caching
   - Country flag display in admin interface
   - Geographic submission tracking

### Frontend

1. **Public Interface (`index.html`)**
   - Two-section display (Confirmed/Undecided judges)
   - Floating submission button
   - Modal form for new submissions
   - Responsive design

2. **Admin Interface**
   - Dashboard with submission statistics
   - Pending submissions review
   - Judge management interface
   - Action logging system
   - Geographic submission visualization

3. **Styling**
   - Custom fonts (Gotham Black, Old Stamper)
   - Responsive design
   - Admin-specific styling
   - Modal animations

### JavaScript Functionality

1. **Public Frontend**
   - Dynamic judge list loading
   - Modal handling
   - Form submission with validation
   - Rate limit feedback

2. **Admin Frontend**
   - Judge status updates
   - Submission processing
   - Interactive statistics
   - Geographic data display

## API Endpoints

1. **Public Endpoints**
   - GET `/` - Main page
   - GET `/judges` - Judge list (confirmed/undecided)
   - POST `/submit-judge` - New judge submission

2. **Admin Endpoints**
   - GET `/admin` - Admin dashboard
   - GET `/admin/pending` - Pending submissions
   - GET `/admin/logs` - Admin action logs
   - POST `/admin/submission/<id>/<action>` - Handle submissions
   - POST `/admin/add` - Add new judge
   - POST `/admin/update/<id>` - Update judge
   - POST `/admin/disable/<id>` - Disable judge

## Security Features

1. **Rate Limiting**
   - Submission cooldown periods
   - IP-based tracking
   - Whitelist system

2. **Admin Security**
   - Session-based authentication
   - IP whitelisting
   - Action logging
   - Geographic tracking

3. **Input Validation**
   - Form validation
   - URL validation
   - Status validation

## Development Workflow

1. **Database Updates**
   - Use create_tables.py for schema changes
   - Use initialize_db.py for seeding
   - Manual SQLite operations for maintenance

2. **Feature Addition**
   - Update app.py for new endpoints
   - Add templates to templates/
   - Update static files as needed
   - Add database migrations when required

3. **Testing**
   - Manual testing through interface
   - Rate limit testing
   - Admin functionality verification
   - Geographic feature testing