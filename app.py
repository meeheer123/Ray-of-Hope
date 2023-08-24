# Import Statements
from flask import (
    Flask,
    request,
    render_template,
    flash,
    url_for,
    redirect,
    session,
    Response,
    jsonify
)
import pyrebase
from flask_session import Session
import requests.exceptions
import ssl
import smtplib
from dotenv import load_dotenv
import os
from helpers import login_required, apology

# loads the data of env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
# Done to make a cookie for the user
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize Firebase config
firebase_config = {
    "apiKey": os.getenv("API_KEY"),
    "authDomain": os.getenv("AUTH_DOMAIN"),
    "databaseURL": os.getenv("DATABASE_URL"),
    "projectId": os.getenv("PROJECT_ID"),
    "storageBucket": os.getenv("STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("MESSAGING_SENDER_ID"),
    "appId": os.getenv("APP_ID"),
    "measurementId": os.getenv("MEASUREMENT_ID"),
}

# done to initialize firebase and use its functions
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
db = firebase.database()


# this will be the home page showing ('i need help' and 'i can help')
@app.route("/", methods=["GET", "POST"])
def home():
    """basically the home page of the program"""
    return render_template("(a)home_page.html")


# redirects to a signin page of helpee
@app.route("/sign_in_helpee", methods=["GET", "POST"])
def sign_in_helpee():
    '''This is the login page of helpee'''
    # Forget any user_id
    session.clear()
    # Set role (this can be used later to check if the person is helper or helpee in the program)
    session["user_role"] = "helpee"

    if request.method == "POST":
        email = request.form.get("helpee_email")
        password = request.form.get("helpee_password")

        # this tries to sign in the user and if the func gives error,
        # it means that the credentials are invalid
        try:
            user = auth.sign_in_with_email_and_password(email, password)

            # this is used later to get data from this user_id
            session["user_id"] = user["localId"]

            # Fetch user data from the database
            user_data = (
                db.child("people").child("helpee").child(
                    session["user_id"]).get().val()
            )

            session["user_data"] = user_data

            return redirect("/rest_page_for_helpee")
        # if the credentails are invalid we show invalid credentails on html
        except requests.exceptions.HTTPError as e:
            return render_template(
                "(helpee)login.html",
                error="Invalid credentials. Please try again.",
                invalid_input=True,
            )

        except requests.exceptions.RequestException as e:
            # Network-related error (e.g., connection error)
            return render_template(
                "(helpee)login.html",
                error="Error occurred during authentication. Please try again later.",
            )

    # If the request method is not POST, render the login form
    return render_template("(helpee)login.html")


@app.route("/sign_up_helpee", methods=["GET", "POST"])
def sign_up_helpee():
    """signup page for helpee"""
    # clearing the data
    session.clear()
    if request.method == "POST":
        try:
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("cpassword")
            self_name = request.form.get("name")
            self_contact = request.form.get("contact_number")
            gender = request.form.get("gender")
            edu = request.form.get("grade_level")
            address = request.form.get("address")
            udid = request.form.get("unique_disability_id")
            parent_name = request.form.get("parent_name")
            institute = request.form.get("institute_name")
            guardian_contact = request.form.get("parent_contact_number")

            # we try to create a user here since if the user is present firebase throws an error
            # this error is caught by our except block returning (The Email Already Exists)
            user = auth.create_user_with_email_and_password(email, password)

        except Exception as e:
            # Error occurred during sign-up, show an error message
            return apology("The Email Already Exists")
        # if sucessful store the local id
        user_id = user["localId"]

        # Create a dictionary with user data
        user_data = {
            "name": self_name,
            "email": email,
            "self_contact": self_contact,
            "gender": gender,
            "edu": edu,
            "address": address,
            "udid": udid,
            "institute": institute,
            "parent_name": parent_name,
            "guardian_contact": guardian_contact,
        }

        # Store the user data in the Firebase Realtime Database under the user ID
        db.child("people").child("helpee").child(
            user_id).child("data").set(user_data)

        # Data successfully saved, render the success template
        return redirect("/sign_in_helpee")

    # print('method get')
    return render_template("(helpee)signup.html")

# this is firebase inbuilt function nothing to do here


@app.route("/forgot_password", methods=["POST"])
def forgot_password():
    """sends an email after which the user can change the password"""
    '''directly using firebase for this so no problem will arize here unless firebase itself messes up'''
    try:
        email = request.json.get("email")

        # Validate the email input
        if not email:
            return Response(status=400, response="Invalid email format.")

        # Send password reset email
        auth.send_password_reset_email(email)

        return Response(status=200)

    except pyrebase.pyrebase.exceptions.HTTPError as e:
        # Handle HTTP errors, e.g., if the email is not found in the authentication system
        return Response(
            status=400, response="Email not found in the authentication system."
        )

    except requests.exceptions.RequestException as e:
        # Handle network-related errors
        return Response(
            status=500,
            response="Error occurred while processing your request. Please try again later.",
        )


@app.route("/rest_page_for_helpee", methods=["GET", "POST"])
@login_required
def rest_page_for_helpee():
    '''This is the page helpee is redirected to after logging in'''
    # this is the complete data here about the user
    user_data = db.child("people").child(
        "helpee").child(session["user_id"]).get().val()

    # check if exams are existing in user_data
    # if there are no exams then pass info as none
    # but in case there are exams present there pass the data as user data and info as the exams of the user
    if "exams" in user_data:
        # Fetch exam-specific data from user_data
        return render_template(
            "(helpee)rest_page.html",
            data=user_data["data"],
            info=user_data.get("exams"),
        )
    else:
        # In case of the user has not asked for help
        print("No exam data here")
        return render_template(
            "(helpee)rest_page.html", data=user_data["data"], info=None
        )


@app.route("/rest_page_for_helper", methods=["GET", "POST"])
@login_required
def rest_page_for_helper():
    '''Redirect helper here after a sucessful login'''
    # this is the complete data here about the user
    user_data = session.get("helper_user_data")
    student_data = db.child("people").child("helpee").get().val()

    exams_with_helper_not_found = []
    # basically we iterate to get the data of exams whose helper_found was false
    if student_data != None:
        for user_id, data in student_data.items():
            exams = data.get("exams", {})
            for exam_id, exam_data in exams.items():
                if not exam_data.get("helper_found", True):
                    exams_with_helper_not_found.append(exam_data)

        session['user_data'] = user_data["data"]

        # display all the data of people who haave helper_found = false
        return render_template(
            "(helper)rest_page.html",
            data=user_data["data"],
            exam_info=exams_with_helper_not_found,
        )
    else:
        # if no student is in the db who needs help
        flash('No students found')
        return render_template('(helper)rest_page.html', data=user_data["data"], info={})


@app.route("/get_help", methods=["GET", "POST"])
@login_required
def get_help():
    try:
        if request.method == "POST":
            # collecting data from forms
            subject = request.form.get("exam_needs_help")
            med_language = request.form.get("language_medium")
            centre = request.form.get("location")
            exam_date = request.form.get("exam_date")
            start_time = request.form.get("exam_time")
            end_time = request.form.get("time_duration")

            # Data json
            helpee_data = {
                "subject": subject,
                "med_language": med_language,
                "location": centre,
                "exam_date": exam_date,
                "start_time": start_time,
                "end_time": end_time,
                "helper_found": False,
                "name": session["user_data"]["data"]["name"],
                "contact": session["user_data"]["data"]["self_contact"],
                "_examid": "",
                "_parentnode": "",
            }

            # this is adding the data no problems
            key = (
                db.child("people")
                .child("helpee")
                .child(session["user_id"])
                .child("exams")
                .push(helpee_data)
            )
            db.child("people").child("helpee").child(session["user_id"]).child(
                "exams"
            ).child(key["name"]).update({"_examid": key["name"]})
            db.child("people").child("helpee").child(session["user_id"]).child(
                "exams"
            ).child(key["name"]).update({"_parentnode": session["user_id"]})

            # Fetch the updated user data from the database after submitting the form
            user_data = (
                db.child("people").child("helpee").child(
                    session["user_id"]).get().val()
            )
            if user_data:
                # Update the session data for 'user_data' and 'exams'
                session["user_data"]["data"] = user_data.get("data", {})
                session["user_data"]["exams"] = user_data.get("exams", {})

            flash(
                "Your request for help has been submitted."
            )  # Display a success message
            return redirect(
                url_for("rest_page_for_helpee")
            )  # Redirect to the rest_page

    except Exception as e:
        flash(
            "An error occurred while processing your request. Please try again later."
        )
        print("Error in get_help:", e)

    # return render_template('(helpee)get_help.html', data=session['user_data']['data']['name'])
    return render_template("(helpee)get_help.html")


# redirects to signin or signup page of helper
@app.route("/sign_in_helper", methods=["GET", "POST"])
# @login_required
def sign_in_helper():
    # forget any user_id
    session.clear()
    session["user_role"] = "helper"
    # print('abcdata', session['user_role'])

    if request.method == "POST":
        email = request.form.get("helper_email")
        password = request.form.get("helper_password")

        try:
            user = auth.sign_in_with_email_and_password(email, password)
            user_id = user["localId"]

            # storing userid in session now
            session["helper_user_id"] = user_id

            # fetch user data from the database
            helper_user_data = (
                db.child("people").child("helper").child(user_id).get().val()
            )
            session["helper_user_data"] = helper_user_data
            # print("helper data: ", session)
            return redirect("/rest_page_for_helper")

        except requests.exceptions.HTTPError as e:
            # Invalid credentials (HTTP 400 status code)
            return render_template(
                "(helper)login.html",
                error="Invalid credentials. Please try again.",
                invalid_input=True,
            )

        except requests.exceptions.RequestException as e:
            # Network-related error (e.g., connection error)
            return render_template(
                "(helper)login.html",
                error="Error occurred during authentication. Please try again later.",
            )

    return render_template("(helper)login.html")


@app.route("/sign_up_helper", methods=["GET", "POST"])
def sign_up_helper():
    # clearing the data
    session.clear()

    if request.method == "POST":
        try:
            name = request.form.get("name")
            email = request.form.get("email")
            password = request.form.get("password")
            confirm_password = request.form.get("cpassword")
            gender = request.form.get("gender")
            edu = request.form.get("grade_level")
            institute = request.form.get("institute_name")
            address = request.form.get("address")
            contact = request.form.get("contact_number")
            occupation = request.form.get("occupation")
            id_proof = request.form.get("id_proof")
            id_proof_value = request.form.get("id_proof_value")

            try:
                user = auth.create_user_with_email_and_password(
                    email, password)
            except Exception as e:
                return apology('user already exists')

            user_id = user["localId"]

            # Create a dictionary with user data
            user_data = {
                "name": name,
                "email": email,
                "gender": gender,
                "edu": edu,
                "institute": institute,
                "address": address,
                "contact": contact,
                "occupation": occupation,
                "id_proof": id_proof + " : " + id_proof_value,
            }

            print(id_proof + " : " + id_proof_value)

            # Store the user data in the Firebase Realtime Database under the user ID
            db.child("people").child("helper").child(user_id).child("data").set(
                user_data
            )
            # Data successfully saved, render the success template
            return redirect("/sign_in_helper")

        except Exception as e:
            # Error occurred during sign-up, show an error message
            return render_template(
                "(helper)signup.html",
                error="An error occurred during sign-up: " + str(e),
            )

    return render_template("(helper)signup.html")


@app.route("/help_button_clicked", methods=["POST"])
def help_button_clicked():
    data = request.get_json()  # Get the JSON data sent in the request body
    exam_id = data.get("examid")  # Extract the '_examid' from the JSON data
    # Extract the '_parentnode' from the JSON data
    parent_node = data.get("parentnode")

    db.child("people").child("helpee").child(parent_node).child("exams").child(
        exam_id
    ).update({"helper_found": True})

    helpee_data = (
        db.child("people").child("helpee").child(
            parent_node).child("data").get().val()
    )
    helper_data = (
        db.child("people")
        .child("helper")
        .child(session["helper_user_id"])
        .child("data")
        .get()
        .val()
    )

    # Return a JSON response (optional)
    response_data = {
        "helpee_name": helpee_data['name'],
        "helpee_email": helpee_data['email'],
        "helper_name": helper_data['name'],
        "helper_email": helper_data['email']
    }

    # Convert the response data to JSON and return
    return jsonify(response_data)


if __name__ == "__main__":
    app.run(debug=True)
