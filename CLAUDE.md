# JAI (Judicial Accountability Initiative) Development Guide

## Commands
- **Run Application**: `./start.sh` (starts both main app on port 5000 and admin app on port 5001)
- **Run Main App Only**: `flask run --port=5000`
- **Run Admin App Only**: `cd admin_app && flask run --port=5001`
- **Initialize Database**: `python initialize_db.py && python create_tables.py`
- **Populate Geolocation Data**: `python populate_ip_geolocation.py`
- **Install Dependencies**: `pip install -r requirements.txt`

## Code Style
- **Formatting**: Follow Black code style
- **Import Order**: Standard library, third-party, local modules (grouped and alphabetized)
- **Docstrings**: Use descriptive docstrings for functions with non-obvious behavior
- **Error Handling**: Use try/except blocks with specific exceptions, log errors appropriately
- **Naming**: snake_case for variables/functions, PascalCase for classes
- **Security**: Never hardcode secrets, use environment variables
- **Types**: Use type hints for function parameters and return values
- **Comments**: Add TODO comments for temporary solutions that need improvement

## Database
- Update database schema in create_tables.py and run initialize_db.py for migrations