# -*- coding: utf-8 -*-
import os
import json
from .constants import CONFIG_PATH

_I18N = {
    # --- img2img アコーディオン ---
    "accordion_desc": {
        "en": "**Check Enable → Click Generate.** (Tip: If using external wildcards in the main box, turn OFF 'Overwrite Prompt' below).",
        "ja": "**有効化 → Generate で自動実行。** (Tip: 外部のワイルドカード等と併用する場合は下の「プロンプトを上書き」をOFFにしてください)。",
    },
    "enable": {
        "en": "✅ Enable (Auto-inject image & prompt)",
        "ja": "✅ 有効化（生成時に自動で画像＋プロンプト投入）",
    },
    "pos_label": {"en": "Pos", "ja": "位置"},
    "pos_front": {"en": "Front", "ja": "前"},
    "pos_back": {"en": "Back", "ja": "後"},
    "pos_smart": {"en": "Smart", "ja": "特定タグの後"},
    "wildcard_1": {"en": "Wildcard 1", "ja": "ワイルドカード1"},
    "wildcard_2": {"en": "Wildcard 2", "ja": "ワイルドカード2"},
    "wildcard_3": {"en": "Wildcard 3", "ja": "ワイルドカード3"},
    "accordion_assets": {"en": "🎲 Random Asset Slots", "ja": "🎲 ランダムアセット・スロット"},
    "tab_settings_wildcards": {"en": "📂 Custom Wildcard Paths", "ja": "📂 カスタム・ワイルドカードのパス設定"},
    "wildcard_path_label": {"en": "Path to {name}", "ja": "{name}のパス"},
    "selection_mode": {
        "en": "🖼️ Image Selection Mode",
        "ja": "🖼️ 画像の選択モード",
    },
    "sel_random": {
        "en": "Random",
        "ja": "ランダムに選ぶ",
    },
    "sel_sequential": {
        "en": "Sequential (One by one in alphabetical order)",
        "ja": "フォルダ内の順番通りに1枚ずつ選ぶ",
    },
    "overwrite_prompt": {
        "en": "Overwrite Prompt (If OFF, append to existing)",
        "ja": "プロンプトを上書き（OFFなら既存の末尾に追加）",
    },
    "auto_optimize_prompt": {
        "en": "✨ Auto-Optimize Prompt Order",
        "ja": "✨ プロンプトの並びを自動最適化する",
    },
    "prompt_polish": {
        "en": "🪄 Prompt Polish",
        "ja": "🪄 プロンプトの洗練",
    },
    "auto_filename": {
        "en": "🏷️ Auto-Filename (AI Naming)",
        "ja": "🏷️ AI 命名 (ファイル名自動生成)",
    },
    "auto_filename_info": {
        "en": "Extract characteristic tags and use them for subfolder/filename organization.",
        "ja": "特徴的なタグを抽出し、フォルダ名やファイル名に組み込んで整理しやすくします。",
    },
    "smart_negative": {
        "en": "🚫 Smart Negative",
        "ja": "🚫 スマート・ネガティブ",
    },
    "smart_negative_info": {
        "en": "Automatically apply the best negative prompt for the selected profile (Synced with 🎨 Optimization Profile).",
        "ja": "選択したプロファイルに最適なネガティブプロンプトを自動適用します（🎨 最適化プロファイルと同期）。",
    },
    "custom_base_tags": {
        "en": "🏷️ Custom Base Tags (Smart Placement)",
        "ja": "🏷️ 「特定タグの後」で参照するタグ",
    },
    "custom_base_tags_info": {
        "en": "Comma-separated. Smart placement will insert after the last of these tags found in prompt.",
        "ja": "カンマ区切り。プロンプト内でこれらが見つかった「最後」の地点に挿入します。",
    },
    "active_profile": {
        "en": "🎨 Optimization Profile",
        "ja": "🎨 最適化プロファイル",
    },
    "active_profile_info": {
        "en": "Switch tag priorities based on the target model. Used by '✨ Auto-Optimize Prompt Order'.",
        "ja": "使用するモデルに合わせてプロンプトの優先順序を切り替えます。'✨ プロンプトの並びを自動最適化する' にて使用します。",
    },
    "btn_apply_profile": {
        "en": "Apply Profile Settings",
        "ja": "プロファイルを適用",
    },
    "resize_mode": {
        "en": "📐 Auto-Resize Mode",
        "ja": "📐 画像サイズ自動調整モード",
    },
    "resize_none": {
        "en": "Do not resize (Use WebUI size)",
        "ja": "変更しない (WebUIのサイズを使用)",
    },
    "resize_slider": {
        "en": "▼ Force long edge to slider value",
        "ja": "▼ スライダー設定値に長辺を強制する",
    },
    "resize_512": {
        "en": "▼ Smart Resize: 512~1024 (SD1.5)",
        "ja": "▼ 元サイズ維持: 512〜1024 の範囲に収める (SD1.5)",
    },
    "resize_1024": {
        "en": "▼ Smart Resize: 1024~1536 (SDXL)",
        "ja": "▼ 元サイズ維持: 1024〜1536 の範囲に収める (SDXL)",
    },
    "resize_1536": {
        "en": "▼ Smart Resize: 1536~1792 (High-Res)",
        "ja": "▼ 元サイズ維持: 1536〜1792 の範囲に収める (高画質)",
    },
    "base_resolution": {
        "en": "📏 Base Resolution (Only valid for 'Force long edge')",
        "ja": "📏 ベース解像度（「長辺を強制する」モード時のみ有効）",
    },
    "tab_header": {
        "en": "Random image → Auto-fetch prompts → Feed to img2img",
        "ja": "ランダム画像 → プロンプト自動取得 → img2img へ投入",
    },
    "tab_settings": {
        "en": "⚙️ Settings & Preview",
        "ja": "⚙️ 設定 & プレビュー",
    },
    "h_settings": {
        "en": "### ⚙️ Settings",
        "ja": "### ⚙️ 設定",
    },
    "image_folder": {
        "en": "📁 Image Folder",
        "ja": "📁 画像フォルダ",
    },
    "image_folder_ph": {
        "en": "ex: C:/images/input",
        "ja": "例: C:/images/input",
    },
    "memo_file": {
        "en": "📄 Memo File",
        "ja": "📄 メモファイル",
    },
    "memo_file_ph": {
        "en": "ex: C:/images/memo.txt",
        "ja": "例: C:/images/memo.txt",
    },
    "match_threshold": {
        "en": "🎯 Match Threshold (0.0=Exact, 0.4=Loose)",
        "ja": "🎯 一致率 (0.0=完全一致, 0.4=あいまい)",
    },
    "lora_manager_desc": {
        "en": "Manage lists for random prompts or LoRAs. Each line is picked randomly.",
        "ja": "ランダムに選ばれるプロンプトやLoRAのリストを管理します。1行につき1項目がランダムに選ばれます。"
    },
    "generation_count": {
        "en": "🔄 Generation Count (Internal Batch)",
        "ja": "🔄 生成回数",
    },
    "fallback_enabled": {
        "en": "☑ Fallback Enabled (Use [default] if not matched)",
        "ja": "☑ フォールバック有効 (該当なしで[default]を使用)",
    },
    "auto_lora": {
        "en": "☑ Auto LoRA Injection Enabled",
        "ja": "☑ auto LoRA injection 有効",
    },
    "btn_save": {
        "en": "💾 Save Settings (Global)",
        "ja": "💾 グローバル設定を保存",
    },
    "btn_save_settings": {
        "en": "💾 Save Settings",
        "ja": "💾 設定を保存",
    },
    "btn_save_preset": {
        "en": "💾 Save Preset",
        "ja": "💾 プリセットを保存",
    },
    "btn_delete_preset": {
        "en": "🗑️ Delete",
        "ja": "🗑️ 削除",
    },
    "preset_label": {
        "en": "📦 Presets",
        "ja": "📦 プリセット",
    },
    "preset_ph": {
        "en": "New preset name",
        "ja": "新規プリセット名",
    },
    "lora_offset": {
        "en": "⚖️ Global LoRA Weight Offset",
        "ja": "⚖️ LoRA一括ウェイト微調整",
    },
    "btn_preview": {
        "en": "👁️ Preview",
        "ja": "👁️ プレビュー",
    },
    "status": {
        "en": "Status",
        "ja": "ステータス",
    },
    "h_preview": {
        "en": "### 👁️ Preview Results",
        "ja": "### 👁️ プレビュー結果",
    },
    "selected_image": {
        "en": "Selected Image",
        "ja": "選択画像",
    },
    "positive_prompt": {
        "en": "📝 Positive Prompt",
        "ja": "📝 Positive",
    },
    "negative_prompt": {
        "en": "🚫 Negative Prompt",
        "ja": "🚫 Negative",
    },
    "log": {
        "en": "Log",
        "ja": "ログ",
    },
    "tab_prompt_gen": {
        "en": "🏷️ Auto-Prompt Gen",
        "ja": "🏷️ プロンプト自動生成",
    },
    "prompt_gen_desc": {
        "en": "### 🏷️ Auto generate prompts with WD14 Tagger\nUpload image → Extract tags by categories below → Append to memo file",
        "ja": "### 🏷️ WD14 Tagger で自動プロンプト生成\n画像をアップロード → 選択したカテゴリのタグを抽出 → メモファイルに追記",
    },
    "h_mosaic_settings": {
        "en": "🧱 Mosaic Auto-Prompt Settings",
        "ja": "🧱 モザイクプロンプト自動付与設定",
    },
    "btn_toggle_cat": {
        "en": "Select All / Deselect All",
        "ja": "全選択 / 解除",
    },
    "btn_deselect_all": {
        "en": "❌ Deselect All Categories",
        "ja": "❌ 全カテゴリ選択解除",
    },
    "btn_toggle_all": {
        "en": "🔄 Select/Deselect All",
        "ja": "🔄 全選択/解除",
    },
    "btn_toggle_all_cats": {
        "en": "🔄 Toggle All Categories",
        "ja": "🔄 全カテゴリ 選択/解除",
    },
    "h_extracted_tags": {
        "en": "🏷️ Extracted Tags Only Display",
        "ja": "🏷️ 抽出されたタグのみ表示",
    },
    "gen_custom_dict_enabled": {
        "en": "Enable Custom Prompt Rules",
        "ja": "条件付与ルールを有効にする",
    },
    "h_pickup_limits": {
        "en": "📏 Tag Pickup Limits",
        "ja": "📏 タグ取得上限設定",
    },
    "limit_base_label": {
        "en": "🖼️ Base Group (Composition, BG, etc.)",
        "ja": "🖼️ 基本グループ (構図・背景等)",
    },
    "limit_char_label": {
        "en": "👩 Character Group (Hair, Clothes, etc.)",
        "ja": "👩 人物グループ (髪・服・体等)",
    },
    "limit_nsfw_label": {
        "en": "🔞 NSFW Group (Actions, Items, etc.)",
        "ja": "🔞 NSFWグループ (行為・属性等)",
    },
    "gen_tags_only": {
        "en": "🏷️ Generated Tags Only",
        "ja": "🏷️ 生成されたタグのみ",
    },
    "gen_tags_only_info": {
        "en": "Comma-separated tags (Easy to copy)",
        "ja": "カンマ区切りのタグのみ（コピー用）",
    },
    "target_image": {
        "en": "📸 Target Image",
        "ja": "📸 解析する画像",
    },
    "section_name": {
        "en": "📌 Section Name",
        "ja": "📌 セクション名",
    },
    "section_ph": {
        "en": "ex: title1",
        "ja": "例: タイトル1",
    },
    "section_info": {
        "en": "Becomes [section_name] in memo file",
        "ja": "メモファイルの [セクション名] になる",
    },
    "h_categories": {
        "en": "### 🏷️ Target Categories (Only checked types extracted)",
        "ja": "### 🏷️ 抽出するタグの種類（チェックした種類のタグだけを抽出します）",
    },
    "cat_base": {
        "en": "🖼️ Base (Composition, Backgrounds)",
        "ja": "🖼️ 基本カテゴリ (構図・背景など)",
    },
    "cat_char": {
        "en": "👩 Character Detail (Hair, Clothes)",
        "ja": "👩 人物・詳細カテゴリ (髪型・服装など)",
    },
    "cat_nsfw": {
        "en": "🔞 NSFW & Fetish (Actions, Genitals, Items)",
        "ja": "🔞 特殊・NSFWカテゴリ (行為・局部・アイテム等)",
    },
    "confidence": {
        "en": "🎯 Tag Confidence Threshold",
        "ja": "🎯 タグ信頼度しきい値",
    },
    "confidence_info": {
        "en": "Lower = more tags",
        "ja": "低いほど多くのタグが含まれる",
    },
    "default_positive": {
        "en": "✨ Default Positive",
        "ja": "✨ デフォルトポジティブ",
    },
    "default_positive_info": {
        "en": "Prepended to output",
        "ja": "抽出されたタグの先頭に自動で付与されるベースプロンプト",
    },
    "custom_dict": {
        "en": "📚 Custom Dictionary",
        "ja": "📚 好みのプロンプト置き場（条件付与）",
    },
    "custom_dict_info": {
        "en": "Format: `condition tag > prompt to add` (Added only if condition matched in image)",
        "ja": "「条件タグ > 追加したいプロンプト」の形式で記述 (複数行可)。画像から条件タグが出た時のみ追加されます。",
    },
    "gen_mosaic_auto": {
        "en": "🧱 Mosaic Auto-Prompt",
        "ja": "🧱 モザイク用プロンプトを自動付与",
    },
    "gen_mosaic_level": {
        "en": "🧱 Mosaic Level",
        "ja": "🧱 モザイクの強度",
    },
    "mosaic_low": {"en": "Low", "ja": "薄い"},
    "mosaic_med": {"en": "Med", "ja": "普通"},
    "mosaic_high": {"en": "High", "ja": "厚い"},
    "cat_composition": {"en": "Composition & Camera", "ja": "構図・カメラ"},
    "cat_pose": {"en": "Pose & Action", "ja": "ポーズ・アクション"},
    "cat_background": {"en": "Background & Scene", "ja": "背景・場所"},
    "cat_nature": {"en": "Nature & Weather", "ja": "自然・天候"},
    "cat_lighting": {"en": "Lighting", "ja": "照明"},
    "cat_atmosphere": {"en": "Atmosphere", "ja": "雰囲気"},
    "cat_meta": {"en": "Meta Tags", "ja": "メタタグ"},
    "cat_char_base": {"en": "👤 Character Body & Traits", "ja": "👤 身体・基本特徴"},
    "cat_char_hair": {"en": "💇 Hair Style & Color", "ja": "💇 髪型・髪色"},
    "cat_char_eyes": {"en": "👀 Eyes & Makeup", "ja": "👀 目・メイク"},
    "cat_char_face": {"en": "🎈 Expression", "ja": "🎈 表情"},
    "cat_char_clothes": {"en": "👗 Clothes & Accessories", "ja": "👗 服装・装飾品"},
    "cat_char_male": {"en": "♂️ Male Character", "ja": "♂️ 男性キャラクター"},
    "cat_nsfw_action": {"en": "🎭 Actions", "ja": "🎭 行為・アクション"},
    "cat_nsfw_creature": {"en": "🦑 Creatures", "ja": "🦑 クリーチャー・追加キャラ"},
    "cat_nsfw_item": {"en": "🧸 Toys & Items", "ja": "🧸 アイテム・玩具"},
    "cat_nsfw_focus": {"en": "🔞 Focus & Angles", "ja": "🔞 特殊構図・フォーカス"},
    "cat_nsfw_fluids": {"en": "💦 Fluids & Mess", "ja": "💦 体液・汚れ系"},
    "cat_nsfw_fetish": {"en": "🥵 Fetish States", "ja": "🥵 表情・フェティッシュ状態"},
    "cat_nsfw_clothes_mess": {"en": "👗 Clothes Mess", "ja": "👗 衣服の乱れ・着脱"},
    "cat_nsfw_genitals": {"en": "🍑 Genitals", "ja": "🍑 局部・デリケートゾーン"},
    "cat_nsfw_mosaic": {"en": "🧱 Mosaic & Censor", "ja": "🧱 モザイク・修正"},
    "msg_settings_saved": {"en": "✅ Settings saved", "ja": "✅ 設定を保存しました"},
    "msg_settings_err": {"en": "❌ Failed to save settings:", "ja": "❌ 設定の保存に失敗しました:"},
    "msg_load_err": {"en": "❌ Failed to load image:", "ja": "❌ 画像を読み込めません:"},
    "msg_tagger_err": {"en": "❌ WD14 Tagger API not found. Please ensure the extension is installed.", "ja": "❌ WD14 Tagger の API が見つかりません。Tagger拡張機能がインストールされているか確認してください。"},
    "msg_api_err": {"en": "❌ API request failed:", "ja": "❌ APIリクエスト失敗:"},
    "msg_tagger_not_found": {"en": "❌ Compatible interrogator not found. Tagger model not downloaded or version unsupported.", "ja": "❌ 対応するインタロゲーターが見つかりません。Taggerのモデルがダウンロードされていないか、拡張のバージョンが非対応です。"},
    "msg_tag_fetch_err": {"en": "❌ Tag fetch error:", "ja": "❌ タグ取得エラー:"},
    "msg_no_upload_err": {"en": "❌ Please upload an image", "ja": "❌ 画像をアップロードしてください"},
    "msg_no_section_err": {"en": "❌ Please enter a section name", "ja": "❌ セクション名を入力してください"},
    "msg_no_img_err": {"en": "❌ No image provided", "ja": "❌ 画像部分の指定がありませんでした"},
    "msg_no_tags_err": {"en": "❌ No matching tags found", "ja": "❌ 該当するタグが見つかりませんでした"},
    "msg_memo_appended": {"en": "✅ Appended to memo file", "ja": "✅ メモファイルに追記しました"},
    "msg_memo_err": {"en": "❌ Failed to append:", "ja": "❌ 追記に失敗しました:"},
    "default_negative": {
        "en": "🚫 Default Negative",
        "ja": "🚫 デフォルトネガティブ",
    },
    "default_negative_info": {
        "en": "Appended to output",
        "ja": "自動生成時に追加するネガティブプロンプト",
    },
    "btn_gen_tags": {
        "en": "🏷️ Generate Tags",
        "ja": "🏷️ タグ解析＆生成",
    },
    "btn_send_img2img": {
        "en": "🚀 Send to img2img",
        "ja": "🚀 img2imgへ送信",
    },
    "msg_sent_img2img": {
        "en": "✅ Sent to img2img tab!",
        "ja": "✅ img2imgタブへ転送しました！",
    },
    "btn_append_memo": {
        "en": "📝 Append to Memo",
        "ja": "📝 メモファイルに追記",
    },
    "append_status": {
        "en": "Append Status",
        "ja": "追記ステータス",
    },
    "health_check_ok": {
        "en": "✅ All paths are healthy.",
        "ja": "✅ すべてのパスが正しく設定されています。",
    },
    "health_check_err": {
        "en": "⚠️ Path Error: {path} not found.",
        "ja": "⚠️ パスエラー: {path} が見つかりません。",
    },
    "health_check_title": {
        "en": "🔍 Path Health Check",
        "ja": "🔍 パス設定のヘルスチェック",
    },
    "output_settings": {
        "en": "📂 Output Folder & Sorting Settings",
        "ja": "📂 出力先・自動フォルダ振り分け設定",
    },
    "sort_mode": {
        "en": "📁 Sorting Mode",
        "ja": "📁 振り分けモード",
    },
    "sort_none": {
        "en": "None (WebUI Default)",
        "ja": "なし (WebUIデフォルト)",
    },
    "sort_preset": {
        "en": "By Preset Name",
        "ja": "プリセット名で分ける",
    },
    "sort_section": {
        "en": "By Matched Section Name",
        "ja": "一致したセクション名で分ける",
    },
    "sort_date": {
        "en": "By Date (YYYY-MM-DD)",
        "ja": "日付で分ける (YYYY-MM-DD)",
    },
    "no_images": {
        "en": "❌ No images found in the folder",
        "ja": "❌ 画像フォルダに画像がありません",
    },
    "language_label": {
        "en": "🌐 Language / 言語",
        "ja": "🌐 Language / 言語",
    },
    "log_sel_sequential": {"en": "⬇️ Selected (Sequential {index}/{total}): {filename}", "ja": "⬇️ 選択画像 (順番 {index}/{total}): {filename}"},
    "log_sel_random": {"en": "🎲 Selected (Random): {filename}", "ja": "🎲 選択画像 (ランダム): {filename}"},
    "log_no_sections": {"en": "⚠️ No sections found in memo file", "ja": "⚠️ メモファイルにセクションが見つかりません"},
    "log_sections_count": {"en": "📖 Sections count: {count}", "ja": "📖 メモセクション数: {count}"},
    "log_fallback": {"en": "⚠️ Fallback to [default] section", "ja": "⚠️ 一致しないため [default] セクションへフォールバックします"},
    "log_no_match": {"en": "⚠️ No matching section found", "ja": "⚠️ 一致するセクションが見つかりませんでした"},
    "log_random_lora": {"en": "🎲 Random LoRA applied: {lora}", "ja": "🎲 ランダムLoRA適用: {lora}"},
    "log_match_count": {"en": "✅ Matched sections: {count}", "ja": "✅ 一致セクション数: {count}"},
    "tab_lora_manager": {"en": "🏷️ Prompt & LoRA Manager", "ja": "🏷️ プロンプト&LoRAマネージャー"},
    "tab_inventory": {"en": "📦 Inventory Logic", "ja": "📦 在庫管理"},
    "inventory_desc": {"en": "Manage how often specific prompts are picked to ensure diversity. Records how many times each item was selected and prioritizes less used items.", "ja": "使用回数の偏りを防ぎ、バリエーション豊かな生成を支援します。各項目の選択回数を記録し、使用頻度の低いものを優先的に選出します。"},
    "inventory_status_label": {"en": "📊 Current Stock Status", "ja": "📊 現在の在庫（使用回数）状況"},
    "lora_type": {"en": "LoRA Category", "ja": "LoRAカテゴリ"},
    "lora_type_char": {"en": "Character", "ja": "キャラクター"},
    "lora_type_sit": {"en": "Situation", "ja": "シチュエーション"},
    "lora_list_label": {"en": "LoRA List (one per line)", "ja": "LoRAリスト（1行に1つ）"},
    "lora_input_label": {"en": "New LoRA entry", "ja": "1件ずつ追加"},
    "btn_append_lora": {"en": "➕ Append to List", "ja": "➕ リストに追記"},
    "btn_save_lora_list": {"en": "💾 Save List", "ja": "💾 リストを保存"},
    "msg_lora_saved": {"en": "LoRA list saved!", "ja": "LoRAリストを保存しました。"},
    "msg_lora_appended": {"en": "Appended!", "ja": "追記しました！"},
    "enable_random_char": {"en": "🎲 Random Character LoRA", "ja": "🎲 キャラLoRAをランダム適用"},
    "enable_random_sit": {"en": "🎲 Random Situation LoRA", "ja": "🎲 シチュLoRAをランダム適用"},
    "log_all_tags": {"en": "📊 Total tags: {count}", "ja": "📊 全タグ数: {count}"},
    "log_filtered_tags": {"en": "✅ Filtered: {count}", "ja": "✅ フィルタ後: {count}"},
    "log_excluded_tags": {"en": "🗑️ Excluded: {count}", "ja": "🗑️ 除外タグ数: {count}"},
    "log_custom_match": {"en": "🎯 Custom match: [{cond}] => Added: {prompt}", "ja": "🎯 条件マッチ: [{cond}] => 追加: {prompt}"},
    "log_no_pos_prompt": {"en": "⚠️ No valid positive prompt", "ja": "⚠️ 有効なポジティブプロンプトがありません"},
    "generated_entry": {
        "en": "📋 Generated Entry (editable)",
        "ja": "📋 生成されたエントリ（編集可能）",
    },
    "generated_entry_info": {
        "en": "Review and edit before appending to memo file",
        "ja": "メモファイルへ追記する前に確認・編集してください",
    },
    "analysis_log": {
        "en": "Analysis Log",
        "ja": "解析ログ"
    },
    "tab_usage": {"en": "📖 Usage", "ja": "📖 使い方"},
    "usage_md": {
        "en": (
            "## 📖 User Manual (v1.1)\n\n"
            "### 1. Basic Flow\n"
            "1. Set your **📁 Image Folder** and **📄 Memo File** paths in the Settings tab.\n"
            "2. In the **img2img** tab, open **🎲 Smart Composer** and check **Enable**.\n"
            "3. Click **Generate**. The script will pick a random image and its matching prompt from your memo file.\n\n"
            "### 2. Memo File Format\n"
            "```text\n"
            "[beach]\n"
            "positive: 1girl, swimming, sea, sunset\n"
            "negative: lowres, blurry\n\n"
            "[forest]\n"
            "1girl, standing in woods, trees, bird\n"
            "```\n"
            "- `[title]` matches image filenames (e.g. `beach_01.png` matches `[beach]`).\n"
            "- If `positive:`/`negative:` are missing, the whole block is positive.\n"
            "- Empty sections will fallback to the `[default]` section.\n\n"
            "### 3. v1.1.2 New Features\n"
            "- **📦 Inventory Logic Tab**: A dedicated tab to manage randomization. Records how many times each item was selected and prioritizes less used items. You can check stock status and reset records here.\n"
            "- **🚀 Enhanced img2img Transfer**: The 'Send to img2img' button in the Auto-Prompt Gen tab now transfers both **Prompts and the Image** itself directly to the main generation tab.\n"
            "- **📏 Tag Pickup Limits**: Set individual limits for Base, Character, and NSFW tag groups during auto-generation to prevent prompt overflow.\n"
            "- **🧱 Mosaic Auto-Prompt**: Automatically detect mosaic/censoring in images and apply appropriate weight-adjusted tags.\n\n"
            "### 4. Advanced Features\n"
            "- **📦 Presets**: Save all settings (paths, thresholds, limits, etc.) as named presets for quick switching.\n"
            "- **⚖️ LoRA Weight Adjustment**: Use the slider to offset all LoRA weights in your prompts collectively.\n"
            "- **📁 Output Sorting**: Automatically organize generated images into subfolders named by Preset, Section, or Date.\n"
            "- **🔍 Health Check**: Invalid paths will show a ❌ mark on their labels.\n"
            "- **🏷️ LoRA Manager**: Manage your character/situation LoRA lists easily."
        ),
        "ja": (
            "## 📖 ユーザーマニュアル (v1.1)\n\n"
            "### 1. 基本的な使い方\n"
            "1. **⚙️ 設定** タブで **📁 画像フォルダ** と **📄 メモファイル** のパスを指定します。\n"
            "2. **img2img** タブ内の **🎲 Smart Composer** アコーディオンを開き、**有効化** にチェックを入れます。\n"
            "3. **Generate** をクリックすると、画像とプロンプトが自動的に送り込まれます。\n\n"
            "### 2. メモファイルの書き方\n"
            "```text\n"
            "[タイトル1]\n"
            "positive: 1girl, 笑顔, 公園\n"
            "negative: 低品質, ぼけ\n\n"
            "[タイトル2]\n"
            "1girl, 立ち姿, 部屋, 夜\n"
            "```\n"
            "- `[タイトル]` 部分が画像ファイル名と部分一致（あいまい検索）します。\n"
            "- `positive:` / `negative:` を省略すると、そのブロック全体がポジティブ扱いになります。\n"
            "- 内容が空のセクションは、自動的に `[default]` セクションの設定へ飛ばされます。\n\n"
            "### 3. v1.1.2 新機能\n"
            "- **📦 在庫管理タブ**: ランダム選出の偏りを防ぐための専用タブです。どのLoRAやワイルドカードが何回選ばれたかを記録し、使用頻度の低いものを優先します。在庫状況の確認やリセットもここで行えます。\n"
            "- **🚀 img2img 連携の強化**: プロンプト自動生成タブの「img2imgへ送信」ボタンが、**プロンプトと画像の両方**をメインタブへ直接転送するようになりました。\n"
            "- **📏 カテゴリ別上限設定**: 自動生成時に「基本」「人物」「NSFW」の各カテゴリごとに抽出するタグの上限数を個別に設定できるようになりました。\n"
            "- **🧱 モザイク自動抽出**: 画像内のモザイクや修正を自動検出し、適切な強度のプロンプトを自動付与します。\n\n"
            "### 4. 便利な機能\n"
            "- **📦 プリセット**: 各パスや上限設定、しきい値などを名前を付けて保存し、一瞬で切り替えられます。\n"
            "- **⚖️ LoRA一括ウェイト微調整**: プロンプトに含まれる全てのLoRAの重みを一律に増減できます。\n"
            "- **📁 自動フォルダ振り分け**: 生成画像を「プリセット名」「セクション名」「日付」ごとに自動整理します。\n"
            "- **🔍 ヘルスチェック**: パスが無効な場合、入力欄のラベルに ❌ が表示されます。\n"
            "- **🏷️ LoRAマネージャー**: キャラクターやシチュエーションごとのLoRAリストを簡単に管理できます。"
        )
    },
    "lora_unsaved_warning": {
        "en": "⚠️ Unsaved changes detected. Save before switching?",
        "ja": "⚠️ 未保存の変更があります。切り替える前に保存しますか？",
    },
    "lora_mgr_placeholder": {
        "en": "Loading...",
        "ja": "読み込み中...",
    },
    "tab_smart_negative": {"en": "🚫 Smart Negative", "ja": "🚫 スマート・ネガティブ"},
    "sn_mode_add": {"en": "Append", "ja": "末尾に追加"},
    "sn_mode_overwrite": {"en": "Overwrite", "ja": "上書き"},
    "btn_check_stock": {"en": "📊 Check Stock", "ja": "📊 在庫を確認"},
    "btn_global_reset": {"en": "🧹 Global Reset", "ja": "🧹 全在庫リセット"},
    "btn_lora_reset": {"en": "🏷️ LoRA Reset", "ja": "🏷️ LoRA在庫のみリセット"},
    "h_inventory_settings": {"en": "### 📦 Inventory Logic Settings", "ja": "### 📦 在庫管理 (Inventory) 設定"},
    "inventory_mode": {"en": "Enable Inventory System", "ja": "在庫管理システムを有効にする"},
    "inventory_mode_info": {"en": "Prioritize selecting less used LoRAs/wildcards.", "ja": "使用回数の少ないLoRAやワイルドカードを優先的に選出します。"},
    "msg_inventory_reset": {"en": "Inventory records reset.", "ja": "在庫記録をリセットしました。"},
    "msg_all_saved": {"en": "All settings saved.", "ja": "すべての設定を保存しました。"},
}

_lang_cache = None

def _get_lang() -> str:
    global _lang_cache
    if _lang_cache is not None:
        return _lang_cache
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                _lang_cache = json.load(f).get("language", "ja")
                return _lang_cache
    except Exception:
        pass
    return "ja"

def invalidate_lang_cache():
    global _lang_cache
    _lang_cache = None

def t(key: str) -> str:
    lang = _get_lang()
    entry = _I18N.get(key, {})
    return entry.get(lang, entry.get("en", key))
