from flask import Flask, render_template, redirect, request, flash, url_for
from flask_mail import Mail, Message
from datetime import datetime
import os
import requests
import json
import jinja2
from dotenv import load_dotenv
import logging
from functools import wraps
import html

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_url_path="/static", static_folder="static")

# Validate required environment variables
required_env_vars = [
    'app_secret_key', 'SITE_KEY', 'SECRET_KEY',
    'MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_DEFAULT_SENDER', 'RECIPIENT_EMAILS'
]

missing_vars = [var for var in required_env_vars if os.getenv(var) is None]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Load environmental variables into program for security purpose
app.secret_key = os.getenv('app_secret_key')
SITE_KEY = os.getenv('SITE_KEY')  # Google reCAPTCHA site key
SECRET_KEY = os.getenv('SECRET_KEY')  # Google reCAPTCHA secret key
MAIL_USERNAME = os.getenv('MAIL_USERNAME')
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
recipients = os.getenv("RECIPIENT_EMAILS", "")
recipient_list = [email.strip() for email in recipients.split(",") if email]

# reCAPTCHA configuration
SITE_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

# Mail configuration
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = ('Optimiseres', MAIL_DEFAULT_SENDER)
mail = Mail(app=app)

# Maximum input lengths for security
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 100
MAX_SUBJECT_LENGTH = 200
MAX_MESSAGE_LENGTH = 5000
MAX_COMPANY_LENGTH = 100
MAX_PROJECT_DETAILS_LENGTH = 10000

# Input validation decorator
def validate_input(**validators):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            form = request.form
            for field, validator in validators.items():
                if field in form:
                    value = form[field]
                    if not validator(value):
                        flash(f"Invalid input for {field}", "danger")
                        return redirect(url_for(request.endpoint))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Validation functions
def validate_length(value, max_length):
    return len(value) <= max_length

def validate_email(email):
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_recaptcha(response):
    """Verify the reCAPTCHA response"""
    if not response:
        return False
    
    try:
        # More secure way to verify reCAPTCHA
        payload = {
            'secret': SECRET_KEY,
            'response': response
        }
        verify_response = requests.post(SITE_VERIFY_URL, data=payload).json()
        
        logger.debug(f"reCAPTCHA verification response: {verify_response}")
        
        if verify_response.get('error-codes'):
            logger.warning(f"reCAPTCHA errors: {verify_response['error-codes']}")
            return False
            
        return verify_response.get('success', False) and verify_response.get('score', 0) >= 0.5
    except Exception as e:
        logger.error(f"reCAPTCHA verification error: {str(e)}")
        return False

def sanitize_input(text):
    """Basic input sanitization"""
    if text is None:
        return ""
    return html.escape(text.strip())

# Favicon routes
@app.route('/favicon.png')
def favicon_png():
    return redirect('/static/images/favicon.png')

@app.route('/favicon.ico')
def favicon_ico():
    return redirect('/static/images/favicon.ico')

# Main routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services/')
def services():
    return render_template('services.html')

@app.route('/services2/')
def services2():
    return render_template('services2.html')

@app.route('/contact-us/', methods=["GET", "POST"])
def contact_us():
    if request.method == "POST":
        # Sanitize input
        name = sanitize_input(request.form.get('name', ''))
        email = sanitize_input(request.form.get('email', ''))
        subject = sanitize_input(request.form.get('subject', ''))
        message = sanitize_input(request.form.get('message', ''))
        
        # Validate lengths
        if not validate_length(name, MAX_NAME_LENGTH):
            flash("Name is too long", "danger")
            return redirect(url_for('contact_us'))
            
        if not validate_length(email, MAX_EMAIL_LENGTH) or not validate_email(email):
            flash("Invalid email address", "danger")
            return redirect(url_for('contact_us'))
            
        if not validate_length(subject, MAX_SUBJECT_LENGTH):
            flash("Subject is too long", "danger")
            return redirect(url_for('contact_us'))
            
        if not validate_length(message, MAX_MESSAGE_LENGTH):
            flash("Message is too long", "danger")
            return redirect(url_for('contact_us'))

        # Validate reCAPTCHA
        recaptcha_response = request.form.get("g-recaptcha-response")
        if not validate_recaptcha(recaptcha_response):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return redirect(url_for('contact_us'))

        # Send email
        try:
            send_contact_mail(
                name=name,
                email=email,
                subject=subject,
                message=message,
                year=datetime.now().year
            )
            flash("Form submitted successfully!", "success")
        except Exception as e:
            logger.error(f"Email sending error: {str(e)}")
            flash("There was an error sending your message. Please try again later.", "danger")

    return render_template('contact.html', SITE_KEY=SITE_KEY)

@app.route('/contact/')
def contact_redirect():
    return redirect(url_for('contact_us'))

def send_contact_mail(name, email, subject, message, year):
    """Send a contact form email to recipients"""
    msg = Message("New Contact Form Submission - Optimiseres", recipients=recipient_list)
    msg.html = render_template(
        'email_template.html', 
        name=name,
        email=email,
        subject=subject,
        message=message, 
        year=year
    )
    
    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Mail sending error: {str(e)}")
        raise

@app.route('/pricing-plan/')
def pricing_plan():
    return render_template('pricing.html', SITE_KEY=SITE_KEY)

@app.route('/pricing/')
def pricing_redirect():
    return redirect(url_for('pricing_plan'))

@app.route('/get-quotation/', methods=["POST"])
def quotation_submission():
    if request.method == "POST":
        # Sanitize inputs
        form_data = {
            'first_name': sanitize_input(request.form.get('first_name', '')),
            'last_name': sanitize_input(request.form.get('last_name', '')),
            'email': sanitize_input(request.form.get('email', '')),
            'company': sanitize_input(request.form.get('company', '')),
            'services_needed': sanitize_input(request.form.get('services_needed', '')),
            'project_timeline': sanitize_input(request.form.get('project_timeline', '')),
            'project_details': sanitize_input(request.form.get('project_details', '')),
        }
        
        # Validate inputs
        if not validate_email(form_data['email']):
            flash("Invalid email address", "danger")
            return redirect(url_for('pricing_plan'))
            
        if not validate_length(form_data['company'], MAX_COMPANY_LENGTH):
            flash("Company name is too long", "danger")
            return redirect(url_for('pricing_plan'))
            
        if not validate_length(form_data['project_details'], MAX_PROJECT_DETAILS_LENGTH):
            flash("Project details are too long", "danger")
            return redirect(url_for('pricing_plan'))

        # Validate reCAPTCHA
        recaptcha_response = request.form.get("g-recaptcha-response")
        if not validate_recaptcha(recaptcha_response):
            flash("reCAPTCHA verification failed. Please try again.", "danger")
            return redirect(url_for('pricing_plan'))
        
        try:
            send_quotation_email(form_data)
            flash("Quotation request submitted successfully!", "success")
        except Exception as e:
            logger.error(f"Quotation email error: {str(e)}")
            flash("There was an error submitting your request. Please try again later.", "danger")
    
    return redirect(url_for('pricing_plan'))

def send_quotation_email(form_data):
    """Send a quotation request email to recipients"""
    # Combine all data needed for the email
    email_context = {
        # Form data
        'first_name': form_data.get('first_name', ''),
        'last_name': form_data.get('last_name', ''),
        'email': form_data.get('email', ''),
        'company': form_data.get('company', 'Not provided'),
        'services_needed': form_data.get('services_needed', ''),
        'project_timeline': form_data.get('project_timeline', ''),
        'project_details': form_data.get('project_details', ''),
        
        # Metadata
        'submission_datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        
        # Company info
        'company_name': 'Optimiseres',
        'current_year': datetime.now().year,
    }
        
    msg = Message("New Quotation Request - Optimiseres", recipients=recipient_list)
    msg.html = render_template('quotation_email.html', context=email_context)

    try:
        mail.send(msg)
    except Exception as e:
        logger.error(f"Mail sending error: {str(e)}")
        raise

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', status=404), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("404.html", status=405), 405

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template("500.html", status=500), 500

if __name__ == "__main__":
    # In production, use a proper WSGI server instead
    # For development only:
    app.run(debug=False)