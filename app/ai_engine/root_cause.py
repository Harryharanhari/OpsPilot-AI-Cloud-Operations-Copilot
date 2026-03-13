from datetime import datetime, timedelta
import logging

class RootCauseAnalyzer:
    def __init__(self):
        pass

    def analyze(self, error_logs: list, metric_anomalies: list, events: list) -> str:
        """
        Correlates logs, metric spikes, and system events to suggest a root cause.
        """
        if not error_logs and not metric_anomalies:
            return "No significant issues detected to analyze."

        summary_parts = []
        
        # Log correlation
        if error_logs:
            error_count = len(error_logs)
            top_errors = {}
            for log in error_logs:
                # Basic clustering
                key = log.message[:50]
                top_errors[key] = top_errors.get(key, 0) + 1
            
            main_error = max(top_errors, key=top_errors.get)
            summary_parts.append(f"Detected {error_count} error(s). Primary issue: '{main_error}'.")

        # Metric correlation
        if metric_anomalies:
            anom_types = set([a['name'] for a in metric_anomalies])
            summary_parts.append(f"Metric anomalies detected in {', '.join(anom_types)}.")

        # Event correlation (e.g., deployments)
        if events:
            summary_parts.append(f"Note: Significant system events occurred recently: {', '.join(events)}.")

        # Logic-based deduction
        if "timeout" in main_error.lower() or "connection" in main_error.lower():
            if "database" in main_error.lower():
                return "Potential Database Connection Issue: Correlation between high error rates and database-related messages suggests the DB might be under heavy load or unreachable."
            return "Potential Network/Connectivity Issue: Timeouts detected across multiple requests."
        
        if "out of memory" in main_error.lower() or "memory" in main_error.lower():
            return "Potential Memory Leak: System is reporting out-of-memory errors which correlate with increasing memory usage metrics."

        ra_explanation = " ".join(summary_parts) + " Preliminary analysis suggests a localized component failure."
        return ra_explanation

root_cause_analyzer = RootCauseAnalyzer()
