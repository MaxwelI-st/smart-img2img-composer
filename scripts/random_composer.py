# -*- coding: utf-8 -*-
"""
Random Img2Img Composer
AUTOMATIC1111 Stable Diffusion WebUI 拡張機能

img2img生成時に、指定フォルダからランダム画像を選択し、
メモファイルから対応プロンプト（positive/negative）を自動取得して投入する。
WD14 Tagger連携でプロンプトの自動生成も可能。
"""

import os
import sys
import json
import random
import re
import traceback
import gradio as gr
from PIL import Image

from modules import script_callbacks, processing, scripts

# ======================================================================
# 定数
# ======================================================================

EXTENSION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(EXTENSION_DIR, "config.json")

DEFAULT_CONFIG = {
    "image_folder": "",
    "memo_file": "",
    "match_threshold": 0.3,
    "generation_count": 1,
    "gen_confidence": 0.35,
    "gen_positive": "(masterpiece:1.1), (best quality:1.0), ",
    "gen_negative": "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts",
    "gen_custom_dict": (
        "night, city > cyberpunk cityscape, neon lights, cinematic lighting, rain reflections, highly detailed\n"
        "sunset, skyline > golden hour lighting, dramatic sky colors, atmospheric perspective\n"
        "1girl, smile > beautiful detailed eyes, soft lighting, expressive face, warm atmosphere\n"
        "outdoors, wind > flowing hair, dynamic pose, motion blur, cinematic composition\n"
        "street, night > urban photography style, moody shadows, film grain, realistic lighting"
    ),
    "gen_categories": [], # _TAG_CATEGORIES初期化時に後でセットするか、Noneで扱う
    "fallback_enabled": True,
    "auto_lora_enabled": True,
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


# ======================================================================
# 設定管理
# ======================================================================

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> str:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return "✅ 設定を保存しました"
    except IOError as e:
        return f"❌ 保存に失敗しました: {e}"


# ======================================================================
# メモファイル解析（positive / negative 対応）
# ======================================================================

def parse_memo_file(memo_path: str) -> dict:
    """
    メモファイルを解析する。
    戻り値: { セクション名: {"positive": "...", "negative": "..."} }
    """
    sections = {}
    if not memo_path or not os.path.isfile(memo_path):
        return sections

    current_key = None
    current_mode = "positive"
    current_positive = []
    current_negative = []
    current_lora = []

    def save_section():
        nonlocal current_key, current_positive, current_negative, current_lora
        if current_key is None:
            return
        pos = _join_lines(current_positive)
        neg = _join_lines(current_negative)
        lora = current_lora[:]
        if pos or neg or lora:
            sections[current_key] = {"positive": pos, "negative": neg, "lora": lora}

    try:
        with open(memo_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n\r")
                stripped = line.strip()

                if stripped.startswith("#"):
                    continue

                match = re.match(r"^\[(.+)\]\s*$", stripped)
                if match:
                    save_section()
                    current_key = match.group(1).strip().lower()
                    current_mode = "positive"
                    current_positive = []
                    current_negative = []
                    current_lora = []
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
                    if current_mode == "negative":
                        current_negative.append(stripped)
                    elif current_mode == "lora":
                        current_lora.append(stripped)
                    else:
                        current_positive.append(stripped)

        save_section()
    except IOError:
        pass

    return sections


def _join_lines(lines: list) -> str:
    if not lines:
        return ""
    combined = ", ".join(lines)
    parts = [p.strip() for p in combined.split(",") if p.strip()]
    return ", ".join(parts)


# ======================================================================
# コアロジック
# ======================================================================

def get_image_files(folder: str) -> list:
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]


def match_image_to_sections(image_path: str, sections: dict, threshold: float) -> list:
    basename = os.path.splitext(os.path.basename(image_path))[0].lower()
    exact_match = []
    partial_match = []

    for section_name, data in sections.items():
        # 完全一致（最優先）
        if basename == section_name:
            exact_match.append(data)
            continue
        # 部分一致：短い側が3文字以上かつ長い側の50%以上の長さである場合のみ
        if section_name in basename or basename in section_name:
            shorter = min(len(basename), len(section_name))
            longer = max(len(basename), len(section_name))
            if shorter >= 3 and longer > 0 and (shorter / longer) >= 0.5:
                partial_match.append(data)
                continue
        # 類似度マッチ（閾値以下の場合のみ試行）
        if threshold < 1.0:
            shorter = min(len(basename), len(section_name))
            longer = max(len(basename), len(section_name))
            if longer > 0:
                common = sum(1 for a, b in zip(basename, section_name) if a == b)
                if common > 0 and (common / longer) >= threshold:
                    partial_match.append(data)

    # 完全一致があれば完全一致のみ返す（混合しない）
    return exact_match if exact_match else partial_match


def check_lora_exists(lora_str: str) -> bool:
    parts = lora_str.split(":")
    lora_name = parts[0].strip()
    try:
        import modules.lora
        if hasattr(modules.lora, 'available_loras'):
            return lora_name in modules.lora.available_loras
    except ImportError:
        pass
    return True

def compose_prompt(image_folder: str, memo_file: str, match_threshold: float) -> tuple:
    """戻り値: (画像パス, positive, negative, ログ)"""
    log = []
    config = load_config()
    fallback_enabled = config.get("fallback_enabled", True)
    auto_lora_enabled = config.get("auto_lora_enabled", True)

    image_files = get_image_files(image_folder)
    if not image_files:
        return None, "", "", "❌ 画像フォルダに画像がありません"

    selected = random.choice(image_files)
    log.append(f"🎲 選択画像: {os.path.basename(selected)}")

    sections = parse_memo_file(memo_file)
    if not sections:
        log.append("⚠️ メモファイルにセクションが見つかりません")
        return selected, "", "", "\n".join(log)

    log.append(f"📖 メモセクション数: {len(sections)}")
    matched = match_image_to_sections(selected, sections, match_threshold)

    if not matched:
        if fallback_enabled and "default" in sections:
            log.append("⚠️ 一致しないため [default] セクションへフォールバックします")
            matched = [sections["default"]]
        else:
            log.append("⚠️ 一致するセクションが見つかりませんでした")
            return selected, "", "", "\n".join(log)

    pos_parts, neg_parts, lora_parts = [], [], []
    seen_pos, seen_neg, seen_lora = set(), set(), set()
    for m in matched:
        p = m.get("positive", "")
        n = m.get("negative", "")
        l_list = m.get("lora", [])
        if p and p not in seen_pos:
            seen_pos.add(p)
            pos_parts.append(p)
        if n and n not in seen_neg:
            seen_neg.add(n)
            neg_parts.append(n)
        for l_item in l_list:
            if l_item and l_item not in seen_lora:
                seen_lora.add(l_item)
                if auto_lora_enabled:
                    if check_lora_exists(l_item):
                        lora_parts.append(f"<lora:{l_item}>")
                    else:
                        parts = l_item.split(":")
                        log.append(f"LoRA not found: {parts[0].strip()}")

    if lora_parts:
        pos_parts = lora_parts + pos_parts

    positive = ", ".join(pos_parts)
    negative = ", ".join(neg_parts)

    log.append(f"✅ 一致数: {len(matched)}件")
    if positive:
        log.append(f"📝 Positive: {positive}")
    if negative:
        log.append(f"🚫 Negative: {negative}")

    return selected, positive, negative, "\n".join(log)


# ======================================================================
# UI ヘルパー
# ======================================================================

def preview_compose(image_folder, memo_file, match_threshold):
    selected, positive, negative, log = compose_prompt(
        image_folder, memo_file, match_threshold
    )
    img = None
    if selected and os.path.isfile(selected):
        try:
            img = Image.open(selected)
        except Exception:
            pass
    return img, positive, negative, log


def save_settings(image_folder, memo_file, match_threshold, generation_count, fallback, auto_lora):
    config = load_config()
    config.update({
        "image_folder": image_folder,
        "memo_file": memo_file,
        "match_threshold": match_threshold,
        "generation_count": int(generation_count),
        "fallback_enabled": fallback,
        "auto_lora_enabled": auto_lora,
    })
    return save_config(config)


def save_gen_settings(confidence, pos, neg, custom, cat_base, cat_char, cat_nsfw):
    categories = cat_base + cat_char + cat_nsfw
    config = load_config()
    config.update({
        "gen_confidence": confidence,
        "gen_positive": pos,
        "gen_negative": neg,
        "gen_custom_dict": custom,
        "gen_categories": categories,
    })
    return save_config(config)


# ======================================================================
# WD14 Tagger 連携 — タグフィルタリング
# ======================================================================
# img2imgで元キャラに干渉しないタグのみ通す（構図/ポーズ/シーン/照明）

# ── 許可タグカテゴリ辞書 ──
_TAG_CATEGORIES = {
    "構図・カメラ": {
        "portrait", "upper_body", "lower_body", "full_body",
        "cowboy_shot", "close-up", "wide_shot", "medium_shot",
        "head_shot", "bust_shot", "knee_shot", "profile", "three-quarter_view",
        "from_above", "from_below", "from_behind", "from_side",
        "from_outside", "dutch_angle", "tilted_frame",
        "pov", "first-person_view", "over-shoulder_shot",
        "bird's-eye_view", "worm's-eye_view", "aerial_view",
        "looking_at_viewer", "looking_away", "looking_back",
        "looking_down", "looking_up", "looking_to_the_side",
        "looking_afar", "looking_at_another",
        "facing_away", "facing_viewer", "rotated",
    },
    "ポーズ・アクション": {
        "standing", "sitting", "lying", "walking", "running",
        "jumping", "crouching", "kneeling", "leaning",
        "leaning_forward", "leaning_back",
        "arms_up", "arms_behind_back", "arms_behind_head",
        "hand_on_hip", "hand_on_own_chest", "hand_on_own_face",
        "hands_on_hips", "hand_up", "hands_up",
        "crossed_arms", "hands_in_pockets",
        "outstretched_arm", "outstretched_arms",
        "reaching", "reaching_out", "pointing", "pointing_at_viewer",
        "spread_arms", "stretching", "waving",
        "v", "peace_sign", "thumbs_up", "double_v",
        "on_back", "on_stomach", "on_side",
        "legs_crossed", "indian_style", "seiza", "wariza",
        "legs_apart", "legs_together",
        "one_knee", "squatting", "head_tilt", "head_rest",
        "arched_back", "fetal_position", "hugging_own_legs",
        "lying_on_back", "lying_on_stomach", "lying_on_side",
        "sitting_on_chair", "sitting_on_floor", "sitting_on_bench",
        "standing_on_one_leg", "contrapposto",
        "back-to-back", "arm_support", "chin_rest",
        "holding", "carrying",
        "dancing", "fighting_stance", "battle_stance",
        "action", "dynamic_pose", "floating",
        "falling", "spinning", "twisting",
    },
    "背景・場所": {
        "outdoors", "indoors", "cityscape", "landscape", "scenery",
        "city", "town", "village", "suburb",
        "sky", "blue_sky", "cloudy_sky", "starry_sky", "night_sky",
        "cloud", "clouds", "sunset", "sunrise", "twilight", "dawn", "dusk",
        "night", "day", "evening", "morning", "afternoon",
        "forest", "woods", "jungle", "mountain", "hill", "cliff", "valley",
        "ocean", "sea", "beach", "shore", "coast",
        "river", "lake", "pond", "waterfall", "stream",
        "field", "meadow", "grassland", "plains",
        "garden", "park", "playground",
        "street", "road", "path", "alley", "sidewalk",
        "school", "classroom", "library", "gym",
        "office", "workplace", "studio",
        "bedroom", "kitchen", "bathroom", "living_room",
        "dining_room", "hallway", "corridor",
        "rooftop", "balcony", "veranda", "patio", "terrace",
        "window", "door", "doorway",
        "castle", "palace", "mansion",
        "temple", "shrine", "church", "cathedral",
        "ruins", "dungeon", "cave", "cavern",
        "bridge", "stairs", "staircase", "escalator",
        "train", "train_interior", "train_station", "platform",
        "bus", "bus_interior", "bus_stop", "car", "car_interior",
        "ship", "boat", "dock", "harbor", "port",
        "airport", "airplane", "airplane_interior",
        "restaurant", "cafe", "bar", "shop", "store",
        "hospital", "prison", "factory",
        "arena", "stadium", "stage", "theater",
        "space", "planet", "moon", "stars",
        "underwater", "floating_island",
        "marketplace", "bazaar", "festival",
        "cemetery", "graveyard",
        "tower", "lighthouse", "windmill",
        "fountain", "statue", "monument",
        "desert", "oasis", "wasteland", "swamp",
        "volcano", "island", "archipelago",
    },
    "自然・天候": {
        "snow", "snowing", "rain", "raining", "storm",
        "fog", "mist", "haze", "wind", "windy", "breeze",
        "lightning", "thunder", "rainbow",
        "cherry_blossoms", "petals", "falling_petals",
        "autumn_leaves", "falling_leaves",
        "flower", "flowers", "bouquet",
        "tree", "trees", "bamboo",
        "grass", "moss", "ivy", "vines",
        "water", "waves", "ripples", "puddle",
        "fire", "flame", "campfire", "bonfire",
        "ice", "icicle", "frost",
        "sunbeam", "light_particles", "sparkle",
        "bubble", "bubbles",
        "feather", "feathers", "leaf", "leaves",
        "butterfly", "bird", "birds",
    },
    "照明": {
        "sunlight", "moonlight", "starlight",
        "backlighting", "backlight",
        "rim_lighting", "rim_light",
        "dramatic_lighting", "soft_lighting",
        "cinematic_lighting", "natural_lighting",
        "volumetric_lighting", "volumetric_light",
        "studio_lighting",
        "light_rays", "crepuscular_rays", "god_rays",
        "lens_flare", "light_leak",
        "shadow", "shadows", "silhouette",
        "reflection", "reflective",
        "glow", "glowing", "neon_lights",
        "candlelight", "firelight", "lamplight",
        "streetlight", "spotlight",
        "warm_lighting", "cool_lighting",
        "ambient_light", "diffused_light",
        "dappled_light", "dappled_sunlight",
        "chiaroscuro", "high_contrast", "low_key",
    },
    "雰囲気": {
        "depth_of_field", "bokeh", "shallow_depth_of_field",
        "blurry_background", "blurry_foreground",
        "detailed_background", "simple_background",
        "white_background", "black_background", "gradient_background",
        "motion_blur", "speed_lines",
        "chromatic_aberration", "film_grain", "noise",
        "vignette", "bloom",
        "atmospheric_perspective", "hazy", "soft_focus",
        "monochrome", "sepia", "desaturated",
        "vibrant", "colorful", "pastel",
        "dark", "bright", "dim",
        "wide_angle", "telephoto", "fisheye",
        "panorama", "split_screen",
    },
    "人物・基本属性": {
        "re:^\\d+girl", "re:^\\d+boy", "solo", "duo", "trio", "multiple_girls", "multiple_boys",
        "couple", "group", "re:.*breasts?$", "re:^slim$", "re:^muscular", "petite", "chubby",
        "thick_thighs", "wide_hips", "narrow_waist", "abs", "navel", "midriff", "cleavage",
        "collarbone", "re:^shoulder", "re:_skin$", "re:^skin_", "pale", "tan", "re:^dark_skin",
        "re:^nail", "re:^lip", "ear", "ears", "nose", "mole", "scar", "tattoo", "freckle"
    },
    "髪型・顔周り": {
        "re:_hair$", "re:^hair_", "bangs", "ponytail", "twintails", "braid", "ahoge", "sidelocks",
        "bob_cut", "hime_cut", "pixie_cut", "drill_hair", "long_hair", "short_hair", "medium_hair",
        "very_long_hair", "re:_eyes$", "heterochromia", "eyelashes", "pupils"
    },
    "表情・口": {
        "smile", "grin", "frown", "smirk", "re:^blush", "open_mouth", "closed_mouth",
        "re:^fang", "tears", "crying", "sweatdrop", "re:^tongue", "pout", "surprised", "angry",
        "embarrassed", "shy", "sad", "happy", "expressionless", "serious"
    },
    "服装・靴・装飾品": {
        "re:^dress", "re:^shirt", "re:^skirt", "pants", "shorts", "re:^uniform", "re:^armor",
        "re:^bikini", "re:^swimsuit", "re:^jacket", "coat", "cape", "cloak", "re:^hoodie",
        "re:^sweater", "vest", "re:^cardigan", "re:^kimono", "yukata", "hanfu", "re:^maid",
        "re:^apron", "suit", "re:^tuxedo", "robe", "toga", "gown", "re:^crop_top", "tank_top",
        "t-shirt", "re:^blouse", "re:^tunic", "re:^corset", "re:^overalls", "re:^jumpsuit",
        "bodysuit", "re:^pajamas", "nightgown", "re:^lingerie", "re:^underwear", "bra", "panties",
        "re:^leotard", "one-piece", "gloves", "boots", "shoes", "socks", "sandals", "sneakers",
        "heels", "slippers", "stockings", "thighhighs", "pantyhose", "kneehighs", "ankle_socks",
        "re:^glasses", "re:^sunglasses", "re:^goggles", "re:^earring", "re:^necklace", "ring",
        "re:^bracelet", "re:^choker", "collar", "scarf", "tie", "necktie", "re:^bowtie", "re:^ribbon",
        "bow", "hat", "cap", "crown", "tiara", "re:^headband", "re:^hairclip", "hair_ornament",
        "hair_ribbon", "re:^hairband", "re:^headpiece", "re:^headwear", "bag", "re:^backpack",
        "re:^purse", "re:^handbag", "umbrella", "parasol", "re:^weapon", "sword", "gun", "staff",
        "wand", "shield", "spear", "axe", "knife", "dagger", "mask", "re:^eyepatch", "re:^wing",
        "re:^zipper", "re:^button", "hood", "re:^hooded",
        "jirai_kei", "yami_kawaii", "cybergoth", "wa_lolita", "qi_lolita", "zettai_ryouiki"
    },
    "🎭 行為・アクション": {
        "sex", "kissing", "hugging", "embracing", "holding_hands",
        "bound", "tied_up", "shibari", "rope", "gag", "gagged",
        "blindfold", "blindfolded", "chained", "cuffs", "handcuffs",
        "sleeping", "crying", "drinking", "eating",
        "fighting", "punching", "kicking", "slapping",
        "petting", "stroking", "licking", "sucking", "biting",
        "missionary", "doggystyle", "paizuri", "blowjob", "handjob", "footjob", "titfuck",
        "masturbation", "fingering", "cunnilingus", "anilingus", "anal", "vaginal", "oral",
        "tribadism", "reverse_cowgirl_position", "cowgirl_position", "mating_press", "spanking",
        "threesome", "group_sex", "gangbang", "orgy",
        "facesitting", "smothering", "breast_smother", "double_penetration", "triple_penetration", 
        "futa_with_futa", "futa_on_female", "choking", "asphyxiation", "spitroast", "thigh_sex", 
        "armpit_sex", "deepthroat",
        "prone_bone", "lying_on_back", "glory_wall", "standing_sex", "standing_split_sex", "anvil_position",
        "girl_on_top", "boy_on_top", "straddling", "upright_straddle", "reverse_upright_straddle",
        "suspended_congress", "reverse_suspended_congress", "full_nelson", "cooperative_paizuri",
        "69_position", "buttjob", "straddling_paizuri", "piledriver_sex", "amazon_position",
        "human_stacking", "grinding", "mutual_fingering", "breast_press", "breast_sucking",
        "self_breast_sucking", "groping", "symmetrical_docking", "torso_grab", "handjob_over_clothes",
        "fingering_through_clothes", "fingering_through_panties", "hand_in_another's_panties",
        "tail_masturbation", "stealth_masturbation", "clothed_masturbation", "female_masturbation",
        "male_masturbation", "clitoral_stimulation", "nipple_pull", "box_tie", "frogtie", "hogtie",
        "shrimp_tie", "strappado", "bound_breasts", "bound_wrists", "bound_ankles", "femdom", "defloration",
        "re:^tentacle", "mind_control", "hypnosis"
    },
    "🦑 クリーチャー・追加キャラ": {
        "monster", "creature", "demon", "devil", "angel",
        "orc", "goblin", "elf", "beast", "dragon",
        "slime", "tentacles", "alien", "ghost", "zombie",
        "robot", "cyborg", "android", "mecha",
        "animal", "dog", "cat", "bird", "fish", "horse", "wolf", "fox"
    },
    "🧸 アイテム・玩具": {
        "toy", "sex_toy", "vibrator", "dildo", "plug", "magic_wand",
        "whip", "crop", "leash", "collar",
        "weapon", "sword", "gun", "knife", "bow", "shield",
        "book", "phone", "smartphone", "laptop", "bag",
        "cup", "glass", "bottle", "plate", "food",
        "re:^wand", "staff", "magic", "cigarette", "pipe",
        "suction_cup_dildo", "used_condom", "hitachi_magic_wand", "crotch_tattoo",
        "crotch_rope", "milking_machine", "breast_pump", "dilation_tape"
    },
    "🔞 特殊構図・フォーカス": {
        "x-ray", "cross-section", "internal_cumshot", "womb", "stomach_deformation",
        "pov", "focus_on_breasts", "focus_on_ass", "focus_on_crotch", "focus_on_thighs", "cameltoe",
        "ass_focus", "breast_focus", "crotch_focus", "thigh_focus", "foot_focus", "armpit_focus",
        "impregnation", "stomach_bulge", "throat_bulge",
        "before_sex", "after_sex", "after_vaginal", "fucked_silly", "cross-section",
        "close-up", "macro", "from_below", "from_above", "dutch_angle"
    },
    "💦 体液・汚れ系": {
        "cum", "creampie", "cum_on_face", "cum_on_breasts", "cum_in_pussy", "cum_inside", "cum_on_stomach",
        "semen", "sperm", "ejaculation", "facial", "bukkake",
        "cum_in_mouth", "cum_in_ass", "cum_on_hair", "cum_pool", "swallowing", "swallowing_cum",
        "sweat", "sweatdrop", "saliva", "drool", "tears", "crying",
        "messy", "dirty", "covered_in_cum", "wet", "wet_clothes", "wet_hair",
        "urine", "peeing", "squirt", "love_nectar",
        "lactation", "breast_milk", "milk", "pussy_juice", "menstruation",
        "cum_drip_creampie", "cum_on_body", "cum_on_clothes", "pussy_juice_drip",
        "pussy_juice_puddle", "pussy_juice_trail", "pussy_juice_stain", "wet_panty",
        "wet_stain_on_panty", "drinking_pee", "peeing_in_cup", "public_urination", "peeing_self"
    },
    "🥵 表情・フェティッシュ状態": {
        "ahegao", "heart-shaped_pupils", "rolled_back_eyes", "empty_eyes", "crazy_eyes",
        "heavy_breathing", "panting", "trembling", "shaking", "blush", "heavy_blush",
        "nosebleed", "open_mouth", "tongue_out", "saliva_trail",
        "mind_break", "corruption", "trance", "hypnotized"
    },
    "👗 衣服の乱れ・着脱": {
        "clothes_pull", "tearing_clothes", "skirt_lift", "shirt_lift", "undressing", 
        "panties_pulled_down", "half-closed_eyes", "partially_unbuttoned",
        "micro_bikini", "slingshot_swimsuit", "pasties",
        "nip_slip", "wardrobe_malfunction", "torn_clothes", "see-through",
        "panty_pull", "bra_pull", "no_panties", "no_bra", "breast_spilling_over", "crotchless_panties",
        "panty_around_knees", "panties_aside", "panties_around_ankles", "panties_around_one_leg",
        "panties_on_head", "pantyshot", "adjusting_panties", "holding_panties", "licking_panties",
        "panty_lift", "smelling_underwear", "wedgie", "tentacles_under_clothes",
        "naked", "nude", "topless", "bottomless"
    },
    "🍆 局所・モザイク": {
        "penis", "balls", "testicles", "erection", "vein", "precum", "foreskin",
        "pussy", "vagina", "clitoris", "labia", "cameltoe", "pubic_hair", "anus",
        "huge_penis", "monster_penis", "horse_penis", "tentacle_penetration", "multiple_penises", "futanari",
        "uncensored", "censored", "bar_censor", "mosaic_censoring", "censor_steam",
        "holding_penis", "rubbing_penis", "fucking_machine", "glory_hole", "crotch",
        "nipples", "erect_nipples", "areola", "ass", "asshole", "butt",
        "spread_pussy", "gaping", "cleft_of_venus", "wet_shiny_vagina", "cervix",
        "urethra", "groin_tendon", "clitoral_hood", "erect_clitoris", "clitoris_slip",
        "puffy_nipples", "inverted_nipples", "presenting_nipples", "presenting_crotch",
        "ofuda_on_pussy", "futa_with_female", "ovum", "fertilization", "sperm_cell"
    },
    "メタタグ": {
        "highres", "absurdres", "masterpiece", "best_quality", "re:_quality$", "re:^rating_",
        "re:^score_", "realistic", "anime", "manga", "official_art", "key_visual",
        "traditional_media", "digital_media"
    }
}


def _filter_tags(tags: dict, confidence_threshold: float = 0.35, selected_categories=None) -> dict:
    """許可タグカテゴリに含まれるタグのみ残すフィルタ"""
    if selected_categories is None:
        selected_categories = list(_TAG_CATEGORIES.keys())

    allowed_tags = set()
    allowed_patterns = []
    
    for cat in selected_categories:
        if cat in _TAG_CATEGORIES:
            for item in _TAG_CATEGORIES[cat]:
                if item.startswith("re:"):
                    allowed_patterns.append(re.compile(item[3:]))
                else:
                    allowed_tags.add(item)

    filtered = {}
    for tag, score in tags.items():
        if score < confidence_threshold:
            continue
            
        tag_clean = tag.strip().lower().replace(" ", "_")
        
        if tag_clean in allowed_tags:
            filtered[tag_clean] = score
            continue
            
        for p in allowed_patterns:
            if p.search(tag_clean):
                filtered[tag_clean] = score
                break
                
    return filtered


def _tags_to_prompt(tags: dict) -> str:
    """タグを信頼度順でプロンプト文字列に変換"""
    if not tags:
        return ""
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    return ", ".join(tag.replace("_", " ") for tag, _ in sorted_tags)


def _find_tagger():
    """WD14 Tagger モジュールを検索"""
    # 方法1: 直接import
    try:
        from tagger import interrogator as tagger_mod
        return tagger_mod, None
    except ImportError:
        pass

    # 方法2: extensions ディレクトリを走査して手動追加
    try:
        webui_root = os.path.dirname(os.path.dirname(EXTENSION_DIR))
        extensions_dir = os.path.join(webui_root, "extensions")
        if os.path.isdir(extensions_dir):
            for dirname in os.listdir(extensions_dir):
                if "tagger" in dirname.lower() or "wd14" in dirname.lower():
                    tagger_path = os.path.join(extensions_dir, dirname)
                    if tagger_path not in sys.path:
                        sys.path.insert(0, tagger_path)
            try:
                from tagger import interrogator as tagger_mod
                return tagger_mod, None
            except ImportError:
                pass
    except Exception:
        pass

    return None, (
        "❌ WD14 Tagger が見つかりません。\n"
        "stable-diffusion-webui-wd14-tagger をインストールしてください:\n"
        "https://github.com/toriato/stable-diffusion-webui-wd14-tagger"
    )


def _interrogate_image(pil_image, confidence_threshold: float = 0.35, selected_categories=None):
    """WD14 Taggerで画像解析 → フィルタ済みタグを返す"""
    tagger_mod, error = _find_tagger()
    if tagger_mod is None:
        return {}, {}, error

    try:
        all_tags = {}
        success = False

        # パターン1: 推奨 - tagger.utils.interrogators から実体インスタンスを取得
        try:
            from tagger import utils as tagger_utils
            if hasattr(tagger_utils, "interrogators") and isinstance(tagger_utils.interrogators, dict) and tagger_utils.interrogators:
                # デフォルトモデルを探す、なければ最初のもの
                default_model = "wd14-convnext.v2"
                if default_model in tagger_utils.interrogators:
                    interrogator_obj = tagger_utils.interrogators[default_model]
                else:
                    interrogator_obj = list(tagger_utils.interrogators.values())[0]

                res = interrogator_obj.interrogate(pil_image)
                # res は (rating_dict, tag_dict) のタプル
                if isinstance(res, tuple) and len(res) >= 2:
                    all_tags = res[1] if isinstance(res[1], dict) else {}
                    success = True
                elif isinstance(res, dict):
                    all_tags = res
                    success = True
        except ImportError:
            pass
        except Exception as e:
            print(f"[Random Composer] tagger.utils pattern error: {e}")

        # パターン2: tagger.api.interrogate (新しいWD14拡張のエンドポイント)
        if not success:
            try:
                import tagger.api as tagger_api
                if hasattr(tagger_api, "interrogate"):
                    res = tagger_api.interrogate(pil_image)
                    if isinstance(res, dict) and "caption" in res:
                        all_tags = res["caption"]
                        success = True
                    elif isinstance(res, dict):
                        all_tags = res
                        success = True
                    elif isinstance(res, tuple) and len(res) >= 2:
                        all_tags = res[1]
                        success = True
            except Exception:
                pass

        # パターン3: インタロゲータークラスのget_interrogators
        if not success and hasattr(tagger_mod, "Interrogator"):
            cls = tagger_mod.Interrogator
            interrogators_dict = {}
            if hasattr(cls, "get_interrogators"):
                res = cls.get_interrogators()
                if isinstance(res, dict):
                    interrogators_dict = res
            elif hasattr(cls, "interrogators"):
                res = cls.interrogators
                if isinstance(res, dict):
                    interrogators_dict = res

            if interrogators_dict:
                interrogator_obj = list(interrogators_dict.values())[0]
                
                # 自動ロードを期待してそのままinterrogate
                res = interrogator_obj.interrogate(pil_image)
                if isinstance(res, tuple) and len(res) >= 2:
                    all_tags = res[1] if isinstance(res[1], dict) else {}
                    success = True
                elif isinstance(res, dict):
                    all_tags = res
                    success = True

        if not success:
            return {}, {}, "❌ 対応するインタロゲーターが見つかりません。Taggerのモデルがダウンロードされていないか、拡張のバージョンが非対応です。"

        return _filter_tags(all_tags, confidence_threshold, selected_categories), all_tags, None

    except Exception as e:
        return {}, {}, f"❌ タグ取得エラー: {e}\n{traceback.format_exc()}"


# ======================================================================
# プロンプト自動生成
# ======================================================================

def get_stable_dimensions(img, base_size=1024):
    """画像のアスペクト比を維持しつつ、指定ベースサイズに合わせた解像度を返す"""
    if not img:
        return base_size, base_size
    w, h = img.size
    aspect = w / h
    if w > h:
        new_w = base_size
        new_h = int(new_w / aspect)
    else:
        new_h = base_size
        new_w = int(new_h * aspect)
    # SDで安定しやすいよう64の倍数にスナップ
    new_w = max(64, round(new_w / 64) * 64)
    new_h = max(64, round(new_h / 64) * 64)
    return new_w, new_h

def autogen_prompt(image, section_name, confidence, pos_prompt, neg_prompt, cat_base, cat_char, cat_nsfw, custom_dict_str):
    """画像を解析してメモエントリを生成"""
    gen_categories = cat_base + cat_char + cat_nsfw
    if image is None:
        return "", "❌ 画像をアップロードしてください"

    if not section_name or not section_name.strip():
        return "", "❌ セクション名を入力してください"

    try:
        section_name = section_name.strip()
        pos = pos_prompt.strip() if pos_prompt else ""
        neg = neg_prompt.strip() if neg_prompt else ""

        filtered, all_tags, error = _interrogate_image(image, confidence, gen_categories)
        if error:
            return "", error

        log_lines = []
        log_lines.append(f"📊 全タグ数: {len(all_tags)}")
        log_lines.append(f"✅ フィルタ後: {len(filtered)}")

        excluded_count = len(all_tags) - len(filtered)
        if excluded_count > 0:
            log_lines.append(f"🗑️ 除外タグ数: {excluded_count}")

        # ==== 好みのプロンプトの条件付与 ====
        matched_custom_prompts = []
        if custom_dict_str and custom_dict_str.strip():
            for line in custom_dict_str.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                separator = "=>" if "=>" in line else "->" if "->" in line else ">" if ">" in line else None
                if not separator:
                    continue
                
                left, right = line.split(separator, 1)
                condition_tags = [t.strip().lower().replace(" ", "_") for t in left.split(",")]
                right_prompt = right.strip()
                
                if not condition_tags or not right_prompt:
                    continue
                
                # すべての条件タグが抽出された全タグ(all_tags)に含まれているかチェック
                match = True
                for c_tag in condition_tags:
                    if c_tag not in all_tags:
                        match = False
                        break
                
                if match:
                    matched_custom_prompts.append(right_prompt)
                    log_lines.append(f"🎯 条件マッチ: [{left}] => 追加: {right_prompt}")

        # タグの文字列化
        generated_tags = _tags_to_prompt(filtered)

        # デフォルトポジティブ、カスタムプロンプト、抽出タグを結合
        components = []
        if pos:
            components.append(pos)
        if matched_custom_prompts:
            components.extend(matched_custom_prompts)
        if generated_tags:
            components.append(generated_tags)
            
        final_positive = ", ".join(components)

        if not final_positive:
            log_lines.append("⚠️ 有効なポジティブプロンプトがありません")
        else:
            log_lines.append(f"📝 Positive: {final_positive}")
            
        if neg:
            log_lines.append(f"🚫 Negative: {neg}")

        entry = (
            f"[{section_name}]\n"
            f"positive:\n"
            f"{final_positive}\n"
            f"\n"
            f"negative:\n"
            f"{neg}\n"
        )
        w, h = get_stable_dimensions(image)
        return entry, "\n".join(log_lines), final_positive, neg, str(w), str(h)

    except Exception as e:
        return "", f"❌ エラー: {e}\n{traceback.format_exc()}", "", "", "512", "512"


def append_to_memo(memo_path, entry):
    """メモファイルにエントリを追記"""
    if not memo_path or not memo_path.strip():
        return "❌ メモファイルパスが未設定です（設定タブで保存してください）"
    if not entry or not entry.strip():
        return "❌ 追記するエントリがありません（まずプロンプトを生成してください）"

    try:
        memo_path = memo_path.strip()
        dirpart = os.path.dirname(memo_path)
        if dirpart:
            os.makedirs(dirpart, exist_ok=True)

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

        return "✅ メモファイルに追記しました"
    except IOError as e:
        return f"❌ 追記に失敗しました: {e}"


# ======================================================================
# img2img フック
# ======================================================================

class RandomComposerScript(scripts.Script):

    def title(self):
        return "Smart Img2Img Composer"

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else False

    def ui(self, is_img2img):
        if not is_img2img:
            return []
        with gr.Accordion("🎲 Smart Img2Img Composer", open=False, elem_id="smart_composer_accordion"):
            gr.Markdown(
                "**有効化 → Generate で自動実行。** 設定は「Smart Img2Img Composer」タブで保存。"
            )
            enabled = gr.Checkbox(
                label="✅ 有効化（生成時にランダム画像＋プロンプト自動投入）",
                value=False,
                elem_id="smart_composer_enabled",
            )
            override_prompt = gr.Checkbox(
                label="プロンプトを上書き（OFFなら既存の末尾に追加）",
                value=True,
                elem_id="smart_composer_override",
            )
            auto_resize = gr.Checkbox(
                label="📐 画像サイズ自動調整（画像に合わせて解像度を変更）",
                value=False,
                elem_id="smart_composer_auto_resize",
            )
            base_resolution = gr.Slider(
                label="📏 ベース解像度（長辺をこの値に合わせる）",
                minimum=512, maximum=2048, step=64,
                value=1024,
                elem_id="smart_composer_base_resolution",
                info="SDXL / Illustrious: 1024〜1536 推奨 ／ SD1.5: 512 推奨",
            )
        return [enabled, override_prompt, auto_resize, base_resolution]

    def before_process(self, p: processing.StableDiffusionProcessing, enabled, override_prompt, auto_resize=False, base_resolution=1024):
        """before_process のみでプロンプト注入を行う（二重実行防止）"""
        if not enabled:
            return

        config = load_config()
        selected, positive, negative, log = compose_prompt(
            config.get("image_folder", ""),
            config.get("memo_file", ""),
            config.get("match_threshold", 0.3),
        )

        generation_count = config.get("generation_count", 1)
        if generation_count > 1:
            p.n_iter = generation_count

        if selected:
            try:
                img = Image.open(selected).convert("RGB")
                p.init_images = [img]
                # 画像サイズ自動調整が有効な場合のみ解像度を変更
                if auto_resize:
                    # ベース解像度の数値を抽出
                    base_size = int(base_resolution) if base_resolution else 1024
                    new_w, new_h = get_stable_dimensions(img, base_size)
                    p.width = new_w
                    p.height = new_h
            except Exception as e:
                print(f"[Smart Img2Img Composer] 画像読み込み失敗: {e}")

        if positive:
            if override_prompt:
                p.prompt = positive
            else:
                p.prompt = f"{p.prompt}, {positive}" if p.prompt else positive

        if negative:
            if override_prompt:
                p.negative_prompt = negative
            else:
                if p.negative_prompt:
                    p.negative_prompt = f"{p.negative_prompt}, {negative}"
                else:
                    p.negative_prompt = negative

        if hasattr(p, "all_prompts") and p.all_prompts:
            p.all_prompts = [p.prompt] * len(p.all_prompts)
        if hasattr(p, "all_negative_prompts") and p.all_negative_prompts:
            p.all_negative_prompts = [p.negative_prompt] * len(p.all_negative_prompts)

        print(f"[Smart Img2Img Composer]\n{log}")


# ======================================================================
# 独立タブ UI
# ======================================================================

def on_ui_tabs():
    config = load_config()

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown(
            "# 🎲 Smart Img2Img Composer\n"
            "ランダム画像 → プロンプト自動取得 → img2img へ投入"
        )

        # ─── 設定 & プレビュー ───
        with gr.Tab("⚙️ 設定 & プレビュー"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### ⚙️ 設定")
                    image_folder = gr.Textbox(
                        label="📁 画像フォルダ",
                        placeholder="例: C:/images/input",
                        value=lambda: load_config().get("image_folder", ""),
                    )
                    memo_file = gr.Textbox(
                        label="📄 メモファイル",
                        placeholder="例: C:/images/memo.txt",
                        value=lambda: load_config().get("memo_file", ""),
                    )
                    match_threshold = gr.Slider(
                        label="🎯 一致率",
                        minimum=0.0, maximum=1.0, step=0.05,
                        value=lambda: load_config().get("match_threshold", 0.3),
                    )
                    generation_count = gr.Slider(
                        label="🔄 生成回数",
                        minimum=1, maximum=100, step=1,
                        value=lambda: load_config().get("generation_count", 1),
                    )
                    fallback_enabled = gr.Checkbox(
                        label="☑ fallback enabled",
                        value=lambda: load_config().get("fallback_enabled", True),
                    )
                    auto_lora_enabled = gr.Checkbox(
                        label="☑ auto LoRA injection enabled",
                        value=lambda: load_config().get("auto_lora_enabled", True),
                    )
                    with gr.Row():
                        save_btn = gr.Button("💾 保存", variant="primary")
                        preview_btn = gr.Button("👁️ プレビュー", variant="secondary")
                    save_status = gr.Textbox(label="ステータス", interactive=False, max_lines=1)

                with gr.Column(scale=1):
                    gr.Markdown("### 👁️ プレビュー結果")
                    preview_image = gr.Image(label="選択画像", type="pil", interactive=False)
                    preview_positive = gr.Textbox(label="📝 Positive", interactive=False, lines=3)
                    preview_negative = gr.Textbox(label="🚫 Negative", interactive=False, lines=2)
                    preview_log = gr.Textbox(label="ログ", interactive=False, lines=6)

            save_btn.click(
                fn=save_settings,
                inputs=[image_folder, memo_file, match_threshold, generation_count, fallback_enabled, auto_lora_enabled],
                outputs=[save_status],
            )
            preview_btn.click(
                fn=preview_compose,
                inputs=[image_folder, memo_file, match_threshold],
                outputs=[preview_image, preview_positive, preview_negative, preview_log],
            )

        # ─── プロンプト自動生成 ───
        with gr.Tab("🏷️ プロンプト自動生成"):
            gr.Markdown(
                "### 🏷️ WD14 Tagger で自動プロンプト生成\n"
                "画像をアップロード → シーン/ポーズ/構図のタグだけ抽出 → メモファイルに追記\n\n"
                "**服装・人物特徴は自動除外されます。**"
            )

            with gr.Row():
                with gr.Column(scale=1):
                    gen_image = gr.Image(
                        label="📸 解析する画像",
                        type="pil",
                        interactive=True,
                    )
                    gen_section = gr.Textbox(
                        label="📌 セクション名",
                        placeholder="例: タイトル1",
                        info="メモファイルの [セクション名] になる",
                    )
                    # --- アコーディオン化されたタグカテゴリ ---
                    _cat_base = ["構図・カメラ", "ポーズ・アクション", "背景・場所", "自然・天候", "照明", "雰囲気", "メタタグ"]
                    _cat_char = ["人物・基本属性", "髪型・顔周り", "表情・口", "服装・靴・装飾品"]
                    _cat_nsfw = ["🎭 行為・アクション", "🦑 クリーチャー・追加キャラ", "🧸 アイテム・玩具", "🔞 特殊構図・フォーカス", "💦 体液・汚れ系", "🥵 表情・フェティッシュ状態", "👗 衣服の乱れ・着脱", "🍆 局所・モザイク"]
                    
                    gr.Markdown("### 🏷️ 抽出するタグの種類（チェックした種類のタグだけを抽出します）")
                    with gr.Accordion("🖼️ 基本カテゴリ (構図・背景など)", open=True):
                        gen_cat_base = gr.CheckboxGroup(
                            choices=_cat_base,
                            value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_base],
                            show_label=False
                        )
                    with gr.Accordion("👩 人物・詳細カテゴリ (髪型・服装など)", open=False):
                        gen_cat_char = gr.CheckboxGroup(
                            choices=_cat_char,
                            value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_char],
                            show_label=False
                        )
                    with gr.Accordion("🔞 特殊・NSFWカテゴリ (行為・アイテム等)", open=False):
                        gen_cat_nsfw = gr.CheckboxGroup(
                            choices=_cat_nsfw,
                            value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_nsfw],
                            show_label=False
                        )
                    # --------------------------------------
                    gen_confidence = gr.Slider(
                        label="🎯 タグ信頼度しきい値",
                        minimum=0.1, maximum=0.9, step=0.05,
                        value=lambda: load_config().get("gen_confidence", 0.35),
                        info="低いほど多くのタグが含まれる",
                    )
                    gen_positive = gr.Textbox(
                        label="✨ デフォルトポジティブ",
                        value=lambda: load_config().get("gen_positive", "(masterpiece:1.1), (best quality:1.0), "),
                        lines=2,
                        info="抽出されたタグの先頭に自動で付与されるベースプロンプト",
                    )
                    gen_custom_dict = gr.Textbox(
                        label="📚 好みのプロンプト置き場（条件付与）",
                        value=lambda: load_config().get("gen_custom_dict", "night, city > cyberpunk cityscape, neon lights, highly detailed, vivid colors\n1girl, smile > beautiful detailed eyes, glowing smile"),
                        lines=3,
                        info="「条件タグ > 追加したいプロンプト」の形式で記述 (複数行可)。画像から条件タグが出た時のみ追加されます。",
                    )
                    gen_negative = gr.Textbox(
                        label="🚫 デフォルトネガティブ",
                        value=lambda: load_config().get("gen_negative", "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts"),
                        lines=2,
                        info="自動生成時に追加するネガティブプロンプト",
                    )
                    with gr.Row():
                        gen_btn = gr.Button("🏷️ タグ解析＆生成", variant="primary")
                        send_to_img2img_btn = gr.Button("🚀 img2imgに送る", variant="primary")
                    with gr.Row():
                        append_btn = gr.Button("📝 メモファイルに追記", variant="secondary")
                        gen_save_btn = gr.Button("💾 設定を保存", variant="secondary")

                try:
                    from modules import generation_parameters_copypaste as params_copypaste
                    params_copypaste.register_paste_params_button(
                        params_copypaste.ParamBinding(
                            paste_button=send_to_img2img_btn, tabname="img2img", source_image_component=gen_image
                        )
                    )
                except Exception as e:
                    print(f"[Smart Img2Img Composer] Image copypaste binding disabled: {e}")

                with gr.Column(scale=1):
                    gen_output = gr.Textbox(
                        label="✨ 生成されたメモエントリ",
                        interactive=True,
                        lines=10,
                        info="編集してからメモファイルに追記できます(不要なタグがあればここで削除)",
                    )
                    gen_log = gr.Textbox(
                        label="解析ログ",
                        interactive=False,
                        lines=8,
                    )
                    with gr.Row():
                        append_status = gr.Textbox(
                            label="追記ステータス",
                            interactive=False,
                            max_lines=1,
                        )
                        gen_save_status = gr.Textbox(
                            label="保存ステータス",
                            interactive=False,
                            max_lines=1,
                        )
                    # 内部保持用の隠しコンポーネント
                    hidden_gen_pos = gr.Textbox(visible=False)
                    hidden_gen_neg = gr.Textbox(visible=False)
                    hidden_gen_w = gr.Textbox(visible=False)
                    hidden_gen_h = gr.Textbox(visible=False)

            gen_btn.click(
                fn=autogen_prompt,
                inputs=[gen_image, gen_section, gen_confidence, gen_positive, gen_negative, gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_custom_dict],
                outputs=[gen_output, gen_log, hidden_gen_pos, hidden_gen_neg, hidden_gen_w, hidden_gen_h],
            )
            
            send_to_img2img_btn.click(
                fn=None,
                _js="""
                function(pos, neg, w, h) {
                    var pos_elem = gradioApp().querySelector('#img2img_prompt textarea');
                    if (pos_elem) {
                        pos_elem.value = pos;
                        updateInput(pos_elem);
                    }
                    var neg_elem = gradioApp().querySelector('#img2img_neg_prompt textarea');
                    if (neg_elem) {
                        neg_elem.value = neg;
                        updateInput(neg_elem);
                    }
                    if (w && h) {
                        var w_num = gradioApp().querySelector('#img2img_width input[type="number"]');
                        var w_range = gradioApp().querySelector('#img2img_width input[type="range"]');
                        if (w_num) { w_num.value = w; updateInput(w_num); }
                        if (w_range) { w_range.value = w; updateInput(w_range); }
                        var h_num = gradioApp().querySelector('#img2img_height input[type="number"]');
                        var h_range = gradioApp().querySelector('#img2img_height input[type="range"]');
                        if (h_num) { h_num.value = h; updateInput(h_num); }
                        if (h_range) { h_range.value = h; updateInput(h_range); }
                    }
                    var tabs = gradioApp().querySelectorAll('#tabs > div > button');
                    if (tabs && tabs.length > 0) {
                        for(var i=0; i<tabs.length; i++){
                            if(tabs[i].innerText.includes('img2img')) {
                                tabs[i].click();
                                break;
                            }
                        }
                    }
                    return [];
                }
                """,
                inputs=[hidden_gen_pos, hidden_gen_neg, hidden_gen_w, hidden_gen_h],
                outputs=None,
            )
            append_btn.click(
                fn=lambda entry: append_to_memo(load_config().get("memo_file", ""), entry),
                inputs=[gen_output],
                outputs=[append_status],
            )
            gen_save_btn.click(
                fn=save_gen_settings,
                inputs=[gen_confidence, gen_positive, gen_negative, gen_custom_dict, gen_cat_base, gen_cat_char, gen_cat_nsfw],
                outputs=[gen_save_status],
            )

        # ─── 使い方 ───
        with gr.Tab("📖 使い方"):
            gr.Markdown(
                "## メモファイルの書き方\n"
                "```\n"
                "[タイトル1]\n"
                "positive:\n"
                "(masterpiece:1.1), 1girl, portrait\n"
                "\n"
                "negative:\n"
                "lowres, blurry, artifact\n"
                "\n"
                "[city]\n"
                "positive:\n"
                "skyline, sunset, cinematic lighting\n"
                "\n"
                "negative:\n"
                "lowres, text, watermark\n"
                "```\n\n"
                "## ルール\n"
                "- `[名前]` = セクション開始\n"
                "- `positive:` の下 = ポジティブプロンプト\n"
                "- `negative:` の下 = ネガティブプロンプト\n"
                "- `positive:` / `negative:` 省略時は全て positive 扱い\n"
                "- `#` = コメント / 空行 = 無視\n\n"
                "## img2img での使い方\n"
                "1. **⚙️ 設定** タブで画像フォルダ・メモファイルを保存\n"
                "2. **img2img** タブで **🎲 Random Composer** → **有効化**\n"
                "3. **Generate** ボタンで自動実行\n\n"
                "## プロンプト自動生成\n"
                "1. **🏷️ プロンプト自動生成** タブで画像をアップロード\n"
                "2. セクション名を入力して **タグ解析＆生成**\n"
                "3. 結果を確認・編集して **メモファイルに追記**\n"
                "4. WD14 Tagger 拡張が必要です"
            )

    return [(tab, "Random Composer", "random_composer_tab")]


script_callbacks.on_ui_tabs(on_ui_tabs)
