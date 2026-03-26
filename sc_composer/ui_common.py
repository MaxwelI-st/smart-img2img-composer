# -*- coding: utf-8 -*-
import os
from .i18n import t
from .utils import _clean_path
from .constants import CONFIG_PATH

def check_individual_health(path: str, label: str) -> str:
    path = _clean_path(path)
    if not path: return label
    if os.path.exists(path):
        return label.replace("❌ ", "").replace(" ❌", "")
    if "❌" not in label:
        return f"❌ {label}"
    return label

def update_ref_tags(profile_name: str):
    from .constants import PROMPT_PROFILES
    profile = PROMPT_PROFILES.get(profile_name, PROMPT_PROFILES["Standard / SDXL"])
    return profile["ref"], profile["neg"]

def _ensure_lora_files():
    from .constants import LORA_CHAR_PATH, LORA_SIT_PATH, LORA_CHAR_TEMPLATE, LORA_SIT_TEMPLATE
    for p, tmp in [(LORA_CHAR_PATH, LORA_CHAR_TEMPLATE), (LORA_SIT_PATH, LORA_SIT_TEMPLATE)]:
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write(tmp)
