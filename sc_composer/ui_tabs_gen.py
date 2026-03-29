# -*- coding: utf-8 -*-
import gradio as gr
from .i18n import t
from .core import load_config, append_to_memo
from .tagger import autogen_prompt
from .constants import _CAT_BASE_KEYS, _CAT_CHAR_KEYS, _CAT_NSFW_KEYS

def on_tab_prompt_gen():
    config = load_config()

    with gr.Row():
        # Left Side (Settings)
        with gr.Column(scale=2):
            with gr.Row():
                with gr.Column(scale=1):
                    gen_image = gr.Image(label=t("target_image"), type="pil")
                with gr.Column(scale=1):
                    gen_section = gr.Textbox(label=t("section_name"), placeholder=t("section_ph"), info=t("section_info"))
            
            gr.Markdown(t("h_categories"))
            btn_toggle_cat_all = gr.Button(t("btn_toggle_cat_all"), variant="primary")
            
            # ▼ 究極のスリム化： [🔄] [0.35] [チェックボックス群] の完全1行配置 ▼
            with gr.Accordion(t("cat_base"), open=True):
                with gr.Row(equal_height=True):
                    btn_toggle_cat_base = gr.Button("🔄", variant="secondary", size="sm", min_width=40, scale=0)
                    conf_base = gr.Number(value=0.35, minimum=0.0, maximum=1.0, step=0.01, show_label=False, container=False, min_width=80, scale=0)
                    gen_cat_base = gr.CheckboxGroup(
                        choices=[(t(c), c) for c in _CAT_BASE_KEYS],
                        value=["cat_composition", "cat_pose", "cat_background", "cat_atmosphere"],
                        show_label=False,
                        scale=1
                    )
            
            with gr.Accordion(t("cat_char"), open=False):
                with gr.Row(equal_height=True):
                    btn_toggle_cat_char = gr.Button("🔄", variant="secondary", size="sm", min_width=40, scale=0)
                    conf_char = gr.Number(value=0.35, minimum=0.0, maximum=1.0, step=0.01, show_label=False, container=False, min_width=80, scale=0)
                    gen_cat_char = gr.CheckboxGroup(
                        choices=[(t(c), c) for c in _CAT_CHAR_KEYS],
                        value=["cat_char_face", "cat_char_male"],
                        show_label=False,
                        scale=1
                    )
            
            with gr.Accordion(t("cat_nsfw"), open=False):
                with gr.Row(equal_height=True):
                    btn_toggle_cat_nsfw = gr.Button("🔄", variant="secondary", size="sm", min_width=40, scale=0)
                    conf_nsfw = gr.Number(value=0.35, minimum=0.0, maximum=1.0, step=0.01, show_label=False, container=False, min_width=80, scale=0)
                    gen_cat_nsfw = gr.CheckboxGroup(
                        choices=[(t(c), c) for c in _CAT_NSFW_KEYS],
                        value=[k for k in _CAT_NSFW_KEYS if k != "cat_nsfw_clothes_mess"],
                        show_label=False,
                        scale=1
                    )

            with gr.Accordion(t("h_pickup_limits"), open=False):
                with gr.Row():
                    limit_base = gr.Number(label=t('limit_base_label'), minimum=1, maximum=50, step=1, value=10, min_width=80)
                    limit_char = gr.Number(label=t('limit_char_label'), minimum=1, maximum=50, step=1, value=10, min_width=80)
                    limit_nsfw = gr.Number(label=t('limit_nsfw_label'), minimum=1, maximum=50, step=1, value=15, min_width=80)

            # ▼ 新規追加：共通信頼性の優先チェックボックスと説明文 ▼
            with gr.Group():
                with gr.Row(equal_height=True):
                    use_global_conf = gr.Checkbox(label=t("use_global_conf"), value=True, min_width=0)
                    gr.HTML(f"<span style='font-size: 0.85em; color: gray; margin-left: 10px; white-space: nowrap;'>{t('use_global_conf_info')}</span>")
                gen_confidence = gr.Slider(label=t('conf_total'), minimum=0.0, maximum=1.0, step=0.05, value=0.35)

            gen_positive = gr.Textbox(label=t("default_positive"), placeholder="masterpiece, 1girl...", lines=2, value=lambda: load_config().get("gen_positive", ""))
            gen_negative = gr.Textbox(label=t("default_negative"), placeholder="lowres, bad anatomy...", lines=2, value=lambda: load_config().get("gen_negative", ""))

            with gr.Accordion(t("gen_custom_dict_enabled_label"), open=False):
                gen_custom_dict_enabled = gr.Checkbox(label=t("gen_custom_dict_enabled_label"), value=False, show_label=False)
                gen_custom_dict = gr.Textbox(label=t("custom_dict"), placeholder="night > neon lights...", lines=3, value=lambda: load_config().get("gen_custom_dict", ""))

            with gr.Accordion(t("h_mosaic_settings"), open=False):
                gen_mosaic_auto = gr.Checkbox(label=t("gen_mosaic_auto"), value=False)
                gen_mosaic_level = gr.Radio(label=t("gen_mosaic_level"), choices=[t("mosaic_low"), t("mosaic_med"), t("mosaic_high")], value=t("mosaic_med"))
                gr.Markdown(t("mosaic_layer_1"))
                gen_cat_mosaic = gr.CheckboxGroup(
                    choices=[("mosaic_censoring", "mosaic_censoring"), ("bar_censor", "bar_censor"), ("censored", "censored"), ("uncensored", "uncensored"), ("detailed_mosaic", "detailed_mosaic")],
                    value=["mosaic_censoring", "bar_censor", "censored"],
                    show_label=False
                )

            with gr.Row():
                gen_btn = gr.Button(t("btn_gen_tags"), variant="primary", scale=2)
                append_btn = gr.Button(t("btn_append_memo"), variant="secondary", scale=1)
                gen_save_btn = gr.Button(t("btn_save_settings"), variant="secondary", scale=1)

        # Right Side (Output)
        with gr.Column(scale=1):
            send_img2img_btn = gr.Button(t("btn_send_img2img"), variant="primary")
            gen_output = gr.Textbox(label=t("generated_entry"), lines=12, interactive=True)
            gen_tags_only = gr.Textbox(label=t("gen_tags_only"), lines=6, interactive=True)
            gen_log = gr.Textbox(label=t("analysis_log"), lines=8, interactive=False)
            append_status = gr.Textbox(label=t("append_status"), interactive=False)

    # --- Category Toggle Helpers ---
    def toggle_group(current, keys):
        if len(current) > 0: return gr.update(value=[])
        return gr.update(value=keys)

    def toggle_all(b, c, n):
        if b or c or n: return gr.update(value=[]), gr.update(value=[]), gr.update(value=[])
        return gr.update(value=_CAT_BASE_KEYS), gr.update(value=_CAT_CHAR_KEYS), gr.update(value=_CAT_NSFW_KEYS)

    btn_toggle_cat_all.click(fn=toggle_all, inputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw], outputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw])
    btn_toggle_cat_base.click(fn=lambda v: toggle_group(v, _CAT_BASE_KEYS), inputs=[gen_cat_base], outputs=[gen_cat_base])
    btn_toggle_cat_char.click(fn=lambda v: toggle_group(v, _CAT_CHAR_KEYS), inputs=[gen_cat_char], outputs=[gen_cat_char])
    btn_toggle_cat_nsfw.click(fn=lambda v: toggle_group(v, _CAT_NSFW_KEYS), inputs=[gen_cat_nsfw], outputs=[gen_cat_nsfw])

    # --- Event Wiring ---
    gen_btn.click(
        fn=autogen_prompt,
        inputs=[
            gen_image, gen_section, gen_confidence, gen_positive, gen_negative, 
            gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_custom_dict, 
            gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled, 
            limit_base, limit_char, limit_nsfw, gen_cat_mosaic,
            conf_base, conf_char, conf_nsfw, use_global_conf
        ],
        outputs=[gen_output, gen_log, gen_tags_only]
    )

    # JS Fix: scSendToImg2img は smart_img2img_composer.js で定義
    # タブ切り替えを 250ms 遅延させることで Gradio の _js 後処理との競合を回避
    send_img2img_btn.click(
        fn=None,
        _js="scSendToImg2img",
        inputs=[gen_image, gen_output, gen_negative],
        outputs=None
    )

    return (
        gen_image, gen_section, gen_confidence, gen_positive, gen_negative, gen_custom_dict,
        gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled,
        limit_base, limit_char, limit_nsfw, gen_cat_mosaic,
        gen_btn, gen_output, gen_log, gen_tags_only, gen_save_btn, append_btn, append_status, send_img2img_btn,
        conf_base, conf_char, conf_nsfw, use_global_conf
    )
