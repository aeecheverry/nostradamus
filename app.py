from flask import Flask, request, jsonify
import pandas as pd
import pickle
import os

app = Flask(__name__)

def convert_time_to_hour(X):
    return pd.to_datetime(X['time']).dt.hour.values.reshape(-1, 1)

model_file = 'model.pkl'
preprocessor_file = 'preprocessor.pkl'

with open(model_file, 'rb') as file:
    model = pickle.load(file)

with open(preprocessor_file, 'rb') as file:
    preprocessor = pickle.load(file)

def predict_severity(model, preprocessor, new_data):
    """
    Predict the severity of a new accident.

    :param model: The trained classification model.
    :param preprocessor: The preprocessing transformer used on the training data.
    :param new_data: Dictionary with the details of the new accident.
    :return: Severity prediction of the accident.
    """
    new_data_df = pd.DataFrame([new_data])

    new_data_processed = preprocessor.transform(new_data_df)

    severity_prediction = model.predict(new_data_processed)

    return int(severity_prediction[0])

def get_severity_type(severity):
    severity_types = {0: "none", 1: "low", 2: "medium", 3: "high"}
    return severity_types.get(severity, "unknown")

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    if isinstance(data, list):
        responses = []
        for accident in data:
            severity = predict_severity(model, preprocessor, accident)
            severity_type = get_severity_type(severity)
            responses.append({'geopoint': accident, 'severity': severity, 'type': severity_type})
        return jsonify(responses)
    else:
        severity = predict_severity(model, preprocessor, data)
        severity_type = get_severity_type(severity)
        return jsonify({'geopoint': data, 'severity': severity, 'type': severity_type})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
