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
                if config.get("gen_categories") == []:
                    config["gen_categories"] = None
                return config
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)

def save_config(config: dict) -> str:
    try:
        dir_path = os.path.dirname(CONFIG_PATH)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        invalidate_lang_cache()
        return t("msg_settings_saved")
    except IOError as e:
        return f"{t('msg_settings_err')} {e}"

def load_inventory():
    if not os.path.exists(INVENTORY_PATH):
        return {}
    try:
        with open(INVENTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_inventory(data):
    try:
        with open(INVENTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Smart Img2Img Composer] Failed to save inventory: {e}")

def get_inventory_weighted_choice(item_list, category_key):
    if not item_list:
        return None
    inventory = load_inventory()
    category_history = dict(inventory.get(category_key, {}))
    counts = [int(category_history.get(item, -1)) for item in item_list]
    existing_counts = [c for c in counts if c >= 0]
    avg_count = int(sum(existing_counts) / len(existing_counts)) if existing_counts else 0
    initial_count = max(0, avg_count - 2)
    for item in item_list:
        if item not in category_history:
            category_history[item] = initial_count
    final_counts = [int(category_history[item]) for item in item_list]
    weights = [1.0 / (float(c) + 1.0) for c in final_counts]
    choice = random.choices(item_list, weights=weights, k=1)[0]
    category_history[choice] = int(category_history[choice]) + 1
    new_inventory = dict(inventory)
    new_inventory[category_key] = category_history
    save_inventory(new_inventory)
    return choice

def parse_memo_file(memo_path: str) -> dict:
    memo_path = _clean_path(memo_path)
    sections = {}
    if not memo_path or not os.path.isfile(memo_path):
        return sections

    def _join_lines(lines: list) -> str:
        if not lines: return ""
        combined = ", ".join(lines)
        parts = [p.strip() for p in combined.split(",") if p.strip()]
        return ", ".join(parts)

    current_key, current_mode = None, "positive"
    current_positive, current_negative, current_lora = [], [], []

    def save_section():
        nonlocal current_key, current_positive, current_negative, current_lora
        if current_key is None: return
        pos = _join_lines(current_positive)
        neg = _join_lines(current_negative)
        lora = list(current_lora)
        if pos or neg or lora:
            sections[current_key] = {"positive": pos, "negative": neg, "lora": lora}

    try:
        content = ""
        for enc in ("utf-8", "utf-8-sig", "cp932"):
            try:
                with open(memo_path, "r", encoding=enc, errors=("ignore" if enc == "cp932" else "strict")) as f:
                    content = f.read()
                break
            except Exception: continue
        
        if not content: return sections

        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"): continue
            match = re.match(r"^\[(.+)\]\s*$", stripped)
            if match:
                save_section()
                current_key = match.group(1).strip().lower()
                current_mode, current_positive, current_negative, current_lora = "positive", [], [], []
                continue
            if stripped.lower() in ("positive:", "positive"):
                current_mode = "positive"
                continue
            if stripped.lower() in ("negative:", "negative"):
                current_mode = "negative"
                continue
            if stripped.lower() in ("lora:", "lora"):
                current_mode = "lora"
                continue
            if current_key is not None and stripped:
                if current_mode == "negative": current_negative.append(stripped)
                elif current_mode == "lora": current_lora.append(stripped)
                else: current_positive.append(stripped)
        save_section()
    except Exception as e:
        print(f"[Smart Img2Img Composer] Memo parse error: {e}")
    return sections

def match_image_to_sections(image_path: str, sections: dict, threshold: float) -> list:
    if not image_path or not sections: return []
    from difflib import SequenceMatcher
    filename = os.path.splitext(os.path.basename(image_path))[0].lower()
    best_matches, max_score = [], 0
    for section in sections.keys():
        if section.lower() == "default": continue
        score = SequenceMatcher(None, filename, section.lower()).ratio()
        if score >= threshold:
            if score > max_score:
                max_score, best_matches = score, [section]
            elif score == max_score:
                best_matches.append(section)
    if best_matches:
        return [sections[best_matches[0]]]
    return []

def compose_prompt(image_folder: str, memo_file: str, match_threshold: float, selection_mode="Random") -> tuple:
    log = []
    config = load_config()
    fallback_enabled = config.get("fallback_enabled", True)
    auto_lora_enabled = config.get("auto_lora_enabled", True)

    image_files = get_image_files(image_folder)
    if not image_files: return None, "", "", t("no_images"), ""

    if selection_mode == "sequential":
        last_index = config.get("last_sequential_index", 0)
        index = last_index % len(image_files)
        selected = image_files[index]
        config["last_sequential_index"] = index + 1
        save_config(config)
        log.append(t("log_sel_sequential").format(index=index + 1, total=len(image_files), filename=os.path.basename(selected)))
    else:
        selected = random.choice(image_files)
        log.append(t("log_sel_random").format(filename=os.path.basename(selected)))

    sections = parse_memo_file(memo_file)
    if not sections:
        log.append(t("log_no_sections"))
        return selected, "", "", "\n".join(log), ""

    log.append(t("log_sections_count").format(count=len(sections)))
    matched = match_image_to_sections(selected, sections, match_threshold)
    matched_section_name = ""

    if not matched:
        if fallback_enabled and "default" in sections:
            log.append(t("log_fallback"))
            matched = [sections["default"]]
            matched_section_name = "default"
        else:
            log.append(t("log_no_match"))
            return selected, "", "", "\n".join(log), ""
    else:
        # Find exact section name for logging
        filename = os.path.splitext(os.path.basename(selected))[0].lower()
        from difflib import SequenceMatcher
        for section in sections.keys():
            if section == "default": continue
            if SequenceMatcher(None, filename, section.lower()).ratio() >= match_threshold:
                matched_section_name = section
                break

    pos_parts, neg_parts, lora_parts = [], [], []
    seen_pos, seen_neg, seen_lora = set(), set(), set()
    
    inventory_mode = config.get("inventory_mode", False)

    for m in [m for m in matched if m.get("positive") or m.get("negative") or m.get("lora")]:
        p, n, l_list = m.get("positive", ""), m.get("negative", ""), m.get("lora", [])
        
        # Handle Dynamic Prompts / Wildcards inside memo
        if "__" in p or "{" in p:
            # If inventory mode is on, we might want to handle it differently
            # but usually WebUI extensions (Dynamic Prompts) handle this later.
            pass

        if p and p not in seen_pos:
            seen_pos.add(p); pos_parts.append(p)
        if n and n not in seen_neg:
            seen_neg.add(n); neg_parts.append(n)
        
        if l_list:
            if inventory_mode:
                l_item = get_inventory_weighted_choice(l_list, f"lora_{matched_section_name}")
            else:
                l_item = random.choice(l_list)
            
            if l_item and l_item not in seen_lora:
                seen_lora.add(l_item)
                if auto_lora_enabled: lora_parts.append(f"<lora:{l_item}>")

    if lora_parts: pos_parts = lora_parts + pos_parts
    positive = _polish_prompt(", ".join(pos_parts))
    negative = _polish_prompt(", ".join(neg_parts))

    log.append(t("log_match_count").format(count=len(matched)))
    return selected, positive, negative, "\n".join(log), matched_section_name

def save_all_settings(lang, img_f, memo, threshold, count, fallback, auto_l, confidence, pos, neg, c_dict, c_base, c_char, c_nsfw, w1, w2, w3, offset, sort, mosaic_auto, mosaic_level, c_dict_enabled, auto_opt, custom_tags, active_prof, polish, smart_neg, auto_file, smart_neg_mode, inventory_mode, limit_base, limit_char, limit_nsfw, c_mosaic):
    config = load_config()
    config.update({
        "language": lang,
        "image_folder": _clean_path(img_f),
        "memo_file": _clean_path(memo),
        "match_threshold": threshold,
        "generation_count": count,
        "fallback_enabled": fallback,
        "auto_lora_enabled": auto_l,
        "gen_confidence": confidence,
        "gen_positive": pos,
        "gen_negative": neg,
        "gen_custom_dict": c_dict,
        "gen_categories": list(c_base) + list(c_char) + list(c_nsfw),
        "wildcard_1_path": _clean_path(w1),
        "wildcard_2_path": _clean_path(w2),
        "wildcard_3_path": _clean_path(w3),
        "lora_offset": offset,
        "output_sort_mode": sort,
        "gen_mosaic_auto": mosaic_auto,
        "gen_mosaic_level": mosaic_level,
        "gen_custom_dict_enabled": c_dict_enabled,
        "auto_optimize_prompt": auto_opt,
        "custom_base_tags": custom_tags,
        "active_profile": active_prof,
        "prompt_polish": polish,
        "smart_negative": smart_neg,
        "smart_negative_mode": smart_neg_mode,
        "auto_filename": auto_file,
        "inventory_mode": inventory_mode,
        "limit_base": limit_base,
        "limit_char": limit_char,
        "limit_nsfw": limit_nsfw,
        "gen_cat_mosaic": list(c_mosaic),
    })
    save_config(config)
    return f"✅ {t('msg_all_saved')}"

def append_to_memo(memo_path, entry):
    if not memo_path or not memo_path.strip():
        return t("msg_memo_err") + " (Path empty)"
    if not entry or not entry.strip():
        return t("msg_memo_err") + " (Entry empty)"
    try:
        memo_path = _clean_path(memo_path)
        dir_path = os.path.dirname(memo_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        separator = ""
        if os.path.isfile(memo_path):
            with open(memo_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content and not content.endswith("\n"):
                separator = "\n\n"
            elif content:
                separator = "\n"
        
        with open(memo_path, "a", encoding="utf-8") as f:
            f.write(separator + entry.strip() + "\n")
        return t("msg_memo_appended")
    except Exception as e:
        return f"{t('msg_memo_err')} {e}"

def pick_random_assets(en_char, en_sit, en_w1, en_w2, en_w3, inventory_mode=False):
    """Pick random LoRAs/wildcards from slots."""
    from .lora_mgr import load_lora_list
    from .i18n import t
    
    results = {
        "char": None, "sit": None, "w1": None, "w2": None, "w3": None
    }
    
    def _pick(label, key):
        content = load_lora_list(label)
        items = [line.strip() for line in content.splitlines() if line.strip() and not line.strip().startswith("#")]
        if not items: return None
        if inventory_mode:
            return get_inventory_weighted_choice(items, f"slot_{key}")
        return random.choice(items)

    if en_char: results["char"] = _pick(t("lora_type_char"), "char")
    if en_sit:  results["sit"]  = _pick(t("lora_type_sit"), "sit")
    if en_w1:   results["w1"]   = _pick(t("wildcard_1"), "w1")
    if en_w2:   results["w2"]   = _pick(t("wildcard_2"), "w2")
    if en_w3:   results["w3"]   = _pick(t("wildcard_3"), "w3")
    
def get_inventory_status():
    inventory = load_inventory()
    if not inventory:
        return t("msg_no_tags_err")
    
    lines = []
    for cat, items in inventory.items():
        lines.append(f"### {cat}")
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)
        for item, count in sorted_items:
            lines.append(f"- {item}: {count}")
    return "\n".join(lines)

def reset_inventory_global():
    save_inventory({})
    return t("msg_inventory_reset")

def reset_inventory_lora():
    inventory = load_inventory()
    new_inventory = {k: v for k, v in inventory.items() if not k.startswith("lora_") and not k.startswith("slot_")}
    save_inventory(new_inventory)
    return t("msg_inventory_reset")
