# -*- coding: utf-8 -*-
import os
import re
from PIL import Image
from .constants import IMAGE_EXTENSIONS

def _clean_path(path: str) -> str:
    if not path or not isinstance(path, str):
        return ""
    return path.strip().strip('"').strip("'").strip()

def _polish_prompt(prompt_str: str) -> str:
    if not prompt_str:
        return ""
    # 連続するカンマや空白を「, 」に置換
    res = re.sub(r',[\s,]+', ', ', prompt_str)
    # 文末ガード: カッコの閉じ際のカンマを削除
    res = re.sub(r',\s*\)', ')', res)
    res = re.sub(r',\s*\]', ']', res)
    # 重複スペースを1つに
    res = re.sub(r'\s+', ' ', res)
    # 前後のカンマと空白を削除
    res = res.strip(", ")
    return res

def _extract_naming_tags(prompt_str: str) -> str:
    if not prompt_str:
        return ""
    exclude = {"masterpiece", "best quality", "highres", "absurdres", "quality", "solo", "1girl", "1boy"}
    tags = [t.strip().lower() for t in re.split(r",\s*(?![^()]*\))", prompt_str) if t.strip()]
    
    naming_parts = []
    for tag in tags:
        clean = re.sub(r'[():\d.]+', '', tag).strip().replace(" ", "_")
        if clean and clean not in exclude and len(clean) > 2:
            naming_parts.append(clean)
        if len(naming_parts) >= 3:
            break
            
    final_str = str("_".join(naming_parts))
    if len(final_str) > 60:
        final_str = final_str[:60].rstrip("_")
    return final_str

def get_stable_dimensions(img, mode="slider", slider_val=1024, min_val=512, max_val=1024):
    if not img:
        return slider_val, slider_val
    w, h = img.size
    aspect = w / h

    new_w, new_h = float(w), float(h)
    max_edge = max(w, h)

    if mode == "slider":
        if w > h:
            new_w = slider_val
            new_h = new_w / aspect
        else:
            new_h = slider_val
            new_w = new_h * aspect
    elif mode == "range":
        if max_edge < min_val:
            scale = min_val / max_edge
            new_w = w * scale
            new_h = h * scale
        elif max_edge > max_val:
            scale = max_val / max_edge
            new_w = w * scale
            new_h = h * scale

    new_w = max(64, round(new_w / 64) * 64)
    new_h = max(64, round(new_h / 64) * 64)
    return new_w, new_h

def get_image_files(folder: str) -> list:
    folder = _clean_path(folder)
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if (os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
            and not f.startswith(".")
            and "config" not in f.lower()
            and "memo" not in f.lower())
    ]

def _clean_prompt(prompt: str) -> str:
    """Helper for cleaning joined prompts before processing."""
    if not prompt: return ""
    return _polish_prompt(prompt)

def check_individual_health(img_f, memo, w1, w2, w3):
    from .i18n import t
    import gradio as gr
    def _get_u(path, label_key):
        if not path or not path.strip(): return gr.update(label=t(label_key))
        p = _clean_path(path)
        exists = os.path.exists(p)
        return gr.update(label=f"✅ {t(label_key)}" if exists else f"❌ {t(label_key)}")
    
    return (
        _get_u(img_f, "image_folder"),
        _get_u(memo, "memo_file"),
        _get_u(w1, "wildcard_1"),
        _get_u(w2, "wildcard_2"),
        _get_u(w3, "wildcard_3"),
    )

def validate_path(path, label_key):
    from .i18n import t
    import gradio as gr
    if not path or not path.strip():
        return gr.update(label=t(label_key))
    p = _clean_path(path)
    exists = os.path.exists(p)
    icon = "✅" if exists else "❌"
    return gr.update(label=f"{icon} {t(label_key)}")
