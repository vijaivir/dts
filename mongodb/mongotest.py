# from pymongo import MongoClient
# # Making Connection
# myclient = MongoClient("mongodb://localhost:27017/")
# # database
# db = myclient["GFG"]
# # Created or Switched to collection
# # names: GeeksForGeeks
# collection = db["Student"]
# # Creating Dictionary of records to be
# # inserted
# record = { "_id": 5,
#         "name": "Raju",
#         "Roll No": "1005",
#         "Branch": "CSE"}
# # Inserting the record1 in the collection
# # by using collection.insert_one()
# rec_id1 = collection.insert_one(record)
# # for x in collection.find():
# #     print(x)

from pymongo import MongoClient

# Define the connection string for the primary node
primary_connection_string = "mongodb://mongo_primary:27017/"

# Define the replica set configuration
replica_set_config = {
    "_id": "rs0",
    "members": [
        {"_id": 0, "host": "mongo_primary:27017"},
        {"_id": 1, "host": "mongo_secondary_1:27018"},
        {"_id": 2, "host": "mongo_secondary_2:27019"}
    ]
}

# Connect to the primary node
client = MongoClient(primary_connection_string)

# Initialize the replica set
client.admin.command("replSetInitiate", replica_set_config)

# Wait for the replica set to finish initializing
while True:
    status = client.admin.command("replSetGetStatus")
    if status["myState"] == 1:
        break

# Add the secondary nodes to the replica set
client.admin.command("replSetAdd", {"host": "mongo_secondary_1:27018"})
client.admin.command("replSetAdd", {"host": "mongo_secondary_2:27019"})

# Verify the replica set status
status = client.admin.command("replSetGetStatus")
print(status)







