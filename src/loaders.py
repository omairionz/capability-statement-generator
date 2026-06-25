# loaders.py - loads YAML files and produces validates instances defined in models.py

from pathlib import Path
import yaml
from src.models import FirmProfile, PastPerformanceLibrary

def load_firm_profile(path: str | Path) -> FirmProfile:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw_yaml_data = yaml.safe_load(f)
    return FirmProfile.model_validate(raw_yaml_data) # this object can be changed to JSON format for Tier 1 Prompting

def load_past_performance(path: str | Path) -> PastPerformanceLibrary:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        raw_yaml_data = yaml.safe_load(f)
    return PastPerformanceLibrary.model_validate(raw_yaml_data) # this object can be changed to JSON format for Tier 1 Prompting 

def load_opportunity(path: str | Path) -> str:
    path = Path(path)
    return path.read_text(encoding="utf-8")
