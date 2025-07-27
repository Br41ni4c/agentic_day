# Invoice Generator

This project is a simple invoice generator that takes user input from a web form and creates a JSON file representing the invoice.

## JSON Schema

The generated JSON files follow this schema:

```json
{
  "id": "string",
  "issuer_name": "string",
  "store_name": "string",
  "store_address": "string",
  "issuer_id": "string",
  "items": [
    {
      "name": "string",
      "cost": "number"
    }
  ],
  "cgst": "number",
  "sgst": "number",
  "gross_amount": "number",
  "timestamp": "string",
  "geo_coordinates": {
    "latitude": "number",
    "longitude": "number"
  }
}
```

## Running the Application

1. Install the required Python libraries:
   ```bash
   pip install Flask
   ```

2. Run the Flask application:
   ```bash
   python app.py
   ```

3. Open your web browser and go to `http://127.0.0.1:5000/` to access the invoice generator.
