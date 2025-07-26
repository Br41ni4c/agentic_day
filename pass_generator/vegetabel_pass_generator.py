import json
import os
import uuid
from datetime import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from google.auth import jwt, crypt


class WalletPassGenerator:
    """
    Class for creating and managing Generic passes in Google Wallet for
    vegetable vendor receipts.
    """

    def __init__(self, issuer_id: str):
        self.issuer_id = issuer_id
        self.key_file_path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')

        if not self.key_file_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "Please set it to the path of your service account key JSON file."
            )

        # Set up authenticated client
        self.auth()

    def auth(self):
        """Creates authenticated HTTP client using a service account file."""
        self.credentials = Credentials.from_service_account_file(
            self.key_file_path,
            scopes=['https://www.googleapis.com/auth/wallet_object.issuer']
        )
        self.client = build('walletobjects', 'v1', credentials=self.credentials)

    def create_or_get_class(self, class_suffix: str) -> str:
        """
        Creates a new Generic Class for vegetable vendor receipts if it doesn't exist,
        or retrieves an existing one.

        Args:
            class_suffix (str): A unique identifier for this class, e.g., 'vegetable_receipt_template'.

        Returns:
            str: The full class ID (e.g., 'ISSUER_ID.vegetable_receipt_template').
        """
        full_class_id = f'{self.issuer_id}.{class_suffix}'

        # Define the Generic pass class for a Vegetable Vendor Receipt
        generic_class_body = {
            'id': full_class_id,
            'classTemplateInfo': {
                'cardTemplateOverride': {
                    'cardRowTemplateInfos': [
                        {
                            'twoItems': {
                                'startItem': {
                                    'firstValue': {
                                        'fields': [
                                            {'fieldPath': 'object.textModulesData["total_amount"]'}
                                        ]
                                    }
                                },
                                'endItem': {
                                    'firstValue': {
                                        'fields': [
                                            {'fieldPath': 'object.textModulesData["purchase_date"]'}
                                        ]
                                    }
                                }
                            }
                        },
                        {
                            'twoItems': {
                                'startItem': {
                                    'firstValue': {
                                        'fields': [
                                            {'fieldPath': 'object.textModulesData["vendor_name"]'}
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                },
                'detailsTemplateOverride': {
                    'detailsItemInfos': [
                        {
                            'item': {
                                'firstValue': {
                                    'fields': [
                                        {'fieldPath': 'class.imageModulesData["vendor_logo_header"]'}
                                    ]
                                }
                            }
                        },
                        {
                            'item': {
                                'firstValue': {
                                    'fields': [
                                        {'fieldPath': 'class.textModulesData["receipt_description"]'}
                                    ]
                                }
                            }
                        },
                        {
                            'item': {
                                'firstValue': {
                                    'fields': [
                                        {'fieldPath': 'class.linksModuleData.uris["vendor_website"]'}
                                    ]
                                }
                            }
                        },
                        {
                            'item': {
                                'firstValue': {
                                    'fields': [
                                        {'fieldPath': 'class.linksModuleData.uris["view_full_receipt"]'}
                                    ]
                                }
                            }
                        }
                    ]
                }
            },
            'imageModulesData': [
                {
                    'mainImage': {
                        'sourceUri': {
                            'uri': 'https://storage.googleapis.com/wallet-lab-tools-codelab-artifacts-public/google-io-2021-card.png',
                        'contentDescription': {
                            'defaultValue': {
                                'language': 'en-US',
                                'value': 'Vegetable Market Banner'
                            }
                        }
                    },
                    'id': 'vendor_logo_header'
                }
                }
            ],
            'textModulesData': [
                {
                    'header': 'Digital Receipt',
                    'body': 'Thank you for your fresh produce purchase!',
                    'id': 'receipt_description'
                }
            ],
            'linksModuleData': {
                'uris': [
                    {
                        'uri': 'https://your-vendor-website.com',
                        'description': 'Visit Our Website',
                        'id': 'vendor_website'
                    },
                    {
                        'uri': 'https://your-receipt-hosting.com/receipts/{receipt_id}', # Placeholder for detailed receipt
                        'description': 'View Full Itemized Receipt',
                        'id': 'view_full_receipt'
                    }
                ]
            },
            'issuerName': 'My Local Greens',
            'reviewStatus': 'UNDER_REVIEW' # Required for new classes
        }

        try:
            # Try to get the class
            self.client.genericclass().get(resourceId=full_class_id).execute()
            print(f'Class {full_class_id} already exists.')
        except HttpError as e:
            if e.status_code == 404:
                # Class does not exist, create it
                print(f'Class {full_class_id} not found. Creating...')
                self.client.genericclass().insert(body=generic_class_body).execute()
                print(f'Class {full_class_id} created successfully.')
            else:
                # Re-raise other HTTP errors
                print(f"Error checking/creating class: {e.content}")
                raise

        return full_class_id

    def create_receipt_pass_link(self, class_id: str, receipt_data: dict) -> str:
        """
        Creates a new generic object for a vegetable vendor receipt and generates
        an "Add to Google Wallet" link for it.

        Args:
            class_id (str): The ID of the generic class this object belongs to.
            receipt_data (dict): A dictionary containing receipt details, e.g.,
                                 'transactionId', 'vendorName', 'purchaseDate',
                                 'totalAmount', 'paymentMethod', 'itemsSummary'.

        Returns:
            str: An "Add to Google Wallet" URL.
        """
        # Generate a unique object ID for this receipt
        # Use transactionId from input, fall back to a UUID if not provided
        transaction_id = receipt_data.get('transactionId', f'TXN_{uuid.uuid4()}')
        object_suffix = f'receipt_{transaction_id}'
        full_object_id = f'{self.issuer_id}.{object_suffix}'

        # Define the Generic pass object for the receipt
        generic_object_body = {
            'id': full_object_id,
            'classId': class_id,
            'state': 'ACTIVE',
            'hexBackgroundColor': '#5cb85c', # A friendly green for vegetables
            'logo': {
                'sourceUri': {
                    'uri': 'https://storage.googleapis.com/tachyon-5-bucket/tachyonion.jpg'
                }
            },
            'cardTitle': {
                'defaultValue': {
                    'language': 'en',
                    'value': 'Digital Receipt'
                }
            },
            'subheader': {
                'defaultValue': {
                    'language': 'en',
                    'value': receipt_data.get('vendorName', 'Local Vegetable Vendor')
                }
            },
            'header': {
                'defaultValue': {
                    'language': 'en',
                    'value': f"Total: ₹ {receipt_data.get('totalAmount', '0.00')}"
                }
            },
            'barcode': {
                'type': 'QR_CODE',
                'value': transaction_id,
                'alternateText': f'Receipt: {transaction_id}'
            },
            'heroImage': {
                'sourceUri': {
                    'uri': 'https://storage.googleapis.com/tachyon-5-bucket/tachyonion.jpg'
                },
                'contentDescription': {
                    'defaultValue': {
                        'language': 'en-US',
                        'value': 'Fresh Vegetables Banner'
                    }
                }
            },
            'textModulesData': [
                {
                    'header': 'VENDOR',
                    'body': receipt_data.get('vendorName', 'N/A'),
                    'id': 'vendor_name'
                },
                {
                    'header': 'DATE',
                    'body': receipt_data.get('purchaseDate', datetime.now().strftime('%Y-%m-%d')),
                    'id': 'purchase_date'
                },
                {
                    'header': 'TOTAL',
                    'body': f"₹ {receipt_data.get('totalAmount', '0.00')}",
                    'id': 'total_amount'
                },
                {
                    'header': 'PAYMENT',
                    'body': receipt_data.get('paymentMethod', 'N/A'),
                    'id': 'payment_method'
                },
                {
                    'header': 'ITEMS',
                    'body': receipt_data.get('itemsSummary', 'No items listed'),
                    'id': 'items_summary'
                },
                {
                    'header': 'RECEIPT ID',
                    'body': transaction_id,
                    'id': 'receipt_id'
                }
            ],
            # Note: For the 'view_full_receipt' link in the class,
            # you might want to dynamically update the URI here with the specific transactionId
            # This would require patching the object after creation if the class link refers to object data.
            # For simplicity, if the link is only in the class, it's a generic link.
            # If you need an object-specific link, you'd add it directly here:
            'linksModuleData': {
                'uris': [
                    {
                        'uri': f'https://your-receipt-hosting.com/receipts/{transaction_id}',
                        'description': 'View Full Itemized Receipt Online',
                        'id': 'full_receipt_link'
                    }
                ]
            }
        }

        # Check if the object already exists
        try:
            self.client.genericobject().get(resourceId=full_object_id).execute()
            print(f'Object {full_object_id} already exists. Generating link for existing object.')
        except HttpError as e:
            if e.status_code == 404:
                # Object does not exist, create it
                print(f'Object {full_object_id} not found. Creating...')
                self.client.genericobject().insert(body=generic_object_body).execute()
                print(f'Object {full_object_id} created successfully.')
            else:
                print(f"Error checking/creating object: {e.content}")
                raise

        # Create the JWT claims for adding the object to Wallet
        claims = {
            'iss': self.credentials.service_account_email,
            'aud': 'google',
            'origins': [], # List of trusted origins for "Add to Google Wallet" button/link
            'typ': 'savetowallet',
            'payload': {
                'genericObjects': [
                    {
                        'id': full_object_id,
                        'classId': class_id
                    }
                ]
            }
        }

        # Sign the JWT with your service account private key
        signer = crypt.RSASigner.from_service_account_file(self.key_file_path)
        token = jwt.encode(signer, claims).decode('utf-8')

        save_url = f'https://pay.google.com/gp/v/save/{token}'
        return save_url


# --- Example Usage ---
if __name__ == '__main__':
    # TODO: Replace with your actual Issuer ID
    YOUR_ISSUER_ID = '3388000000022973951' # Example Issuer ID. Get yours from Google Wallet API Console

    # Define a suffix for your class
    CLASS_SUFFIX_RECEIPT = 'vegetable_receipt_class_v1'

    try:
        wallet_generator = WalletPassGenerator(YOUR_ISSUER_ID)

        # 1. Ensure the pass class exists (or create it if not)
        receipt_class_id = wallet_generator.create_or_get_class(CLASS_SUFFIX_RECEIPT)
        print(f"\nUsing Pass Class ID: {receipt_class_id}")

        # 2. Prepare sample receipt data
        sample_receipt_data = {
            'transactionId': f"TXN_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}",
            'vendorName': 'Fresh Greens Market',
            'purchaseDate': datetime.now().strftime('%Y-%m-%d'),
            'totalAmount': '125.50',
            'paymentMethod': 'UPI',
            'itemsSummary': 'Tomatoes (1kg), Spinach (500g), Onions (2kg), Coriander (1 bunch)'
        }

        # 3. Create the pass object and get the "Add to Google Wallet" link
        save_link = wallet_generator.create_receipt_pass_link(receipt_class_id, sample_receipt_data)

        print("\n--- Success! ---")
        print("Copy and paste this link into your browser to add the pass to your Google Wallet:")
        print(save_link)
        print("\nNote: For the pass to appear correctly, the class needs to be approved by Google. "
              "New classes start as 'UNDER_REVIEW'.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except HttpError as e:
        print(f"Google API Error: {e.status_code} - {e.error_details}")
        if e.status_code == 403:
            print("Check if your service account has the 'Google Wallet API Issuer' role.")
        elif e.status_code == 404:
            print("Ensure your Issuer ID is correct and the Wallet API is enabled for your project.")
        print("Full error response:", e.content.decode('utf-8'))
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
