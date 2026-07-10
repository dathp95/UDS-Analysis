import json

def load_uds_config (path="config/uds_config.json"):

    with open(path,"r", encoding="utf-8") as f:
        return json.load(f)