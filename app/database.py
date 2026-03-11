from pymongo import MongoClient

client = MongoClient("mongodb+srv://devsecops:Dhakshitha123@cluster0.ch67hhy.mongodb.net/?appName=Cluster0")

db = client["devsecops"]

reports_collection = db["reports"]