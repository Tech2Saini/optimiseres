from flask import Flask,render_template,redirect,request,flash, url_for
from flask_mail import Mail,Message
from datetime import datetime
import os,requests,json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the authtoken from the .env file
SITE_KEY= os.getenv('SITE_KEY')
SECRET_KEY=os.getenv('SECRET_KEY')
SITE_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify'


app = Flask(__name__,static_url_path="/static",static_folder="static")
app.secret_key = "bRaUynYLIISQPPOPyy7NWmXvj-MgX0BEr2E5hdldWNY"

app.config['MAIL_SERVER'] = "smtp.gmail.com"
app.config['MAIL_PORT']  = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = "hackingkali789@gmail.com"
app.config['MAIL_PASSWORD'] = "liux ysxd bali erau"
app.config['MAIL_DEFAULT_SENDER'] = ('Optimiseres', 'contact_us@optimiseres.com')
mail = Mail(app=app)



@app.route('/favicon.png')
def fevicon():
    return redirect('/static/images/favicon.png')

@app.route('/favicon.ico')
def feviconIco():
    return redirect('/static/images/favicon.ico')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/services/')
def services():
    return render_template('services.html')

@app.route('/services2/')
def services2():
    return render_template('services2.html')

@app.route('/pricing-plan/')
def pricingPlan():
    return render_template('pricing.html')

@app.route('/pricing/')
def pricing():
    return redirect("/pricing-plan/")

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

        verify_responose = requests.post(url=f"https://www.google.com/recaptcha/api/siteverify?secret={SECRET_KEY}&response={re_captche_response}").json()

        # {'success': True, 'challenge_ts': '2025-04-13T12:07:51Z', 'hostname': '127.0.0.1', 'score': 0.9, 'action': 'submit'}

        if verify_responose.get('error-codes',False):
            flash(message= verify_responose['error-codes'],category= "danger")
            return redirect(url_for('contactUs'))
            
        if verify_responose['success'] == False or verify_responose['score'] < 0.5:
            flash(message="Invalid Google captcha !",category= "danger")
            return redirect(url_for('contactUs'))


        try:
            send_mail(
                name=name,
                email=email,
                subject=subject,
                message=message,
                year=datetime.now().year
            )

        except Exception as e:
            flash(e, "danger")

    return render_template('contact.html',SITE_KEY = SITE_KEY)

@app.route('/contact/')
def contactPOST():
    return redirect('/contact-us/')

def send_mail(name,email,subject, message, year):

    msg = Message("Hello Optimiseres",recipients=["hackingkali789@gmail.com",])  # Change this
    msg.html = render_template('email_template.html', name=name,email = email,subject = subject,message = message, year = year)
    
    try:
        mail.send(msg)
        flash("Form submited successfully !", "success")

    except Exception as e:
        print("The error : ",e)
        flash(e, "danger")

    return redirect('contactUs')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',status= 404), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return render_template("404.html",status=405), 405

if __name__=="__main__":
    app.run(debug=False,host='0.0.0.0')