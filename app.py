import os  
import pandas as pd
import io
from datetime import datetime
from flask import Flask, make_response, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.utils import secure_filename 
from werkzeug.security import generate_password_hash
from fpdf import FPDF 
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from config import Config
from extensions import mail

# SQL kodları yerine db_manager'ı çağırıyoruz
import db_manager as db

app = Flask(__name__)
app.config.from_object(Config)

# Eklentileri başlat
mail.init_app(app)
serializer = URLSafeTimedSerializer(app.secret_key)

# Blueprint Kayıt
from blueprints.auth import auth_bp
from blueprints.main import main_bp
from blueprints.customer import customer_bp
from blueprints.admin import admin_bp

from blueprints.api import api_bp

app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(customer_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(api_bp)

# --- YARDIMCI: MAIL GÖNDERME ---
def send_email(to, subject, template):
    try:
        msg = Message(subject, recipients=[to], html=template)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Mail Hatası: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=True)