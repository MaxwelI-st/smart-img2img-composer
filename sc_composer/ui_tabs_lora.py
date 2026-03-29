# -*- coding: utf-8 -*-
import gradio as gr
from .i18n import t
from .lora_mgr import load_lora_list, save_lora_list, append_lora_list

def on_tab_lora_manager():
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown(t("lora_manager_desc"))
            lora_type = gr.Radio(
                label=t("lora_type"),
                choices=[t("lora_type_char"), t("lora_type_sit"), t("wildcard_1"), t("wildcard_2"), t("wildcard_3")],
                value=t("lora_type_char")
            )
            lora_list = gr.Textbox(label=t("lora_list_label"), lines=15, placeholder=t("lora_mgr_placeholder"))
            
            with gr.Row():
                save_btn = gr.Button(t("btn_save_lora_list"), variant="primary")
                status = gr.Markdown("")
        
        with gr.Column(scale=1):
            gr.Markdown("### \u2795 Quick Append")
            lora_input = gr.Textbox(label=t("lora_input_label"), placeholder="<lora:name:1.0> or tag")
            append_btn = gr.Button(t("btn_append_lora"), variant="secondary")

    # Events
    lora_type.change(fn=load_lora_list, inputs=[lora_type], outputs=[lora_list])
    
    # Matching save_lora_list return values
    def _do_save(label, content):
        msg, new_content = save_lora_list(label, content)
        return msg

    save_btn.click(fn=_do_save, inputs=[lora_type, lora_list], outputs=[status])
    
    def _do_append(label, input_text):
        # Append logic: return updated list and clear input box
        new_list, _ = append_lora_list(label, input_text)
        return new_list, ""

    append_btn.click(fn=_do_append, inputs=[lora_type, lora_input], outputs=[lora_list, lora_input])

    return lora_list
