import os
from google.cloud import firestore


def get_firestore_document(collection: str, document_id: str) -> str:
    """
    Fetches a single document from a specified Firestore collection.

    Args:
        collection: The name of the Firestore collection.
        document_id: The ID of the document to retrieve.

    Returns:
        A string containing the document data as a dictionary, or an
        error message if the document is not found or an error occurs.
    """
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        return "Error: The GCP_PROJECT_ID environment variable is not set."

    try:
        print(f"Connecting to Firestore project '{project_id}'...")
        db = firestore.Client(project=project_id)
        doc_ref = db.collection(collection).document(document_id)
        doc = doc_ref.get()

        if doc.exists:
            return f"Success: Found document. Data: {doc.to_dict()}"
        else:
            return f"Error: No document found with ID '{document_id}' in collection '{collection}'."

    except Exception as e:
        return f"An unexpected error occurred: {e}"


# This allows you to run the file directly to test the tool
if __name__ == "__main__":
    # To test, set your project ID and run this script.
    # You will need to have a collection and document that matches.
    # For example:
    # os.environ["GCP_PROJECT_ID"] = "your-gcp-project-id"
    # print(get_firestore_document(collection="your-collection", document_id="your-doc-id"))

    if not os.environ.get("GCP_PROJECT_ID"):
        print("Please set the GCP_PROJECT_ID environment variable to test this script.")
    else:
        # Replace with a real collection and document ID from your Firestore DB for testing
        # For example:
        # result = get_firestore_document(collection="users", document_id="alovelace")
        # print(result)
        print(
            "Firestore tool script is ready. Please test with a real collection and document ID."
        )
        get_firestore_document("item_metadata", "03415462-aef0-4758-90ea-48cc35d002bc")
