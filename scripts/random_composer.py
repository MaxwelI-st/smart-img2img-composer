# -*- coding: utf-8 -*-
import os
import sys
import random
from pathlib import Path

# --- Ensure path for sc_composer (from root) ---
ext_root = str(Path(__file__).parent.parent)
if ext_root not in sys.path:
    sys.path.insert(0, ext_root)  # insert(0) で優先順位を上げる
print(f"[Smart Img2Img Composer] ext_root={ext_root}")

import gradio as gr
from modules import scripts, shared, images
from modules.processing import Processed, process_images

from sc_composer.constants import PROMPT_PROFILES
from sc_composer.i18n import t
from sc_composer.utils import _clean_path, _polish_prompt, get_stable_dimensions
from sc_composer.core import load_config, compose_prompt, pick_random_assets

class RandomComposerScript(scripts.Script):
    def title(self):
        return "Smart Img2Img Composer v1.1.2"

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else False

    def ui(self, is_img2img):
        if not is_img2img: return []
        from sc_composer.ui_img2img import on_ui_img2img
        return on_ui_img2img()

    def before_process(self, p, *args):
        if not args or not args[0]:
            return  # Early return if not enabled
        if getattr(p, "_sc_processed", False):
            return  # Prevent double processing
        setattr(p, "_sc_processed", True)

        config = load_config()
        p.n_iter = config.get("generation_count", 1)

        try:
            overwrite_prompt = args[1]
            resize_mode = args[2]
            base_res = args[3]
            selection_mode = args[4]
            en_char = args[5]
            pos_char_mode = args[6]
            en_sit = args[7]
            pos_sit_mode = args[8]
            en_w1 = args[9]
            pos_w1_mode = args[10]
            en_w2 = args[11]
            pos_w2_mode = args[12]
            en_w3 = args[13]
            pos_w3_mode = args[14]
            output_sort_mode = args[15]
            auto_optimize = args[16]
            custom_base_tags = args[17]
            active_profile = args[18]
            prompt_polish = args[19]
            auto_filename = args[20]
        except IndexError:
            print("[Smart Img2Img Composer] UI components count mismatch.")
            return
        
        actual_preset_name = config.get("last_preset", "Default")
        image_folder = config.get("image_folder", ""); memo_file = config.get("memo_file", "")
        match_threshold = config.get("match_threshold", 0.3); inventory_mode = config.get("inventory_mode", False)

        sel_mode_str = "sequential" if "sequential" in str(selection_mode).lower() else "random"
        img_path, pos, neg, log, section_name = compose_prompt(image_folder, memo_file, match_threshold, selection_mode=sel_mode_str)
        if not img_path: return

        from PIL import Image
        image = Image.open(img_path); p.init_images = [image]
        assets = pick_random_assets(en_char, en_sit, en_w1, en_w2, en_w3, inventory_mode=inventory_mode)
        
        def _inject(prompt, asset, pos_mode, is_lora=True):
            if not asset: return prompt
            item = f"<lora:{asset}:1.0>" if is_lora else f"__{asset}__"
            if pos_mode == t("pos_front"): return f"{item}, {prompt}"
            elif pos_mode == t("pos_back"): return f"{prompt}, {item}"
            else:
                base_tags = [bt.strip().lower() for bt in custom_base_tags.split(",") if bt.strip()]
                tags = [tag.strip() for tag in prompt.split(",") if tag.strip()]
                last_idx = -1
                for i, tag in enumerate(tags):
                    if any(bt in tag.lower() for bt in base_tags): last_idx = i
                if last_idx != -1:
                    tags.insert(last_idx + 1, item)
                    return ", ".join(tags)
                return f"{item}, {prompt}"

        pos = _inject(pos, assets["char"], pos_char_mode, True)
        pos = _inject(pos, assets["sit"], pos_sit_mode, True)
        pos = _inject(pos, assets["w1"], pos_w1_mode, False)
        pos = _inject(pos, assets["w2"], pos_w2_mode, False)
        pos = _inject(pos, assets["w3"], pos_w3_mode, False)

        if resize_mode != t("resize_none"):
            new_w, new_h = get_stable_dimensions(image, mode=resize_mode, base_res=base_res)
            if new_w: p.width, p.height = new_w, new_h

        full_pos = pos; full_neg = neg
        if not overwrite_prompt:
            full_pos = f"{p.prompt}, {pos}"; full_neg = f"{p.negative_prompt}, {neg}"

        if config.get("smart_negative", False):
            profile = PROMPT_PROFILES.get(active_profile, next(iter(PROMPT_PROFILES.values())))
            profile_neg = profile.get("neg", "")
            if config.get("smart_negative_mode", "overwrite") == "overwrite": full_neg = profile_neg
            else: full_neg = f"{full_neg}, {profile_neg}"

        lora_offset = config.get("lora_offset", 0.0)
        if lora_offset != 0.0:
            from sc_composer.core import apply_lora_offset
            full_pos = apply_lora_offset(full_pos, lora_offset)

        if prompt_polish:
            full_pos = _polish_prompt(full_pos); full_neg = _polish_prompt(full_neg)
        if auto_optimize:
            from sc_composer.utils import optimize_prompt_order
            full_pos = optimize_prompt_order(full_pos, active_profile)

        p.prompt = full_pos; p.negative_prompt = full_neg
        # Ensure extra_generation_params is a dict (handles None or non-dict)
        if not hasattr(p, 'extra_generation_params') or not isinstance(p.extra_generation_params, dict):
            p.extra_generation_params = {}
        p.extra_generation_params["SC_Section"] = section_name
        p.extra_generation_params["SC_Preset"] = actual_preset_name
        p.extra_generation_params["SC_AutoFilename"] = auto_filename
        p.extra_generation_params["SC_SortMode"] = output_sort_mode

def on_before_image_saved(params):
    p = params.p
    if not p or not hasattr(p, 'extra_generation_params') or p.extra_generation_params is None: return # B6: guard
    egp = p.extra_generation_params
    auto_filename = egp.get("SC_AutoFilename", False)
    sort_mode = egp.get("SC_SortMode", "None")
    section = egp.get("SC_Section", "Default")
    preset = egp.get("SC_Preset", "Default")

    # 元の保存先ディレクトリ（outputs等）を必ず確保する
    orig_dir = os.path.dirname(params.filename)
    new_basename = os.path.basename(params.filename)

    subfolder = ""
    if sort_mode == "By Preset": subfolder = preset
    elif sort_mode == "By Section": subfolder = section
    elif sort_mode == "By Date":
        from datetime import datetime
        subfolder = datetime.now().strftime("%Y-%m-%d")
    
    # フォルダパスの安全な結合（元のパスを絶対に消さない）
    if subfolder:
        subfolder = "".join(c for c in subfolder if c.isalnum() or c in (" ", "-", "_")).strip()
        if subfolder:
            orig_dir = os.path.join(orig_dir, subfolder)
            os.makedirs(orig_dir, exist_ok=True)

    # 自動ファイル名生成
    if auto_filename and hasattr(p, 'prompt') and p.prompt:
        tags = [tok.strip() for tok in p.prompt.split(",") if ":" not in tok and "<" not in tok and "_" in tok]
        naming = "-".join(tags[:3]).replace(" ", "_")
        if naming:
            new_basename = f"{naming}_{new_basename}"

    # 最終決定したパスをセット
    params.filename = os.path.join(orig_dir, new_basename)

from modules import script_callbacks
try:
    from sc_composer.ui_tabs import on_ui_tabs
    script_callbacks.on_ui_tabs(on_ui_tabs)
    script_callbacks.on_before_image_saved(on_before_image_saved)
except Exception as e:
    import traceback
    print(f"[Smart Img2Img Composer] FATAL callback registration error: {e}")
    traceback.print_exc()
