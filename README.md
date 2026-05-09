# MANZIL – Digital Real Estate Platform

## Project Overview
MANZIL is a web-based platform for buying, selling, and renting properties. Users can browse listings, filter searches by location, price, and type, view detailed property pages with images, and communicate with sellers or agents.

## Features
- User authentication (register, login, logout)
- Create, edit, and remove property listings with images
- Search and filtering by multiple criteria
- Messaging / contact between users and listers
- Admin views for managing listings and users
- Responsive UI for desktop and mobile

## Tech Stack
- **Backend:** Flask, SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite (default)

## Dependencies
The application uses the exact packages listed in `requirements.txt`.

- blinker==1.9.0
- click==8.3.0
- colorama==0.4.6
- Flask==3.1.2
- Flask-Login==0.6.3
- Flask-SQLAlchemy==3.1.1
- greenlet==3.2.4
- itsdangerous==2.2.0
- Jinja2==3.1.6
- MarkupSafe==3.0.3
- passlib==1.7.4
- SQLAlchemy==2.0.44
- typing_extensions==4.15.0
- Werkzeug==3.1.3

Install with:

```bash
python -m venv venv
# macOS / Linux
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configuration
- The repository includes an `instance/` folder for local configuration. Create or update `instance/config.py` (or set environment variables) to provide secrets and database URLs.
- Typical environment variables used by the app:
	- `FLASK_APP=app.py`
	- `FLASK_ENV=development` (for local development)
	- `DATABASE_URL` (optional; defaults to SQLite if unset)

On Windows PowerShell:

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"
flask run
```

## Database & Migrations
- This repo includes a `migrations/` folder (Alembic). If you need to run or update migrations, install Alembic and run:

```bash
pip install alembic
alembic upgrade head
```

If you prefer Flask-Migrate workflows, you can adapt the migration steps accordingly.

## Running the App
1. Activate your virtual environment
2. Install dependencies (`pip install -r requirements.txt`)
3. Set environment variables (see Configuration)
4. Initialize or migrate the database if needed
5. Start the server: `flask run`

Access the app at: http://127.0.0.1:5000

## Team & Credits
- Project Lead - Sameer Ahmed: https://github.com/sameer7075
- Muhammad Subhan: https://github.com/Denarzai
- Affaf Shahid: https://github.com/Affaf-Shahid

This project was developed by a 3-person team as part of a Software Engineering university course.

## Team Responsibilities

### Sameer Ahmed (Team Lead)
- Designed overall system architecture
- Implemented backend using Flask
- Developed authentication system (Flask-Login)
- Set up database models and relationships (SQLAlchemy)
- Managed project structure and integration
- Coordinated tasks and ensured feature completion

### Muhammad Subhan
- Assisted in frontend development
- Worked on UI components and styling
- Supported feature integration

### Affaf Shahid
- Assisted in frontend and testing
- Helped with UI improvements and bug fixes
- Supported documentation and project refinement

## Contributing
Contributions are welcome. Typical workflow:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m "Add feature"`
4. Push and open a pull request

