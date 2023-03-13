
from flask import Flask, request
from pymongo import MongoClient
import xml.etree.ElementTree as ET
import xml.dom.minidom
import time
import requests

# container name for mongo db
client = MongoClient("mongodb://mongo_database", 27017)

db = client.user_database
# Create two collections (user_table, transaction_table)
user_table = db.user_table
transaction_table = db.transaction_table

app = Flask(__name__)
