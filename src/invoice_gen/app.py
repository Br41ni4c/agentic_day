import dotenv
from flask import Flask, request, jsonify, render_template, redirect, url_for
import json
import uuid
from datetime import datetime
import os

app = Flask(__name__)

SETTINGS_FILE = 'settings.json'

dotenv.load_dotenv()

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

@app.route('/')
def index():
    settings = load_settings()
    if not settings:
        return redirect(url_for('settings'))
    return render_template('index.html', store_name=settings.get('store_name', ''), store_address=settings.get('store_address', ''))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        settings = {
            'store_name': request.form['store_name'],
            'store_address': request.form['store_address'],
            'issuer_id': request.form.get('issuer_id', '')
        }
        save_settings(settings)
        return redirect(url_for('index'))
    settings = load_settings()
    return render_template('settings.html', store_name=settings.get('store_name', ''), store_address=settings.get('store_address', ''), issuer_id=settings.get('issuer_id', ''))

@app.route('/generate_invoice', methods=['POST'])
def generate_invoice():
    data = request.form.to_dict(flat=False)
    settings = load_settings()
    gst_percentage = float(data['gst'][0])
    cgst_percentage = gst_percentage
    sgst_percentage = gst_percentage

    invoice = {
        'id': str(uuid.uuid4()),
        'issuer_name': data['issuer_name'][0],
        'store_name': settings.get('store_name', ''),
        'store_address': settings.get('store_address', ''),
        'issuer_id': settings.get('issuer_id', ''),
        'items': [],
        'cgst': cgst_percentage,
        'sgst': sgst_percentage,
        'gross_amount': 0,
        'timestamp': datetime.now().isoformat(),
        'geo_coordinates': {
            'latitude': 37.7749,
            'longitude': -122.4194
        }
    }
    total_cost = 0
    for i in range(len(data['item_name[]'])):
        item_name = data['item_name[]'][i]
        item_cost = float(data['item_cost[]'][i])
        invoice['items'].append({'name': item_name, 'cost': item_cost})
        total_cost += item_cost

    invoice['gross_amount'] = total_cost * (1 + (cgst_percentage + sgst_percentage) / 100)

    invoice_dir = os.path.join(app.root_path, 'invoices')
    os.makedirs(invoice_dir, exist_ok=True)
    invoice_filepath = os.path.join(invoice_dir, f"invoice_{invoice['id']}.json")
    with open(invoice_filepath, 'w') as f:
        json.dump(invoice, f, indent=4)

    # Call the function to create a wallet pass
    # from src.pass_generator.wallet_pass import create_wallet_pass_from_invoice
    # wallet_pass_response = create_wallet_pass_from_invoice(invoice)
    # print(f"Wallet Pass Creation Response: {wallet_pass_response}")
    from src.pass_generator_1 import main, makeReceiptData
    main(makeReceiptData(
        transactionId=invoice["id"],
        vendorName=invoice["issuer_name"],
        totalAmount=invoice["gross_amount"],
        itemsSummary=" ".join(i["name"] for i in invoice["items"])
    ))


    return jsonify(invoice)

if __name__ == '__main__':
    app.run(debug=True)
