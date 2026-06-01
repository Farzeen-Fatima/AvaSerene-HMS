# AvaSerene-HMS

A desktop-based Hospital Management System built with Python, PyQt5, and PostgreSQL. The application streamlines hospital operations through secure role-based access, patient management, reporting, and automated receipt generation.

## Features

- Secure role-based authentication using `bcrypt`
- Separate Admin and Worker dashboards
- Patient registration and queue management
- Real-time hospital analytics and statistics
- Automated PDF thermal receipt generation with `reportlab`
- CSV export for daily and monthly reports
- PostgreSQL triggers for validation and audit logging

## Tech Stack

- **Language:** Python 3
- **GUI Framework:** PyQt5
- **Database:** PostgreSQL (`psycopg2`)
- **Security:** bcrypt
- **PDF Generation:** reportlab

## Screenshots

### Admin Dashboard
<img src="assets/admin_dashboard.png" alt="Admin Dashboard" width="700">

### Worker Dashboard
<img src="assets/worker_dashboard.png" alt="Worker Dashboard" width="700">

### Patient Registration
<img src="assets/register_patient.png" alt="Patient Registration" width="300">

## Installation

### Clone the Repository

```bash
git clone https://github.com/Farzeen-Fatima/AvaSerene-HMS.git
cd AvaSerene-HMS
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Setup Database

Create a PostgreSQL database and run the schema file:

```bash
psql -U postgres -d ava_serene_hospital -f ava_serene_hospital.sql
```

### Run the Application

```bash
python login_window.py
```

## Key Highlights

- Designed a normalized PostgreSQL database with triggers and audit logging.
- Implemented secure authentication and role-based authorization.
- Built a complete desktop GUI using PyQt5.
- Developed reporting and PDF receipt generation functionality.
