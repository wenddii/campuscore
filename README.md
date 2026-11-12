# CampusCore – University Student Registration System

A web-based student registration and management system designed for Bahir Dar University to digitize and simplify non-cafeteria student registration.

## Overview

CampusCore is a university registration platform built to replace manual, paper-based registration processes with a centralized digital system.

The platform allows students to submit their registration information online, while administrators can manage, review, and organize student records through a dedicated dashboard.

The goal is to make registration more efficient, reduce paperwork, minimize data-entry errors, and provide administrators with better control over registration activities.

## Key Features

### Student Portal
- Online student registration.
- Student information submission.
- Bank account information collection.
- Bank book image upload.
- Student registration status checking using student ID.
- Registration availability controlled by administrators.

### Administration Dashboard
- Centralized student record management.
- View and manage registered students.
- Filter students by department, academic year, and section.
- Search student records.
- View submitted bank book images.
- Registration status management.
- Ability to open and close registration.

### Data Management
- Structured student records.
- Organized registration information.
- Cloud-based database storage.
- Secure handling of uploaded documents.

## Technology Stack

- **Backend:** Python, Django
- **Frontend:** Django Templates, HTML, CSS, JavaScript
- **Database:** PostgreSQL (Neon)
- **Image Storage:** Cloudinary
- **Deployment:** Vercel
- **Environment Management:** Python dotenv

## System Architecture

CampusCore uses Django as its backend framework to handle registration logic, validation, administrative operations, and database communication.

PostgreSQL stores structured student information, while Cloudinary handles uploaded bank book images.

The application separates student-facing registration functionality from administrative management operations.

## Student Information

The registration system collects relevant student information, including:

- Student ID
- Full name
- Department
- Academic year
- Section
- Bank account number
- Bank book image

Input validation helps ensure submitted information follows the required university registration format.

## Getting Started

### 1. Clone the repository

```bash
git clone YOUR_REPOSITORY_URL
cd YOUR_PROJECT_DIRECTORY
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**
```bash
venv\Scripts\activate
```

**Linux/macOS**
```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and configure the required settings, including:

- Django secret key
- Database connection URL
- Cloudinary credentials
- Deployment configuration

Never commit sensitive credentials to version control.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Run the development server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in your browser.

## Project Goals

CampusCore was developed to address the challenges of manual university registration processes by providing:

- A more organized registration workflow.
- Reduced administrative workload.
- Better access to student registration records.
- Improved information management.
- A centralized platform for registration administration.

## Future Improvements

- Advanced registration analytics and reporting.
- Exportable student registration records.
- More comprehensive administrative access controls.
- Enhanced audit logging and activity tracking.

## License

This project was developed as a university-focused software solution. All rights reserved unless otherwise specified.

---

**CampusCore**

Digitizing University Registration.
