from flask import Flask, render_template, request, redirect, session, jsonify
from flask_pymongo import PyMongo
from dotenv import load_dotenv
from datetime import datetime
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
app.secret_key = os.getenv("SECRET_KEY") or "fallback-secret-key-for-development"

# MongoDB configuration
mongo_uri = os.getenv("MONGO_URI")
if mongo_uri:
    app.config["MONGO_URI"] = mongo_uri
    try:
        mongo = PyMongo(app)
        print("MongoDB connection initialized successfully")
    except Exception as e:
        print(f"MongoDB connection error: {str(e)}")
        mongo = None
else:
    print("WARNING: MONGO_URI not found in environment variables")
    mongo = None

# Configure Gemini API
gemini_api_key = os.getenv("GEMINI_API_KEY")
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("Gemini API configured successfully")
    except Exception as e:
        print(f"Gemini API configuration error: {str(e)}")
        model = None
else:
    print("WARNING: GEMINI_API_KEY not found in environment variables")
    model = None

def send_otp_email(email, otp):
    """Send OTP email using Python's smtplib instead of Node.js subprocess"""
    try:
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("OTP_EMAIL")
        sender_password = os.getenv("OTP_PASS")
        
        if not sender_email or not sender_password:
            print("Email credentials not found in environment variables")
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Your OTP Code"
        msg['From'] = f'"Chat Bot-Project" <{sender_email}>'
        msg['To'] = email
        
        # HTML content
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; color: #333; margin-bottom: 20px; }}
                .otp {{ font-size: 24px; font-weight: bold; color: #007bff; text-align: center; margin: 20px 0; padding: 10px; background-color: #f8f9fa; border-radius: 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                .warning {{ color: #dc3545; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">Chat Bot</h1>
                <p>Hi,</p>
                <p>Your OTP code is:</p>
                <div class="otp">{otp}</div>
                <p class="warning">This OTP is valid for a limited time. Do not share it with anyone.</p>
                <div class="footer">
                    <p>Made by <strong>Pranav Rayban</strong></p>
                    <p><a href="https://linkedin.com/in/pranav-rayban">LinkedIn</a></p>
                </div>
            </div>
        </body>
        </html>
        '''
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"OTP email sent successfully to {email}")
        return True
        
    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        return False

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/health")
def health_check():
    """Health check endpoint for debugging"""
    status = {
        "status": "ok",
        "mongodb": "connected" if mongo else "not available",
        "gemini": "configured" if model else "not available",
        "email": "configured" if os.getenv("OTP_EMAIL") and os.getenv("OTP_PASS") else "not configured"
    }
    return jsonify(status)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            # Check if MongoDB is available
            if not mongo:
                print("MongoDB not available")
                return jsonify({"error": "Database connection error"}), 500
                
            email = request.form.get("email")
            if not email:
                print("Email not provided in form")
                return jsonify({"error": "Email is required"}), 400
                
            print(f"Processing login for email: {email}")
            otp = str(random.randint(100000, 999999))
            session["pending_email"] = email
            session["otp"] = otp
            print(f"Generated OTP: {otp}")
            
            # Send OTP using Python instead of Node.js subprocess
            if send_otp_email(email, otp):
                print("OTP sent successfully")
                return render_template("verify.html")
            else:
                print("Failed to send OTP")
                return jsonify({"error": "Failed to send OTP"}), 500
                
        except Exception as e:
            print(f"Login error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal server error"}), 500
            
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        try:
            # Check if MongoDB is available
            if not mongo:
                print("MongoDB not available")
                return jsonify({"error": "Database connection error"}), 500
                
            name = request.form.get("name")
            email = request.form.get("email")
            
            if not name or not email:
                print("Name or email not provided")
                return jsonify({"error": "Name and email are required"}), 400
                
            print(f"Processing signup for: {name}, {email}")
            otp = str(random.randint(100000, 999999))
            session["pending_email"] = email
            session["name"] = name
            session["otp"] = otp
            print(f"Generated OTP: {otp}")
            
            # Send OTP using Python instead of Node.js subprocess
            if send_otp_email(email, otp):
                print("OTP sent successfully")
                return render_template("verify.html")
            else:
                print("Failed to send OTP")
                return jsonify({"error": "Failed to send OTP"}), 500
                
        except Exception as e:
            print(f"Signup error: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": "Internal server error"}), 500
            
    return render_template("signup.html")

@app.route("/verify", methods=["POST"])
def verify():
    try:
        # Check if MongoDB is available
        if not mongo:
            print("MongoDB not available")
            return jsonify({"error": "Database connection error"}), 500
            
        input_otp = request.form.get("otp")
        if not input_otp:
            return jsonify({"error": "OTP is required"}), 400
            
        print(f"Verifying OTP: {input_otp} against {session.get('otp')}")
        
        if input_otp == session.get("otp"):
            email = session.get("pending_email")
            name = session.get("name", "")
            
            print(f"OTP verified for {email}")
            
            user = mongo.db.users.find_one({"email": email})
            if not user:
                print(f"Creating new user: {email}")
                mongo.db.users.insert_one({"email": email, "name": name, "chats": []})
            
            session["user_email"] = email
            # Clear temporary session data
            session.pop("pending_email", None)
            session.pop("otp", None)
            session.pop("name", None)
            
            return redirect("/dashboard")
        else:
            print("Invalid OTP provided")
            return jsonify({"error": "Invalid OTP"}), 403
            
    except Exception as e:
        print(f"Verify error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Internal server error"}), 500

@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect("/login")
        
    try:
        # Check if MongoDB is available
        if not mongo:
            print("MongoDB not available")
            return render_template("500.html"), 500
            
        user = mongo.db.users.find_one({"email": session["user_email"]})
        if not user:
            print(f"User not found: {session['user_email']}")
            return redirect("/login")
            
        # Reverse the chats list to show most recent first
        chats = user.get("chats", [])
        chats.reverse()
        return render_template("dashboard.html", chats=chats)
        
    except Exception as e:
        print(f"Dashboard error: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template("500.html"), 500

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
        if not user:
            return jsonify({"error": "User not found"}), 404
            
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

# Vercel serverless function handler
def handler(request):
    return app(request.environ, lambda status, response_headers: None)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
