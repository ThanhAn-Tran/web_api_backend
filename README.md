# 🛒 Online Shop API Backend

This is the backend for an AI-powered e-commerce chatbot system, built with FastAPI and SQL Server. It provides RESTful APIs for user management, product catalog, cart, orders, payments, and a context-aware AI chatbot.

---

## 🚀 Deployment Guide

### 1. Prerequisites
- **Python 3.10+**
- **SQL Server** (local or remote)
- **pip** (Python package manager)

### 2. Clone the Repository
```
git clone <your-repo-link>
cd web_api_backend
```

> **Note:** This backend is designed to work with a Flutter frontend. You will need to update the frontend link in this README after pushing both projects to GitHub.

### 3. Install Dependencies
```
pip install -r requirements.txt
```

### 4. Configure Environment
- Edit `app/config.py`:
  - Set your `DATABASE_CONFIG` for SQL Server.
  - Set your `OPENAI_API_KEY` (get one from https://platform.openai.com/).
  - Adjust CORS settings if needed.

### 5. Database Setup
- Create the database using the provided `ShopDB.sql` script.
- Run any migrations in `database/migrations/` if needed.
- (Optional) Seed sample data using scripts in `database/seeds/`.

### 6. Run the API Server
```
uvicorn app.main:app --reload
```
- The API will be available at: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### 7. Connect the Frontend
- The backend is ready to connect with your Flutter frontend.
- **After pushing both projects to GitHub, update this README with the frontend repo link.**

---

## 📁 Project Structure
- `app/` - Main FastAPI app (routers, services, models)
- `database/` - Migrations and seed scripts
- `static/` - Product images and assets
- `tests/` - Test scripts (integration, debug, manual)

---

## 🧠 Key Features
- Product catalog & search
- Cart & order management
- AI chatbot (OpenAI GPT, context-aware)

---

## 🔗 Frontend (Flutter)
https://github.com/ThanhAn-Tran/web_selling_chatbot.git
