from flask import Flask, session
import flask_sqlalchemy
import flask_bcrypt

app = Flask(__name__, template_folder="views")
bcrypt = flask_bcrypt.Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db' # REPLACE THIS.
db = flask_sqlalchemy.SQLAlchemy(app)
app.secret_key="VERY SECRET KEY" # Update for production.

@app.route('/')
def home():
    return 'Welcome to PlantSpeak!'

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
