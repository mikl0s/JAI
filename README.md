# JAI (Judicial Accountability Initiative)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/mikl0s/JAI/graphs/commit-activity)

A comprehensive web application for tracking judicial accountability through community submissions and voting, featuring advanced IP geolocation tracking, rate limiting, and administrative controls.

## 🚀 Features

- **Secure Authentication System**: Admin login portal with session management and IP whitelisting
- **Submission Management**: Process and track judicial submissions with status tracking
- **Voting System**: Community voting on judicial accountability with rate limiting
- **IP Geolocation**: Track and verify submission origins with detailed geolocation data
- **Rate Limiting**: IP-based submission and voting rate controls
- **Administrative Dashboard**:
  - Pending submissions review
  - Voting statistics and patterns
  - Submission logs with geolocation data
  - Real-time status updates
  - Judge management interface
- **Custom Styling**: Modern UI with custom fonts and responsive design
- **Security Features**:
  - Browser fingerprint validation
  - Input validation and sanitization
  - Action logging and monitoring

## 📦 Project Structure

JAI consists of two separate applications:

1. **Main Application**: Public-facing website where users can view judges, vote, and submit new judges
   - Located in the project root directory
   - Runs on port 5000 by default

2. **Admin Application**: Administrative interface for managing judges, reviewing submissions, and monitoring system activity
   - Located in the `admin_app` directory
   - Runs on port 5001 by default
   - Requires authentication to access

## 🛠️ Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Authentication**: Flask-Login with session management
- **Styling**: Custom CSS with Gotham and Old Stamper fonts
- **Security**: Flask-Talisman, CSRF protection
- **Geolocation**: IP-based geolocation with IPGeolocation API
- **Rate Limiting**: Custom implementation with IP tracking

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- PostgreSQL
- Screen (for running services in the background)
- IPGeolocation API account and key (https://ipgeolocation.io/)

## 🔧 Installation

1. Clone the repository:
```bash
git clone git@github.com:mikl0s/JAI.git
cd JAI
```

2. Set up the main application:
```bash
# Create and activate a virtual environment for the main app
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

3. Set up the admin application:
```bash
# Navigate to the admin app directory
cd admin_app

# Create and activate a virtual environment for the admin app
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
cd ..
```

4. Configure environment variables:
   - Copy `.env.example` to `.env.local` in the project root
   - Copy `admin_app/.env.example` to `admin_app/.env.local`
   - Update both files with your PostgreSQL connection details and IPGeolocation API key

5. Database setup:
```bash
# Activate the main app virtual environment
source venv/bin/activate

# Run the database initialization script
python init_db.py

# Deactivate when done
deactivate
```

## 🚦 Running the Applications

Use the `services.sh` script to manage both applications:

```bash
# Make the script executable
chmod +x services.sh

# For help and available commands
./services.sh --help
```

## 📱 Accessing the Applications

- Main interface: `http://localhost:5000`
- Admin panel: `http://localhost:5001`

## 🔐 Security Features

- **Rate Limiting**:
  - Submission cooldown periods
  - Vote rate limiting (1 vote per judge per day)
- **IP Geolocation**:
  - Track submission origins
  - Identify suspicious voting patterns
- **Admin Security**:
  - IP whitelist for admin access
  - Secure session management
  - Activity logging