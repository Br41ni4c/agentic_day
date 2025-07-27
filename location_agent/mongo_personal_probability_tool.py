import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# --- Configuration ---
# IMPORTANT: Change these values to match your database and collection names.
DATABASE_NAME = "bill-mgmt"
COLLECTION_NAME = "item_metadata"
# -------------------


def get_mongo_client():
    """
    Establishes a connection to the MongoDB database using a connection
    string from the MONGO_URI environment variable.
    """
    mongo_uri = os.environ.get("MONGO_URI")
    if not mongo_uri:
        raise ConnectionFailure("The MONGO_URI environment variable is not set.")

    client = MongoClient(mongo_uri)
    # The ismaster command is cheap and does not require auth, allowing a quick
    # check to see if the server is available.
    client.admin.command("ismaster")
    return client


def calculate_user_location_probability(uid: str, location: str) -> str:
    """
    Calculates the probability of a user's documents being from a specific location.

    This tool connects to a MongoDB collection, counts the total number of
    documents for a given user (uid), and then determines what percentage of
    those documents include the specified location string in their 'geoInfo' field.

    Args:
        uid: The unique identifier for the user.
        location: The location string to search for (e.g., 'Nellore').

    Returns:
        A string describing the calculated probability or an error message.
    """
    client = None
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        print(f"Querying database for user '{uid}' and location '{location}'...")

        # Query for the total number of documents for the user
        total_docs_query = {"uid": uid}
        total_docs_count = collection.count_documents(total_docs_query)

        if total_docs_count == 0:
            return f"No documents found for user '{uid}'. Cannot calculate probability."

        # Query for the number of documents for the user that contain the location.
        # The 'geoInfo' field is a JSON string, so we do a case-insensitive substring search.
        location_docs_query = {
            "uid": uid,
            "geoInfo": {"$regex": location, "$options": "i"},
        }
        location_docs_count = collection.count_documents(location_docs_query)

        # Calculate the probability
        probability = (location_docs_count / total_docs_count) * 100

        return (
            f"Based on their history, the probability of a document from user "
            f"'{uid}' being from '{location}' is {probability:.2f}%."
        )

    except (ConnectionFailure, OperationFailure, Exception) as e:
        return f"An error occurred: {e}"
    finally:
        if client:
            client.close()


def _setup_mock_data():
    """A helper function to insert sample data for testing."""
    print("Setting up mock data...")
    client = None
    try:
        client = get_mongo_client()
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        collection.delete_many({"uid": "a36fcca2-70e1-4eeb-9f25-565de0ecfc32"})

        mock_data = [
            {
                "Document Name": "/item_metadata/doc1",
                "uid": "a36fcca2-70e1-4eeb-9f25-565de0ecfc32",
                "geoInfo": json.dumps({"location": "20, Kala Circle, Nellore-128613"}),
                "other_field": "value1",
            },
            {
                "Document Name": "/item_metadata/doc2",
                "uid": "a36fcca2-70e1-4eeb-9f25-565de0ecfc32",
                "geoInfo": json.dumps(
                    {"location": "15, Main Street, Bangalore-560001"}
                ),
                "other_field": "value2",
            },
            {
                "Document Name": "/item_metadata/doc3",
                "uid": "a36fcca2-70e1-4eeb-9f25-565de0ecfc32",
                "geoInfo": json.dumps(
                    {"location": "Shop 5, Market Square, Nellore-128613"}
                ),
                "other_field": "value3",
            },
            {
                "Document Name": "/item_metadata/doc4",
                "uid": "a36fcca2-70e1-4eeb-9f25-565de0ecfc32",
                "geoInfo": json.dumps({"location": "7, Tech Park, Hyderabad-500081"}),
                "other_field": "value4",
            },
        ]
        collection.insert_many(mock_data)
        print("Mock data has been set up successfully.")
    except (ConnectionFailure, OperationFailure, Exception) as e:
        print(f"Could not set up mock data: {e}")
    finally:
        if client:
            client.close()


# This allows you to run the file directly to test the tool
if __name__ == "__main__":
    if not os.environ.get("MONGO_URI"):
        print("Please set the MONGO_URI environment variable to test this script.")
    else:
        _setup_mock_data()
        # Test case
        probability = calculate_user_location_probability(
            uid="a36fcca2-70e1-4eeb-9f25-565de0ecfc32", location="Nellore"
        )
        print(probability)

