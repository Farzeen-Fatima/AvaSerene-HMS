# AvaSerene-HMS

A fully native PostgreSQL and PyQt5 desktop application for hospital management. It separates administrative controls from worker operations, featuring secure role-based access, real-time analytics, and automated PDF slip generation.

## Features

* **Role-Based Access Control:** Secure `bcrypt` password hashing for Admin and Worker dashboards.
* **Admin Dashboard:** Monitor hospital analytics, manage staff credentials, and track patient volumes.
* **Worker Dashboard:** Register patients, manage live queues, and update consultation statuses.
* **Automated PDF Receipts:** Generates pixel-perfect 80mm thermal slips using `reportlab`.
* **Robust Database Integrity:** Engineered with PostgreSQL triggers to ensure data validation (e.g., age limits, fee constraints) and automated audit logging for all CRUD operations.

## Tech Stack

* **Language:** Python 3
* **GUI Framework:** PyQt5
* **Database:** PostgreSQL (via `psycopg2`)
* **Security:** `bcrypt`
* **Document Generation:** `reportlab`

##  Screenshots

![Admin Dashboard](assets/admin_dashboard.png)
![Worker Queue](assets/worker_queue.png)

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/yourusername/MedQueue.git](https://github.com/yourusername/M.git)
   cd MedQueue
