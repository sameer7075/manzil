# MANZIL – Digital Real Estate Platform

## Project Overview
MANZIL is a web-based platform for buying, selling, and renting properties. Users can browse property listings, filter searches by location, price, type, and other criteria, and communicate directly with property owners or agents. The platform simplifies property transactions while providing a smooth and user-friendly experience.

---

## Features
- User authentication (register, login, logout)
- Add, edit, and delete property listings
- Advanced search and filtering of properties
- Detailed property pages with images and descriptions
- Contact system for buyers/renters and sellers/agents
- Responsive design for desktop and mobile
- Admin panel for managing users and listings (optional)

---

## Tech Stack
- **Backend:** Flask (Python), SQLAlchemy ORM
- **Frontend:** HTML, CSS, JavaScript
- **Database:** SQLite

---

## Installation
1. **Clone the repository**
git clone https://github.com/sameer7075/manzil.git
cd manzil

2. **Create a virtual environment**
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate

3. **Install dependencies**
pip install -r requirements.txt

4. **Set environment variables**
export FLASK_APP=app.py
export FLASK_ENV=development
# Windows PowerShell
$env:FLASK_APP = "app.py"
$env:FLASK_ENV = "development"

5. **Run the application**
flask run
Access the platform at http://127.0.0.1:5000

---

## Usage
- Register or login to your account
- Browse available property listings
- Use filters to refine search results
- Add a new listing if you’re a seller

---

## Contributing

Contributions are welcome! To contribute

1. **Fork the repository**
2. **Create a new branch (git checkout -b feature-name)**
3. **Commit your changes (git commit -m "Add feature")**
4. **Push to your branch (git push origin feature-name)**
5. **Open a Pull Request**