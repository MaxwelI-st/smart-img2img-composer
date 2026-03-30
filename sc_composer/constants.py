# -*- coding: utf-8 -*-
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(BASE_DIR, "config.json")
LORA_CHAR_PATH = os.path.join(BASE_DIR, "lora_char.txt")
LORA_SIT_PATH = os.path.join(BASE_DIR, "lora_sit.txt")
WILD_1_PATH = os.path.join(BASE_DIR, "wildcard_1.txt")
WILD_2_PATH = os.path.join(BASE_DIR, "wildcard_2.txt")
WILD_3_PATH = os.path.join(BASE_DIR, "wildcard_3.txt")
INVENTORY_PATH = os.path.join(BASE_DIR, "inventory.json")

DEFAULT_CONFIG = {
    "language": "ja",
    "image_folder": "",
    "memo_file": "",
    "match_threshold": 0.3,
    "generation_count": 1,
    "gen_conf_base": 0.35,
    "gen_conf_char": 0.35,
    "gen_conf_nsfw": 0.35,
    "gen_confidence": 0.35,
    "gen_positive": "(masterpiece:1.1), (best quality:1.0), ",
    "gen_negative": "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts",
    "gen_custom_dict": (
        "night, city > cyberpunk cityscape, neon lights, cinematic lighting, rain reflections, highly detailed\n"
        "sunset, skyline > golden hour lighting, dramatic sky colors, atmospheric perspective\n"
        "indoor, room > detailed background, interior design"
    ),
    "wildcard_1_path": WILD_1_PATH,
    "wildcard_2_path": WILD_2_PATH,
    "wildcard_3_path": WILD_3_PATH,
    "fallback_enabled": True,
    "auto_lora_enabled": True,
    "lora_offset": 0.0,
    "output_sort_mode": "None",
    "presets": {},
    "gen_categories": None,
    "custom_base_tags": "masterpiece, best quality, 1girl, solo",
    "auto_optimize_prompt": False,
    "active_profile": "Standard / SDXL",
    "auto_filename": False,
    "prompt_polish": False,
    "smart_negative": False,
    "smart_negative_mode": "append",
    "inventory_mode": False,
    "gen_mosaic_auto": False,
    "gen_mosaic_level": "Mosaic Med",
    "gen_custom_dict_enabled": False,
    "limit_base": 10,
    "limit_char": 10,
    "limit_nsfw": 15,
    "debug": False,
}

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"]

# ▼ 詳細なタグ定義 (AIによる機能性維持のための温存)
_TAG_CATEGORIES = {
    "cat_composition": ["re:.*_view", "re:.*_shot", "re:.*_perspective", "portrait", "upper_body", "lower_body", "full_body", "wide_shot", "from_above", "from_below", "from_side", "from_behind"],
    "cat_pose": ["re:.*_standing", "re:.*_sitting", "re:.*_lying", "re:.*_leaning", "re:.*_kneeling", "arm_up", "arms_behind_back", "arms_behind_head", "hand_on_hip", "hand_to_mouth", "leg_up"],
    "cat_background": ["re:.*_background", "indoor", "outdoor", "room", "bedroom", "bathroom", "kitchen", "classroom", "forest", "beach", "cityscape", "ocean", "street", "park"],
    "cat_nature": ["re:sky", "re:cloud", "re:sun", "re:rain", "re:snow", "flower", "tree", "grass", "mountain", "river", "sea", "forest"],
    "cat_lighting": ["re:.*_lighting", "sunlight", "moonlight", "backlighting", "rim_lighting", "soft_lighting", "cinematic_lighting", "neon_lights"],
    "cat_atmosphere": ["moody", "calm", "vibrant", "dark", "light", "colorful", "monochrome", "sepia"],
    "cat_meta": ["masterpiece", "best_quality", "highres", "absurdres", "quality", "solo", "1girl", "1boy"],
    "cat_char_base": ["re:skin", "re:body", "re:age", "small_breasts", "medium_breasts", "large_breasts", "huge_breasts", "flat_chest", "curvy", "slim", "muscular"],
    "cat_char_hair": ["re:.*_hair", "short_hair", "medium_hair", "long_hair", "very_long_hair", "ponytail", "twintails", "braid", "bob_cut", "blunt_bangs"],
    "cat_char_eyes": ["re:.*_eyes", "blue_eyes", "red_eyes", "green_eyes", "yellow_eyes", "brown_eyes", "purple_eyes", "pink_eyes", "heterochromia"],
    "cat_char_face": ["re:.*_smile", "re:expression", "blush", "open_mouth", "closed_eyes", "tsundere", "kuudere", "yandere"],
    "cat_char_clothes": ["re:.*_wear", "re:.*_outfit", "dress", "skirt", "shirt", "pants", "shorts", "swimsuit", "bikini", "uniform", "school_uniform", "maid_outfit"],
    "cat_char_male": ["1boy", "male_focus", "guy", "man", "muscular_male", "beard", "abs"],
    "cat_nsfw_action": ["re:.*_sex", "re:.*_position", "blowjob", "cunnilingus", "handjob", "footjob", "paizuri", "penetration", "vaginal", "anal", "group_sex", "irrumatio", "fellatio", "oral_sex", "deep_throat", "mutual_masturbation", "public_sex", "outdoor_sex", "public_intimacy", "al_fresco", "shibari", "spanking", "flogging", "impact_play", "sensory_play", "role_play"],
    "cat_nsfw_creature": ["tentacles", "monster", "demon", "orc", "goblin", "beast", "creature", "tentacle_play", "monster_sex", "tentacle_sex"],
    "cat_nsfw_item": ["vibrator", "dildo", "sex_toy", "handcuffs", "blindfold", "gag", "rope", "bondage", "milking_machine", "breast_pump", "lactation", "sybian", "automaton", "mechanical_arm", "bondage_machine", "fucking_machine", "spanking_machine", "whip", "collar", "chain", "harness", "chastity_belt", "straitjacket", "leash", "muzzle", "bit_gag", "ball_gag"],
    "cat_nsfw_focus": ["re:.*_focus", "ass_focus", "breast_focus", "pussy_focus", "penis_focus", "crotch_focus", "feet_focus", "armpit_focus", "navel_focus", "thigh_focus"],
    "cat_nsfw_fluids": ["cum", "cum_on_body", "cum_on_face", "cum_in_pussy", "cum_in_mouth", "precum", "sweat", "saliva", "urine", "body_fluids", "cum_all_over", "squirt", "splash", "gush", "spurt"],
    "cat_nsfw_fetish": ["re:.*_fingering", "re:.*_fisting", "ahegao", "tongue_out", "eyes_rolled_back", "drool", "foot_fetish", "armpit_fetish", "toe_sucking", "foot_worship", "sole_licking", "foot_trample", "pedal_play", "corruption", "fall", "descent", "decay", "malevolence", "depravity", "sinister", "nefarious", "shame", "embarrassment", "humiliation", "degradation", "dishonor"],
    "cat_nsfw_clothes_mess": ["re:.*_lift", "re:.*_pull", "re:.*_removal", "undressing", "clotheless", "naked", "topless", "bottomless", "exhibitionism", "public_exposure", "flashing", "undressing_self", "clothing_around_ankles"],
    "cat_nsfw_genitals": ["pussy", "penis", "testicles", "anus", "nipples", "erection", "clitoris", "genitals", "labia", "scrotum", "large_clitoris", "huge_penis"],
}

_CAT_BASE_KEYS = ["cat_composition", "cat_pose", "cat_background", "cat_nature", "cat_lighting", "cat_atmosphere", "cat_meta"]
_CAT_CHAR_KEYS = ["cat_char_base", "cat_char_hair", "cat_char_eyes", "cat_char_face", "cat_char_clothes", "cat_char_male"]
_CAT_NSFW_KEYS = ["cat_nsfw_action", "cat_nsfw_creature", "cat_nsfw_item", "cat_nsfw_focus", "cat_nsfw_fluids", "cat_nsfw_fetish", "cat_nsfw_clothes_mess", "cat_nsfw_genitals"]

LORA_CHAR_TEMPLATE = """# Character LoRA or Tags
# Usage:
# <lora:name:1.0>
# <lora:name:0.8>, character_tag, series_tag
#
# List your assets below:
"""

LORA_SIT_TEMPLATE = """# Situation LoRA or Tags
# Usage:
# <lora:name:1.0>
# <lora:name:0.8>, sitting, indoors
#
# List your assets below:
"""

# ▼ 復元されたプロファイル本体
PROMPT_PROFILES = {
    "Standard / SDXL": {
        "order": ["subject", "environment", "lighting", "camera", "style"],
        "ref": "(masterpiece:1.2), best quality, highres, highly detailed",
        "neg": "worst quality, low quality, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, ugly, watermark, signature"
    },
    "Pony Diffusion V6 XL": {
        "order": ["score", "rating", "subject", "environment", "lighting", "camera", "style"],
        "ref": "score_9, score_8_up, score_7_up, score_6_up, source_anime, masterpiece, best quality",
        "neg": "score_4, score_5, score_6, source_pony, source_furry, source_cartoon, 3d"
    },
    "Illustrious XL": {
        "order": ["quality", "rating", "subject", "environment", "lighting", "camera", "style"],
        "ref": "masterpiece, best quality, very aesthetic, absurdres, highres, extremely detailed",
        "neg": "worst quality, bad quality, low quality, displeasing, very displeasing, chromatic aberration, abstract"
    },
    "Animagine XL 3.x": {
        "order": ["quality", "rating", "subject", "environment", "lighting", "camera", "style"],
        "ref": "masterpiece, best quality, very aesthetic, absurdres, highres",
        "neg": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry"
    },
    "SD 1.5 (Anime / Danbooru)": {
        "order": ["quality", "subject", "clothing", "environment", "lighting", "camera", "style"],
        "ref": "masterpiece, best quality, ultra-detailed, highres, illustration",
        "neg": "worst quality, low quality, bad anatomy, bad hands, missing fingers, extra digit, fewer digits, ugly, watermark, signature"
    }
}
