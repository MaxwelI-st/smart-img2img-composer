# -*- coding: utf-8 -*-
import gradio as gr
from .i18n import t
from .core import load_config, get_inventory_status, reset_inventory_global, reset_inventory_lora

def on_tab_inventory():
    config = load_config()
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(t("inventory_desc"))
            inventory_mode_chk = gr.Checkbox(
                label=t("inventory_mode"),
                value=lambda: load_config().get("inventory_mode", False),
                info=t("inventory_mode_info")
            )
            
            with gr.Row():
                check_btn = gr.Button(t("btn_check_stock"), variant="primary")
                reset_lora_btn = gr.Button(t("btn_lora_reset"), variant="secondary")
                reset_all_btn = gr.Button(t("btn_global_reset"), variant="secondary")
            
            status_msg = gr.Markdown("")
            
        with gr.Column(scale=1):
            gr.Markdown(f"### {t('inventory_status_label')}")
            inventory_display = gr.Textbox(label=None, lines=20, interactive=False)

    # Events
    check_btn.click(fn=get_inventory_status, outputs=[inventory_display])
    reset_lora_btn.click(fn=reset_inventory_lora, outputs=[status_msg])
    reset_all_btn.click(fn=reset_inventory_global, outputs=[status_msg])

    return inventory_mode_chk
