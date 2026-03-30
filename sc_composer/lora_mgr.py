# -*- coding: utf-8 -*-
import os
from .i18n import t
from .core import load_config
from .constants import LORA_CHAR_PATH, LORA_SIT_PATH, WILD_1_PATH, WILD_2_PATH, WILD_3_PATH

def get_mgr_path(mgr_label):
    config = load_config()
    label_to_key = {
        t("lora_type_char"): "char",
        t("lora_type_sit"): "sit",
        t("wildcard_1"): "w1",
        t("wildcard_2"): "w2",
        t("wildcard_3"): "w3",
    }
    mgr_key = label_to_key.get(mgr_label, "char")
    mapping = {
        "char": LORA_CHAR_PATH,
        "sit": LORA_SIT_PATH,
        "w1": config.get("wildcard_1_path") or WILD_1_PATH,
        "w2": config.get("wildcard_2_path") or WILD_2_PATH,
        "w3": config.get("wildcard_3_path") or WILD_3_PATH,
    }
    return mapping.get(mgr_key)

def _ensure_dir(path):
    if not path: return
    d = os.path.dirname(path)
    if d: os.makedirs(d, exist_ok=True)

def load_lora_list(mgr_label):
    if mgr_label is None: return ""
    path = get_mgr_path(mgr_label)
    if path and os.path.exists(path):
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                with open(path, "r", encoding=enc, errors=("ignore" if enc == "cp932" else "strict")) as f:
                    return f.read()
            except Exception: continue
    return ""

def save_lora_list(mgr_label, content):
    path = get_mgr_path(mgr_label)
    if path:
        _ensure_dir(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return t("msg_lora_saved"), content
    return "Error", content

def append_lora_list(mgr_label, input_text):
    if not input_text or not input_text.strip():
        return load_lora_list(mgr_label), ""
    
    path = get_mgr_path(mgr_label)
    if not path: return "Error: Path not found", ""

    current = load_lora_list(mgr_label)
    new_line = input_text.strip()
    if current and not current.endswith("\n"):
        current += "\n"
    current += new_line + "\n"

    _ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(current)
    return current, ""
