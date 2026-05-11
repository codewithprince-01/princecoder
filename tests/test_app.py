import pytest

import app as app_module


@pytest.fixture
def client():
    app_module.app.config.update(TESTING=True)
    return app_module.app.test_client()


def valid_form_data():
    return {
        "name": "Test User",
        "service": "Web Development",
        "duration": "7 days",
        "num": "9876543210",
        "wnum": "9876543210",
        "email": "test@example.com",
        "address": "Test Address",
        "pin": "123456",
        "message": "Build a test website",
    }


def test_home_page_renders_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"Hiring Form" in response.data
    assert b"Submit Hiring Request" in response.data


def test_empty_submit_shows_validation_errors(client):
    response = client.post("/", data={})
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please correct the highlighted details." in html
    assert "Name is required." in html
    assert "Contact number must be exactly 10 digits." in html


def test_invalid_email_is_rejected(client):
    data = valid_form_data()
    data["email"] = "not-an-email"

    response = client.post("/", data=data)
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Please enter a valid email address." in html


def test_valid_submit_redirects_without_real_email(client, monkeypatch):
    sent_messages = []

    def fake_send_hiring_email(data):
        sent_messages.append(data.copy())

    monkeypatch.setattr(app_module, "send_hiring_email", fake_send_hiring_email)

    response = client.post("/", data=valid_form_data(), follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["Location"] == "/?success=1"
    assert len(sent_messages) == 1


def test_missing_email_config_shows_safe_error(client, monkeypatch):
    monkeypatch.delenv("SENDER_EMAIL", raising=False)
    monkeypatch.delenv("SENDER_PASSWORD", raising=False)
    monkeypatch.delenv("RECEIVER_EMAIL", raising=False)

    response = client.post("/", data=valid_form_data())
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert app_module.EMAIL_SEND_ERROR in html
    assert "Missing email configuration" not in html
    assert "SENDER_PASSWORD" not in html
