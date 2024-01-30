def get_severity_type(severity):
    severity_types = {0: "none", 1: "low", 2: "medium", 3: "high"}
    return severity_types.get(severity, "unknown")

def calculate_probability(day_of_year, probability_dict):
    return probability_dict.get(day_of_year, 0)
