from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')

# Access the database
db = client['satellite']

# Access the collection
collection = db['data']

# Fetch all entries
entries = collection.find(projection={'_id': False}, sort=[('country_of_origin', 1)])



# Print each entry
for entry in entries:
    print(entry)

# Close the connection
client.close()