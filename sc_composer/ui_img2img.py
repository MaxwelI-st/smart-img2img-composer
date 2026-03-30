# -*- coding: utf-8 -*-
import gradio as gr
from .i18n import t
from .core import load_config
from .constants import PROMPT_PROFILES

def on_ui_img2img():
    config = load_config()

    with gr.Accordion("\U0001F3B2 Smart Img2Img Composer", open=False, elem_id="smart_composer_accordion"):
        gr.Markdown(t("accordion_desc"))
        
        enabled = gr.Checkbox(
            label=t("enable"),
            value=False,
            elem_id="smart_composer_enabled",
        )

        # Assets
        with gr.Accordion(t("accordion_assets"), open=False):
            with gr.Row():
                gr.Markdown(f"<div style='text-align: right; padding-right: 15px;'><b>{t('pos_label')}</b></div>")
            
            _pos_choices = [t("pos_front"), t("pos_back"), t("pos_smart")]

            with gr.Row():
                en_char = gr.Checkbox(label=t("enable_random_char"), value=False, scale=8)
                pos_char = gr.Radio(choices=_pos_choices, value=t("pos_back"), show_label=False, scale=2, min_width=180)
            
            with gr.Row():
                en_sit = gr.Checkbox(label=t("enable_random_sit"), value=False, scale=8)
                pos_sit = gr.Radio(choices=_pos_choices, value=t("pos_back"), show_label=False, scale=2, min_width=180)
            
            with gr.Row():
                en_w1 = gr.Checkbox(label=t("wildcard_1"), value=False, scale=8)
                pos_w1 = gr.Radio(choices=_pos_choices, value=t("pos_back"), show_label=False, scale=2, min_width=180)
            
            with gr.Row():
                en_w2 = gr.Checkbox(label=t("wildcard_2"), value=False, scale=8)
                pos_w2 = gr.Radio(choices=_pos_choices, value=t("pos_back"), show_label=False, scale=2, min_width=180)
            
            with gr.Row():
                en_w3 = gr.Checkbox(label=t("wildcard_3"), value=False, scale=8)
                pos_w3 = gr.Radio(choices=_pos_choices, value=t("pos_back"), show_label=False, scale=2, min_width=180)

        with gr.Row():
            selection_mode = gr.Radio(
                label=t("selection_mode"),
                choices=[(t("sel_random"), "random"), (t("sel_sequential"), "sequential")],
                value="random",
            )
            override_prompt = gr.Checkbox(
                label=t("overwrite_prompt"),
                value=True,
            )

        active_profile = gr.Dropdown(
            label=t("active_profile"),
            choices=list(PROMPT_PROFILES.keys()),
            value=lambda: load_config().get("active_profile", "Standard / SDXL"),
            visible=False
        )
        custom_base_tags = gr.Textbox(
            label=t("custom_base_tags"),
            value=lambda: load_config().get("custom_base_tags", "masterpiece, best quality, 1girl, solo"),
            visible=False
        )

        with gr.Row():
            auto_optimize = gr.Checkbox(
                label=t("auto_optimize_prompt"),
                value=lambda: load_config().get("auto_optimize_prompt", False),
            )
            prompt_polish = gr.Checkbox(
                label=t("prompt_polish"),
                value=lambda: load_config().get("prompt_polish", False),
            )

        with gr.Row():
            _resize_choices = [t("resize_none"), t("resize_slider_base"), t("resize_512"), t("resize_1024"), t("resize_1536")]
            resize_mode = gr.Dropdown(
                label=t("resize_mode"),
                choices=_resize_choices,
                value=_resize_choices[0],
            )
            base_resolution = gr.Slider(
                label=t("base_resolution"),
                minimum=512, maximum=2048, step=64,
                value=1024,
            )

        with gr.Accordion(t("output_settings"), open=False):
            output_sort_mode = gr.Dropdown(
                label=t("sort_mode"),
                # Internal keys: "None", "By Preset", "By Section", "By Date"
                choices=[(t("sort_none"), "None"), (t("sort_preset"), "By Preset"), (t("sort_section"), "By Section"), (t("sort_date"), "By Date")],
                value="None"
            )
            auto_filename_chk = gr.Checkbox(
                label=t("auto_filename"),
                value=lambda: load_config().get("auto_filename", False),
            )

    return [
        enabled, override_prompt, resize_mode, base_resolution, selection_mode,
        en_char, pos_char, en_sit, pos_sit, en_w1, pos_w1, en_w2, pos_w2, en_w3, pos_w3,
        output_sort_mode, auto_optimize, custom_base_tags, active_profile, prompt_polish, auto_filename_chk
    ]
