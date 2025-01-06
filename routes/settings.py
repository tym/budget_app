from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.api_client import ApiClient
from flask_login import login_required, current_user
from models.models import Expense, db   


bp = Blueprint('settings', __name__, url_prefix='/settings')

PLAID_CLIENT_ID = '677b2f530e534e0022b15cbe'
PLAID_SECRET = 'ee4bb64cb716566c8cd8b45fdaa17f'
PLAID_ENV = 'sandbox'  # Change to 'development' or 'production' as needed
# Initialize the API client
api_client = ApiClient()
api_client.configuration.api_key["PLAID-CLIENT-ID"] = PLAID_CLIENT_ID
api_client.configuration.api_key["PLAID-SECRET"] = PLAID_SECRET
api_client.configuration.host = f"https://{PLAID_ENV}.plaid.com"  # Ensure correct environment URL

# Create the Plaid API client
plaid_client = plaid_api.PlaidApi(api_client)

# Base route for settings page
@bp.route("/", methods=["GET"])
@login_required
def settings():
    return render_template('settings.html')

@bp.route("/link", methods=["GET", "POST"])
@login_required
def link_plaid_account():
    if request.method == 'POST':
        try:
            # Create Plaid link token
            link_token_response = plaid_client.LinkToken.create({
                'user': {'client_user_id': str(current_user.id)},  # Use a unique user identifier
                'client_name': 'Budget App',
                'products': ['transactions'],
                'country_codes': ['US'],
                'language': 'en',
            })
            
            # Print the link token response for debugging
            print(f"Link Token Response: {link_token_response}")

            link_token = link_token_response['link_token']

            # Render the template with the generated link token
            return render_template('link_plaid.html', link_token=link_token)

        except Exception as e:
            print(f"Error creating Plaid link token: {e}")
            return jsonify({'error': 'Error creating Plaid link token'}), 400

    return render_template('settings.html')



@bp.route("/exchange_public_token", methods=["POST"])
@login_required
def exchange_public_token():
    try:
        public_token = request.json.get('public_token')
        exchange_response = plaid_client.Item.public_token.exchange(public_token)
        access_token = exchange_response['access_token']

        # Store the access token securely, linked to the user's account
        current_user.plaid_access_token = access_token
        db.session.commit()

        return jsonify({'message': 'Account linked successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@bp.route("/fetch_transactions", methods=["GET"])
@login_required
def fetch_transactions():
    try:
        access_token = current_user.plaid_access_token

        # Fetch recent transactions from Plaid
        transactions_response = plaid_client.Transactions.get(
            access_token, start_date='2023-01-01', end_date='2023-12-31')
        transactions = transactions_response['transactions']

        # Process and store transactions in the expenses table
        for txn in transactions:
            new_expense = Expense(
                description=txn['name'],
                amount=txn['amount'],
                date=datetime.strptime(txn['date'], '%Y-%m-%d').date(),
                category='Bank Transaction',  # Set appropriate category
                cleared=True,
                linked_id=None  # Add logic for linking the transaction to bills/income if needed
            )
            db.session.add(new_expense)
        db.session.commit()

        return jsonify({'message': 'Transactions fetched successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 400