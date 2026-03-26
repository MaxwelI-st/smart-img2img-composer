# -*- coding: utf-8 -*-
"""
Smart Img2Img Composer v1.1 Stable
Restoration Version (v1.0.3 Style UI + Modular Backend)
"""
import os
import sys
import random
from pathlib import Path

# --- Ensure path for sc_composer (from root) ---
ext_root = str(Path(__file__).parent.parent)
if ext_root not in sys.path:
    sys.path.append(ext_root)

import gradio as gr
from modules import scripts, shared, images
from modules.processing import Processed, process_images

# --- Import from sub-package ---
from sc_composer.constants import PROMPT_PROFILES, DEFAULT_CONFIG
from sc_composer.i18n import t
from sc_composer.utils import _clean_path, _polish_prompt, get_stable_dimensions
from sc_composer.core import load_config, compose_prompt, pick_random_assets
from sc_composer.ui_tabs import on_ui_tabs
from sc_composer.ui_img2img import on_ui_img2img

print("[Smart Img2Img Composer] v1.1 Stable - Modular Backend Initialized.")

class RandomComposerScript(scripts.Script):
    def title(self):
        return "Smart Img2Img Composer v1.1 Stable"

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else False

    def ui(self, is_img2img):
        if not is_img2img:
            return []
        return on_ui_img2img()

    def before_process(self, p, *args):
        # args unpacking (Matches on_ui_img2img return order)
        if len(args) < 21: return
        
        enabled = args[0]
        if not enabled: return

        overwrite_prompt = args[1]
        resize_mode      = args[2]
        base_res         = args[3]
        selection_mode   = args[4]
        en_char          = args[5]
        pos_char        = args[6]
        en_sit           = args[7]
        pos_sit         = args[8]
        en_w1            = args[9]
        pos_w1          = args[10]
        en_w2            = args[11]
        pos_w2          = args[12]
        en_w3            = args[13]
        pos_w3          = args[14]
        output_sort_mode = args[15]
        auto_optimize    = args[16]
        custom_base_tags = args[17]
        active_profile   = args[18]
        prompt_polish    = args[19]
        auto_filename    = args[20]

        config = load_config()
        image_folder = config.get("image_folder", "")
        memo_file = config.get("memo_file", "")
        match_threshold = config.get("match_threshold", 0.3)
        inventory_mode = config.get("inventory_mode", False)

        # 1. Compose Prompt & Select Image from Memo
        img_path, pos, neg, log, section_name = compose_prompt(
            image_folder, memo_file, match_threshold, 
            selection_mode="sequential" if "sequential" in str(selection_mode).lower() else "random"
        )

        if not img_path:
            print(f"[Smart Img2Img Composer] Error: {log}")
            return

        from PIL import Image
        image = Image.open(img_path)
        p.init_images = [image]

        # 2. Pick Random Assets (Slots)
        assets = pick_random_assets(en_char, en_sit, en_w1, en_w2, en_w3, inventory_mode=inventory_mode)
        
        def _inject(prompt, asset, pos_mode, is_lora=True):
            if not asset: return prompt
            item = f"<lora:{asset}:1.0>" if is_lora else f"__{asset}__"
            if pos_mode == t("pos_front"):
                return f"{item}, {prompt}"
            elif pos_mode == t("pos_back"):
                return f"{prompt}, {item}"
            else: # Smart
                base_tags = [bt.strip().lower() for bt in custom_base_tags.split(",") if bt.strip()]
                tags = [tag.strip() for tag in prompt.split(",") if tag.strip()]
                last_idx = -1
                for i, tag in enumerate(tags):
                    if any(bt in tag.lower() for bt in base_tags):
                        last_idx = i
                if last_idx != -1:
                    tags.insert(last_idx + 1, item)
                    return ", ".join(tags)
                return f"{item}, {prompt}"

        pos = _inject(pos, assets["char"], pos_char, True)
        pos = _inject(pos, assets["sit"],  pos_sit, True)
        pos = _inject(pos, assets["w1"],   pos_w1, False)
        pos = _inject(pos, assets["w2"],   pos_w2, False)
        pos = _inject(pos, assets["w3"],   pos_w3, False)

        # 3. Resize Logic
        if resize_mode != t("resize_none"):
            mode_map = {
                t("resize_slider"): ("slider", base_res, 0, 0),
                t("resize_512"): ("range", 0, 512, 1024),
                t("resize_1024"): ("range", 0, 1024, 1536),
                t("resize_1536"): ("range", 0, 1536, 1792)
            }
            m, s, mi, ma = mode_map.get(resize_mode, ("slider", base_res, 0, 0))
            new_w, new_h = get_stable_dimensions(image, mode=m, slider_val=s, min_val=mi, max_val=ma)
            p.width, p.height = new_w, new_h

        # 4. Final Prompt Integration
        if overwrite_prompt:
            p.prompt = pos
            p.negative_prompt = neg
        else:
            p.prompt = f"{p.prompt}, {pos}"
            p.negative_prompt = f"{p.negative_prompt}, {neg}"

        # 5. Smart Negative
        if config.get("smart_negative", True):
            profile = PROMPT_PROFILES.get(active_profile, next(iter(PROMPT_PROFILES.values())))
            profile_neg = profile.get("neg", "")
            if config.get("smart_negative_mode", "append") == "overwrite":
                p.negative_prompt = profile_neg
            else:
                p.negative_prompt = f"{p.negative_prompt}, {profile_neg}"

        # 6. Polish
        if prompt_polish:
            p.prompt = _polish_prompt(p.prompt)
            p.negative_prompt = _polish_prompt(p.negative_prompt)

        print(f"[Smart Img2Img Composer] Applied: {os.path.basename(img_path)} (Section: {section_name})")

# Register the independent tab
from modules import script_callbacks
try:
    script_callbacks.on_ui_tabs(on_ui_tabs)
except Exception as e:
    print(f"[Smart Img2Img Composer] Error during on_ui_tabs: {e}")
    import traceback
    traceback.print_exc()
