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
    "smart_negative": True,
    "smart_negative_mode": "append",
    "inventory_mode": False,
    "gen_mosaic_auto": False,
    "gen_mosaic_level": "Mosaic Med",
    "gen_custom_dict_enabled": False,
    "limit_base": 10,
    "limit_char": 10,
    "limit_nsfw": 15,
}

PROMPT_PROFILES = {
    "Standard / SDXL": {
        "order": ["quality", "composition", "subject", "outfit", "background", "nsfw", "lora"],
        "ref": "masterpiece, best quality, 1girl, solo",
        "neg": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry"
    },
    "Pony V6": {
        "order": ["score", "rating", "subject", "background", "nsfw", "lora"],
        "ref": "score_9, score_8_up, score_7_up, rating_explicit, rating_questionable",
        "neg": "score_6, score_5, score_4, (worst quality:1.2), (low quality:1.2), (normal quality:1.2), lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, jpeg artifacts, signature, watermark, username, blurry"
    },
    "Illustrious-XL": {
        "order": ["quality", "rating", "subject", "scene", "lora"],
        "ref": "masterpiece, best quality, 1girl, solo, rating_explicit",
        "neg": "(low quality, worst quality:1.4), (bad anatomy, bad hands:1.2), text, signature, watermark, username, lowres, blurry, error, cropped, jpeg artifacts"
    },
    "Animagine XL V3.1": {
        "order": ["quality", "subject", "action", "outfit", "background", "style", "lora"],
        "ref": "score_9, score_8_up, 1girl",
        "neg": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry"
    },
    "Juggernaut XL / Realistic": {
        "order": ["quality_photo", "subject", "action", "environment", "lighting", "lora"],
        "ref": "photograph, portrait, RAW photo",
        "neg": "(worst quality, low quality, normal quality:1.4), lowres, blurry, bad anatomy, bad hands, text, error, cropped, jpeg artifacts, signature, watermark, username"
    },
    "SD 1.5 / Realistic Vision": {
        "order": ["medium", "subject", "detail", "environment", "mood", "lora"],
        "ref": "8k, UHD, RAW photo, masterpiece",
        "neg": "(worst quality, low quality:1.4), (bad anatomy, bad hands:1.2), lowres, blurry, text, signature, watermark"
    },
    "NoobAI-XL": {
        "order": ["aesthetic", "style", "subject", "outfit", "scene", "lora"],
        "ref": "masterpiece, (best quality:1.2), 1girl",
        "neg": "(low quality, worst quality:1.2), very displeasing, (bad anatomy:1.2), (bad hands:1.2), text, signature, watermark, username, lowres, blurry, error, cropped, jpeg artifacts"
    },
    "Hyper-SD / Lightning": {
        "order": ["quality", "subject", "detail", "lighting", "lora"],
        "ref": "masterpiece, (high quality:1.2)",
        "neg": "lowres, worst quality, low quality, bad anatomy, bad hands, text, error, cropped, jpeg artifacts, signature, watermark, username, blurry"
    }
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# LoRA テンプレート
LORA_CHAR_TEMPLATE = """\
# LoRA キャラクターリスト（1行1エントリ）
# 書式: <lora:LoRA名:強度>  または  任意のプロンプト文字列
# 例:
# <lora:my_character_v2:0.8>, 1girl, blue hair
# <lora:another_char:0.7>, 1boy, white hair
"""

LORA_SIT_TEMPLATE = """\
# LoRA シチュエーションリスト（1行1エントリ）
# 書式: <lora:LoRA名:強度>  または  任意のプロンプト文字列
# 例:
# <lora:outdoor_scene:0.6>, park, sunlight
# <lora:indoor_cozy:0.7>, living room, warm lighting
"""

# タグカテゴリのキー定義
_CAT_BASE_KEYS = ["cat_composition", "cat_pose", "cat_background", "cat_nature", "cat_lighting", "cat_atmosphere", "cat_meta"]
_CAT_CHAR_KEYS = ["cat_char_base", "cat_char_hair", "cat_char_eyes", "cat_char_face", "cat_char_clothes", "cat_char_male"]
_CAT_NSFW_KEYS = ["cat_nsfw_action", "cat_nsfw_creature", "cat_nsfw_item", "cat_nsfw_focus", "cat_nsfw_fluids", "cat_nsfw_fetish", "cat_nsfw_clothes_mess", "cat_nsfw_genitals"]

# 詳細なタグ定義 (v1.0.3 より移植)
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
    "cat_nsfw_mosaic": ["mosaic_censoring", "bar_censor", "censored", "uncensored", "detailed_mosaic"],
    "cat_nsfw_scenario": ["impregnation", "fertilization", "fertility", "ovulation", "gestation", "pregnancy", "breast_expansion", "stomach_expansion", "body_writing", "double_penetration", "triple_penetration", "gangbang", "orgy", "threesome", "foursome", "abandonment", "neglect", "ear_licking", "ear_caressing", "lesbian", "lesbianism", "dyke", "butch", "femme"],
}
