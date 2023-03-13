from pymongo import MongoClient
# Making Connection
myclient = MongoClient("mongodb://localhost:27017/")
# database
db = myclient["GFG"]
# Created or Switched to collection
# names: GeeksForGeeks
collection = db["Student"]
# Creating Dictionary of records to be
# inserted
record = { "_id": 5,
        "name": "Raju",
        "Roll No": "1005",
        "Branch": "CSE"}
# Inserting the record1 in the collection
# by using collection.insert_one()
rec_id1 = collection.insert_one(record)
# for x in collection.find():
#     print(x)







