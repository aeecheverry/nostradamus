import pickle
from flask import Flask, request, jsonify
from models.predictor import Predictor
import pandas as pd
from flask_cors import CORS 
from utils.helpers import get_severity_type, calculate_day_probability
import os
from api import api

app = Flask(__name__)
app.register_blueprint(api)
CORS(app)

def convert_time_to_hour(X):
    return pd.to_datetime(X['time']).dt.hour.values.reshape(-1, 1)

# Crear instancias de los modelos
model_severity = Predictor('model.pkl', 'preprocessor.pkl')
model_restdays = Predictor('model_restdays.pkl', 'preprocessor.pkl')

with open('probability.pkl', 'rb') as file:
    probability_dict = pickle.load(file)
with open('gender_distribution.pkl', 'rb') as f:
    prob_gender = pickle.load(f)
with open('vehicle_type_distribution.pkl', 'rb') as f:
    prob_vehicle_type = pickle.load(f)
with open('age_distribution.pkl', 'rb') as f:
    prob_age = pickle.load(f)

def get_age_group(age):
    """ Clasifica la edad en uno de los grupos predefinidos. """
    if age < 18:
        return '0-18'
    elif age < 30:
        return '19-30'
    elif age < 40:
        return '31-40'
    elif age < 50:
        return '41-50'
    elif age < 60:
        return '51-60'
    else:
        return '61-100'

def calculate_probability(accident):
    """Calcula la probabilidad compuesta basada en las distribuciones guardadas."""
    gender = accident['gender']
    age = accident['age']
    vehicle_type = accident['vehicle_type']
    age_group = get_age_group(age)
    gender_prob = prob_gender.get(gender, 0)
    vehicle_type_prob = prob_vehicle_type.get(vehicle_type, 0)
    age_prob = prob_age.get(age_group, 0)

    day_of_year = pd.to_datetime(accident['timestamp']).dayofyear
    day_probability = calculate_day_probability(day_of_year, probability_dict)

    return gender_prob * age_prob * vehicle_type_prob * day_probability

#Temporal Severity
def calculate_severity(restdays):
    if restdays < 10:
        return 0
    elif restdays < 20:
        return 1
    else:
        return 2

def process_accident_data(accident):
    """Procesa los datos de un accidente individual."""
    # Extraer y calcular información relevante
    if 'time' not in accident:
        accident['time'] = pd.to_datetime(accident['timestamp']).time().strftime('%H:%M:%S')

    accident.pop('timestamp', None)
    return accident

def make_prediction(accident):
    """Realiza predicciones basadas en los datos del accidente."""
    severity = model_severity.predict(accident)
    restdays = model_restdays.predict(accident)
    severity_type = get_severity_type(severity)
    return severity, restdays, severity_type

@app.route('/predict', methods=['POST'])
def predict_endpoint():
    data = request.json
    responses = []

    if not isinstance(data, list):
        data = [data]

    for accident in data:
        probability = calculate_probability(accident)
        processed_accident = process_accident_data(accident)
        severity, restdays, _ = make_prediction(processed_accident)
        severity = calculate_severity(restdays)
        severity_type = get_severity_type(severity)

        response = {
            'id': accident['id'],
            'severity': severity,
            'restdays': restdays,
            'probability': probability,
            'type': severity_type
        }
        responses.append(response)
    return jsonify(responses)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
