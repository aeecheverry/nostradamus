import pickle
from flask import Flask, request, jsonify
from models.predictor import Predictor
import pandas as pd
from utils.helpers import get_severity_type, calculate_probability
import os

app = Flask(__name__)

def convert_time_to_hour(X):
    return pd.to_datetime(X['time']).dt.hour.values.reshape(-1, 1)

# Crear instancias de los modelos
model_severity = Predictor('model.pkl', 'preprocessor.pkl')
model_restdays = Predictor('model_restdays.pkl', 'preprocessor.pkl')

# Cargar el diccionario de probabilidades
with open('probability.pkl', 'rb') as file:
    probability_dict = pickle.load(file)

def process_accident_data(accident):
    """Procesa los datos de un accidente individual."""
    # Extraer y calcular información relevante
    day_of_year = pd.to_datetime(accident['timestamp']).dayofyear
    accident_probability = calculate_probability(day_of_year, probability_dict)

    if 'time' not in accident:
        accident['time'] = pd.to_datetime(accident['timestamp']).time().strftime('%H:%M:%S')

    accident.pop('timestamp', None)
    return accident, accident_probability

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
        processed_accident, accident_probability = process_accident_data(accident)
        severity, restdays, severity_type = make_prediction(processed_accident)
        print("#$#####################",  severity, restdays, severity_type)
        response = {
            'id': accident['id'],
            'severity': severity,
            'restdays': restdays,
            'probability': accident_probability,
            'type': severity_type
        }
        responses.append(response)
    print(responses)
    return jsonify(responses)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
