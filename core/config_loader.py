import json
from  config.paths import CONFIG_DIR

def load_uds_config (path=CONFIG_DIR / "uds_config.json"):

    with open(path,"r", encoding="utf-8") as f:
        return json.load(f)