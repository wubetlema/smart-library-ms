# Smart Library Management System

A full-featured library management web application built with **Django 4.2**, **MySQL**, and **Bootstrap 5**.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Django](https://img.shields.io/badge/Django-4.2-green?logo=django)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5-purple?logo=bootstrap)

---

## Features

### Three Role System
| Feature | Student | Librarian | Admin |
|---|---|---|---|
| Browse & search books | ✅ | ✅ | ✅ |
| Borrow books (max 3) | ✅ | ✅ | ✅ |
| Reserve unavailable books | ✅ | ✅ | ✅ |
| Rate & review books | ✅ | — | — |
| View borrowing history | ✅ | ✅ | ✅ |
| Add / edit books | — | ✅ | ✅ |
| Manage members | — | ✅ | ✅ |
| Process returns & fines | — | ✅ | ✅ |
| Mark fines as paid | — | ✅ | ✅ |
| Export CSV / PDF reports | — | ✅ | ✅ |
| Admin dashboard & charts | — | ✅ | ✅ |
| Manage all users & roles | — | — | ✅ |
| Approve / deactivate accounts | — | — | ✅ |
| Data backup | — | — | ✅ |
| Activity log | — | — | ✅ |

### Highlights
- Book catalog with search by title, author, category, availability
- Borrow & return workflow with **ETB 2/day** fine calculation
- Book reservations with email notification when available
- Student borrow limit enforcement (max 3 books)
- Book ratings & reviews (students who have borrowed)
- PDF book reader & online read URL support
- Admin dashboard with Chart.js (monthly trends, category stats, top authors)
- Reports with PDF & CSV export (ReportLab)
- Activity log & data backup via management commands
- Notification system (bell dropdown + notifications page)
- QR codes for books and member library cards
- Password reset via email
- Login rate limiting with 15-minute lockout
- Dark mode, responsive design (Bootstrap 5)

---

## Tech Stack

- **Backend:** Django 4.2, Python 3.10+
- **Database:** MySQL (via XAMPP)
- **Frontend:** Bootstrap 5, Chart.js, Bootstrap Icons
- **PDF Export:** ReportLab
- **QR Codes:** qrcode
- **Image handling:** Pillow

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- XAMPP (MySQL/MariaDB)
- Git

### 2. Clone & setup
```bash
git clone https://github.com/wubetlema/smart-library-ms.git
cd smart-library-ms
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r library_system/requirements.txt
```

### 3. Configure environment
```bash
cp library_system/.env.example library_system/.env
```

Edit `library_system/.env`:
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

### 6. Run the server
```bash
python manage.py runserver
```

Open: http://127.0.0.1:8000/

### Default admin account
| Username | Password |
|---|---|
| admin | Admin1234 |

---

## Email Configuration

By default, emails print to the console. To send real emails, add to `.env`:
```
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password
```

---

## Project Structure

```
library_system/
├── accounts/       # CustomUser, roles, auth, approval
├── books/          # Book, Category, BookReview
├── borrowing/      # BorrowRecord, Reservation, reports
├── activity/       # ActivityLog, Notification, middleware
├── templates/      # Global templates (404, 500, about, contact)
├── .env.example
└── manage.py
```

---

## Screenshots

> Coming soon

---

## License

MIT
