from flask import Blueprint, render_template, request, redirect, url_for
import plaid

bp = Blueprint('settings', __name__, url_prefix='/settings')

PLAID_CLIENT_ID = 'your_plaid_client_id'
PLAID_SECRET = 'your_plaid_secret'
PLAID_PUBLIC_KEY = 'your_plaid_public_key'
PLAID_ENV = 'sandbox'  # Change to 'development' or 'production' as needed

client = plaid.Client(client_id=PLAID_CLIENT_ID,
                      secret=PLAID_SECRET,
                      public_key=PLAID_PUBLIC_KEY,
                      environment=PLAID_ENV)

@bp.route("/link", methods=["GET", "POST"])
def link_plaid_account():
    if request.method == 'POST':
        # Implement Plaid Link creation and handling logic here
        link_token_response = client.LinkToken.create({
            'user': {'client_user_id': 'unique_user_id'},  # Use a unique user identifier here
            'client_name': 'Your App Name',
            'products': ['transactions'],
            'country_codes': ['US'],
            'language': 'en',
        })
        link_token = link_token_response['link_token']
        return render_template('link_plaid.html', link_token=link_token)

    return render_template('settings.html')

@bp.route("/exchange_public_token", methods=["POST"])
def exchange_public_token():
    try:
        public_token = request.json.get('public_token')
        exchange_response = client.Item.public_token.exchange(public_token)
        access_token = exchange_response['access_token']

        # Store the access token securely, linked to the user's account
        user = get_current_user()  # Implement this method based on your user system
        user.plaid_access_token = access_token
        db.session.commit()

        return {'message': 'Account linked successfully'}

    except Exception as e:
        return {'error': str(e)}, 400