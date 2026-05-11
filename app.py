import logging
import os
import re
import smtplib
from email.mime.text import MIMEText

from flask import Flask, redirect, render_template, request, url_for

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return False

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

SERVICES = ["Web Development", "Graphic Design", "Data Entry"]
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_SEND_ERROR = "Hiring form could not be sent right now. Please try again later."


def is_digits(value, length):
    return value.isdigit() and len(value) == length


def is_valid_email(value):
    return bool(EMAIL_PATTERN.fullmatch(value))


def get_hiring_data():
    return {
        "name": request.form.get("name", "").strip(),
        "service": request.form.get("service", "").strip(),
        "duration": request.form.get("duration", "").strip(),
        "num": request.form.get("num", "").strip(),
        "wnum": request.form.get("wnum", "").strip(),
        "email": request.form.get("email", "").strip(),
        "address": request.form.get("address", "").strip(),
        "pin": request.form.get("pin", "").strip(),
        "message": request.form.get("message", "").strip(),
    }


def validate_hiring_data(data):
    errors = {}

    required_fields = {
        "name": "Name is required.",
        "duration": "Work duration is required.",
        "email": "Email is required.",
        "address": "Address is required.",
        "message": "Project message is required.",
    }

    for field, error_message in required_fields.items():
        if not data[field]:
            errors[field] = error_message

    if data["service"] not in SERVICES:
        errors["service"] = "Please select a valid service."

    if data["email"] and not is_valid_email(data["email"]):
        errors["email"] = "Please enter a valid email address."

    if not is_digits(data["pin"], 6):
        errors["pin"] = "Pincode must be exactly 6 digits."

    if not is_digits(data["num"], 10):
        errors["num"] = "Contact number must be exactly 10 digits."

    if not is_digits(data["wnum"], 10):
        errors["wnum"] = "Whatsapp number must be exactly 10 digits."

    return errors


def build_email_message(data):
    return f"""
Hiring Form Submission

Client Name: {data['name']}

Client Contact Number: {data['num']}

Client Whatsapp Number: {data['wnum']}

Client Work/Service: {data['service']}

Work Duration: {data['duration']}

Client Email: {data['email']}

Address: {data['address']}

Pincode: {data['pin']}

Project Message:
{data['message']}
"""


def get_email_config():
    config = {
        "sender_email": os.environ.get("SENDER_EMAIL", "").strip(),
        "sender_password": os.environ.get("SENDER_PASSWORD", "").strip(),
        "receiver_email": os.environ.get("RECEIVER_EMAIL", "").strip(),
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com").strip(),
        "smtp_port": os.environ.get("SMTP_PORT", "587").strip(),
    }

    required = ["sender_email", "sender_password", "receiver_email"]
    missing = [key.upper() for key in required if not config[key]]
    if missing:
        raise RuntimeError(f"Missing email configuration: {', '.join(missing)}")

    try:
        config["smtp_port"] = int(config["smtp_port"])
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be a number.") from exc

    return config


def send_hiring_email(data):
    config = get_email_config()
    msg = MIMEText(build_email_message(data), "plain", "utf-8")
    msg["Subject"] = "Hiring Form Submission"
    msg["From"] = config["sender_email"]
    msg["To"] = config["receiver_email"]

    with smtplib.SMTP(
        config["smtp_host"],
        config["smtp_port"],
        timeout=10,
    ) as server:
        server.starttls()
        server.login(config["sender_email"], config["sender_password"])
        server.sendmail(
            config["sender_email"],
            config["receiver_email"],
            msg.as_string(),
        )


@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        data = get_hiring_data()
        errors = validate_hiring_data(data)

        if errors:
            return render_template(
                "index.html",
                data=data,
                errors=errors,
                services=SERVICES,
                error="Please correct the highlighted details.",
            )

        try:
            send_hiring_email(data)
            return redirect(url_for("home", success=1))
        except Exception:
            app.logger.exception("Hiring form submission failed")
            return render_template(
                "index.html",
                data=data,
                errors={},
                services=SERVICES,
                error=EMAIL_SEND_ERROR,
            )

    success = None
    if request.args.get("success") == "1":
        success = "Hiring form submitted successfully."

    return render_template("index.html", services=SERVICES, success=success)


if __name__ == "__main__":
    app.run(debug=False)
