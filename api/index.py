from flask import Flask, render_template, request, redirect, session, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
import os
import random
import subprocess
import google.generativeai as genai

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app with proper template and static folder paths
app = Flask(
    __name__,
    template_folder="../templates",
    static_folder="../static"
)

# Secret key for session management
app.secret_key = os.getenv("SECRET_KEY")

# MongoDB configuration
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        otp = str(random.randint(100000, 999999))
        session["pending_email"] = email
        session["otp"] = otp
        subprocess.run(["node", "otp_sender.js", email, otp])
        return render_template("verify.html")
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        otp = str(random.randint(100000, 999999))
        session["pending_email"] = email
        session["name"] = name
        session["otp"] = otp
        subprocess.run(["node", "otp_sender.js", email, otp])
        return render_template("verify.html")
    return render_template("signup.html")

@app.route("/verify", methods=["POST"])
def verify():
    input_otp = request.form.get("otp")
    if input_otp == session.get("otp"):
        email = session.get("pending_email")
        name = session.get("name", "")
        user = mongo.db.users.find_one({"email": email})
        if not user:
            mongo.db.users.insert_one({"email": email, "name": name, "chats": []})
        session["user_email"] = email
        return redirect("/dashboard")
    return "Invalid OTP", 403

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect("/login")
    user = mongo.db.users.find_one({"email": session["user_email"]})
    # Reverse the chats list to show most recent first
    chats = user.get("chats", [])
    chats.reverse()
    return render_template("dashboard.html", chats=chats)

@app.route("/chat", methods=["POST"])
def chat():
    if "user_email" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        prompt = request.form.get("prompt")
        if not prompt:
            return jsonify({"error": "No prompt provided"}), 400
            
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Generate response using Gemini API
        response = model.generate_content(prompt)
        response_text = response.text if response.text else "Sorry, I couldn't generate a response."
        
        # Save to database
        mongo.db.users.update_one(
            {"email": session["user_email"]},
            {"$push": {"chats": {"prompt": prompt, "response": response_text, "timestamp": timestamp}}}
        )
        
        return jsonify({"response": response_text})
        
    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({"error": "Failed to generate response"}), 500

@app.route("/logout")
def logout():
    """Handle user logout"""
    session.clear()
    return redirect("/")

@app.route("/delete_history", methods=["POST"])
def delete_history():
    """Delete a specific chat history item"""
    if "user_email" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        data = request.get_json()
        index = data.get("index")
        
        if index is None:
            return jsonify({"error": "No index provided"}), 400
        
        # Get user's current chats
        user = mongo.db.users.find_one({"email": session["user_email"]})
        chats = user.get("chats", [])
        
        # Reverse index since we display chats in reverse order
        actual_index = len(chats) - 1 - index
        
        if 0 <= actual_index < len(chats):
            # Remove the chat at the specified index
            chats.pop(actual_index)
            
            # Update the database
            mongo.db.users.update_one(
                {"email": session["user_email"]},
                {"$set": {"chats": chats}}
            )
            
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Invalid index"}), 400
            
    except Exception as e:
        print(f"Delete history error: {str(e)}")
        return jsonify({"error": "Failed to delete history"}), 500

@app.route("/clear_all_history", methods=["POST"])
def clear_all_history():
    """Clear all chat history for the current user"""
    if "user_email" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        # Clear all chats for the user
        mongo.db.users.update_one(
            {"email": session["user_email"]},
            {"$set": {"chats": []}}
        )
        
        return jsonify({"success": True})
        
    except Exception as e:
        print(f"Clear all history error: {str(e)}")
        return jsonify({"error": "Failed to clear history"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template("500.html"), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)