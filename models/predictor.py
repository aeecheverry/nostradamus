import pickle
import pandas as pd

class Predictor:
    def __init__(self, model_path, preprocessor_path):
        with open(model_path, 'rb') as file:
            self.model = pickle.load(file)
        with open(preprocessor_path, 'rb') as file:
            self.preprocessor = pickle.load(file)

    def predict(self, data):
        data_df = pd.DataFrame([data])
        data_processed = self.preprocessor.transform(data_df)
        prediction = self.model.predict(data_processed)
        return int(prediction[0])