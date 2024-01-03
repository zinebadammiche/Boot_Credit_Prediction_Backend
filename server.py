from flask import Flask, jsonify, request
import joblib
import pandas as pd
from functools import wraps 

app = Flask(__name__)
API_KEY = 'LPSIBD'


loaded_model = joblib.load('logistic_regression_model.pkl')

def require_api_key(view_function):
    @wraps(view_function)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('API-Key')

        if not api_key or api_key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401

        return view_function(*args, **kwargs)

    return decorated_function
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

if __name__ == '__main__':
    app.run(port=5000)  # Run Flask app on a specific port
