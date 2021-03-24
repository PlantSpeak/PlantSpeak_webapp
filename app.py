from flask import Flask

app = Flask(__name__, template_folder="views")

@app.route('/')
def home():
    return 'Welcome to PlantSpeak!'

if __name__ == '__main__':
    app.run()
