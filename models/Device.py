from database import db
import time
from models.Plant import NAME_MAX_LENGTH, LOCATION_MAX_LENGTH

MAC_ADDR_LEN = 17

# A class designed to contain information about a device when one is detected by the webapp.
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(MAC_ADDR_LEN), unique=True)
    last_seen = db.Column(db.Integer)
    label = db.Column(db.String(NAME_MAX_LENGTH))
    location = db.Column(db.String(LOCATION_MAX_LENGTH))
    registered = db.Column(db.Integer)

    def __init__(self, mac_addr, last_seen_time):
        self.mac_address = mac_addr
        self.last_seen = last_seen_time