from flask import Flask, request, session, url_for
from models.User import User
from controllers.UserController import LoginForm, RegistrationForm
from database import db

import pytest

testUsername = 'test123'
testPassword = 'password'

@pytest.fixture()
def setup(app):
    testUser = User(password=testPassword, username=testUsername, email='email@example.com')
    client = app.test_client()
    db.session.add(testUser)
    db.session.commit()
    yield ""
    db.session.delete(testUser)
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
    client.post("/login", data={'username':testUsername, 'password':testPassword+"!"})
    with client:
        client.get('/')
        assert session.get('username') is None

# import flask_unittest
#
# class RegisterUserTest(UserTest):
#     def test_registration(self, client):
#         form = RegistrationForm(request.form)
#         client.post(url_for('register'), data={form: form})
#         self.assertIsNotNone(User.query.first())