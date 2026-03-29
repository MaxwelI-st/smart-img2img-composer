# -*- coding: utf-8 -*-
import gradio as gr
import os
import traceback
from .i18n import t
from .core import load_config, save_all_settings, handle_load_preset, handle_save_preset, handle_delete_preset, compose_prompt, compose_prompt_preview, append_to_memo
from .utils import _clean_path, check_individual_health
from .constants import WILD_1_PATH, WILD_2_PATH, WILD_3_PATH, PROMPT_PROFILES

def on_ui_tabs():
    try:
        from .ui_tabs_gen import on_tab_prompt_gen
        from .ui_tabs_lora import on_tab_lora_manager

        config = load_config()

        # 旧版に倣い、Block内部で丁寧に構築
        with gr.Blocks(analytics_enabled=False) as tab_interface:
            gr.Markdown(f"# 🎲 Smart Img2Img Composer v1.1.2 Stable\n{t('tab_header')}")

            with gr.Tabs() as tabs_root:
                # --- Tab 1: Settings & Preview ---
                with gr.Tab(t("tab_settings")):
                    with gr.Row():
                        with gr.Column(scale=1):
                            gr.Markdown(t("h_settings"))
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
                                    delete_preset_btn = gr.Button("🗑️", variant="stop", scale=1, min_width=40)

                            with gr.Group():
                                with gr.Row():
                                    image_folder = gr.Textbox(label=t("image_folder"), value=lambda: load_config().get("image_folder", ""), lines=1, scale=8)
                                    with gr.Column(scale=1, min_width=120):
                                        status_img = gr.HTML("")
                                with gr.Row():
                                    memo_file = gr.Textbox(label=t("memo_file"), value=lambda: load_config().get("memo_file", ""), lines=1, scale=8)
                                    with gr.Column(scale=1, min_width=120):
                                        status_memo = gr.HTML("")
                                
                                match_threshold = gr.Slider(label=t("match_threshold"), minimum=0.0, maximum=1.0, step=0.05, value=lambda: load_config().get("match_threshold", 0.3))
                                generation_count = gr.Slider(label=t("generation_count"), minimum=1, maximum=100, step=1, value=lambda: load_config().get("generation_count", 1))

                            with gr.Group():
                                lora_offset = gr.Slider(label=t("lora_offset"), minimum=-1.0, maximum=1.0, step=0.05, value=lambda: load_config().get("lora_offset", 0.0))
                                with gr.Row():
                                    wildcard_1_path = gr.Textbox(label=t("wildcard_1"), value=lambda: load_config().get("wildcard_1_path", WILD_1_PATH), lines=1, scale=8)
                                    with gr.Column(scale=1, min_width=120):
                                        status_w1 = gr.HTML("")
                                with gr.Row():
                                    wildcard_2_path = gr.Textbox(label=t("wildcard_2"), value=lambda: load_config().get("wildcard_2_path", WILD_2_PATH), lines=1, scale=8)
                                    with gr.Column(scale=1, min_width=120):
                                        status_w2 = gr.HTML("")
                                with gr.Row():
                                    wildcard_3_path = gr.Textbox(label=t("wildcard_3"), value=lambda: load_config().get("wildcard_3_path", WILD_3_PATH), lines=1, scale=8)
                                    with gr.Column(scale=1, min_width=120):
                                        status_w3 = gr.HTML("")

                            with gr.Group():
                                fallback_enabled = gr.Checkbox(label=t("fallback_enabled"), value=lambda: load_config().get("fallback_enabled", True))
                                auto_lora_enabled = gr.Checkbox(label=t("auto_lora_enabled"), value=lambda: load_config().get("auto_lora_enabled", True))
                                inventory_mode = gr.Checkbox(label=t("inventory_mode"), value=lambda: load_config().get("inventory_mode", False))
                            
                            with gr.Group():
                                auto_optimize_prompt = gr.Checkbox(label=t("auto_optimize_prompt"), value=lambda: load_config().get("auto_optimize_prompt", False))
                                active_profile = gr.Dropdown(label=t("active_profile"), choices=list(PROMPT_PROFILES.keys()), value=lambda: load_config().get("active_profile", "Standard / SDXL"))
                                custom_base_tags = gr.Textbox(label=t("custom_base_tags"), value=lambda: load_config().get("custom_base_tags", ""), lines=2)
                            
                            with gr.Group():
                                prompt_polish = gr.Checkbox(label=t("prompt_polish"), value=lambda: load_config().get("prompt_polish", False))
                                smart_negative = gr.Checkbox(label=t("smart_negative"), value=lambda: load_config().get("smart_negative", False))
                                smart_negative_mode = gr.Radio(label=t("smart_negative_mode"), choices=[(t("sn_mode_add"), "append"), (t("sn_mode_overwrite"), "overwrite")], value=lambda: load_config().get("smart_negative_mode", "append"))

                        with gr.Column(scale=1):
                            gr.Markdown(t("h_preview"))
                            preview_output = gr.Textbox(label=t("preview_output"), lines=8, interactive=False)
                            test_btn = gr.Button(t("btn_preview"), variant="primary")
                            
                            gr.Markdown(t("language_label"))
                            lang_dropdown = gr.Dropdown(choices=["ja", "en"], value=lambda: load_config().get("language", "ja"), show_label=False)
                            save_btn = gr.Button(t("btn_save"), variant="primary")
                            status = gr.Markdown("")

                            # P3: output_sort_mode / auto_filename を設定タブから保存できるよう hidden コンポーネントとして追加
                            output_sort_hidden = gr.Textbox(
                                value=lambda: load_config().get("output_sort_mode", "None"),
                                visible=False, label="output_sort_mode_hidden"
                            )
                            auto_filename_hidden = gr.Checkbox(
                                value=lambda: load_config().get("auto_filename", False),
                                visible=False, label="auto_filename_hidden"
                            )

                # --- Tab 2: Prompt Generator ---
                with gr.Tab(t("tab_prompt_gen")):
                    gen_comps = on_tab_prompt_gen()
                    # 展開 (ui_tabs_gen.py の戻り値に合わせる)
                    (
                        gen_image, gen_section, gen_confidence, gen_positive, gen_negative, gen_custom_dict,
                        gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled,
                        limit_base, limit_char, limit_nsfw, gen_cat_mosaic,
                        gen_btn, gen_output, gen_log, gen_tags_only, gen_save_btn, append_btn, append_status, send_img2img_btn,
                        conf_base_val, conf_char_val, conf_nsfw_val, use_global_conf
                    ) = gen_comps

                # --- Tab 3: LoRA/Wildcard Manager ---
                with gr.Tab(t("tab_lora_manager")):
                    on_tab_lora_manager()

                # --- Tab 4: Manual ---
                with gr.Tab(t("tab_usage")):
                    gr.Markdown(t("usage_md"))

            # --- Wiring ---
            preset_args_list = [
                image_folder, memo_file, match_threshold, generation_count,
                fallback_enabled, auto_lora_enabled,
                gen_confidence, gen_positive, gen_negative, gen_custom_dict,
                wildcard_1_path, wildcard_2_path, wildcard_3_path,
                lora_offset,
                gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled,
                auto_optimize_prompt, custom_base_tags, active_profile, 
                prompt_polish, smart_negative, smart_negative_mode,
                inventory_mode, limit_base, limit_char, limit_nsfw,
                gen_cat_base, gen_cat_char, gen_cat_nsfw,
                conf_base_val, conf_char_val, conf_nsfw_val,
                use_global_conf
            ]

            preset_dropdown.change(fn=handle_load_preset, inputs=[preset_dropdown], outputs=preset_args_list)
            save_preset_btn.interactive = False

            def _toggle_save_preset_btn(name):
                return gr.update(interactive=bool(name and name.strip()))

            preset_name_input.input(
                fn=_toggle_save_preset_btn,
                inputs=[preset_name_input],
                outputs=[save_preset_btn]
            )

            save_preset_btn.click(
                fn=handle_save_preset,
                inputs=[preset_name_input] + preset_args_list,
                outputs=[status, preset_dropdown]
            )
            delete_preset_btn.click(fn=handle_delete_preset, inputs=[preset_dropdown], outputs=[status, preset_dropdown])

            def _save_all(
                lang, img_f, memo, threshold, count, fallback, auto_l, confidence, pos, neg, c_dict, 
                c_base, c_char, c_nsfw, w1, w2, w3, offset, mosaic_auto, mosaic_level, c_dict_enabled, 
                auto_opt, custom_tags, active_prof, polish, smart_neg, smart_neg_mode, inventory_mode, 
                limit_base, limit_char, limit_nsfw, c_mosaic, conf_base, conf_char, conf_nsfw, ug_conf,
                sort_mode="None", auto_file=False
            ):
                return save_all_settings(
                    lang, img_f, memo, threshold, count, fallback, auto_l, confidence, pos, neg, c_dict, 
                    c_base, c_char, c_nsfw, w1, w2, w3, offset, mosaic_auto, mosaic_level, c_dict_enabled, 
                    auto_opt, custom_tags, active_prof, polish, smart_neg, smart_neg_mode, inventory_mode, 
                    limit_base, limit_char, limit_nsfw, c_mosaic, conf_base, conf_char, conf_nsfw, ug_conf,
                    sort_mode, auto_file
                )

            all_settings_inputs = [
                lang_dropdown, image_folder, memo_file, match_threshold, generation_count,
                fallback_enabled, auto_lora_enabled,
                gen_confidence, gen_positive, gen_negative, gen_custom_dict,
                gen_cat_base, gen_cat_char, gen_cat_nsfw,
                wildcard_1_path, wildcard_2_path, wildcard_3_path, lora_offset,
                gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled, 
                auto_optimize_prompt, custom_base_tags, active_profile, 
                prompt_polish, smart_negative, smart_negative_mode, inventory_mode,
                limit_base, limit_char, limit_nsfw, gen_cat_mosaic,
                conf_base_val, conf_char_val, conf_nsfw_val, use_global_conf,
                output_sort_hidden, auto_filename_hidden  # P3: sort_mode / auto_file を保存に含める
            ]
            
            save_btn.click(fn=_save_all, inputs=all_settings_inputs, outputs=[status])
            gen_save_btn.click(fn=_save_all, inputs=all_settings_inputs, outputs=[append_status])

            test_btn.click(fn=compose_prompt_preview, inputs=[
                image_folder, memo_file, match_threshold, fallback_enabled, auto_lora_enabled, lora_offset, wildcard_1_path, wildcard_2_path, wildcard_3_path, active_profile, inventory_mode
            ], outputs=[preview_output])

            def _do_append(memo, entry):
                return append_to_memo(memo, entry)
            append_btn.click(fn=_do_append, inputs=[memo_file, gen_output], outputs=[append_status])

            # --- HEALTH CHECK WIRING ---
            health_inputs = [image_folder, memo_file, wildcard_1_path, wildcard_2_path, wildcard_3_path]
            health_outputs = [status_img, status_memo, status_w1, status_w2, status_w3]

            def _init_health():
                c = load_config()
                return check_individual_health(
                    c.get("image_folder", ""),
                    c.get("memo_file", ""),
                    c.get("wildcard_1_path", WILD_1_PATH),
                    c.get("wildcard_2_path", WILD_2_PATH),
                    c.get("wildcard_3_path", WILD_3_PATH)
                )

            for comp in health_inputs:
                comp.change(fn=check_individual_health, inputs=health_inputs, outputs=health_outputs)
            
            # 旧版で実績のある tab.load による初期化手順の復元
            tab_interface.load(fn=_init_health, outputs=health_outputs)

        # Tab ID を旧版と同じ "smart_composer_tabs_root" に差し戻し
        return [(tab_interface, "Smart Img2Img Composer", "smart_composer_tabs_root")]

    except Exception as e:
        err_f = traceback.format_exc()
        print(f"[Smart Img2Img Composer] FATAL: {e}")
        with gr.Blocks() as err_ui:
            gr.Markdown(f"## ❌ Smart Img2Img Composer: Load Error\n```{err_f}```")
        return [(err_ui, "Composer Error", "sc_error_tab")]
