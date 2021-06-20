# PlantSpeak
Github Repository: https://github.com/PlantSpeak/PlantSpeak_webapp

This software is intended to be used in conjunction with [PlantSpeak_device](https://github.com/PlantSpeak/PlantSpeak_device) - software for the device that this web application communicates with.

## Software Requirements
- Python 3
- An MQTT broker such as Eclipse Mosquitto (this has been tested and works well for the purposes of the app).

## System Requirements
In terms of system requirements, these have not been tested rigorously and so are subject to speculation. However, because of the overhead of the python interpreter, additional libraries used and Mosquitto (MQTT broker) all having to run simultaneously, it is recommended that a few hundred MB of RAM be available on the system at idle (after booting when the OS has been loaded) for the software to run reliably. More RAM will be required to use PostgreSQL as the database server. The web application is known to run well with SQLite on a VPS with 1GB of RAM and a single modern virtual CPU core.

## Running the Development Server
### Install Prerequisites
First you must install python and python pip (package manager) on your system. The process will vary depending on operating system, but as an example you would type:

`sudo apt-get install python python-pip mosquitto`

to install on Ubuntu.

### Running the web application
#### Unix-based (Mac OS and Linux)
Enter the following commands into your unix terminal after pulling from github. This program requires python3 and python pip (package manager).

    cd <plantspeak_directory>

where ``plantspeak_directory`` is the folder containing the repository you pulled (PlantSpeak code). Then...

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py

#### Microsoft Windows
FOR WINDOWS MACHINES, Then...

    python3 -m venv venv
    venv/bin/activate
    pip install -r requirements.txt
    python app.py

You should now have the webserver running and accessible on localhost at port 5000.
Enter the following address in the web browser to access the webapp: ``localhost:5000``.

## Example Deployment
A deployment of the web application will be hosted on a Cloud VPS at the following address: https://www.plantspeak.tech
Alternatively, if this link does not work, the server can be accessed at http://128.199.252.105

Please note that connecting with HTTPS (via the first link) is required to receieve push notifications (in-browser).
