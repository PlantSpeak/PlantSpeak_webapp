# PlantSpeak
## Running the Development Server
Enter the following commands into your unix terminal after pulling from github. This program requires python3 and python pip (package manager).

    cd <plantspeak_directory>

where ``plantspeak_directory`` is the folder containing the repository you pulled (PlantSpeak code). Then...

    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py
	
FOR WINDOWS MACHINES, Then...

    python3 -m venv venv
    venv/bin/activate
    pip install -r requirements.txt
    python app.py

You should now have the webserver running and accessible on localhost at port 5000.
Enter the following address in the web browser to access the webapp: ``localhost:5000``.

## Example Deployment
A deployment of the web application will be hosted on a Cloud VPS at the address: http://128.199.252.105

Please note that HTTPS is not supported in this implementation and so will need to be changed to http in the prefix of the web address.
