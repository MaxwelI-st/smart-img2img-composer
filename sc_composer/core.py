# -*- coding: utf-8 -*-
import os
import json
import random
import re
from datetime import datetime
from PIL import Image
from .constants import CONFIG_PATH, DEFAULT_CONFIG, INVENTORY_PATH, IMAGE_EXTENSIONS
from .utils import _clean_path, _polish_prompt, get_image_files
from .i18n import t, invalidate_lang_cache

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = {**DEFAULT_CONFIG, **json.load(f)}
                for k in ["image_folder", "memo_file", "wildcard_1_path", "wildcard_2_path", "wildcard_3_path"]:
                    if k in config and isinstance(config[k], str):
                        config[k] = _clean_path(config[k])
                return config
        except Exception: pass
    return dict(DEFAULT_CONFIG)

def save_config(config: dict) -> str:
    try:
        dir_path = os.path.dirname(CONFIG_PATH)
        if dir_path: os.makedirs(dir_path, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        invalidate_lang_cache()
        return t("msg_settings_saved")
    except IOError as e:
        return f"{t('msg_settings_err')} {e}"

def load_inventory():
    if not os.path.exists(INVENTORY_PATH): return {}
    try:
        with open(INVENTORY_PATH, "r", encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

def save_inventory(data):
    try:
        with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception: pass

def get_inventory_weighted_choice(item_list, category_key):
    if not item_list: return None
    inventory = load_inventory()
    cat_hist = dict(inventory.get(category_key, {}))
    for item in item_list:
        if item not in cat_hist: cat_hist[item] = 0
    weights = [1.0 / (float(cat_hist[item]) + 1.0) for item in item_list]
    choice = random.choices(item_list, weights=weights, k=1)[0]
    cat_hist[choice] += 1
    inventory[category_key] = cat_hist
    save_inventory(inventory)
    return choice

def parse_memo_file(memo_path: str) -> dict:
    memo_path = _clean_path(memo_path)
    sections = {}
    if not memo_path or not os.path.isfile(memo_path): return sections
    try:
        content = ""
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                with open(memo_path, "r", encoding=enc) as f: content = f.read()
                break
            except Exception: continue
        if not content: return sections
        cur_key, cur_data, mode = None, {"positive": [], "negative": [], "lora": []}, "positive"
        def _save():
            if cur_key:
                sections[cur_key] = {
                    "positive": ", ".join(cur_data["positive"]),
                    "negative": ", ".join(cur_data["negative"]),
                    "lora": cur_data["lora"]
                }
        for line in content.splitlines():
            s_raw = line.strip()
            if not s_raw or s_raw.startswith("#"): continue
            m = re.match(r"^\[(.+)\]$", s_raw)
            if m:
                _save(); cur_key = m.group(1).strip().lower()
                cur_data, mode = {"positive": [], "negative": [], "lora": []}, "positive"
                continue
            
            # P2: "positive:" と "positive" 両方を受け付ける
            s_low = s_raw.lower().rstrip(":").strip()
            if s_low in ("positive", "negative", "lora"):
                mode = s_low; continue
            if cur_key: cur_data[mode].append(s_raw)
        _save()
    except Exception: pass
    return sections

def compose_prompt(folder, memo, threshold, fallback=True, auto_l=True, l_off=0.0, w1="", w2="", w3="", prof_name="Standard / SDXL", inv_mode=False, selection_mode="random"):
    """5タプル (img_path, pos, neg, log, section_name) を返す共通関数。
    UI プレビュー用には compose_prompt_preview() を使うこと。"""
    return _compose_core(folder, memo, threshold, selection_mode=selection_mode)

def compose_prompt_preview(folder, memo, threshold, fallback=True, auto_l=True, l_off=0.0, w1="", w2="", w3="", prof_name="Standard / SDXL", inv_mode=False):
    """設定タブの「構成テスト」ボタン用: プレビュー文字列を返す。"""
    img, pos, neg, log, sec = _compose_core(folder, memo, threshold)
    if not img: return log
    from .constants import PROMPT_PROFILES
    profile = PROMPT_PROFILES.get(prof_name, next(iter(PROMPT_PROFILES.values())))
    p_neg = profile.get("neg", "")
    return f"--- PREVIEW ---\nSection: [{sec}]\nImage: {os.path.basename(img)}\n\nPositive:\n{pos}\n\nNegative:\n{neg}\n(Profile Neg: {p_neg})\n\nLog:\n{log}"

def _compose_core(folder, memo, threshold, selection_mode="random"):
    from .utils import get_image_files, _clean_path
    folder_clean = _clean_path(folder)
    memo_clean = _clean_path(memo)
    files = get_image_files(folder_clean)
    if not files: return None, "", "", t("no_images"), ""
    config = load_config()
    if selection_mode == "sequential":
        idx = config.get("last_sequential_index", 0) % len(files)
        sel = files[idx]; config["last_sequential_index"] = idx + 1; save_config(config)
    else: sel = random.choice(files)
    sections = parse_memo_file(memo_clean)
    if not sections: return sel, "", "", t("log_no_sections"), ""
    from difflib import SequenceMatcher
    fname = os.path.splitext(os.path.basename(sel))[0].lower()
    # Score should be -1.0 to allow 0.0 match
    for k in sections:
        if k == "default": continue
        sc = SequenceMatcher(None, fname, k).ratio()
        if sc >= threshold and sc > best_score: best_score, best_sec = sc, k
    if not best_sec:
        if "default" in sections: best_sec = "default"
        else: return sel, "", "", t("log_no_match"), ""
    
    data = sections[best_sec]
    pos = data.get("positive", "")
    neg = data.get("negative", "")
    loras = data.get("lora", [])
    if loras:
        # Append LoRA tags to positive prompt
        pos = ", ".join([pos] + loras) if pos else ", ".join(loras)
    return sel, pos, neg, f"Matched: {best_sec} ({best_score:.2f})", best_sec

def apply_lora_offset(prompt: str, offset: float) -> str:
    if offset == 0.0: return prompt
    def repl(m):
        base, val = m.group(1), float(m.group(2))
        new_val = max(0.0, min(2.0, val + offset))
        return f"<lora:{base}:{new_val:.2f}>"
    return re.sub(r'<lora:([^:]+):([-+]?\d*\.?\d+)>', repl, prompt)

def save_all_settings(lang, img_f, memo, threshold, count, fallback, auto_l, confidence, pos, neg, c_dict, c_base, c_char, c_nsfw, w1, w2, w3, offset, mosaic_auto, mosaic_level, c_dict_enabled, auto_opt, custom_tags, active_prof, polish, smart_neg, smart_neg_mode, inventory_mode, limit_base, limit_char, limit_nsfw, c_mosaic, conf_base, conf_char, conf_nsfw, use_global_conf, sort_mode="None", auto_file=False):
    config = load_config()
    config.update({
        "language": lang, "image_folder": _clean_path(img_f), "memo_file": _clean_path(memo),
        "match_threshold": threshold, "generation_count": count, "fallback_enabled": fallback,
        "auto_lora_enabled": auto_l, "gen_confidence": confidence, "gen_positive": pos,
        "gen_negative": neg, "gen_custom_dict": c_dict, "gen_categories": list(c_base) + list(c_char) + list(c_nsfw),
        "wildcard_1_path": _clean_path(w1), "wildcard_2_path": _clean_path(w2), "wildcard_3_path": _clean_path(w3),
        "lora_offset": offset, "output_sort_mode": sort_mode, "auto_filename": auto_file, "gen_mosaic_auto": mosaic_auto, "gen_mosaic_level": mosaic_level,
        "gen_custom_dict_enabled": c_dict_enabled, "auto_optimize_prompt": auto_opt, "custom_base_tags": custom_tags,
        "active_profile": active_prof, "prompt_polish": polish, "smart_negative": smart_neg,
        "smart_negative_mode": smart_neg_mode, "inventory_mode": inventory_mode,
        "limit_base": limit_base, "limit_char": limit_char, "limit_nsfw": limit_nsfw, "gen_cat_mosaic": list(c_mosaic),
        "gen_conf_base": conf_base, "gen_conf_char": conf_char, "gen_conf_nsfw": conf_nsfw,
        "use_global_conf": use_global_conf
    })
    save_config(config)
    return f"\u2705 {t('msg_all_saved')}"

def handle_load_preset(name):
    config = load_config(); presets = config.get("presets", {}); p = presets.get(name)
    if not p: return (
        "", "", 0.3, 1,           # image_folder, memo_file, threshold, count
        True, True,               # fallback, auto_lora
        0.35, "", "", "",         # confidence, pos, neg, custom_dict
        "", "", "",               # w1, w2, w3
        0.0, False, "Med", True,  # lora_offset, mosaic_auto, mosaic_level, custom_dict_enabled
        False, "", "Standard / SDXL",  # auto_opt, custom_tags, profile
        False, False, "append",   # polish, smart_neg, sn_mode
        False, 10, 10, 15,        # inventory_mode, limit_base, limit_char, limit_nsfw
        [], [], [],               # c_base, c_char, c_nsfw (CheckboxGroup は [] が正しい)
        0.35, 0.35, 0.35,         # conf_base, conf_char, conf_nsfw
        True                      # use_global_conf
    )
    config["last_preset"] = name; save_config(config)
    all_cats = p.get("gen_categories", [])
    from .constants import _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS, WILD_1_PATH, WILD_2_PATH, WILD_3_PATH
    c_base = [k for k in all_cats if k in _CAT_BASE_KEYS]
    c_char = [k for k in all_cats if k in _CAT_CHAR_KEYS]
    c_nsfw = [k for k in all_cats if k in _CAT_NSFW_KEYS]
    return (
        p.get("image_folder", ""), p.get("memo_file", ""), p.get("match_threshold", 0.3), p.get("generation_count", 1),
        p.get("fallback_enabled", True), p.get("auto_lora_enabled", True),
        p.get("gen_confidence", 0.35), p.get("gen_positive", ""), p.get("gen_negative", ""),
        p.get("gen_custom_dict", ""), 
        p.get("wildcard_1_path", WILD_1_PATH), p.get("wildcard_2_path", WILD_2_PATH), p.get("wildcard_3_path", WILD_3_PATH),
        p.get("lora_offset", 0.0), p.get("gen_mosaic_auto", False), p.get("gen_mosaic_level", "Med"),
        p.get("gen_custom_dict_enabled", True),
        p.get("auto_optimize_prompt", False), p.get("custom_base_tags", ""), p.get("active_profile", "Standard / SDXL"),
        p.get("prompt_polish", False), p.get("smart_negative", False), p.get("smart_negative_mode", "append"),
        p.get("inventory_mode", False), p.get("limit_base", 10),
        p.get("limit_char", 10), p.get("limit_nsfw", 15),
        c_base, c_char, c_nsfw,
        p.get("conf_base", 0.35), p.get("conf_char", 0.35), p.get("conf_nsfw", 0.35),
        p.get("use_global_conf", True)
    )

def handle_save_preset(name, *args):
    if not name or not name.strip(): return "Error: Name empty", None
    config = load_config(); presets = config.get("presets", {})
    # args: [0:img, 1:memo, 2:thr, 3:cnt, 4:fall, 5:al, 6:g_conf, 7:g_pos, 8:g_neg, 9:g_cust, 10:w1, 11:w2, 12:w3, 13:l_off, 14:m_auto, 15:m_lvl, 16:c_en, 17:a_opt, 18:c_tags, 19:prof, 20:p_pol, 21:s_neg, 22:s_neg_mode, 23:inv_m, 24:l_base, 25:l_char, 26:l_nsfw, 27:c_base, 28:c_char, 29:c_nsfw, 30:conf_b, 31:conf_c, 32:conf_n, 33:ug_conf]
    presets[name.strip()] = {
        "image_folder": args[0], "memo_file": args[1], "match_threshold": args[2],
        "generation_count": args[3], "fallback_enabled": args[4], "auto_lora_enabled": args[5],
        "gen_confidence": args[6], "gen_positive": args[7], "gen_negative": args[8],
        "gen_custom_dict": args[9], "wildcard_1_path": args[10], "wildcard_2_path": args[11],
        "wildcard_3_path": args[12], "lora_offset": args[13], "gen_mosaic_auto": args[14],
        "gen_mosaic_level": args[15], "gen_custom_dict_enabled": args[16],
        "auto_optimize_prompt": args[17], "custom_base_tags": args[18], "active_profile": args[19],
        "prompt_polish": args[20], "smart_negative": args[21], "smart_negative_mode": args[22],
        "inventory_mode": args[23], "limit_base": args[24], "limit_char": args[25],
        "limit_nsfw": args[26], "gen_categories": list(args[27]) + list(args[28]) + list(args[29]),
        "conf_base": args[30], "conf_char": args[31], "conf_nsfw": args[32], "use_global_conf": args[33]
    }
    config["presets"] = presets; config["last_preset"] = name.strip(); save_config(config)
    import gradio as gr
    return f"\u2705 Saved: {name}", gr.update(choices=["Default"] + list(presets.keys()))

def handle_delete_preset(name):
    if not name or name == "Default": return "Cannot delete Default", None
    config = load_config(); presets = config.get("presets", {})
    if name in presets: del presets[name]
    config["presets"] = presets; save_config(config)
    import gradio as gr
    return f"\U0001f5d1\ufe0f Deleted: {name}", gr.update(choices=["Default"] + list(presets.keys()))

def get_inventory_status():
    inventory = load_inventory()
    if not inventory: return t("msg_no_tags_err")
    lines = []
    for cat, items in inventory.items():
        lines.append(f"### {cat}")
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
        for item, count in sorted_items: lines.append(f"- {item}: {count}")
    return "\n".join(lines)

def reset_inventory_global():
    save_inventory({})
    return t("msg_inventory_reset")

def reset_inventory_lora():
    inventory = load_inventory()
    new_inventory = {k: v for k, v in inventory.items() if not k.startswith("lora_") and not k.startswith("slot_")}
    save_inventory(new_inventory)
    return t("msg_inventory_reset")

def append_to_memo(memo_path, entry):
    if not memo_path or not entry: return t("msg_memo_err")
    try:
        memo_path = _clean_path(memo_path)
        dir_path = os.path.dirname(memo_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(memo_path, "a", encoding="utf-8") as f: f.write("\n\n" + entry.strip() + "\n")
        return t("msg_memo_appended")
    except Exception as e: return f"Error: {e}"

def pick_random_assets(en_char, en_sit, en_w1, en_w2, en_w3, inventory_mode=False):
    from .lora_mgr import load_lora_list
    res = {"char": None, "sit": None, "w1": None, "w2": None, "w3": None}
    def _p(l, k):
        items = [i.strip() for i in load_lora_list(l).splitlines() if i.strip() and not i.strip().startswith('#')]
        if not items: return None
        return get_inventory_weighted_choice(items, k) if inventory_mode else random.choice(items)
    if en_char: res["char"] = _p(t("lora_type_char"), "slot_char")
    if en_sit: res["sit"] = _p(t("lora_type_sit"), "slot_sit")
    if en_w1: res["w1"] = _p(t("wildcard_1"), "slot_w1")
    if en_w2: res["w2"] = _p(t("wildcard_2"), "slot_w2")
    if en_w3: res["w3"] = _p(t("wildcard_3"), "slot_w3")
    return res
