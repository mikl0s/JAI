# JAI (Judicial Accountability Initiative)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/mikl0s/JAI/graphs/commit-activity)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
- **Service Management**: Unified service management script for both main and admin applications

## 🛠️ Tech Stack

- **Backend**: Python/Flask
- **Database**: PostgreSQL with advanced indexing
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Authentication**: Flask-Login with session management
- **Styling**: Custom CSS with Gotham and Old Stamper fonts
- **Security**: Flask-Talisman, CSRF protection
- **Geolocation**: IP-based geolocation with caching
- **Rate Limiting**: Custom implementation with IP tracking
- **Caching**: Flask-Caching for improved performance

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- PostgreSQL (running externally)

## 🔧 Installation

1. Clone the repository:
```bash
git clone git@github.com:mikl0s/JAI.git
cd JAI
```

2. Set up environment variables:
Create `.env` files for both main and admin applications with the following variables:

For main app (`.env`):
```
FLASK_SECRET_KEY=your_secret_key
DB_NAME=jai_db
DB_USER=jai
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

For admin app (`admin_app/.env`):
```
FLASK_SECRET_KEY=your_admin_secret_key
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
DB_NAME=jai_db
DB_USER=jai
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

3. Set up virtual environments and install dependencies using the services script:
```bash
./services.sh setup
```

4. Initialize the PostgreSQL database:
```bash
python migrate_to_postgres.py
```

## 🚦 Usage

### Service Management

The project includes a comprehensive `services.sh` script to manage both the main and admin applications:

```bash
# Start both applications
./services.sh start

# Start only the main application
./services.sh start main

# Start only the admin application
./services.sh start admin

# Stop all running applications
./services.sh stop

# Restart all applications
./services.sh restart

# Check status of running applications
./services.sh status

# Set up virtual environments and install dependencies
./services.sh setup

# Display help information
./services.sh help
```

Both applications run in debug mode during development, which enables automatic reloading when code changes are detected.

### Accessing the Applications

- Main interface: `http://localhost:5000`
- Admin panel: `http://localhost:5001`

### Development Workflow

- Database migrations: Use PostgreSQL migration scripts
- Testing: Manual testing through interface and database verification
- Deployment: Ensure proper security configurations and environment variables

## 🔐 Security Features

- **Rate Limiting**:
  - Submission cooldown periods
  - Vote rate limiting (1 vote per judge per day)
  - IP-based tracking
  - Whitelist system
  - Browser fingerprint validation

- **Admin Security**:
  - Session-based authentication
  - IP whitelisting
  - Action logging
  - Geographic tracking
  - Vote pattern monitoring

- **Input Validation**:
  - Form validation
  - URL validation
  - Status validation
  - Vote validation

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Before contributing, please:
- Review the codebase documentation in codebase.md
- Ensure your changes follow the existing security patterns
- Include appropriate tests and documentation updates
- Verify database schema compatibility

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape JAI
- Special thanks to the Flask community for excellent documentation
- Inspiration from judicial accountability initiatives worldwide

## 📞 Contact

Project Link: [https://github.com/mikl0s/JAI](https://github.com/mikl0s/JAI)
Issue Tracker: [https://github.com/mikl0s/JAI/issues](https://github.com/mikl0s/JAI/issues)