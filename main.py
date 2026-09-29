from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
import os
import json
import requests
from datetime import datetime

# 1. DEFINE APP FIRST
app = FastAPI(title="Local Windows Coal RAG Dashboard")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

DEMO_USER = "coaladmin"
DEMO_PASS = "coal2026"

KAGGLE_NGROK_URL = "https://quill-winnings-hamster.ngrok-free.dev/run-rag"

# 2. THEN DEFINE YOUR ROUTES
@app.get("/", response_class=HTMLResponse)
def login_page():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Login</title></head>
    <body style="font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh; background: #f4f6f9;">
        <div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 300px;">
            <h2 style="color: #1B5E20; text-align: center;">Local Coal RAG</h2>
            <form action="/login" method="post">
                <input type="text" name="username" placeholder="Username (coaladmin)" required style="width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;">
                <input type="password" name="password" placeholder="Password (coal2026)" required style="width: 100%; padding: 10px; margin: 10px 0; box-sizing: border-box;">
                <button type="submit" style="width: 100%; background: #1B5E20; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; font-weight: bold;">Login</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/login")
def handle_login(username: str = Form(...), password: str = Form(...)):
    if username == DEMO_USER and password == DEMO_PASS:
        resp = RedirectResponse(url="/dashboard", status_code=303)
        resp.set_cookie(key="session_token", value="active_demo_session")
        return resp
    return RedirectResponse(url="/?error=1", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    if request.cookies.get("session_token") != "active_demo_session":
        return RedirectResponse(url="/", status_code=303)
    
    latest_file = os.path.join(DATA_DIR, "latest.json")
    latest_data = {}
    if os.path.exists(latest_file):
        with open(latest_file, "r", encoding="utf-8") as f:
            latest_data = json.load(f)
            
    query = latest_data.get("query", "Type a query below to run RAG...")
    final_answer = latest_data.get("final_answer", "No response generated yet.")
    map_html_repr = latest_data.get("map_html", "<p>No map data.</p>")
    isl_code = latest_data.get("isl_dashboard", {}).get("widget_code", "<p>No ISL widget available.</p>")

    return f"""
    <!DOCTYPE html>
    <html>
    <head><title>Dashboard</title></head>
    <body style="font-family: Arial; background: #f8f9fa; padding: 30px;">
        <div style="max-width: 1000px; margin: auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
            <a href="/" style="float: right; background: #c62828; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px;">Logout</a>
            <h1 style="color: #1B5E20;">🇮🇳 Indian Coal Sector RAG Dashboard</h1>
            
            <div style="background: #e3f2fd; padding: 20px; border-radius: 6px; margin: 20px 0;">
                <h3>Ask a Query (Forwarded to Kaggle GPU Engine):</h3>
                <form action="/query" method="post">
                    <textarea name="user_query" placeholder="e.g., What was Odisha's coal production?" style="width: 100%; height: 80px; padding: 10px; box-sizing: border-box;" required></textarea>
                    <button type="submit" style="background: #1B5E20; color: white; border: none; padding: 10px 20px; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 10px;">Run Pipeline</button>
                </form>
            </div>

            <h3>Latest Query Executed:</h3>
            <p><b>{query}</b></p>
            
            <h2>Extracted Answer / Table Data</h2>
            <div style="background: #fafafa; border: 1px solid #ddd; padding: 15px; border-radius: 6px;">{final_answer}</div>
            
            <h2>Geospatial Map Spotlight</h2>
            <div>{map_html_repr}</div>

            <h2>Indian Sign Language (ISL) Widget</h2>
            <div>{isl_code}</div>
        </div>
    </body>
    </html>
    """

@app.post("/query")
def handle_user_query(user_query: str = Form(...)):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        response = requests.post(KAGGLE_NGROK_URL, json={"query": user_query}, timeout=300)
        result_data = response.json()
        
        final_answer = result_data.get("final_answer", "No answer returned.")
        isl_widget_code = result_data.get("isl_widget_code", "<p>No ISL data</p>")
        map_html_repr = result_data.get("map_html", "<p>No map data</p>")
        
    except Exception as e:
        final_answer = f"<p style='color:red;'>Failed to connect to Kaggle backend: {e}</p>"
        isl_widget_code = ""
        map_html_repr = ""

    save_data = {
        "timestamp": timestamp,
        "query": user_query,
        "final_answer": final_answer,
        "map_html": map_html_repr,
        "isl_dashboard": {"widget_code": isl_widget_code}
    }

    with open(os.path.join(DATA_DIR, "latest.json"), "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=4)

    with open(os.path.join(DATA_DIR, "all_answers.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(save_data) + "\n")

    return RedirectResponse(url="/dashboard", status_code=303)