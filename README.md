# Task_Managment_API

A RESTful API for managing personal tasks.  
Built with **Django REST Framework**, **JWT Authentication**, **Celery**, and **Redis**.  
Features user registration/login, task CRUD, filtering, search, task sharing, and due-date email reminders.

---

## Features

- **User Authentication** (Register & Login with JWT tokens)
- **Task CRUD** (Create, Read, Update, Delete)
- **Task Filtering & Search**  
  - Filter by completion status and due date
  - Search by title
- **Task Sharing** (share tasks with other users)
- **Email Notifications**  
  - Celery task sends reminders for tasks due within 24 hours
- **Rate Limiting**  
  - 100 requests/day per user
- **Interactive API Documentation** with Swagger UI (drf-spectacular)

---

## Tech Stack

- **Backend:** Django, Django REST Framework
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Asynchronous Tasks:** Celery + Redis
- **API Documentation:** drf-spectacular (Swagger UI)
- **Database:** PostgreSQL
- **Containerization:** Docker (Redis)

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone git@github.com:ashfaqkhan509/Task_Managment_API.git
cd task_manager
