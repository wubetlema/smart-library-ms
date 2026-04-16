# Smart Library Management System

A full-stack library management system built with Django 4.2, MySQL, and Bootstrap 5.

## Features

- **3 roles**: Admin, Librarian, Student
- Book catalog with search by title, author, category
- Borrow & return workflow with ETB 5/day fine calculation
- Book reservations for unavailable titles
- Student borrow limit (max 3 books)
- Book ratings & reviews
- Admin dashboard with Chart.js charts
- Reports with PDF & CSV export
- Activity log & data backup
- Dark mode, responsive design
- Password reset via email

---

## Quick Start

### 1. Prerequisites

- Python 3.10+
- XAMPP (MySQL/MariaDB)
- Git

### 2. Clone & setup

```bash
git clone <repo-url>
cd librarypy
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r library_system/requirements.txt
```

### 3. Configure environment

```bash
cp library_system/.env.example library_system/.env
```

Edit `.env` with your values:

```
SECRET_KEY=your-random-secret-key
DEBUG=True
DB_NAME=library_db
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 4. Create database

Start XAMPP MySQL, then in phpMyAdmin create a database named `library_db`.

### 5. Run migrations

```bash
cd library_system
python manage.py migrate
```

### 6. Create admin account

```bash
python manage.py createsuperuser
```

Or use the seeded admin: username `admin`, password `Admin1234`.

### 7. Run the server

```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

---

## Email Configuration

By default, emails print to the console (development mode).

To send real emails, add to your `.env`:

```
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

**Gmail App Password setup:**
1. Go to myaccount.google.com/apppasswords
2. Generate a password for "Mail"
3. Paste it as `EMAIL_HOST_PASSWORD`

---

## Automatic Due Reminders

To send daily email reminders automatically, run `setup_scheduler.bat` as Administrator once:

```
library_system\setup_scheduler.bat
```

This registers a Windows Task Scheduler job that runs every day at 8:00 AM.

To trigger manually:
```bash
python manage.py send_due_reminders
```

---

## Running Tests

```bash
python manage.py test                    # all tests
python manage.py test borrowing          # borrowing tests only
python manage.py test books              # books tests only
python manage.py test accounts           # accounts tests only
```

---

## Project Structure

```
library_system/
├── accounts/       # CustomUser, roles, auth
├── books/          # Book, Category, BookReview
├── borrowing/      # BorrowRecord, Reservation, views
├── activity/       # ActivityLog, middleware
├── templates/      # Global templates (404, 500, about)
├── .env.example    # Environment variable template
├── .gitignore
└── manage.py
```

---

## API

This project is server-rendered (Django templates). There is no REST API.
For future extensibility, Django REST Framework can be added to expose endpoints for a mobile app or third-party integration.

---

## License

MIT
