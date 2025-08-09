# VarProject -  Seat Booking System

![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/javascript-%23323330.svg?style=for-the-badge&logo=javascript&logoColor=%23F7DF1E)
![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white)

A full-stack web application for a modern library seat booking system, featuring a powerful Django backend and a sleek, responsive frontend built with JavaScript and Tailwind CSS.

The design is inspired by top-tier booking platforms like Paytm, focusing on a clean, bright aesthetic and an intuitive user journey from start to finish.

**[Live Demo](https://varproject.onrender.com/)**

---

## About the Developer

This project was designed and developed by:

-   **Prakash Vardhan**
-   **Django & Python Developer**
-   B.Tech, CSE Aspirant at **Aditya University**

This project showcases my ability to architect and build a complete, end-to-end web application, from the server-side logic and database design in Django to a polished, user-centric interface in JavaScript and Tailwind CSS.

## Features

-   **Intuitive Booking Interface:** A clean, card-based layout allows users to find and book seats with ease.
-   **User Authentication:** Secure user registration and login system powered by the Django backend.
-   **Dynamic Seat Discovery:** A responsive results page displays available seats as a clear, filterable list.
-   **User Dashboard:** A dedicated "My Bookings" area where users can view their upcoming and past reservations.
-   **QR Code Integration:** Upcoming bookings feature a "Show QR Code" button, which opens a modal displaying a unique QR code for a seamless check-in experience.
-   **Fully Responsive Design:** Meticulously crafted with Tailwind CSS to be fully responsive on any device.
-   **Admin Views:** Includes mockups for an Administrator Dashboard and a Check-In page.

## Technology Stack

This project is a full-stack application composed of two main parts:

### Backend
-   **Framework:** Django
-   **Language:** Python
-   **Database:** SQLite3 (for development)
-   **API:** Django REST Framework for serving data to the frontend.

### Frontend
-   **Structure:** HTML5
-   **Styling:** **Tailwind CSS** - A utility-first CSS framework.
-   **Logic & Interactivity:** Vanilla JavaScript (ES6+)
-   **Development Tooling:** Node.js/npm for managing frontend dependencies.

## Getting Started

Follow these instructions to set up and run the entire project on your local machine. You will need to run the backend and frontend servers simultaneously.

### Prerequisites

-   Python 3.8+
-   Node.js and npm

### Backend Setup

1.  **Create and activate a virtual environment:**
    ```bash
    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    py -m venv venv
    venv\Scripts\activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Apply database migrations:**
    ```bash
    python manage.py migrate
    ```

4.  **Run the Django server:**
    ```bash
    python manage.py runserver
    ```
    The backend API will be running at `http://127.0.0.1:8000`.

### Frontend Setup

1.  **Open a new, separate terminal window.**

2.  **Install frontend dependencies:**
    ```bash
    npm install
    ```

3.  **Start the frontend development server:**
    This command will watch for changes in your HTML and JS files and recompile your Tailwind CSS.
    ```bash
    npm run dev  # Or the equivalent script in your package.json
    ```
    The frontend will be available at `http://localhost:5173` (or another port specified in your terminal).
