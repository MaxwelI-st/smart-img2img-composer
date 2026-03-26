# -*- coding: utf-8 -*-
import os
import re
import sys
import traceback
try:
    import yaml
except ImportError:
    yaml = None

from .i18n import t
from .constants import BASE_DIR, _TAG_CATEGORIES, _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS

_compiled_cat_patterns = {}

def _get_easy_prompt_tags():
    if yaml is None:
        return set()

    tags = set()
    extensions_root = os.path.dirname(BASE_DIR)
    _CANDIDATES = [
        ("sdweb-easy-prompt-selector", "tags"),
        ("easy-prompt-selector",       "tags"),
        ("a1111-sd-webui-tagcomplete", "tags"),
        ("sd-webui-tagcomplete",       "tags"),
    ]

    installed = os.listdir(extensions_root) if os.path.isdir(extensions_root) else []
    found_dirs = []
    for ext_name, sub in _CANDIDATES:
        candidate = os.path.join(extensions_root, ext_name, sub)
        if os.path.isdir(candidate):
            found_dirs.append(candidate)
        for name in installed:
            if name.startswith(ext_name):
                c2 = os.path.join(extensions_root, name, sub)
                if os.path.isdir(c2) and c2 not in found_dirs:
                    found_dirs.append(c2)

    def _extract(d):
        for v in d.values():
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and not item.startswith(("<lora:", "__")):
                        tags.add(item.strip().lower().replace(" ", "_"))
            elif isinstance(v, dict):
                _extract(v)

    for d in found_dirs:
        try:
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith((".yml", ".yaml")):
                        with open(os.path.join(root, f), "r", encoding="utf-8") as file:
                            data = yaml.safe_load(file)
                        if isinstance(data, dict):
                            _extract(data)
        except Exception:
            continue
    return tags

def _filter_tags(tags: dict, confidence: float, selected_cats=None, protect_easy=True, limits=None):
    global _compiled_cat_patterns
    if not selected_cats:
        selected_cats = list(_TAG_CATEGORIES.keys())

    filtered = {}
    easy_tags = _get_easy_prompt_tags() if protect_easy else set()
    
    cache_key = tuple(sorted(selected_cats))
    if cache_key in _compiled_cat_patterns:
        allowed_tags, allowed_patterns = _compiled_cat_patterns[cache_key]
    else:
        allowed_tags = set()
        allowed_patterns = []
        for cat in selected_cats:
            if cat in _TAG_CATEGORIES:
                for item in _TAG_CATEGORIES[cat]:
                    if item.startswith("re:"):
                        allowed_patterns.append(re.compile(item[3:]))
                    else:
                        allowed_tags.add(item)
        _compiled_cat_patterns[cache_key] = (allowed_tags, allowed_patterns)

    # Dynamic limits based on groups
    if limits is None:
        limits = {"base": 10, "char": 10, "nsfw": 15}

    cat_matches = {cat: [] for cat in selected_cats}
    easy_protected = {}

    for tag, score in tags.items():
        if score < confidence: continue
        tag_clean = tag.strip().lower().replace(" ", "_")
        
        if protect_easy and tag_clean in easy_tags:
            easy_protected[tag_clean] = score
            continue

        matched_cat = None
        if tag_clean in allowed_tags:
            for cat in selected_cats:
                if cat in _TAG_CATEGORIES and tag_clean in _TAG_CATEGORIES[cat]:
                    matched_cat = cat; break
        else:
            for cat in selected_cats:
                if cat in _TAG_CATEGORIES:
                    for item in _TAG_CATEGORIES[cat]:
                        if item.startswith("re:"):
                            p = re.compile(item[3:])
                            if p.search(tag_clean):
                                matched_cat = cat; break
                    if matched_cat: break

        if matched_cat:
            cat_matches[matched_cat].append((tag_clean, score))

    for cat in selected_cats:
        matches = cat_matches.get(cat, [])
        # Determine limit based on group
        limit = 999
        if cat in _CAT_BASE_KEYS:
            limit = limits.get("base", 10)
        elif cat in _CAT_CHAR_KEYS:
            limit = limits.get("char", 10)
        elif cat in _CAT_NSFW_KEYS:
            limit = limits.get("nsfw", 15)
        
        sorted_m = sorted(matches, key=lambda x: x[1], reverse=True)
        for t_c, s in sorted_m[:limit]:
            if t_c not in filtered:
                filtered[t_c] = s

    filtered.update(easy_protected)
    return filtered

def _find_tagger():
    try:
        from tagger import interrogator as tagger_mod
        return tagger_mod, None
    except ImportError:
        pass
    try:
        ext_dir = os.path.dirname(BASE_DIR)
        if os.path.isdir(ext_dir):
            for d in os.listdir(ext_dir):
                if "tagger" in d.lower() or "wd14" in d.lower():
                    tp = os.path.join(ext_dir, d)
                    if tp not in sys.path: sys.path.insert(0, tp)
            from tagger import interrogator as tagger_mod
            return tagger_mod, None
    except Exception:
        pass
    return None, t("msg_tagger_not_found")

def _interrogate_image(image, confidence: float, selected_cats=None, limits=None):
    tagger_mod, err = _find_tagger()
    if tagger_mod is None: return {}, {}, err
    try:
        all_tags = {}
        success = False
        try:
            from tagger import utils as tu
            if hasattr(tu, "interrogators") and tu.interrogators:
                obj = tu.interrogators.get("wd14-convnext.v2") or list(tu.interrogators.values())[0]
                res = obj.interrogate(image)
                if isinstance(res, tuple) and len(res) >= 2:
                    all_tags = res[1] if isinstance(res[1], dict) else {}
                    success = True
                elif isinstance(res, dict):
                    all_tags = res; success = True
        except Exception: pass

        if not success:
            try:
                import tagger.api as ta
                res = ta.interrogate(image)
                if isinstance(res, dict):
                    all_tags = res.get("caption") or res
                    success = True
            except Exception: pass

        if not success: return {}, {}, t("msg_tagger_not_found")
        return _filter_tags(all_tags, confidence, selected_cats, limits=limits), all_tags, None
    except Exception as e:
        return {}, {}, f"{t('msg_tag_fetch_err')} {e}"

def autogen_prompt(image, section_name, confidence, pos, neg, cat_base, cat_char, cat_nsfw, custom_dict, gen_mosaic=False, mosaic_level="Mosaic Med", custom_enabled=True, limit_base=10, limit_char=10, limit_nsfw=15, cat_mosaic=None):
    from .utils import get_stable_dimensions
    cats = list(cat_base) + list(cat_char) + list(cat_nsfw)
    if cat_mosaic:
        cats += list(cat_mosaic)
    if image is None: return "", t("msg_no_upload_err"), "", "", "512", "512", ""
    if not section_name or not section_name.strip(): return "", t("msg_no_section_err"), "", "", "512", "512", ""

    try:
        limits = {"base": limit_base, "char": limit_char, "nsfw": limit_nsfw}
        filtered, all_tags, err = _interrogate_image(image, confidence, cats, limits=limits)
        if err: return "", err, "", "", "512", "512", ""

        log = [t("log_all_tags").format(count=len(all_tags)), t("log_filtered_tags").format(count=len(filtered))]
        
        mosaic_extra = []
        if gen_mosaic:
            l_val = str(mosaic_level)
            if any(tag in all_tags for tag in ["mosaic_censoring", "censored", "bar_censor"]):
                if "Low" in l_val or "薄" in l_val:
                    mosaic_extra = ["(mosaic_censoring:0.8)", "(light_mosaic:1.1)"]
                elif "High" in l_val or "厚" in l_val:
                    mosaic_extra = ["(mosaic_censoring:1.4)", "(thick_mosaic:1.2)"]
                else:
                    mosaic_extra = ["(mosaic_censoring:1.1)", "(detailed_mosaic:1.0)"]
                log.append(f"🧱 Mosaic Auto-Prompt added ({mosaic_level})")

        matched_custom = []
        if custom_enabled and custom_dict:
            for line in custom_dict.splitlines():
                if not line or line.startswith("#"): continue
                sep = "=>" if "=>" in line else "->" if "->" in line else ">" if ">" in line else None
                if not sep: continue
                l, r = line.split(sep, 1)
                conds = [ct.strip().lower().replace(" ", "_") for ct in l.split(",")]
                if all(c in all_tags for c in conds):
                    matched_custom.append(r.strip())
                    log.append(t("log_custom_match").format(cond=l, prompt=r.strip()))

        gen_tags = ", ".join(tag.replace("_", " ") for tag in filtered.keys())
        parts = [pos.strip()] if pos else []
        parts.extend(mosaic_extra)
        parts.extend(matched_custom)
        if gen_tags: parts.append(gen_tags)
        
        final_pos = ", ".join(parts)
        entry = f"[{section_name.strip()}]\npositive:\n{final_pos}\n\nnegative:\n{neg}\n"
        return entry, "\n".join(log), ", ".join(filtered.keys())
    except Exception as e:
        return "", f"❌ Error: {e}", ""
