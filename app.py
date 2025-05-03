from flask import Flask,render_template,redirect,request,flash, url_for
from flask_mail import Mail,Message
from datetime import datetime
import os,requests,json,jinja2
from dotenv import load_dotenv

load_dotenv()

# Load environment variables from .env file
app = Flask(__name__,static_url_path="/static",static_folder="static")

# Get the authtoken from the .env file
SITE_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'

# Load environmental veriables into program for security purpose
app.secret_key = os.getenv('app_secret_key') # app secret key make unique from other apps in same environment
SITE_KEY= os.getenv('SITE_KEY') # google ceptcha secret key 
SECRET_KEY=os.getenv('SECRET_KEY') # google ceptcha public key
MAIL_USERNAME = os.getenv('MAIL_USERNAME') # username/email of mail sender
MAIL_PASSWORD = os.getenv('MAIL_PASSWORD') # app password for above email
MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') # default email of sender
recipients = os.getenv("RECIPIENT_EMAILS", "") # list of recipients  user or admin who access the form submition in there email inbox
recipient_list = [email.strip() for email in recipients.split(",") if email] # recipients list

#Configuring the flask app to setup the SMTP server to send the emails to admin. 
#This is useful for admin to aware about activities for website. User are done some activities on contact form or quotation form
app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT']  = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = ('Optimiseres',MAIL_DEFAULT_SENDER)
mail = Mail(app=app)


# Handling different types of favicon to help bookmark or save the website with icon
@app.route('/favicon.png')
def fevicon():
    return redirect('/static/images/favicon.png')

@app.route('/favicon.ico')
def feviconIco():
    return redirect('/static/images/favicon.ico')

# Handling google ceptch varification with secret,public and response from frontend templates 
def captchaVarification(response=None):
    return requests.post(url=f"https://www.google.com/recaptcha/api/siteverify?secret={SECRET_KEY}&response={response}").json()

# Handling home templates 
@app.route('/')
def home():
    return render_template('index.html')


# Handling services templates 
@app.route('/services/')
def services():
    return render_template('services.html')
#different possible rout for services page
@app.route('/services2/')
def services2():
    return render_template('services2.html')


# Handling contact templates and also send email template to receipients emails address
@app.route('/contact-us/',methods = ["GET","POST"])
def contactUs():

    if request.method == "POST":
        form = request.form
        print("The form is : ",form,end="\n\n")
        name = form.get('name')
        email = form.get('email')
        subject = form.get('subject')
        message = form.get('message')

        re_captche_response = form.get("g-recaptcha-response")

        verify_responose = captchaVarification(response=re_captche_response)

        if verify_responose.get('error-codes',False):
            flash(message= verify_responose['error-codes'],category= "danger")
            return redirect(url_for('contactUs'))
            
        if verify_responose['success'] == False or verify_responose['score'] < 0.5:
            flash(message="Invalid Google captcha !",category= "danger")
            return redirect(url_for('contactUs'))


        try:
            send_contact_mail(
                name=name,
                email=email,
                subject=subject,
                message=message,
                year=datetime.now().year
            )

        except Exception as e:
            flash(e, "danger")

    return render_template('contact.html',SITE_KEY = SITE_KEY)
#different possible rout for contact page
@app.route('/contact/')
def contactPOST():
    return redirect('/contact-us/')

#contact page email submition process with email contact template
def send_contact_mail(name,email,subject, message, year):


    msg = Message("Hello Optimiseres",recipients=recipient_list)  # Change this
    msg.html = render_template('email_template.html', name=name,email = email,subject = subject,message = message, year = year)
    
    try:
        mail.send(msg)
        flash("Form submited successfully !", "success")

    except Exception as e:
        print("The error : ",e)
        flash(e, "danger")

    return redirect('contactUs')


# Handling pricing templates and also send email template to receipients emails address
@app.route('/pricing-plan/')
def pricingPlan():
    return render_template('pricing.html',SITE_KEY = SITE_KEY)
#different possible rout for pricing pricing page
@app.route('/pricing/')
def pricing():
    return redirect("/pricing-plan/")

#  Rendering the html email template for quotation to admin the site submited by any user
def quotation_email_template(form_data):
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
        
    msg = Message("Hello Optimiseres! New quotation request is received",recipients=recipient_list)  # Change this
    msg.html = render_template('quotation_email.html',context=email_context)

    try:
        mail.send(msg)
        flash("Form submited successfully !", "success")

    except Exception as e:
        print("The error : ",e)
        flash(e, "danger")

    return redirect('contactUs')
#This is to handle the quotation submition submited by any user from frontend   
@app.route('/get-quotation/',methods = ["POST"])
def quotationSubmition():
    if request.method == "POST":
        form = request.form

        re_captche_response = form.get("g-recaptcha-response")

        verify_responose = captchaVarification(response=re_captche_response)
        print("Google Ceptcha verify_responose : ",verify_responose)
        
        if verify_responose.get('error-codes',False):
            flash(message= verify_responose['error-codes'],category= "danger")
            return redirect(url_for('pricingPlan'))
            
        if verify_responose['success'] == False or verify_responose['score'] < 0.5:
            flash(message="Invalid Google captcha !",category= "danger")
            return redirect(url_for('pricingPlan'))
        
        quotation_email_template(form)
    
    return redirect('/pricing/')



#This is to handle the page not fount error
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',status= 404), 404

#This is to handle the url not found or user want to access the GET request funtion/urls but it's support only POST request urls
@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("404.html",status=405), 405

# To start the app from same file(The app will not start it execute from other program or file due to line if __name__....:)
if __name__=="__main__":
    app.run(debug=True,host='0.0.0.0')