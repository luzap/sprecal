import os
from googleapiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

CLIENT_SECRET_FILE = "client_secret.json"
SCOPES = "https://www.googleapis.com/auth/spreadsheets"
APPLICATION_NAME = "Sprecal"
