# src/core/config_manager.py
import json
import os

CONFIG_FILE = "mapping_config.json"

def save_mapping_config(mapping_dict):
    """Saves the user's column choices to a JSON file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(mapping_dict, f)
    except Exception as e:
        print(f"Failed to save config: {e}")

def load_mapping_config():
    """Loads previous column choices if they exist."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}