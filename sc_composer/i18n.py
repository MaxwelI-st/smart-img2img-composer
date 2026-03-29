# -*- coding: utf-8 -*-
import os
import json
from .constants import CONFIG_PATH

_I18N = {
    "tab_header": {"en": "Smart Img2Img Composer Settings", "ja": "スマート・img2imgコンポーザー 設定"},
    "tab_settings": {"en": "⚙️ Settings & Preview", "ja": "⚙️ 設定 & プレビュー"},
    "h_settings": {"en": "⚙️ Global Settings", "ja": "⚙️ 全般設定"},
    "h_preview": {"en": "👀 Generation Preview", "ja": "👀 生成プレビュー"},
    "language_label": {"en": "UI Language", "ja": "表示言語"},
    "image_folder": {"en": "Reference Image Folder", "ja": "参照画像フォルダ"},
    "memo_file": {"en": "Memo File (.txt)", "ja": "メモファイル (.txt)"},
    "match_threshold": {"en": "Match Threshold", "ja": "ファイル名一致しきい値"},
    "generation_count": {"en": "Batch Count", "ja": "生成枚数"},
    "lora_offset": {"en": "LoRA Offset", "ja": "LoRA 強度オフセット"},
    "btn_save": {"en": "💾 Save All Settings", "ja": "💾 全ての設定を保存"},
    "btn_preview": {"en": "🔎 Test Composition", "ja": "🔎 構成テスト"},
    "positive_prompt": {"en": "Positive Prompt", "ja": "生成ポジティブ"},
    "negative_prompt": {"en": "Negative Prompt", "ja": "生成ネガティブ"},
    "log": {"en": "Log", "ja": "ログ"},
    "tab_prompt_gen": {"en": "🏷️Auto-Prompt Gen", "ja": "🏷️タグ解析＋メモ生成"},
    "tab_lora_manager": {"en": "📦Asset Lists", "ja": "📦アセットリスト管理"},
    "tab_inventory": {"en": "⚖️ Inventory Control", "ja": "⚖️ 在庫管理"},
    "tab_usage": {"en": "📖 Manual", "ja": "📖 使い方"},
    "selected_image": {"en": "Selected Image", "ja": "選択された画像"},
    
    # Preset
    "preset_label": {"en": "Load Preset", "ja": "プリセット一覧"},
    "preset_ph": {"en": "New Preset Name", "ja": "新しいプリセット名"},
    
    # Logic Settings
    "auto_optimize_prompt": {"en": "✨ Auto-Optimize Prompt", "ja": "✨ プロンプト自動最適化"},
    "prompt_polish": {"en": "🪄 Prompt Polish", "ja": "🪄 プロンプト洗練"},
    "active_profile": {"en": "🎨 Profile", "ja": "🎨 最適化プロファイル"},
    "custom_base_tags": {"en": "Base Tags", "ja": "基本タグ"},
    "smart_negative": {"en": "🚫 Smart Negative", "ja": "🚫 ネガティブ補強"},
    "sn_mode_add": {"en": "Append", "ja": "追加"},
    "sn_mode_overwrite": {"en": "Overwrite", "ja": "上書き"},
    "smart_negative_mode": {"en": "Mode", "ja": "ネガティブ挿入モード"},
    "auto_lora_enabled":        {"en": "Auto LoRA Apply",          "ja": "LoRA 自動適用"},
    "preview_output":            {"en": "Preview Output",            "ja": "プレビュー出力"},
    "fallback_enabled": {"en": "Fallback Section", "ja": "一致しない場合は [default] セクションを使用"},
    "output_settings": {"en": "Output Management", "ja": "出力設定"},
    "sort_mode": {"en": "Sort Subfolders", "ja": "サブフォルダ分け"},
    "sort_none": {"en": "None", "ja": "なし"},
    "sort_preset": {"en": "By Preset", "ja": "プリセット別"},
    "sort_section": {"en": "By Section", "ja": "セクション別"},
    "sort_date": {"en": "By Date", "ja": "日付別"},
    "auto_filename": {"en": "🏷️ Auto-Filename", "ja": "🏷️ 自動命名"},
    
    # Tab 2: Gen
    "prompt_gen_desc": {"en": "Analyze images and create memo entries.", "ja": "画像を解析してメモ用のエントリを自動生成します。"},
    "target_image": {"en": "Target Image", "ja": "📸 解析する画像"},
    "section_name": {"en": "Section Name", "ja": "📌 セクション名 (Memo Key)"},
    "section_ph": {"en": "e.g. Character A", "ja": "例: タイトル1"},
    "section_info": {"en": "Matches image filename in img2img.", "ja": "img2img 生成時のファイル名一致に使用します。"},
    "h_extracted_tags": {"en": "Extracted Tags (Current)", "ja": "抽出タグ"},
    "gen_tags_only": {"en": "Tags Only Mode", "ja": "タグのみ出力"},
    "gen_tags_only_info": {"en": "Do not compose with template.", "ja": "メモテンプレートを使わず、タグのみを出力します。"},
    "btn_gen_tags": {"en": "🏷️ Generate Tags", "ja": "🏷️ タグ解析＆生成"},
    "h_categories": {"en": "Categories (Extract checked types)", "ja": "🏷️ 抽出するタグの種類（チェックした種類のタグだけを抽出します）"},
    "btn_toggle_cat_all": {"en": "🔄 Select/Deselect All", "ja": "🔄 全選択/解除"},
    "cat_base": {"en": "Base Categories", "ja": "基本カテゴリ (構図・背景など)"},
    "cat_char": {"en": "Character Categories", "ja": "人物・詳細カテゴリ (髪型・服装・性別など)"},
    "cat_nsfw": {"en": "NSFW Categories", "ja": "特殊・NSFWカテゴリ (行為・局部・アイテム等)"},
    
    # Detailed Categories
    "cat_composition": {"en": "Composition", "ja": "構図・画角"},
    "cat_pose": {"en": "Pose / Action", "ja": "ポーズ・動作"},
    "cat_background": {"en": "Background", "ja": "背景・場所"},
    "cat_nature": {"en": "Nature / Environment", "ja": "自然・環境"},
    "cat_lighting": {"en": "Lighting", "ja": "照明・ライティング"},
    "cat_atmosphere": {"en": "Atmosphere / Mood", "ja": "雰囲気・ムード"},
    "cat_meta": {"en": "Meta / Quality", "ja": "品質・メタタグ"},
    "cat_char_base": {"en": "Body Type", "ja": "体型・ボディ"},
    "cat_char_hair": {"en": "Hair Style", "ja": "髪型・ヘア"},
    "cat_char_eyes": {"en": "Eyes", "ja": "瞳・目元"},
    "cat_char_face": {"en": "Face / Expression", "ja": "顔・表情"},
    "cat_char_clothes": {"en": "Outfits", "ja": "服装・衣装"},
    "cat_char_male": {"en": "Male Specific", "ja": "男性要素"},

    "cat_nsfw_action": {"en": "Sex Actions", "ja": "性行為内容"},
    "cat_nsfw_creature": {"en": "Creatures", "ja": "人外・触手等"},
    "cat_nsfw_item": {"en": "Toys / Items", "ja": "道具・アイテム"},
    "cat_nsfw_focus": {"en": "Body Part Focus", "ja": "部位フォーカス"},
    "cat_nsfw_fluids": {"en": "Body Fluids", "ja": "体液・汁"},
    "cat_nsfw_fetish": {"en": "Fetish / Kink", "ja": "フェティッシュ"},
    "cat_nsfw_clothes_mess": {"en": "Undressing", "ja": "着衣乱れ・露出"},
    "cat_nsfw_genitals": {"en": "Genitals", "ja": "局部・性器"},
    "cat_nsfw_scenario": {"en": "Scenarios", "ja": "シチュエーション・特殊"},
    "btn_toggle_cat": {"en": "Select All / Deselect All", "ja": "全選択 / 解除"},
    
    "h_tag_analysis_settings": {"en": "⚙️ Tag Analysis Settings", "ja": "⚙️ タグ解析・設定"},
    "conf_base": {"en": "Base Group (BG, etc.)", "ja": "基本グループ (背景等)"},
    "conf_char": {"en": "Character Group (Face, Clothes)", "ja": "人物グループ (顔・服)"},
    "conf_nsfw": {"en": "NSFW Group (Genitals, Actions)", "ja": "NSFWグループ (局部・行為)"},
    "conf_total": {"en": "Tag Confidence (Total)", "ja": "タグ信頼性 (共通)"},
    
    "gen_custom_dict_enabled_label": {"en": "Enable Custom Dictionary", "ja": "カスタム読替え辞書を有効にする"},
    "h_mosaic_settings": {"en": "🧱 Mosaic Auto-Prompt Settings", "ja": "🧱 モザイクプロンプト自動付与設定"},
    "gen_mosaic_auto": {"en": "Auto Detect", "ja": "自動検知"},
    "gen_mosaic_level": {"en": "Level", "ja": "モザイクの濃さ"},
    "mosaic_layer_1": {"en": "Mosaic Layer 1", "ja": "モザイク一層目"},
    "mosaic_low": {"en": "Thin", "ja": "薄い"},
    "mosaic_med": {"en": "Med", "ja": "普通"},
    "mosaic_high": {"en": "Thick", "ja": "厚い"},
    "cat_nsfw_mosaic": {"en": "Categories", "ja": "検知タイプ"},
    "h_pickup_limits": {"en": "Pickup Limits", "ja": "📏 抽出本数上限"},
    "limit_base_label": {"en": "Base", "ja": "基本グループ（背景等）"},
    "limit_char_label": {"en": "Char", "ja": "人物グループ（顔・服）"},
    "limit_nsfw_label": {"en": "NSFW", "ja": "NSFWグループ（局部・行為）"},
    "default_positive": {"en": "Positive Template", "ja": "✨ デフォルトポジティブ"},
    "default_negative": {"en": "Negative Template", "ja": "🚫 デフォルトネガティブ"},
    "custom_dict": {"en": "Custom Dictionary", "ja": "カスタム読替え辞書"},
    "generated_entry": {"en": "📋 Generated Entry (editable)", "ja": "📋 生成されたエントリ（編集可能）"},
    "generated_entry_info": {"en": "Paste this to memo file.", "ja": "これをメモファイルに貼り付けてください。"},
    "btn_append_memo": {"en": "📝 Append to Memo", "ja": "📝 メモファイルに追記"},
    "btn_send_img2img": {"en": "🚀 img2img Transfer", "ja": "🚀 img2imgへ送信"},
    "analysis_log": {"en": "Analysis Log", "ja": "解析ログ"},
    "btn_save_settings": {"en": "💾 Save Settings", "ja": "💾 設定を保存"},
    "append_status": {"en": "Append Status", "ja": "追記ステータス"},
    
    # Tab 3: LoRA
    "lora_manager_desc": {"en": "Manage asset lists.", "ja": "ランダムアセットのリストを管理します。"},
    "lora_type": {"en": "Target Slot", "ja": "対象スロット"},
    "lora_type_char": {"en": "Char LoRA", "ja": "キャラ LoRA"},
    "lora_type_sit": {"en": "Sit LoRA", "ja": "シチュ LoRA"},
    "wildcard_1": {"en": "W1", "ja": "ワイルド1"},
    "wildcard_2": {"en": "W2", "ja": "ワイルド2"},
    "wildcard_3": {"en": "W3", "ja": "ワイルド3"},
    "lora_list_label": {"en": "List Content", "ja": "リスト内容"},
    "lora_mgr_placeholder": {"en": "Enter items...", "ja": "1行ごとに入力してください。"},
    "btn_save_lora_list": {"en": "Save List", "ja": "リストを保存"},
    "lora_input_label": {"en": "Quick Add", "ja": "クイック追加"},
    "btn_append_lora": {"en": "Add", "ja": "追加"},
    
    # Tab 4: Inventory
    "inventory_desc": {"en": "Manage usage statistics.", "ja": "アセットの使用回数を管理します。"},
    "inventory_mode": {"en": "Enable Inventory Logic", "ja": "在庫管理ロジックを有効にする"},
    "inventory_mode_info": {"en": "Prioritizes lower usage items.", "ja": "使用回数が少ない項目を優先します。"},
    "btn_check_stock": {"en": "View Stats", "ja": "使用統計を表示"},
    "btn_lora_reset": {"en": "Reset Usage", "ja": "使用履歴リセット"},
    "btn_global_reset": {"en": "Reset All", "ja": "全データリセット"},
    "inventory_status_label": {"en": "Status", "ja": "ステータス"},
    
    # Manual
    "usage_md": {
        "en": """
### 🎲 How to Use Smart Img2Img Composer v1.1.2

This extension is a powerful tool to synchronize your image metadata with your prompt generation workflow.

#### 1. ⚙️ Settings & Preview
- **Reference Image Folder**: The directory where your source images are stored.
- **Memo File**: A .txt file containing prompt entries for each image name.
- **Health Check (✅/❌)**: Real-time validation of your paths.
- **Preset Management**: Save and load different configurations easily.

#### 2. 🏷️ Tag Analysis (Tagger)
- **Auto-Prompt Gen**: Uses deep learning to analyze your uploaded image and generate tags.
- **Category Sliders**: Fine-tune confidence thresholds for different types of tags.
- **Mosaic Auto-Prompt**: Automatically adds NSFW/Mosaic-safe tags based on visual analysis.

#### 3. 📦 Asset Lists (LoRA/Wildcards)
- Manage your LoRA and Wildcard lists globally. These are used when 'Inventory Logic' is enabled.

#### 4. ⚖️ Inventory Logic
- Prevents repetition by tracking which assets have been used and prioritizing unused ones.

---
*Created by Antigravity Team*
        """,
        "ja": """
### 🎲 Smart Img2Img Composer v1.1.2 マニュアル

本拡張機能は、参照画像のファイル名とメモファイルを紐付け、複雑な img2img 構成を自動化するプロフェッショナルツールです。

#### 1. ⚙️ 設定 & プレビュー (基本操作)
- **参照画像フォルダ**: img2img で読み込む画像の保存先を指定します。
- **メモファイル**: ファイル名に基づいたプロンプト（LoRAやタグ）を記述した .txt ファイルです。
- **ヘルスチェック (✅/❌)**: パスが正しいかリアルタイムで判定します。
- **プリセット**: 「SDXL用」「Pony用」など、設定をまるごと保存・読込できます。

#### 2. 🏷️ タグ解析＋メモ生成 (Tagger)
- **タグ抽出**: アップロードした画像をAIが解析し、全自動でプロンプトを生成します。
- **カテゴリ別信頼性**: 背景、衣装、行為などのグループごとに抽出の厳しさを調整可能。
- **モザイク自動付与**: 画像からモザイク属性を検知し、適切なタグを自動挿入します。

#### 3. 📦 アセットリスト管理
- ランダムに使用する LoRA やワイルドカードのリストを一括管理できます。

#### 4. ⚖️ 在庫管理 (Inventory Logic)
- **使用回数カウント**: 同じ LoRA ばかりが出ないよう、使用回数が少ない順に優先して抽選します。

---
*Developed by Antigravity*
        """
    },
    
    # msgs
    "msg_all_saved": {"en": "Saved", "ja": "保存しました"},
    "msg_inventory_reset": {"en": "Reset done", "ja": "リセット完了"},
    "msg_memo_appended": {"en": "Appended", "ja": "追記完了"},
    "msg_memo_err": {"en": "Error", "ja": "エラー"},
    "msg_lora_saved": {"en": "List saved", "ja": "リストを保存しました"},
    "no_images": {"en": "No images", "ja": "画像なし"},
    "log_no_sections": {"en": "No sections", "ja": "セクションなし"},
    "log_no_match": {"en": "No match", "ja": "一致なし"},
    "msg_tagger_not_found": {"en": "Tagger missing", "ja": "タガーが見つかりません"},
    "msg_tag_fetch_err": {"en": "Tag error", "ja": "タグ解析エラー"},
    "msg_no_upload_err": {"en": "Upload first", "ja": "画像をアップロードしてください"},
    "msg_no_section_err": {"en": "Name section", "ja": "セクション名を入力してください"},
    "log_all_tags": {"en": "{count} tags found", "ja": "{count} 個のタグを検出"},
    "log_filtered_tags": {"en": "{count} tags picked", "ja": "{count} 個のタグを抽出"},
    "log_custom_match": {"en": "Rule hit: {cond} -> {prompt}", "ja": "カスタムルール一致: {cond} -> {prompt}"},

    # --- 欠損していたキー群の追加 ---
    "pos_label": {"en": "Injection Position", "ja": "挿入位置"},
    "resize_slider": {"en": "Slider Value", "ja": "スライダー値"},

    "accordion_desc": {"en": "Description", "ja": "説明"},
    "enable": {"en": "Enable", "ja": "有効化"},
    "accordion_assets": {"en": "Assets", "ja": "アセット"},
    "pos_front": {"en": "Front", "ja": "前"},
    "pos_back": {"en": "Back", "ja": "後"},
    "pos_smart": {"en": "Smart", "ja": "スマート"},
    "enable_random_char": {"en": "Random Char", "ja": "ランダムキャラ"},
    "enable_random_sit": {"en": "Random Situation", "ja": "ランダムシチュ"},
    "selection_mode": {"en": "Selection Mode", "ja": "選択モード"},
    "sel_random": {"en": "Random", "ja": "ランダム"},
    "sel_sequential": {"en": "Sequential", "ja": "順番"},
    "overwrite_prompt": {"en": "Overwrite Prompt", "ja": "プロンプト上書き"},
    "resize_mode": {"en": "Resize Mode", "ja": "リサイズモード"},
    "resize_none": {"en": "None", "ja": "なし"},
    "resize_slider_base": {"en": "Slider (Base Res)", "ja": "スライダー指定"}, # キー重複を避けるため変更
    "resize_512": {"en": "512-1024", "ja": "512-1024"},
    "resize_1024": {"en": "1024-1536", "ja": "1024-1536"},
    "resize_1536": {"en": "1536-1792", "ja": "1536-1792"},
    "base_resolution": {"en": "Base Res", "ja": "基本解像度"},
    "msg_settings_saved": {"en": "Settings Saved", "ja": "設定を保存しました"},
    "msg_settings_err": {"en": "Save Error", "ja": "保存エラー"},
    "msg_no_tags_err": {"en": "No Tags", "ja": "タグがありません"},
    "use_global_conf": {"en": "Prioritize Global Confidence", "ja": "タグ信頼性(共通)を優先する"},
    "use_global_conf_info": {"en": "* If unchecked, individual category values will be prioritized.", "ja": "※チェックを外すと、各カテゴリ（基本・キャラ・NSFW）の個別数値が優先されます。"},
    "health_check_ok": {"en": "✅ Ready", "ja": "✅ 正常"},
    "health_check_err": {"en": "❌ Not Found", "ja": "❌ 異常"},
}

_lang_cache = None

def _get_lang() -> str:
    global _lang_cache
    if _lang_cache is not None: return _lang_cache
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _lang_cache = json.load(f).get("language", "ja")
                return _lang_cache
    except Exception: pass
    return "ja"

def invalidate_lang_cache():
    global _lang_cache
    _lang_cache = None

def t(key: str) -> str:
    lang = _get_lang()
    entry = _I18N.get(key, {})
    return entry.get(lang, entry.get("en", key))
