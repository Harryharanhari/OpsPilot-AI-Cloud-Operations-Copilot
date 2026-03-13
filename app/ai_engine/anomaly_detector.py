import numpy as np
from sklearn.ensemble import IsolationForest
import logging

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False

    def detect(self, data: list) -> list:
        """
        Data should be a list of values (e.g., CPU, Memory, Latency)
        Returns a list of booleans: True if anomaly, False otherwise
        """
        if len(data) < 10: # Need some minimum data points to be meaningful
            return [False] * len(data)
        
        try:
            X = np.array(data).reshape(-1, 1)
            # Fits and predicts in one go for simple window-based detection
            # In a real system, we might maintain a rolling model
            predictions = self.model.fit_predict(X)
            # IsolationForest returns -1 for anomalies and 1 for normal
            return [p == -1 for p in predictions]
        except Exception as e:
            logging.error(f"Anomaly detection error: {e}")
            return [False] * len(data)

    def detect_zscore(self, data: list, threshold=3.0) -> list:
        """Simple Z-score anomaly detection"""
        if len(data) < 2:
            return [False] * len(data)
        
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return [False] * len(data)
            
        z_scores = [abs((x - mean) / std) for x in data]
        return [z > threshold for z in z_scores]

anomaly_detector = AnomalyDetector()
