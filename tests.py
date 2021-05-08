from flask import Flask, request, session, url_for
from models.User import User
from controllers.UserController import LoginForm, RegistrationForm
from database import db

import pytest

testUsername = 'test123'
testUsername2 = 'test1234'
testPassword = 'password'
incorrectPassword = 'password!'

testEmail = 'email@example.com'

@pytest.fixture()
def setup(app):
    testUser = User(password=testPassword, username=testUsername, email='email@example.com')
    client = app.test_client()
    db.session.add(testUser)
    db.session.commit()
    yield ""
    db.session.delete(testUser)
    db.session.commit()

def test_register_form_valid(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email=testEmail)
    assert not form.validate()

def test_register_form_invalid_email(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email="test@testcom")
    assert not form.validate()

def test_register_form_invalid_password(app):
    form = RegistrationForm(username=testUsername, password=testPassword, email=testEmail)
    assert not form.validate()

def test_register(app):
    client = app.test_client()
    receipt=client.post("/register", data={'username': testUsername2, 'password': testPassword, 'confirm_password': testPassword, 'email': testEmail})
    with client:
        user = User.query.filter_by(username=testUsername2).one_or_none()
        assert user
        assert user.login(testPassword)
    db.session.delete(User.query.filter_by(username=testUsername2).one())
    db.session.commit()

def test_login(app, setup):
    client = app.test_client()
    client.post("/login", data={'username':testUsername, 'password':testPassword})
    with client:
        client.get('/')
        assert session.get('username') is not None
    assert User.query.filter_by(username=testUsername).one() is not None

def test_incorrect_password(app, setup):
    client = app.test_client()
    receipt = client.post("/login", data={'username':testUsername, 'password':incorrectPassword})
    with client:
        assert "Incorrect password" in str(receipt.get_data())
        assert session.get('username') is None

def test_multiple_incorrect_passwords(app, setup):
    client = app.test_client()
    for i in range(6):
        receipt = client.post("/login", data={'username':testUsername, 'password':incorrectPassword})
    with client:
        assert "You have exceeded the maximum number of password attempts. Please try again later." in str(receipt.get_data())
        assert session.get('username') is None

# import flask_unittest
#
# class RegisterUserTest(UserTest):
#     def test_registration(self, client):
#         form = RegistrationForm(request.form)
#         client.post(url_for('register'), data={form: form})
#         self.assertIsNotNone(User.query.first())