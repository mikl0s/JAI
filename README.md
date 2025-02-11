# JAI (Judicial Accountability Initiative)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/mikl0s/JAI/graphs/commit-activity)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A web application for tracking and managing judicial accountability through community submissions, featuring advanced IP geolocation tracking and administrative controls.

## 🚀 Features

- **Secure Authentication System**: Admin login portal with session management
- **Submission Management**: Process and track judicial submissions
- **IP Geolocation**: Track and verify submission origins
- **Administrative Dashboard**: 
  - Pending submissions review
  - Submission logs
  - Real-time status updates
- **Custom Styling**: Modern UI with custom fonts and responsive design

## 🛠️ Tech Stack

- **Backend**: Python/Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Styling**: Custom CSS with Gotham and Old Stamper fonts

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## 🔧 Installation

1. Clone the repository:
```bash
git clone git@github.com:mikl0s/JAI.git
cd JAI
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python initialize_db.py
```

5. Create required tables:
```bash
python create_tables.py
```

## 🚦 Usage

1. Start the Flask application:
```bash
python app.py
```

2. Access the application:
- Main interface: `http://localhost:5000`
- Admin panel: `http://localhost:5000/admin`

## 🔐 Environment Variables

Create a `.env.local` file with the following variables:
```
FLASK_SECRET_KEY=your_secret_key
ADMIN_USERNAME=your_admin_username
ADMIN_PASSWORD=your_admin_password
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to all contributors who have helped shape JAI
- Special thanks to the Flask community for excellent documentation

## 📞 Contact

Project Link: [https://github.com/mikl0s/JAI](https://github.com/mikl0s/JAI)