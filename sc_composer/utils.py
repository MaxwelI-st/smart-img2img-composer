# -*- coding: utf-8 -*-
import re
import os
from PIL import Image
from .constants import PROMPT_PROFILES, IMAGE_EXTENSIONS

def _clean_path(path: str) -> str:
    if not path or not isinstance(path, str): return ""
    return path.strip().strip('"').strip("'").strip()

def _polish_prompt(prompt_str: str) -> str:
    if not prompt_str: return ""
    res = re.sub(r',[\s,]+', ', ', prompt_str)
    res = re.sub(r',\s*\)', ')', res)
    res = re.sub(r',\s*\]', ']', res)
    res = re.sub(r'\s+', ' ', res)
    res = res.strip(", ")
    return res

_EXT_SET = {ext.lower() for ext in IMAGE_EXTENSIONS}

def get_image_files(folder: str) -> list:
    folder = _clean_path(folder)
    if not folder or not os.path.isdir(folder): return []
    res = []
    for f in os.listdir(folder):
        ext = os.path.splitext(f)[1].lower()
        if ext in _EXT_SET:
            res.append(os.path.join(folder, f))
    return sorted(res)

def get_stable_dimensions(img, mode, base_res=1024):
    if not img: return None, None
    w, h = img.size
    if "slider" in mode.lower() or "\u30b9\u30e9\u30a4\u30c0\u30fc" in mode:
        if w > h:
            nw = base_res; nh = int(h * (base_res / w))
        else:
            nh = base_res; nw = int(w * (base_res / h))
        return nw, nh
    mi, mx = 512, 1024
    if "512" in mode: mi, mx = 512, 1024
    elif "1024" in mode: mi, mx = 1024, 1536
    elif "1536" in mode: mi, mx = 1536, 1792
    else: return w, h
    long_edge = max(w, h)
    if long_edge <= mi: scale = mi / long_edge
    elif long_edge >= mx: scale = mx / long_edge
    else: return (w // 64 * 64), (h // 64 * 64)
    return (int(w * scale) // 64 * 64), (int(h * scale) // 64 * 64)


# P3: カテゴリ分類キーワード辞書
# PROMPT_PROFILES の order に登場するカテゴリに対してキーワードで仕分ける
_CAT_KEYWORDS = {
    # quality / score / rating 系
    "quality":  {"masterpiece", "best quality", "ultra-detailed", "highres", "highly detailed",
                 "very aesthetic", "absurdres", "illustration"},
    "score":    {"score_9", "score_8_up", "score_7_up", "score_6_up", "score_5_up",
                 "score_4_up", "score_4", "score_5", "score_6"},
    "rating":   {"source_anime", "source_pony", "source_furry", "source_cartoon",
                 "rating_safe", "rating_questionable", "rating_explicit",
                 "general", "sensitive", "nsfw"},
    # subject 系（人物描写）
    "subject":  {"1girl", "1boy", "2girls", "2boys", "multiple girls", "multiple boys",
                 "solo", "duo", "group", "standing", "sitting", "lying", "smile", "closed eyes",
                 "looking at viewer", "long hair", "short hair", "blonde hair", "black hair",
                 "blue eyes", "brown eyes"},
    # clothing 系
    "clothing": {"dress", "shirt", "skirt", "jacket", "coat", "uniform", "bikini",
                 "swimsuit", "naked", "nude", "topless", "bottomless", "underwear",
                 "lingerie", "pantyhose", "thighhighs", "socks", "shoes", "boots"},
    # environment / background 系
    "environment": {"outdoors", "indoors", "background", "sky", "cloud", "forest", "city",
                    "ocean", "beach", "room", "classroom", "garden", "street", "night",
                    "day", "sunset", "sunrise", "rain", "snow", "nature", "urban"},
    # lighting 系
    "lighting": {"light", "shadow", "bright", "dark", "backlight", "rim light",
                 "soft lighting", "hard lighting", "dramatic lighting", "bloom",
                 "glow", "neon", "sunlight", "moonlight", "candlelight"},
    # camera / composition 系
    "camera":   {"close-up", "close up", "full body", "upper body", "cowboy shot",
                 "portrait", "from above", "from below", "from behind", "side view",
                 "wide shot", "medium shot", "dutch angle", "fisheye", "bokeh",
                 "depth of field", "motion blur"},
    # style 系
    "style":    {"anime", "manga", "realistic", "3d", "digital art", "watercolor",
                 "oil painting", "sketch", "line art", "flat color", "cel shading",
                 "photorealistic", "hyperrealistic", "painterly"},
}

def _classify_tag(tag: str, categorized: dict) -> str | None:
    """タグを categorized のキーにマッピングして返す。マッチしなければ None。"""
    lower = tag.lower()
    for cat, keywords in _CAT_KEYWORDS.items():
        if cat not in categorized: continue
        if any(kw in lower for kw in keywords):
            return cat
    return None

def optimize_prompt_order(prompt: str, profile: str = "Standard / SDXL") -> str:
    if profile not in PROMPT_PROFILES: return prompt
    order = PROMPT_PROFILES[profile]["order"]
    tags = [tag.strip() for tag in prompt.split(",") if tag.strip()]
    categorized = {cat: [] for cat in order}
    others = []
    for tag in tags:
        lower = tag.lower()
        # LoRA / wildcard は専用処理
        if "<lora:" in lower:
            if "lora" in categorized: categorized["lora"].append(tag)
            else: others.append(tag)
            continue
        if "__" in tag and tag.startswith("__") and tag.endswith("__"):
            if "wildcard" in categorized: categorized["wildcard"].append(tag)
            else: others.append(tag)
            continue
        # キーワード辞書でカテゴリ分類
        cat = _classify_tag(tag, categorized)
        if cat:
            categorized[cat].append(tag)
        else:
            others.append(tag)
    # カテゴリ順に並べる
    # others（未分類）は order に subject があればその直前に、なければ末尾に挿入
    if "subject" in order:
        sub_idx = order.index("subject")
        before = []
        for cat in order[:sub_idx]:
            before.extend(categorized.get(cat, []))
        after = []
        for cat in order[sub_idx:]:
            after.extend(categorized.get(cat, []))
        return ", ".join(before + others + after)
    result = []
    for cat in order:
        result.extend(categorized.get(cat, []))
    return ", ".join(result + others)

def check_individual_health(image_folder, memo_file, w1, w2, w3):
    from .i18n import t
    def check(p, is_file=False):
        if not p: 
            msg = t("health_check_ok")
        else:
            p_clean = _clean_path(p)
            exists = os.path.isfile(p_clean) if is_file else os.path.isdir(p_clean)
            msg = t("health_check_ok") if exists else "❌ " + t("health_check_err").format(path=os.path.basename(p_clean) or "Invalid")
        
        # ▼ Gradioに押し潰されないための「強制CSS化」▼
        return f"<div style='margin-top: 36px; font-weight: bold; white-space: nowrap;'>{msg}</div>"
    
    return (
        check(image_folder, False),
        check(memo_file, True),
        check(w1, True),
        check(w2, True),
        check(w3, True)
    )
