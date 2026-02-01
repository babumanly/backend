# plant_disease_backend/app/economic_service.py

# Data contains:
# - 'yield_per_acre_kg': Average yield in kilograms per acre.
# - 'market_price_per_kg': Average market price in INR per kilogram.
# - 'max_loss_factor': The maximum potential yield loss from this disease (as a decimal).

CROP_DATA = {
    "Apple___Apple_scab": {
        "yield_per_acre_kg": 8000,  # Approx. 8-10 tonnes
        "market_price_per_kg": 135,
        "max_loss_factor": 0.70, # Can be up to 70%
        "crop_name": "Apple"
    },
    "Tomato___Late_blight": {
        "yield_per_acre_kg": 20000, # Approx. 20 tonnes/ha
        "market_price_per_kg": 18,
        "max_loss_factor": 0.80, # Can be up to 80-100%
        "crop_name": "Tomato"
    },
    "Potato___Late_blight": {
        "yield_per_acre_kg": 12000, # Approx. 12 tonnes/ha for AP
        "market_price_per_kg": 15,
        "max_loss_factor": 0.75,
        "crop_name": "Potato"
    },
    # Add a default for diseases not in this specific list
    "default": {
        "yield_per_acre_kg": 15000,
        "market_price_per_kg": 20,
        "max_loss_factor": 0.30, # A conservative default
        "crop_name": "General Crop"
    }
}

def get_disease_key(disease_name: str) -> str:
    """Finds the matching key in CROP_DATA, even with prefixes."""
    for key in CROP_DATA.keys():
        if key.lower() in disease_name.lower():
            return key
    return "default"

def calculate_economic_impact(disease_name: str, severity: float) -> dict:
    """
    Calculates the estimated financial loss based on disease and severity.
    """
    disease_key = get_disease_key(disease_name)
    data = CROP_DATA[disease_key]

    # Simple linear model: financial_loss = (total_value_per_acre) * (max_loss_factor) * (severity_as_decimal)
    total_value = data['yield_per_acre_kg'] * data['market_price_per_kg']
    
    # We use the severity as a direct indicator of potential loss percentage
    severity_decimal = severity / 100
    
    potential_loss = total_value * data['max_loss_factor'] * severity_decimal

    return {
        "crop_name": data['crop_name'],
        "potential_financial_loss_min": int(potential_loss * 0.75), # Provide a range
        "potential_financial_loss_max": int(potential_loss),
        "yield_loss_percentage": int(data['max_loss_factor'] * severity_decimal * 100)
    }