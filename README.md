# KanMind

![KanMind Logo](/frontend/assets/icons/logo_icon.svg)  
*A simple kanban board application with a Django REST API and a vanilla-JavaScript frontend.*

KanMind is designed as a teaching project to help students at Developer Akademie learn full-stack development. The backend is built with Django REST Framework (DRF), and the frontend is a lightweight vanilla JavaScript application (no frameworks).

---

## Project Overview

KanMind consists of two main parts:
1. **Backend (Django + DRF)**  
   - Provides a token-based REST API (register/login, boards, tasks, comments).  
   - Implements all business logic and data storage (SQLite by default).  

2. **Frontend (Vanilla JavaScript)**  
   - Single-page application (SPA) that consumes the DRF API.  
   - Implements basic Kanban-style UI: listing boards, tasks, adding comments.  
   - Pure JavaScript, HTML & CSS; no frameworks like React or Angular.

> **Intent:**  
> This project targets Developer Akademie students who already have some backend experience. The goal is to show how an API is constructed and then how a minimal frontend can integrate with it.

---

## Getting Started

### Backend Setup

1. **Navigate to the backend directory**  
   cd backend

2. **Create a virtuel environment**
    python3 -m venv env
    source env/bin/activate   # macOS/Linux
    # or
    .\env\Scripts\Activate.ps1  # Windows PowerShell

3. **Install Python dependencies**
    pip install -r requirements.txt

4. **Optional: Create a superuser**
    python manage.py createsuperuser

5. **Run the backend server**
    python manage.py runserver

    The API will be available at "http://127.0.0.1:8000"

---

### Frontend Setup

1. **Open the frontend folder**  
    In your code editor (e.g., VS Code), open the frontend directory.

2. **Start a local static server**
    - Right-click on index.html (inside frontend) and select "Open with Live Server" if you have VS Code Live Server installed
    - The frontend will run at "http://127.0.0.1:5500/"

---