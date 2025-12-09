# 🍳 Recipe Explorer & Studio

A powerful web application for exploring, analyzing, and creating cooking recipes. Built with **Flask**, **MongoDB**, and **Vanilla JavaScript**.

![Recipe Studio](/Users/sooryakumar/.gemini/antigravity/brain/aa5860b6-37cf-4fdc-bb99-1c9fb9e05cc4/spacious_analyze_ui_1765216078290.png)

## ✨ Features

### 🔍 Recipe Explorer
- **Smart Search**: Find recipes by name, ingredient, or cuisine.
- **Advanced Filtering**: Filter by preparation time, calories, cuisine, and difficulty.
- **Detailed Views**: View step-by-step instructions, ingredients, and nutritional info.

### 🧪 Recipe Studio (New!)
- **Analyze & Draft**: Create new recipes with a real-time analysis engine.
- **Flavor Profiling**: Visualize the taste balance (Sweet, Spicy, Sour, etc.) with an interactive Radar Chart.
- **Comparison Engine**: Compare your recipe's health metrics against global averages.
- **Publishing**: Contribute your masterpiece to the database.

### 📊 Statistics Dashboard
- **Data Visualization**: Interactive charts showing cuisine distribution and difficulty levels.
- **Insights**: Aggregate data from the entire recipe collection.

## 🛠️ Technology Stack
- **Backend**: Python, Flask, PyMongo, Pandas
- **Frontend**: HTML5, CSS3 (Custom Variables), JavaScript (ES6+), Chart.js
- **Database**: MongoDB (Local)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- MongoDB installed and running locally

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository_url>
    cd cooking-recipe-analysis
    ```

2.  **Set up Backend**
    ```bash
    cd backend
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Populate Database** (If running for the first time)
    ```bash
    # From the project root
    python insert_db2.py
    ```

4.  **Run the Application**
    ```bash
    # From the project root (ensure venv is active)
    python backend/app.py
    ```

    The application will launch at `http://localhost:5005`

## 📂 Project Structure

```
cooking-recipe-analysis/
├── backend/
│   ├── app.py                 # Main Flask application
│   ├── utils/                 # Analysis and Database utilities
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── index.html             # Single Page Application entry
│   ├── css/style.css          # Custom styling with CSS Variables
│   └── js/app.js              # Frontend logic (SPA routing, API calls)
├── data/                      # MongoDB data storage
├── recipes.json               # Seed dataset
└── insert_db2.py              # Database seeding script
```

## 🔮 Future Roadmap
- [ ] User Authentication & Profiles
- [ ] Image Uploads for Recipes
- [ ] AI-powered detailed nutritional breakdown
- [ ] Social Sharing features

---
*Created for the Advanced Agentic Coding Project*
