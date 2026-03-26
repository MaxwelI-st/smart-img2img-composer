# -*- coding: utf-8 -*-
import gradio as gr
import os
from .i18n import t, _I18N
from .core import (
    load_config, save_config, save_all_settings, compose_prompt, append_to_memo, pick_random_assets,
    get_inventory_status, reset_inventory_global, reset_inventory_lora
)
from .utils import _clean_path, _polish_prompt, check_individual_health, validate_path
from .tagger import autogen_prompt
from .lora_mgr import load_lora_list, save_lora_list, append_lora_list, get_mgr_path
from .constants import (
    PROMPT_PROFILES, WILD_1_PATH, WILD_2_PATH, WILD_3_PATH,
    _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS
)

def preview_compose(img_f, memo, threshold, active_prof, smart_neg, smart_neg_mode, polish):
    selected, pos, neg, log, matched_name = compose_prompt(img_f, memo, threshold)
    if not selected: return selected, pos, neg, log

    # Apply Smart Negative
    if smart_neg:
        from .constants import PROMPT_PROFILES
        profile = PROMPT_PROFILES.get(active_prof, next(iter(PROMPT_PROFILES.values())))
        profile_neg = profile.get("neg", "")
        if smart_neg_mode == "overwrite":
            neg = profile_neg
        else:
            neg = (f"{neg}, " if neg else "") + profile_neg
    
    # Apply Polish
    if polish:
        pos = _polish_prompt(pos)
        neg = _polish_prompt(neg)

    return selected, pos, neg, log

def toggle_gen_cat(current_vals, all_keys):
    if len(current_vals) > 0:
        return gr.update(value=[])
    return gr.update(value=all_keys)

def toggle_all_gen_cats(base, char, nsfw):
    all_vals = list(base) + list(char) + list(nsfw)
    if all_vals:
        return gr.update(value=[]), gr.update(value=[]), gr.update(value=[])
    from .constants import _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS
    return gr.update(value=_CAT_BASE_KEYS), gr.update(value=_CAT_CHAR_KEYS), gr.update(value=_CAT_NSFW_KEYS)

def handle_save_preset(name, *args):
    if not name or name == "Default":
        return "❌ Invalid preset name", gr.update()
    config = load_config()
    presets = config.get("presets", {})
    # args match _common_save_inputs
    presets[name] = {
        "language": args[0], "image_folder": args[1], "memo_file": args[2],
        "match_threshold": args[3], "generation_count": args[4], "fallback_enabled": args[5],
        "auto_lora_enabled": args[6], "gen_confidence": args[7], "gen_positive": args[8],
        "gen_negative": args[9], "gen_custom_dict": args[10], "gen_categories": list(args[11]) + list(args[12]) + list(args[13]),
        "wildcard_1_path": args[14], "wildcard_2_path": args[15], "wildcard_3_path": args[16],
        "lora_offset": args[17], "output_sort_mode": args[18], "gen_mosaic_auto": args[19],
        "gen_mosaic_level": args[20], "gen_custom_dict_enabled": args[21],
        "auto_optimize_prompt": args[22], "custom_base_tags": args[23],
        "active_profile": args[24], "prompt_polish": args[25], "smart_negative": args[26],
        "auto_filename": args[27], "smart_negative_mode": args[28], "inventory_mode": args[29],
        "limit_base": args[30], "limit_char": args[31], "limit_nsfw": args[32], "gen_cat_mosaic": list(args[33]),
    }
    config["presets"] = presets
    save_config(config)
    return f"✅ Preset '{name}' saved!", gr.update(choices=["Default"] + list(presets.keys()), value=name)

def handle_delete_preset(name):
    if not name or name == "Default":
        return "❌ Cannot delete Default", gr.update()
    config = load_config()
    presets = config.get("presets", {})
    if name in presets:
        del presets[name]
        config["presets"] = presets
        save_config(config)
        return f"🗑️ Deleted '{name}'", gr.update(choices=["Default"] + list(presets.keys()), value="Default")
    return "❌ Not found", gr.update()

def handle_load_preset(name):
    from .constants import WILD_1_PATH, WILD_2_PATH, WILD_3_PATH
    if name == "Default":
        # 34 elements for _common_save_inputs
        vals = (
            "ja", "", "", 0.3, 1, True, True, 0.35, "(masterpiece:1.1), (best quality:1.0), ", 
            "lowres, blurry, artifact, bad anatomy, worst quality, low quality", "", 
            _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS, WILD_1_PATH, WILD_2_PATH, WILD_3_PATH, 
            0.0, t("sort_none"), False, t("mosaic_med"), False, False, "masterpiece, best quality, 1girl, solo", 
            "Standard / SDXL", False, True, False, "append", False, 10, 10, 15, ["mosaic_censoring", "bar_censor", "censored"]
        )
        health = check_individual_health("", "", WILD_1_PATH, WILD_2_PATH, WILD_3_PATH)
        return vals + health + (t("msg_load_success") if "msg_load_success" in _I18N else "Default Settings loaded",)
    
    config = load_config()
    p = config.get("presets", {}).get(name)
    if not p:
        # 34 common inputs + 5 health + 1 log
        return (gr.update(),) * 34 + (gr.update(),) * 5 + ("Not found",)
    
    # helper for gen_categories split
    gc = p.get("gen_categories", [])
    c_base = [c for c in gc if c in _CAT_BASE_KEYS]
    c_char = [c for c in gc if c in _CAT_CHAR_KEYS]
    c_nsfw = [c for c in gc if c in _CAT_NSFW_KEYS]

    vals = (
        p.get("language", "ja"), p.get("image_folder", ""), p.get("memo_file", ""),
        p.get("match_threshold", 0.3), p.get("generation_count", 1), p.get("fallback_enabled", True),
        p.get("auto_lora_enabled", True), p.get("gen_confidence", 0.35), p.get("gen_positive", ""),
        p.get("gen_negative", ""), p.get("gen_custom_dict", ""), c_base, c_char, c_nsfw,
        p.get("wildcard_1_path", WILD_1_PATH), p.get("wildcard_2_path", WILD_2_PATH), p.get("wildcard_3_path", WILD_3_PATH),
        p.get("lora_offset", 0.0), p.get("output_sort_mode", t("sort_none")), p.get("gen_mosaic_auto", False),
        p.get("gen_mosaic_level", t("mosaic_med")), p.get("gen_custom_dict_enabled", False),
        p.get("auto_optimize_prompt", False), p.get("custom_base_tags", ""),
        p.get("active_profile", "Standard / SDXL"), p.get("prompt_polish", False),
        p.get("smart_negative", True), p.get("auto_filename", False), p.get("smart_negative_mode", "append"), p.get("inventory_mode", False),
        p.get("limit_base", 10), p.get("limit_char", 10), p.get("limit_nsfw", 15), p.get("gen_cat_mosaic", ["mosaic_censoring", "bar_censor", "censored"])
    )
    health = check_individual_health(p.get("image_folder", ""), p.get("memo_file", ""), p.get("wildcard_1_path", WILD_1_PATH), p.get("wildcard_2_path", WILD_2_PATH), p.get("wildcard_3_path", WILD_3_PATH))
    return vals + health + (f"✅ {t('msg_loaded_preset')}: {name}",)

_img2img_comps = {}

def send_to_img2img(image, prompt):
    # This will be handled by JavaScript on the frontend side for better reliability
    # but we return the values here just in case or for future use.
    return image, prompt, gr.update(visible=True)

def on_ui_tabs():
    config = load_config()

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown(f"# 🎲 Smart Img2Img Composer v1.1.2 Stable\n{t('tab_header')}")

        def get_init_label(key, ptype, label_base):
            path = config.get(key, "")
            if not path: return label_base
            path = _clean_path(path)
            exists = False
            if ptype == "dir": exists = os.path.isdir(path)
            elif ptype == "file": exists = os.path.isfile(path)
            else: exists = os.path.exists(path)
            return f"✅ {label_base}" if exists else f"❌ {label_base}"

        with gr.Tabs() as tabs_root:
            # --- Tab 1: Settings & Preview ---
            with gr.Tab(t("tab_settings")):
                with gr.Row():
                    # Left: Settings
                    with gr.Column(scale=1):
                        gr.Markdown(t("h_settings"))
                        
                        # Presets (v1.1.0 compact style)
                        with gr.Group():
                            with gr.Row():
                                preset_dropdown = gr.Dropdown(
                                    label=t("preset_label"),
                                    choices=["Default"] + list(load_config().get("presets", {}).keys()),
                                    value="Default",
                                )
                            with gr.Row():
                                preset_name_input = gr.Textbox(placeholder=t("preset_ph"), label=None, scale=10)
                                save_preset_btn = gr.Button("💾", variant="secondary", scale=1, min_width=40)
                                delete_preset_btn = gr.Button("🗑️", variant="secondary", scale=1, min_width=40)

                        language_selector = gr.Radio(
                            label=t("language_label"),
                            choices=["ja", "en"],
                            value=lambda: load_config().get("language", "ja"),
                        )
                        image_folder = gr.Textbox(
                            label=get_init_label("image_folder", "dir", t("image_folder")),
                            placeholder=t("image_folder_ph"),
                            value=lambda: load_config().get("image_folder", ""),
                        )
                        memo_file = gr.Textbox(
                            label=get_init_label("memo_file", "file", t("memo_file")),
                            placeholder=t("memo_file_ph"),
                            value=lambda: load_config().get("memo_file", ""),
                        )
                        match_threshold = gr.Slider(
                            label=t("match_threshold"),
                            minimum=0.0, maximum=1.0, step=0.05,
                            value=lambda: load_config().get("match_threshold", 0.3),
                        )
                        generation_count = gr.Slider(
                            label=t("generation_count"),
                            minimum=1, maximum=100, step=1,
                            value=lambda: load_config().get("generation_count", 1),
                        )
                        lora_offset_slider = gr.Slider(
                            label=t("lora_offset"),
                            minimum=-1.0, maximum=1.0, step=0.05,
                            value=lambda: load_config().get("lora_offset", 0.0),
                        )
                        
                        with gr.Row():
                            auto_optimize_chk = gr.Checkbox(
                                label=t("auto_optimize_prompt"),
                                value=lambda: load_config().get("auto_optimize_prompt", False),
                            )
                            prompt_polish_chk = gr.Checkbox(
                                label=t("prompt_polish"),
                                value=lambda: load_config().get("prompt_polish", False),
                            )

                        active_profile_selector = gr.Dropdown(
                            label=t("active_profile"),
                            choices=list(PROMPT_PROFILES.keys()),
                            value=lambda: load_config().get("active_profile", "Standard / SDXL"),
                            info=t("active_profile_info"),
                        )
                        custom_base_tags_input = gr.Textbox(
                            label=t("custom_base_tags"),
                            placeholder="masterpiece, 1girl, solo...",
                            value=lambda: load_config().get("custom_base_tags", "masterpiece, best quality, 1girl, solo"),
                            info=t("custom_base_tags_info"),
                        )

                        with gr.Accordion(t("smart_negative"), open=False):
                            smart_negative_chk = gr.Checkbox(
                                label=t("smart_negative"),
                                value=lambda: load_config().get("smart_negative", True),
                            )
                            smart_negative_mode_selector = gr.Radio(
                                choices=[(t("sn_mode_add"), "append"), (t("sn_mode_overwrite"), "overwrite")],
                                label=t("smart_negative_mode"),
                                value=lambda: load_config().get("smart_negative_mode", "append"),
                            )

                        with gr.Row():
                            fallback_enabled = gr.Checkbox(
                                label=t("fallback_enabled"),
                                value=lambda: load_config().get("fallback_enabled", True),
                            )
                            auto_lora_enabled = gr.Checkbox(
                                label=t("auto_lora"),
                                value=lambda: load_config().get("auto_lora_enabled", True),
                            )

                        with gr.Accordion(t("output_settings"), open=False):
                            output_sort_selector = gr.Dropdown(
                                label=t("sort_mode"),
                                choices=[t("sort_none"), t("sort_preset"), t("sort_section"), t("sort_date")],
                                value=lambda: load_config().get("output_sort_mode", t("sort_none"))
                            )
                            auto_filename_chk = gr.Checkbox(
                                label=t("auto_filename"),
                                value=lambda: load_config().get("auto_filename", False),
                            )

                        with gr.Accordion(t("tab_settings_wildcards"), open=False):
                            w1_path = gr.Textbox(
                                label=get_init_label("wildcard_1_path", "any", t("wildcard_1")),
                                value=lambda: load_config().get("wildcard_1_path", WILD_1_PATH),
                            )
                            w2_path = gr.Textbox(
                                label=get_init_label("wildcard_2_path", "any", t("wildcard_2")),
                                value=lambda: load_config().get("wildcard_2_path", WILD_2_PATH),
                            )
                            w3_path = gr.Textbox(
                                label=get_init_label("wildcard_3_path", "any", t("wildcard_3")),
                                value=lambda: load_config().get("wildcard_3_path", WILD_3_PATH),
                            )

                        with gr.Row():
                            save_btn = gr.Button(t("btn_save"), variant="primary", scale=2)
                            reload_btn = gr.Button("🔄", variant="secondary", scale=0)
                            preview_btn = gr.Button(t("btn_preview"), variant="secondary")
                        
                        save_status = gr.Textbox(label=t("status"), interactive=False, max_lines=1)

                    # Right: Preview
                    with gr.Column(scale=1):
                        gr.Markdown(t("h_preview"))
                        with gr.Row():
                            auto_save_settings = gr.Checkbox(label="Auto Save Settings on Preview/Run", value=True, visible=False)
                        preview_image = gr.Image(label=t("selected_image"), type="filepath", interactive=False)
                        preview_positive = gr.Textbox(label=t("positive_prompt"), interactive=False, lines=4)
                        preview_negative = gr.Textbox(label=t("negative_prompt"), interactive=False, lines=2)
                        preview_log = gr.Textbox(label=t("log"), interactive=False, lines=6)

            # --- Tab 2: Auto-Prompt Gen ---
            with gr.Tab(t("tab_prompt_gen")):
                gr.Markdown(t("prompt_gen_desc"))
                with gr.Row():
                    with gr.Column(scale=2):
                        gen_image = gr.Image(label=t("target_image"), type="pil", interactive=True)
                        gen_section = gr.Textbox(label=t("section_name"), placeholder=t("section_ph"))
                        
                        gr.Markdown(t("h_categories"))
                        btn_all_cats_toggle = gr.Button(t("btn_toggle_cat"), variant="primary", size="sm")
                        
                        with gr.Accordion(t("cat_base"), open=True):
                            btn_base_toggle = gr.Button(t("btn_toggle_cat"), variant="secondary", size="sm")
                            gen_cat_base = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _CAT_BASE_KEYS],
                                value=lambda: [c for c in (load_config().get("gen_categories") or _CAT_BASE_KEYS) if c in _CAT_BASE_KEYS],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_char"), open=False):
                            btn_char_toggle = gr.Button(t("btn_toggle_cat"), variant="secondary", size="sm")
                            gen_cat_char = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _CAT_CHAR_KEYS],
                                value=lambda: [c for c in (load_config().get("gen_categories") or _CAT_CHAR_KEYS) if c in _CAT_CHAR_KEYS],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_nsfw"), open=False):
                            btn_nsfw_toggle = gr.Button(t("btn_toggle_cat"), variant="secondary", size="sm")
                            gen_cat_nsfw = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _CAT_NSFW_KEYS],
                                value=lambda: [c for c in (load_config().get("gen_categories") or _CAT_NSFW_KEYS) if c in _CAT_NSFW_KEYS],
                                show_label=False
                            )
                        

                        with gr.Accordion(t("h_pickup_limits"), open=True):
                            limit_base = gr.Slider(label=t("limit_base_label"), minimum=1, maximum=50, step=1, value=lambda: load_config().get("limit_base", 10))
                            limit_char = gr.Slider(label=t("limit_char_label"), minimum=1, maximum=50, step=1, value=lambda: load_config().get("limit_char", 10))
                            limit_nsfw = gr.Slider(label=t("limit_nsfw_label"), minimum=1, maximum=50, step=1, value=lambda: load_config().get("limit_nsfw", 15))

                        gen_confidence = gr.Slider(label=t("confidence"), minimum=0.1, maximum=0.9, step=0.05, value=lambda: load_config().get("gen_confidence", 0.35))
                        gen_positive = gr.Textbox(label=t("default_positive"), value=lambda: load_config().get("gen_positive", "(masterpiece:1.1), (best quality:1.0), "), lines=2)
                        gen_negative = gr.Textbox(label=t("default_negative"), value=lambda: load_config().get("gen_negative", "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts"), lines=2)
                        
                        with gr.Accordion(t("custom_dict"), open=False):
                            gen_custom_dict_enabled = gr.Checkbox(label=t("gen_custom_dict_enabled"), value=lambda: load_config().get("gen_custom_dict_enabled", False))
                            gen_custom_dict = gr.Textbox(label=None, lines=3, show_label=False, value=lambda: load_config().get("gen_custom_dict", ""))
                        
                        with gr.Accordion(t("h_mosaic_settings"), open=False):
                            with gr.Row():
                                gen_mosaic_auto = gr.Checkbox(label=t("gen_mosaic_auto"), value=lambda: load_config().get("gen_mosaic_auto", False))
                                gen_mosaic_level = gr.Radio(choices=[t("mosaic_low"), t("mosaic_med"), t("mosaic_high")], label=t("gen_mosaic_level"), value=lambda: load_config().get("gen_mosaic_level", t("mosaic_med")))
                            
                            gr.Markdown(t("cat_nsfw_mosaic"))
                            gen_cat_mosaic = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in ["mosaic_censoring", "bar_censor", "censored", "uncensored", "detailed_mosaic"]],
                                value=lambda: load_config().get("gen_cat_mosaic", ["mosaic_censoring", "bar_censor", "censored"]),
                                show_label=False
                            )

                        with gr.Row():
                            gen_btn = gr.Button(t("btn_gen_tags"), variant="primary")
                            append_btn = gr.Button(t("btn_append_memo"), variant="secondary")
                            gen_save_btn = gr.Button(t("btn_save_settings"), variant="secondary")
                    
                    with gr.Column(scale=1):
                        with gr.Row():
                            send_img2img_btn = gr.Button(t("btn_send_img2img"), variant="primary")
                        
                        gen_output = gr.Textbox(label=t("generated_entry"), interactive=True, lines=8)
                        gen_tags_only = gr.Textbox(label=t("gen_tags_only"), interactive=True, lines=4, info=t("gen_tags_only_info"))
                        
                        gen_log = gr.Textbox(label=t("analysis_log"), interactive=False, lines=6)
                        append_status = gr.Textbox(label=t("append_status"), interactive=False, max_lines=1)

            # --- Tab 3: LoRA Manager ---
            with gr.Tab(t("tab_lora_manager")):
                gr.Markdown(t("lora_manager_desc"))
                with gr.Row():
                    lora_mgr_type = gr.Dropdown(
                        label=t("lora_type"),
                        choices=[t("lora_type_char"), t("lora_type_sit"), t("wildcard_1"), t("wildcard_2"), t("wildcard_3")],
                        value=t("lora_type_char")
                    )
                with gr.Row():
                    lora_mgr_input = gr.Textbox(label=t("lora_input_label"), lines=2)
                    append_lora_btn = gr.Button(t("btn_append_lora"), variant="primary")
                
                lora_mgr_content = gr.Textbox(label=t("lora_list_label"), lines=15, value=lambda: load_lora_list(t("lora_type_char")))
                
                with gr.Row():
                    save_lora_mgr_btn = gr.Button(t("btn_save_lora_list"), variant="primary")
                    lora_mgr_msg = gr.Markdown("")

            # --- Tab 4: Inventory Logic ---
            with gr.Tab(t("tab_inventory")):
                gr.Markdown(t("inventory_desc"))
                inventory_mode_chk = gr.Checkbox(
                    label=t("inventory_mode"),
                    value=lambda: load_config().get("inventory_mode", False),
                    info=t("inventory_mode_info")
                )
                with gr.Row():
                    btn_check_stock = gr.Button(t("btn_check_stock"), variant="secondary")
                    btn_lora_reset = gr.Button(t("btn_lora_reset"), variant="secondary")
                    btn_global_reset = gr.Button(t("btn_global_reset"), variant="secondary")
                
                inventory_status_box = gr.Textbox(label=t("inventory_status_label"), lines=15, interactive=False)

            # --- Tab 5: Usage ---
            with gr.Tab(t("tab_usage")):
                gr.Markdown(t("usage_md"))

        # --- Event Handlers ---

        # Common Save Inputs
        _common_save_inputs = [
            language_selector, image_folder, memo_file, match_threshold, generation_count, fallback_enabled, auto_lora_enabled,
            gen_confidence, gen_positive, gen_negative, gen_custom_dict, gen_cat_base, gen_cat_char, gen_cat_nsfw,
            w1_path, w2_path, w3_path, lora_offset_slider, output_sort_selector,
            gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled,
            auto_optimize_chk, custom_base_tags_input, active_profile_selector,
            prompt_polish_chk, smart_negative_chk, auto_filename_chk, smart_negative_mode_selector,
            inventory_mode_chk, limit_base, limit_char, limit_nsfw, gen_cat_mosaic
        ]
        
        _health_outputs = [image_folder, memo_file, w1_path, w2_path, w3_path]

        def _do_save(*args):
            msg = save_all_settings(*args)
            health = check_individual_health(args[1], args[2], args[14], args[15], args[16])
            return (msg,) + health

        save_btn.click(fn=_do_save, inputs=_common_save_inputs, outputs=[save_status] + _health_outputs)
        gen_save_btn.click(fn=_do_save, inputs=_common_save_inputs, outputs=[save_status] + _health_outputs)

        preview_btn.click(
            fn=preview_compose,
            inputs=[image_folder, memo_file, match_threshold, active_profile_selector, smart_negative_chk, smart_negative_mode_selector, prompt_polish_chk],
            outputs=[preview_image, preview_positive, preview_negative, preview_log]
        )
        reload_btn.click(
            fn=preview_compose,
            inputs=[image_folder, memo_file, match_threshold, active_profile_selector, smart_negative_chk, smart_negative_mode_selector, prompt_polish_chk],
            outputs=[preview_image, preview_positive, preview_negative, preview_log]
        )

        preset_dropdown.change(fn=handle_load_preset, inputs=[preset_dropdown], outputs=_common_save_inputs + _health_outputs + [save_status])
        save_preset_btn.click(fn=handle_save_preset, inputs=[preset_name_input] + _common_save_inputs, outputs=[save_status, preset_dropdown])
        delete_preset_btn.click(fn=handle_delete_preset, inputs=[preset_dropdown], outputs=[save_status, preset_dropdown])

        # Tagger
        gen_btn.click(
            fn=autogen_prompt,
            inputs=[gen_image, gen_section, gen_confidence, gen_positive, gen_negative, gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_custom_dict, gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled, limit_base, limit_char, limit_nsfw, gen_cat_mosaic],
            outputs=[gen_output, gen_log, gen_tags_only]
        )
        append_btn.click(
            fn=lambda entry: append_to_memo(load_config().get("memo_file", ""), entry),
            inputs=[gen_output],
            outputs=[append_status]
        )

        send_img2img_btn.click(
            fn=None,
            _js="sc_send_to_img2img",
            inputs=[gen_image, gen_tags_only],
            outputs=[]
        )

        # LoRA Manager
        lora_mgr_type.change(fn=load_lora_list, inputs=[lora_mgr_type], outputs=[lora_mgr_content])
        save_lora_mgr_btn.click(fn=save_lora_list, inputs=[lora_mgr_type, lora_mgr_content], outputs=[lora_mgr_msg, lora_mgr_content])
        append_lora_btn.click(fn=append_lora_list, inputs=[lora_mgr_type, lora_mgr_input], outputs=[lora_mgr_content, lora_mgr_input])

        # Inventory Manager
        btn_check_stock.click(fn=get_inventory_status, outputs=[inventory_status_box])
        btn_lora_reset.click(fn=reset_inventory_lora, outputs=[inventory_status_box])
        btn_global_reset.click(fn=reset_inventory_global, outputs=[inventory_status_box])

        # Category Toggle Buttons
        btn_all_cats_toggle.click(
            fn=toggle_all_gen_cats,
            inputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw],
            outputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw]
        )
        btn_base_toggle.click(fn=lambda v: toggle_gen_cat(v, _CAT_BASE_KEYS), inputs=[gen_cat_base], outputs=[gen_cat_base])
        btn_char_toggle.click(fn=lambda v: toggle_gen_cat(v, _CAT_CHAR_KEYS), inputs=[gen_cat_char], outputs=[gen_cat_char])
        btn_nsfw_toggle.click(fn=lambda v: toggle_gen_cat(v, _CAT_NSFW_KEYS), inputs=[gen_cat_nsfw], outputs=[gen_cat_nsfw])

        def _init_health():
            c = load_config()
            return check_individual_health(
                c.get("image_folder", ""),
                c.get("memo_file", ""),
                c.get("wildcard_1_path", WILD_1_PATH),
                c.get("wildcard_2_path", WILD_2_PATH),
                c.get("wildcard_3_path", WILD_3_PATH)
            )

        tab.load(fn=_init_health, outputs=_health_outputs)

        # Real-time path health check
        image_folder.change(fn=lambda p: validate_path(p, "image_folder"), inputs=[image_folder], outputs=[image_folder])
        memo_file.change(fn=lambda p: validate_path(p, "memo_file"), inputs=[memo_file], outputs=[memo_file])
        w1_path.change(fn=lambda p: validate_path(p, "wildcard_1"), inputs=[w1_path], outputs=[w1_path])
        w2_path.change(fn=lambda p: validate_path(p, "wildcard_2"), inputs=[w2_path], outputs=[w2_path])
        w3_path.change(fn=lambda p: validate_path(p, "wildcard_3"), inputs=[w3_path], outputs=[w3_path])

    return [(tab, "Smart Img2Img Composer", "smart_composer_tabs_root")]
