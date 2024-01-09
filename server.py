from flask import Flask, jsonify, request
import joblib
import pandas as pd
from functools import wraps 
from pymongo import MongoClient
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json
from bson import ObjectId
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, unset_jwt_cookies
)
app = Flask(__name__)
API_KEY = 'LPSIBD'
# Initialize JWT manager
app.config['JWT_SECRET_KEY'] = 'HAMZA_ELHAIKI'  # Replace with a secure secret key
jwt = JWTManager(app)


loaded_model = joblib.load('logistic_regression_model.pkl')

uri = "mongodb+srv://agile:agile@cluster0.xkmpvai.mongodb.net/"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client.get_database('pred1')  # Replace 'mydatabase' with your database name
collection = db['Loan_data']  # Replace 'mycollection' with your collection name
users_collection = db['Users']  # Replace 'Users' with your collection name for user data

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('API-Key')

        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401

        return view_function(*args, **kwargs)

    return decorated_function

@app.route('/save_loan_data', methods=['POST'])
def save_loan_data():
    try:
        # Get the JSON data from the POST request
        request_data = request.get_json()
        # Extract required fields from the JSON data
        data_to_insert = {
            'id_user': request_data.get('id_user'),
            'ApplicantIncome': request_data.get('ApplicantIncome'),
            'Gender': request_data.get('Gender'),
            'Married': request_data.get('Married'),
            'Dependents': request_data.get('Dependents'),
            'Education': request_data.get('Education'),
            'Self_Employed': request_data.get('Self_Employed'),
            'CoapplicantIncome': request_data.get('CoapplicantIncome'),
            'LoanAmount': request_data.get('LoanAmount'),
            'Loan_Amount_Term': request_data.get('Loan_Amount_Term'),
            'Credit_History': request_data.get('Credit_History'),
            'Property_Area': request_data.get('Property_Area'),
            'LoanStatus': request_data.get('LoanStatus')
        }

        # Insert data into the MongoDB collection
        collection.insert_one(data_to_insert)

        return jsonify({'message': 'Data saved successfully'}), 200
    except Exception as e:
        return jsonify({'message': 'Failed to save data', 'error': str(e)}), 500

@app.route('/get_loan_data/<user_id>', methods=['GET'])
def get_data_by_id(user_id):
    try:
        # Find all data based on the provided user ID
        cursor = collection.find({'id_user': user_id})

        # Convert the cursor to a list of dictionaries with ObjectId converted to string
        data_list = json.loads(json.dumps(list(cursor), cls=CustomJSONEncoder))

        if data_list:
            return jsonify({'message': 'Data found', 'data': data_list}), 200
        else:
            return jsonify({'message': 'No data found for the user ID'}), 404

    except Exception as e:
        return jsonify({'message': 'Failed to fetch data', 'error': str(e)}), 500


@app.route('/predictLoanStatus', methods=['POST'])
@require_api_key
def predict_loan_status():
    data = request.json
    # Extract input data from request
    ApplicantIncome = data.get('ApplicantIncome')
    Gender = data.get('Gender')
    Married = data.get('Married')
    Dependents = data.get('Dependents')
    Education = data.get('Education')
    Self_Employed = data.get('Self_Employed')
    CoapplicantIncome = data.get('CoapplicantIncome')
    LoanAmount = data.get('LoanAmount')
    Loan_Amount_Term = data.get('Loan_Amount_Term')
    Credit_History = data.get('Credit_History')
    Property_Area = data.get('Property_Area')

    # Call prediction function
    prediction = predict_loan_status_logic(ApplicantIncome, Gender, Married, Dependents, Education, Self_Employed, CoapplicantIncome, LoanAmount, Loan_Amount_Term, Credit_History, Property_Area)

    # Return prediction as JSON response
    return jsonify({"prediction": prediction})

def predict_loan_status_logic(ApplicantIncome, Gender, Married, Dependents, Education, Self_Employed, CoapplicantIncome, LoanAmount, Loan_Amount_Term, Credit_History, Property_Area):
    # Create a DataFrame with the user input
    user_input = pd.DataFrame({
        'Gender': [int(Gender)],
        'Married': [int(Married)],
        'Dependents': [int(Dependents)],
        'Education': [int(Education)],
        'Self_Employed': [int(Self_Employed)],
        'ApplicantIncome': [int(ApplicantIncome)],
        'CoapplicantIncome': [int(CoapplicantIncome)],
        'LoanAmount': [int(LoanAmount)],
        'Loan_Amount_Term': [int(Loan_Amount_Term)],
        'Credit_History': [int(Credit_History)],
        'Property_Area': [int(Property_Area)]
    })

    # Encode categorical variables
    user_input = pd.get_dummies(user_input)

    prediction = loaded_model.predict(user_input)

    if prediction == 0:
        return "No"
    else:
        return "Yes"

bcrypt = Bcrypt(app)

@app.route('/register', methods=['POST'])
def register():
    try:
        # Get the JSON data from the POST request
        request_data = request.get_json()

        # Check if the username or email already exists
        existing_user = users_collection.find_one({
            '$or': [
                {'username': request_data.get('username')},
                {'email': request_data.get('email')}
            ]
        })

        if existing_user:
            return jsonify({'message': 'Username or email already exists'}), 400

        # Hash the password before storing it
        hashed_password = bcrypt.generate_password_hash(request_data.get('password')).decode('utf-8')

        # Prepare user data to insert into the MongoDB collection
        user_data = {
            'username': request_data.get('username'),
            'email': request_data.get('email'),
            'password': hashed_password  # Store the hashed password
        }

        # Insert the user data into the Users collection
        users_collection.insert_one(user_data)

        return jsonify({'message': 'User created successfully'}), 201
    except Exception as e:
        return jsonify({'message': 'Failed to create user', 'error': str(e)}), 500

@app.route('/current_user', methods=['GET'])
@jwt_required()
def current_user():
    current_user_id = get_jwt_identity()
    return jsonify({'user_id': current_user_id}), 200
@app.route('/login', methods=['POST'])
def login():
    try:
        # Get the JSON data from the POST request
        request_data = request.get_json()

        # Find the user by username or email
        user = users_collection.find_one({
            '$or': [
                {'username': request_data.get('username')},
                {'email': request_data.get('email')}
            ]
        })

        if user and bcrypt.check_password_hash(user['password'], request_data.get('password')):
            # Authentication successful, generate JWT token
            access_token = create_access_token(identity=str(user['_id']))

            # Return the token as a response
            return jsonify({'access_token': access_token}), 200
        else:
            # Authentication failed
            return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'message': 'Failed to authenticate', 'error': str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    resp = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(resp)
    return resp, 200
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)  # Example port, adjust as needed
