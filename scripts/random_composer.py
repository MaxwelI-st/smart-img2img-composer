# -*- coding: utf-8 -*-
"""
Random Img2Img Composer
AUTOMATIC1111 Stable Diffusion WebUI 拡張機能 v1.0 (Stable)

img2img生成時に、指定フォルダからランダム画像を選択し、
メモファイルから対応プロンプト（positive/negative）を自動取得して投入する。
WD14 Tagger連携でプロンプトの自動生成も可能。

【v1.0 修正内容】
- Release: 正式版 v1.0 リリース
- UI/UX: 全カテゴリの「一括選択/解除」ボタンを実装
- UI/UX: 有用性の高い「基本」カテゴリのみアコーディオンをデフォルト開に設定
- Logic: v2.4.3 までの全修正と安定化ロジックを統合
"""

import os
import sys
import json
import random
import re
import traceback
import difflib
import gradio as gr
from PIL import Image

try:
    import yaml
except ImportError:
    yaml = None

from modules import script_callbacks, processing, scripts

# ======================================================================
# 定数
# ======================================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXTENSION_DIR = os.path.dirname(BASE_DIR)

CONFIG_PATH = os.path.join(EXTENSION_DIR, "config.json")
LORA_CHAR_PATH = os.path.join(EXTENSION_DIR, "lora_char.txt")
LORA_SIT_PATH = os.path.join(EXTENSION_DIR, "lora_sit.txt")
WILD_1_PATH = os.path.join(EXTENSION_DIR, "wildcard_1.txt")
WILD_2_PATH = os.path.join(EXTENSION_DIR, "wildcard_2.txt")
WILD_3_PATH = os.path.join(EXTENSION_DIR, "wildcard_3.txt")

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
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}

# ======================================================================
# i18n 翻訳辞書
# ======================================================================

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
    # --- 独立タブ: 設定 & プレビュー ---
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
    # --- 独立タブ: プロンプト自動生成 ---
    "tab_prompt_gen": {
        "en": "🏷️ Auto-Prompt Gen",
        "ja": "🏷️ プロンプト自動生成",
    },
    "prompt_gen_desc": {
        "en": "### 🏷️ Auto generate prompts with WD14 Tagger\nUpload image → Extract scene/pose/composition tags ONLY → Append to memo file\n\n**(Character traits and clothes are automatically EXCLUDED)**",
        "ja": "### 🏷️ WD14 Tagger で自動プロンプト生成\n画像をアップロード → シーン/ポーズ/構図のタグだけ抽出 → メモファイルに追記\n\n**服装・人物特徴は自動除外されます。**",
    },
    # Refactor #1: 二重定義を解消 - このキーは旧来の短いラベル（未使用）だったため削除
    # UI 側では h_categories（2つ目の定義 = ### 付きフル版）を使用する
    "h_mosaic_settings": {
        "en": "🧱 Mosaic Auto-Prompt Settings",
        "ja": "🧱 モザイクプロンプト自動付与設定",
    },
    "btn_deselect_all": {
        "en": "❌ Deselect All Categories",
        "ja": "❌ 全カテゴリ選択解除",
    },
    "btn_toggle_all": {
        "en": "🔄 Select/Deselect All",
        "ja": "🔄 全選択/解除",
    },
    # UI Fix #1: btn_toggle_all_cats が _I18N に未定義だったためキー名がそのまま表示されていた
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
    # --- タグカテゴリ名 ---
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
    # --- 関数戻り値メッセージ ---
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
        "ja": "🚀 img2imgに送る",
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
    # --- 言語設定UI ---
    "language_label": {
        "en": "🌐 Language / 言語",
        "ja": "🌐 Language / 言語",
    },
    # --- ログメッセージ ---
    "log_sel_sequential": {"en": "⬇️ Selected (Sequential {index}/{total}): {filename}", "ja": "⬇️ 選択画像 (順番 {index}/{total}): {filename}"},
    "log_sel_random": {"en": "🎲 Selected (Random): {filename}", "ja": "🎲 選択画像 (ランダム): {filename}"},
    "log_no_sections": {"en": "⚠️ No sections found in memo file", "ja": "⚠️ メモファイルにセクションが見つかりません"},
    "log_sections_count": {"en": "📖 Sections count: {count}", "ja": "📖 メモセクション数: {count}"},
    "log_fallback": {"en": "⚠️ Fallback to [default] section", "ja": "⚠️ 一致しないため [default] セクションへフォールバックします"},
    "log_no_match": {"en": "⚠️ No matching section found", "ja": "⚠️ 一致するセクションが見つかりませんでした"},
    "log_random_lora": {"en": "🎲 Random LoRA applied: {lora}", "ja": "🎲 ランダムLoRA適用: {lora}"},
    "log_match_count": {"en": "✅ Matched sections: {count}", "ja": "✅ 一致セクション数: {count}"},
    "tab_lora_manager": {"en": "🏷️ Prompt & LoRA Manager", "ja": "🏷️ プロンプト&LoRAマネージャー"},
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
    # --- Bug Fix: 翻訳キー追加 (generated_entry, analysis_log) ---
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
    # --- 使い方タブ ---
    "tab_usage": {"en": "📖 Usage", "ja": "📖 使い方"},
    "usage_md": {
        "en": (
            "## 📖 User Manual (v1.0 Stable)\n\n"
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
            "### 3. Advanced Features\n"
            "- **📦 Presets**: Save all settings (paths, thresholds, etc.) as named presets for quick switching.\n"
            "- **⚖️ LoRA Weight Adjustment**: Use the slider to offset all LoRA weights in your prompts collectively (e.g., -0.1 to weaken all).\n"
            "- **📁 Output Sorting**: Automatically organize generated images into subfolders named by Preset, Section, or Date.\n"
            "- **🔍 Health Check**: Invalid paths will show a ❌ mark on their labels. Empty paths are ignored.\n"
            "- **🏷️ LoRA Manager**: Manage your character/situation LoRA lists. Unsaved changes trigger a warning dialog.\n"
            "- **🎲 Asset Slots**: Use multiple folders as random sources by enabling extra slots.\n\n"
            "### 4. Integration\n"
            "- **WD14 Tagger**: Use the 'Auto-Prompt Gen' tab to analyze images and append tags to your memo file.\n"
            "- **Dynamic Prompts**: Supports `__wildcards__` and `{A|B}` syntax within the memo file."
        ),
        "ja": (
            "## 📖 ユーザーマニュアル (v1.0 Stable)\n\n"
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
            "### 3. 便利な機能\n"
            "- **📦 プリセット**: 各パスや設定値を名前を付けて保存し、一瞬で切り替えられます。\n"
            "- **⚖️ LoRA一括ウェイト微調整**: プロンプトに含まれる全てのLoRAの重みをスライサーで一律に増減（例：全体的に少し弱める等）できます。\n"
            "- **📁 自動フォルダ振り分け**: 生成画像を「プリセット名」「セクション名」「日付」ごとのサブフォルダに自動で整理して保存します。\n"
            "- **🔍 ヘルスチェック**: パスが無効な場合、各入力欄のラベルに ❌ が表示されます。未入力（空欄）の場合は警告されません。\n"
            "- **🏷️ LoRAマネージャー**: キャラクターやシチュエーションごとのLoRAリストを管理できます。未保存で切り替えようとすると警告が出ます。\n"
            "- **🎲 アセットスロット**: 複数の画像フォルダをランダムソースとして併用したい場合にスロットを有効化して使用します。\n\n"
            "### 4. 外部機能連携\n"
            "- **WD14 Tagger**: 「プロンプト自動生成」タブで画像を解析し、その場でメモファイルへタグを追記できます。\n"
            "- **Dynamic Prompts**: メモファイル内で `__wildcard__` や `{A|B}` などの構文がそのまま利用可能です。"
        )
    },
    # --- UI/UX: LoRAマネージャー未保存警告 ---
    "lora_unsaved_warning": {
        "en": "⚠️ Unsaved changes detected. Save before switching?",
        "ja": "⚠️ 未保存の変更があります。切り替える前に保存しますか？",
    },
    "lora_mgr_placeholder": {
        "en": "Loading...",
        "ja": "読み込み中...",
    },
}


# ======================================================================
# 言語キャッシュ管理 (Bug Fix: 二重定義を解消し1か所に統合)
# ======================================================================

_lang_cache = None


def _get_lang() -> str:
    """config.jsonからlanguage設定を読み取る (デフォルト: ja)"""
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
    """翻訳キーを現在の言語に変換して返す"""
    lang = _get_lang()
    entry = _I18N.get(key, {})
    return entry.get(lang, entry.get("en", key))


# ======================================================================
# 設定管理
# ======================================================================

def _clean_path(path: str) -> str:
    """パスの前後から空白や引用符を削除する"""
    if not path or not isinstance(path, str):
        return ""
    return path.strip().strip('"').strip("'").strip()


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = {**DEFAULT_CONFIG, **json.load(f)}
                for k in ["image_folder", "memo_file", "wildcard_1_path", "wildcard_2_path", "wildcard_3_path"]:
                    if k in config and isinstance(config[k], str):
                        config[k] = _clean_path(config[k])
                return config
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> str:
    """設定をconfig.jsonに保存し、キャッシュをクリアする"""
    try:
        dir_path = os.path.dirname(CONFIG_PATH)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        # Refactor #2: _lang_cache の直接操作を廃止し invalidate_lang_cache() に統一
        invalidate_lang_cache()
        return t("msg_settings_saved")
    except IOError as e:
        return f"{t('msg_settings_err')} {e}"


def check_individual_health(image_folder, memo_file, w1, w2, w3):
    """
    パスの生存確認を行い、各コンポーネント用の gr.update を返す。
    空欄（未入力）の場合はエラーとせず、正常（✅なし）として扱う。
    """
    def get_status(path, ptype, label_base):
        path = _clean_path(path)
        if not path:
            return gr.update(label=label_base, info="")
        
        exists = False
        if ptype == "dir":
            exists = os.path.isdir(path)
        elif ptype == "file":
            exists = os.path.isfile(path)
        else:
            exists = os.path.exists(path)
        
        if not exists:
            # 威圧感を抑えつつ、❌マークとinfoで警告
            return gr.update(label=f"❌ {label_base}", info=f"⚠️ {t('health_check_err').format(path=path)}")
        else:
            return gr.update(label=f"✅ {label_base}", info="")

    return (
        get_status(image_folder, "dir", t("image_folder")),
        get_status(memo_file, "file", t("memo_file")),
        get_status(w1, "any", t("wildcard_1")),
        get_status(w2, "any", t("wildcard_2")),
        get_status(w3, "any", t("wildcard_3")),
    )


# ======================================================================
# メモファイル解析（positive / negative 対応）
# ======================================================================

def parse_memo_file(memo_path: str) -> dict:
    """
    メモファイルを解析する。
    戻り値: { セクション名: {"positive": "...", "negative": "...", "lora": [...]} }
    """
    memo_path = _clean_path(memo_path)
    sections = {}
    if not memo_path or not os.path.isfile(memo_path):
        if memo_path:
            print(f"[Smart Img2Img Composer] Memo file not found: {memo_path}")
        return sections

    current_key = None
    current_mode = "positive"
    current_positive = []
    current_negative = []
    current_lora = []

    def save_section():
        nonlocal current_key, current_positive, current_negative, current_lora
        if current_key is None:
            return
        pos = _join_lines(current_positive)
        neg = _join_lines(current_negative)
        lora = current_lora[:]
        if pos or neg or lora:
            sections[current_key] = {"positive": pos, "negative": neg, "lora": lora}

    try:
        content = ""
        try:
            with open(memo_path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(memo_path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            except Exception:
                with open(memo_path, "r", encoding="cp932", errors="ignore") as f:
                    content = f.read()
        except Exception:
            return sections

        for line in content.splitlines():
            stripped = line.strip()

            if stripped.startswith("#"):
                continue

            match = re.match(r"^\[(.+)\]\s*$", stripped)
            if match:
                save_section()
                current_key = match.group(1).strip().lower()
                current_mode = "positive"
                current_positive = []
                current_negative = []
                current_lora = []
                continue

            if stripped.lower() in ("positive:", "positive"):
                current_mode = "positive"
                continue
            if stripped.lower() in ("negative:", "negative"):
                current_mode = "negative"
                continue
            if stripped.lower() in ("lora:", "lora"):
                current_mode = "lora"
                continue

            if current_key is not None and stripped:
                if current_mode == "negative":
                    current_negative.append(stripped)
                elif current_mode == "lora":
                    current_lora.append(stripped)
                else:
                    current_positive.append(stripped)

        save_section()
    except Exception as e:
        print(f"[Smart Img2Img Composer] Memo parse error: {e}")

    return sections


def _join_lines(lines: list) -> str:
    if not lines:
        return ""
    combined = ", ".join(lines)
    parts = [p.strip() for p in combined.split(",") if p.strip()]
    return ", ".join(parts)


# ======================================================================
# コアロジック
# ======================================================================

def get_image_files(folder: str) -> list:
    folder = _clean_path(folder)
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if (os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
            and not f.startswith(".")
            and "config" not in f.lower()
            and "memo" not in f.lower())
    ]


def match_image_to_sections(image_path: str, sections: dict, threshold: float) -> list:
    """difflib.SequenceMatcherを使用して、ファイル名に最も類似したプロンプトセクションを特定する"""
    if not image_path or not sections:
        return []

    from difflib import SequenceMatcher
    filename = os.path.splitext(os.path.basename(image_path))[0].lower()

    best_matches = []
    max_score = 0

    for section in sections.keys():
        if section.lower() == "default":
            continue

        score = SequenceMatcher(None, filename, section.lower()).ratio()

        if score >= threshold:
            if score > max_score:
                max_score = score
                best_matches = [section]
            elif score == max_score:
                best_matches.append(section)

    if best_matches:
        target_section = best_matches[0]
        return [sections[target_section]]

    return []


def check_lora_exists(lora_str: str) -> bool:
    """
    LoRAが実際にインストールされているか確認する。
    Bug Fix: lora_registry.items() を正しくメソッド呼び出しするよう修正。
    """
    try:
        from modules import extra_networks
        raw = lora_str.replace("<", "").replace(">", "")
        if ":" not in raw:
            return False
        parts = raw.split(":")
        lora_name = parts[1].strip() if parts[0].lower() == "lora" else parts[0].strip()

        registry = getattr(extra_networks, "extra_network_registry", {})
        lora_registry = registry.get("lora")
        if lora_registry and hasattr(lora_registry, "items"):
            # Bug Fix: .items はメソッドであり dict ではない → .items() を呼び出す
            # または networks モジュールから直接検索する
            try:
                items_dict = lora_registry.items()
                return lora_name in dict(items_dict)
            except TypeError:
                # items が dict の場合 (属性として定義されている場合)
                return lora_name in lora_registry.items
        return False
    except (ImportError, KeyError, AttributeError):
        return False


def _clean_prompt(prompt: str) -> str:
    """カンマ区切りのプロンプトから重複を削除し、クリーニングする"""
    if not prompt:
        return ""
    parts = [p.strip() for p in prompt.split(",")]
    seen = set()
    unique = []
    for p in parts:
        if p and p.lower() not in seen:
            seen.add(p.lower())
            unique.append(p)
    return ", ".join(unique)


def get_random_asset(path: str) -> str:
    """指定されたテキストファイルからランダムに1行選んで返す"""
    path = _clean_path(path)
    if not path:
        return ""
    if not os.path.exists(path):
        print(f"[Smart Img2Img Composer] Asset file not found: {path}")
        return ""
    try:
        content = ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(path, "r", encoding="utf-8-sig") as f:
                    content = f.read()
            except Exception:
                with open(path, "r", encoding="cp932", errors="ignore") as f:
                    content = f.read()

        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith("#")]
        if not lines:
            return ""

        row = random.choice(lines)
        if ":" in row:
            row = re.sub(r"(:)(\d+\.\d+)\.\d+(\)|>)", r"\1\2\3", row)
        return row
    except Exception as e:
        print(f"[Smart Img2Img Composer] Asset load error ({path}): {e}")
        return ""


def compose_prompt(image_folder: str, memo_file: str, match_threshold: float, selection_mode="Random") -> tuple:
    """戻り値: (画像パス, positive, negative, ログ, matched_section_name)"""
    log = []
    config = load_config()
    fallback_enabled = config.get("fallback_enabled", True)
    auto_lora_enabled = config.get("auto_lora_enabled", True)

    image_files = get_image_files(image_folder)
    if not image_files:
        return None, "", "", t("no_images"), ""

    if selection_mode == "sequential":
        last_index = config.get("last_sequential_index", 0)
        index = last_index % len(image_files)
        selected = image_files[index]
        config["last_sequential_index"] = index + 1
        save_config(config)
        log.append(t("log_sel_sequential").format(index=index + 1, total=len(image_files), filename=os.path.basename(selected)))
    else:
        selected = random.choice(image_files)
        log.append(t("log_sel_random").format(filename=os.path.basename(selected)))

    print(f"[Smart Img2Img Composer] Selected image: {selected}")

    sections = parse_memo_file(memo_file)
    if not sections:
        log.append(t("log_no_sections"))
        return selected, "", "", "\n".join(log), ""

    log.append(t("log_sections_count").format(count=len(sections)))
    matched = match_image_to_sections(selected, sections, match_threshold)

    # Bug Fix: matched_section_name を追跡して before_process で使えるようにする
    matched_section_name = ""

    if not matched:
        if fallback_enabled and "default" in sections:
            print(f"[Smart Img2Img Composer] No match for {os.path.basename(selected)}. Fallback to [default].")
            log.append(t("log_fallback"))
            matched = [sections["default"]]
            matched_section_name = "default"
        else:
            print(f"[Smart Img2Img Composer] No match for {os.path.basename(selected)}. (Match failed)")
            log.append(t("log_no_match"))
            return selected, "", "", "\n".join(log), ""
    else:
        # マッチしたセクション名を取得
        filename = os.path.splitext(os.path.basename(selected))[0].lower()
        from difflib import SequenceMatcher
        for section in sections.keys():
            if section == "default":
                continue
            score = SequenceMatcher(None, filename, section.lower()).ratio()
            if score >= match_threshold:
                matched_section_name = section
                break

    final_matched = []
    for m in matched:
        if m.get("positive") or m.get("negative") or m.get("lora"):
            final_matched.append(m)

    if not final_matched:
        if fallback_enabled and "default" in sections:
            print(f"[Smart Img2Img Composer] Matched section is empty. Fallback to [default].")
            log.append(t("log_fallback"))
            final_matched = [sections["default"]]
            matched_section_name = "default"
        else:
            log.append(t("log_no_match"))
            return selected, "", "", "\n".join(log), ""

    pos_parts, neg_parts, lora_parts = [], [], []
    seen_pos, seen_neg, seen_lora = set(), set(), set()
    for m in final_matched:
        p = m.get("positive", "")
        n = m.get("negative", "")
        l_list = m.get("lora", [])
        if p and p not in seen_pos:
            seen_pos.add(p)
            pos_parts.append(p)
        if n and n not in seen_neg:
            seen_neg.add(n)
            neg_parts.append(n)
        for l_item in l_list:
            if l_item and l_item not in seen_lora:
                seen_lora.add(l_item)
                if auto_lora_enabled:
                    if check_lora_exists(l_item):
                        lora_parts.append(f"<lora:{l_item}>")
                    else:
                        parts = l_item.split(":")
                        log.append(f"LoRA not found: {parts[0].strip()}")

    if lora_parts:
        pos_parts = lora_parts + pos_parts

    positive = _clean_prompt(", ".join(pos_parts))
    negative = _clean_prompt(", ".join(neg_parts))

    log.append(t("log_match_count").format(count=len(matched)))
    if positive:
        log.append(f"📝 Positive: {positive}")
    if negative:
        log.append(f"🚫 Negative: {negative}")

    return selected, positive, negative, "\n".join(log), matched_section_name


# ======================================================================
# UI ヘルパー
# ======================================================================

def preview_compose(image_folder, memo_file, match_threshold):
    config = load_config()
    selected, positive, negative, log_str, _ = compose_prompt(
        image_folder, memo_file, match_threshold
    )

    log = [log_str] if log_str else []

    asset_slots = [
        (config.get("enable_random_char", False), LORA_CHAR_PATH, config.get("pos_char", "Back"), "Char"),
        (config.get("enable_random_sit", False), LORA_SIT_PATH, config.get("pos_sit", "Back"), "Sit"),
        (config.get("enable_random_w1", False), config.get("wildcard_1_path", WILD_1_PATH), config.get("pos_w1", "Back"), "W1"),
        (config.get("enable_random_w2", False), config.get("wildcard_2_path", WILD_2_PATH), config.get("pos_w2", "Back"), "W2"),
        (config.get("enable_random_w3", False), config.get("wildcard_3_path", WILD_3_PATH), config.get("pos_w3", "Back"), "W3"),
    ]

    f_assets, b_assets, asset_logs = [], [], []
    for en, path, pos, name in asset_slots:
        if en:
            line = get_random_asset(path)
            if line:
                if pos == t("pos_front") or pos == "Front":
                    f_assets.insert(0, line)
                else:
                    b_assets.append(line)
                asset_logs.append(f"{name}: {line}")

    if asset_logs:
        log.append(f"🎲 Preview Assets: {' | '.join(asset_logs)}")

        parts = []
        if f_assets:
            parts.append(", ".join(f_assets))
        if positive:
            parts.append(positive)
        if b_assets:
            parts.append(", ".join(b_assets))
        positive = ", ".join(parts)

    img = None
    if selected and os.path.isfile(selected):
        try:
            img = Image.open(selected)
        except Exception:
            pass
    return img, positive, negative, "\n".join(log)


def save_all_settings(language, image_folder, memo_file, match_threshold, generation_count, fallback, auto_lora,
                      gen_confidence, gen_positive, gen_negative, gen_custom, cat_base, cat_char, cat_nsfw,
                      w1_path, w2_path, w3_path, lora_offset, output_sort_mode,
                      gen_mosaic_auto=False, gen_mosaic_level="Mosaic Med", gen_custom_dict_enabled=True):
    config = load_config()
    categories = cat_base + cat_char + cat_nsfw
    config.update({
        "language": language,
        "image_folder": _clean_path(image_folder),
        "memo_file": _clean_path(memo_file),
        "match_threshold": match_threshold,
        "generation_count": int(generation_count),
        "fallback_enabled": fallback,
        "auto_lora_enabled": auto_lora,
        "gen_confidence": gen_confidence,
        "gen_positive": gen_positive,
        "gen_negative": gen_negative,
        "gen_custom_dict": gen_custom,
        "gen_categories": categories,
        "wildcard_1_path": _clean_path(w1_path),
        "wildcard_2_path": _clean_path(w2_path),
        "wildcard_3_path": _clean_path(w3_path),
        "lora_offset": float(lora_offset) if lora_offset is not None else 0.0,
        "output_sort_mode": output_sort_mode,
        "gen_mosaic_auto": gen_mosaic_auto,
        "gen_mosaic_level": gen_mosaic_level,
        "gen_custom_dict_enabled": gen_custom_dict_enabled,
    })
    return save_config(config)


# ======================================================================
# WD14 Tagger 連携 — タグフィルタリング
# ======================================================================

_TAG_CATEGORIES = {
    "cat_composition": {
        "portrait", "upper_body", "lower_body", "full_body",
        "cowboy_shot", "close-up", "wide_shot", "medium_shot",
        "head_shot", "bust_shot", "knee_shot", "profile", "three-quarter_view",
        "from_above", "from_below", "from_behind", "from_side",
        "from_outside", "dutch_angle", "tilted_frame",
        "pov", "first-person_view", "over-shoulder_shot",
        "bird's-eye_view", "worm's-eye_view", "aerial_view",
        "looking_at_viewer", "looking_away", "looking_back",
        "looking_down", "looking_up", "looking_to_the_side",
        "looking_afar", "looking_at_another",
        "facing_away", "facing_viewer", "rotated",
    },
    "cat_pose": {
        "standing", "sitting", "lying", "walking", "running",
        "jumping", "crouching", "kneeling", "leaning",
        "leaning_forward", "leaning_back",
        "arms_up", "arms_behind_back", "arms_behind_head",
        "hand_on_hip", "hand_on_own_chest", "hand_on_own_face",
        "hands_on_hips", "hand_up", "hands_up",
        "crossed_arms", "hands_in_pockets",
        "outstretched_arm", "outstretched_arms",
        "reaching", "reaching_out", "pointing", "pointing_at_viewer",
        "spread_arms", "stretching", "waving",
        "v", "peace_sign", "thumbs_up", "double_v",
        "on_back", "on_stomach", "on_side",
        "legs_crossed", "indian_style", "seiza", "wariza",
        "legs_apart", "legs_together",
        "one_knee", "squatting", "head_tilt", "head_rest",
        "arched_back", "fetal_position", "hugging_own_legs",
        "lying_on_back", "lying_on_stomach", "lying_on_side",
        "sitting_on_chair", "sitting_on_floor", "sitting_on_bench",
        "standing_on_one_leg", "contrapposto",
        "back-to-back", "arm_support", "chin_rest",
        "holding", "carrying",
        "dancing", "fighting_stance", "battle_stance",
        "action", "dynamic_pose", "floating",
        "falling", "spinning", "twisting",
    },
    "cat_background": {
        "outdoors", "indoors", "cityscape", "landscape", "scenery",
        "city", "town", "village", "suburb",
        "sky", "blue_sky", "cloudy_sky", "starry_sky", "night_sky",
        "cloud", "clouds", "sunset", "sunrise", "twilight", "dawn", "dusk",
        "night", "day", "evening", "morning", "afternoon",
        "forest", "woods", "jungle", "mountain", "hill", "cliff", "valley",
        "ocean", "sea", "beach", "shore", "coast",
        "river", "lake", "pond", "waterfall", "stream",
        "field", "meadow", "grassland", "plains",
        "garden", "park", "playground",
        "street", "road", "path", "alley", "sidewalk",
        "school", "classroom", "library", "gym",
        "office", "workplace", "studio",
        "bedroom", "kitchen", "bathroom", "living_room",
        "dining_room", "hallway", "corridor",
        "rooftop", "balcony", "veranda", "patio", "terrace",
        "window", "door", "doorway",
        "castle", "palace", "mansion",
        "temple", "shrine", "church", "cathedral",
        "ruins", "dungeon", "cave", "cavern",
        "bridge", "stairs", "staircase", "escalator",
        "train", "train_interior", "train_station", "platform",
        "bus", "bus_interior", "bus_stop", "car", "car_interior",
        "ship", "boat", "dock", "harbor", "port",
        "airport", "airplane", "airplane_interior",
        "restaurant", "cafe", "bar", "shop", "store",
        "hospital", "prison", "factory",
        "arena", "stadium", "stage", "theater",
        "space", "planet", "moon", "stars",
        "underwater", "floating_island",
        "marketplace", "bazaar", "festival",
        "cemetery", "graveyard",
        "tower", "lighthouse", "windmill",
        "fountain", "statue", "monument",
        "desert", "oasis", "wasteland", "swamp",
        "volcano", "island", "archipelago",
    },
    "cat_nature": {
        "snow", "snowing", "rain", "raining", "storm",
        "fog", "mist", "haze", "wind", "windy", "breeze",
        "lightning", "thunder", "rainbow",
        "cherry_blossoms", "petals", "falling_petals",
        "autumn_leaves", "falling_leaves",
        "flower", "flowers", "bouquet",
        "tree", "trees", "bamboo",
        "grass", "moss", "ivy", "vines",
        "water", "waves", "ripples", "puddle",
        "fire", "flame", "campfire", "bonfire",
        "ice", "icicle", "frost",
        "sunbeam", "light_particles", "sparkle",
        "bubble", "bubbles",
        "feather", "feathers", "leaf", "leaves",
        "butterfly", "bird", "birds",
    },
    "cat_lighting": {
        "sunlight", "moonlight", "starlight",
        "backlighting", "backlight",
        "rim_lighting", "rim_light",
        "dramatic_lighting", "soft_lighting",
        "cinematic_lighting", "natural_lighting",
        "volumetric_lighting", "volumetric_light",
        "studio_lighting",
        "light_rays", "crepuscular_rays", "god_rays",
        "lens_flare", "light_leak",
        "shadow", "shadows", "silhouette",
        "reflection", "reflective",
        "glow", "glowing", "neon_lights",
        "candlelight", "firelight", "lamplight",
        "streetlight", "spotlight",
        "warm_lighting", "cool_lighting",
        "ambient_light", "diffused_light",
        "dappled_light", "dappled_sunlight",
        "chiaroscuro", "high_contrast", "low_key",
    },
    "cat_atmosphere": {
        "depth_of_field", "bokeh", "shallow_depth_of_field",
        "blurry_background", "blurry_foreground",
        "detailed_background", "simple_background",
        "white_background", "black_background", "gradient_background",
        "motion_blur", "speed_lines",
        "chromatic_aberration", "film_grain", "noise",
        "vignette", "bloom",
        "atmospheric_perspective", "hazy", "soft_focus",
        "monochrome", "sepia", "desaturated",
        "vibrant", "colorful", "pastel",
        "dark", "bright", "dim",
        "wide_angle", "telephoto", "fisheye",
        "panorama", "split_screen",
    },
    "cat_char_base": {
        "re:^\\d+girl", "re:^\\d+boy", "solo", "duo", "trio", "multiple_girls", "multiple_boys",
        "couple", "group", "re:.*breasts?$", "re:^slim$", "re:^muscular", "petite", "chubby",
        "thick_thighs", "wide_hips", "narrow_waist", "abs", "navel", "midriff", "cleavage",
        "collarbone", "re:^shoulder", "re:_skin$", "re:^skin_", "pale", "tan", "re:^dark_skin",
        "re:^nail", "re:^lip", "ear", "ears", "nose", "mole", "scar", "tattoo", "freckle",
        "curvy", "plump", "slender", "fit", "athletic", "tall", "short", "average_body",
        "1girl", "sole_female"
    },
    "cat_char_male": {
        "1boy", "male", "guy", "man", "solo_male", "older_man", "muscular_male", "otoko", "re:^\\d+boys?"
    },
    "cat_char_hair": {
        "re:_hair$", "re:^hair_", "re:hair$", "bangs", "ponytail", "twintails", "braid", "ahoge", "sidelocks",
        "bob_cut", "hime_cut", "pixie_cut", "drill_hair", "long_hair", "short_hair", "medium_hair",
        "very_long_hair", "bald", "shaved_head", "hair_bun", "hair_ornament", "over_one_eye", "hair_between_eyes"
    },
    "cat_char_eyes": {
        "re:_eyes$", "re:^eyes_", "heterochromia", "eyelashes", "pupils", "makeup", "mascara", "eyeliner", "eyeshadow",
        "re:.*_eyes$"
    },
    "cat_char_face": {
        "smile", "grin", "frown", "smirk", "re:^blush", "open_mouth", "closed_mouth",
        "re:^fang", "tears", "crying", "sweatdrop", "re:^tongue", "pout", "surprised", "angry",
        "embarrassed", "shy", "sad", "happy", "expressionless", "serious"
    },
    "cat_char_clothes": {
        "re:^dress", "re:^shirt", "re:^skirt", "pants", "shorts", "re:^uniform", "re:^armor",
        "re:^bikini", "re:^swimsuit", "re:^jacket", "coat", "cape", "cloak", "re:^hoodie",
        "re:^sweater", "vest", "re:^cardigan", "re:^kimono", "yukata", "hanfu", "re:^maid",
        "re:^apron", "suit", "re:^tuxedo", "robe", "toga", "gown", "re:^crop_top", "tank_top",
        "t-shirt", "re:^blouse", "re:^tunic", "re:^corset", "re:^overalls", "re:^jumpsuit",
        "bodysuit", "re:^pajamas", "nightgown", "re:^lingerie", "re:^underwear", "bra", "panties",
        "re:^leotard", "one-piece", "gloves", "boots", "shoes", "socks", "sandals", "sneakers",
        "heels", "slippers", "stockings", "thighhighs", "pantyhose", "kneehighs", "ankle_socks",
        "re:^glasses", "re:^sunglasses", "re:^goggles", "re:^earring", "re:^necklace", "ring",
        "re:^bracelet", "re:^choker", "collar", "scarf", "tie", "necktie", "re:^bowtie", "re:^ribbon",
        "bow", "hat", "cap", "crown", "tiara", "re:^headband", "re:^hairclip", "hair_ornament",
        "hair_ribbon", "re:^hairband", "re:^headpiece", "re:^headwear", "bag", "re:^backpack",
        "re:^purse", "re:^handbag", "umbrella", "parasol", "re:^weapon", "sword", "gun", "staff",
        "wand", "shield", "spear", "axe", "knife", "dagger", "mask", "re:^eyepatch", "re:^wing",
        "re:^zipper", "re:^button", "hood", "re:^hooded",
        "jirai_kei", "yami_kawaii", "cybergoth", "wa_lolita", "qi_lolita", "zettai_ryouiki"
    },
    "cat_nsfw_action": {
        "sex", "kissing", "hugging", "embracing", "holding_hands",
        "bound", "tied_up", "shibari", "rope", "gag", "gagged",
        "blindfold", "blindfolded", "chained", "cuffs", "handcuffs",
        "sleeping", "crying", "drinking", "eating",
        "fighting", "punching", "kicking", "slapping",
        "petting", "stroking", "licking", "sucking", "biting",
        "missionary", "doggystyle", "paizuri", "blowjob", "handjob", "footjob", "titfuck",
        "masturbation", "fingering", "cunnilingus", "anilingus", "anal", "vaginal", "oral",
        "tribadism", "reverse_cowgirl_position", "cowgirl_position", "mating_press", "spanking",
        "threesome", "group_sex", "gangbang", "orgy",
        "facesitting", "smothering", "breast_smother", "double_penetration", "triple_penetration",
        "futa_with_futa", "futa_on_female", "choking", "asphyxiation", "spitroast", "thigh_sex",
        "armpit_sex", "deepthroat",
        "prone_bone", "lying_on_back", "glory_wall", "standing_sex", "standing_split_sex", "anvil_position",
        "girl_on_top", "boy_on_top", "straddling", "upright_straddle", "reverse_upright_straddle",
        "suspended_congress", "reverse_suspended_congress", "full_nelson", "cooperative_paizuri",
        "69_position", "buttjob", "straddling_paizuri", "piledriver_sex", "amazon_position",
        "human_stacking", "grinding", "mutual_fingering", "breast_press", "breast_sucking",
        "self_breast_sucking", "groping", "symmetrical_docking", "torso_grab", "waist_grab",
        "neck_grab", "wrist_grab", "arm_grab", "leg_grab", "hand_grab",
        "hand_on_another's_waist", "hand_on_another's_hip", "hand_on_another's_ass", "hand_on_another's_breast",
        "handjob_over_clothes",
        "fingering_through_clothes", "fingering_through_panties", "hand_in_another's_panties",
        "tail_masturbation", "stealth_masturbation", "clothed_masturbation", "female_masturbation",
        "male_masturbation", "clitoral_stimulation", "nipple_pull", "box_tie", "frogtie", "hogtie",
        "shrimp_tie", "strappado", "bound_breasts", "bound_wrists", "bound_ankles", "femdom", "defloration",
        "re:^tentacle", "mind_control", "hypnosis"
    },
    "cat_nsfw_creature": {
        "monster", "creature", "demon", "devil", "angel",
        "orc", "goblin", "elf", "beast", "dragon",
        "slime", "tentacles", "alien", "ghost", "zombie",
        "robot", "cyborg", "android", "mecha",
        "animal", "dog", "cat", "bird", "fish", "horse", "wolf", "fox"
    },
    "cat_nsfw_item": {
        "toy", "sex_toy", "vibrator", "dildo", "plug", "magic_wand",
        "whip", "crop", "leash", "collar",
        "weapon", "sword", "gun", "knife", "bow", "shield",
        "book", "phone", "smartphone", "laptop", "bag",
        "cup", "glass", "bottle", "plate", "food",
        "re:^wand", "staff", "magic", "cigarette", "pipe",
        "suction_cup_dildo", "used_condom", "hitachi_magic_wand", "crotch_tattoo",
        "crotch_rope", "milking_machine", "breast_pump", "dilation_tape"
    },
    "cat_nsfw_focus": {
        "x-ray", "cross-section", "internal_cumshot", "womb", "stomach_deformation",
        "pov", "focus_on_breasts", "focus_on_ass", "focus_on_crotch", "focus_on_thighs", "cameltoe",
        "ass_focus", "breast_focus", "crotch_focus", "thigh_focus", "foot_focus", "armpit_focus",
        "impregnation", "stomach_bulge", "throat_bulge",
        "before_sex", "after_sex", "after_vaginal", "fucked_silly", "cross-section",
        "close-up", "macro", "from_below", "from_above", "dutch_angle",
        "disembodied_limb", "disembodied_arm", "disembodied_leg", "disembodied_hand", "disembodied_foot",
        "severed_arm", "severed_leg", "amputation", "amputee", "grabbing", "reaching_out", "multiple_hands"
    },
    "cat_nsfw_fluids": {
        "cum", "creampie", "cum_on_face", "cum_on_breasts", "cum_in_pussy", "cum_inside", "cum_on_stomach",
        "semen", "sperm", "ejaculation", "facial", "bukkake",
        "cum_in_mouth", "cum_in_ass", "cum_on_hair", "cum_pool", "swallowing", "swallowing_cum",
        "sweat", "sweatdrop", "saliva", "drool", "tears", "crying",
        "messy", "dirty", "covered_in_cum", "wet", "wet_clothes", "wet_hair",
        "urine", "peeing", "squirt", "love_nectar",
        "lactation", "breast_milk", "milk", "pussy_juice", "menstruation",
        "cum_drip_creampie", "cum_on_body", "cum_on_clothes", "pussy_juice_drip",
        "pussy_juice_puddle", "pussy_juice_trail", "pussy_juice_stain", "wet_panty",
        "wet_stain_on_panty", "drinking_pee", "peeing_in_cup", "public_urination", "peeing_self"
    },
    "cat_nsfw_fetish": {
        "ahegao", "heart-shaped_pupils", "rolled_back_eyes", "empty_eyes", "crazy_eyes",
        "heavy_breathing", "panting", "trembling", "shaking", "blush", "heavy_blush",
        "nosebleed", "open_mouth", "tongue_out", "saliva_trail",
        "mind_break", "corruption", "trance", "hypnotized"
    },
    "cat_nsfw_clothes_mess": {
        "clothes_pull", "tearing_clothes", "skirt_lift", "shirt_lift", "undressing",
        "panties_pulled_down", "half-closed_eyes", "partially_unbuttoned",
        "micro_bikini", "slingshot_swimsuit", "pasties",
        "nip_slip", "wardrobe_malfunction", "torn_clothes", "see-through",
        "panty_pull", "bra_pull", "no_panties", "no_bra", "breast_spilling_over", "crotchless_panties",
        "panty_around_knees", "panties_aside", "panties_around_ankles", "panties_around_one_leg",
        "panties_on_head", "pantyshot", "adjusting_panties", "holding_panties", "licking_panties",
        "panty_lift", "smelling_underwear", "wedgie", "tentacles_under_clothes",
        "naked", "nude", "topless", "bottomless"
    },
    "cat_nsfw_genitals": {
        "penis", "balls", "testicles", "erection", "vein", "precum", "foreskin",
        "pussy", "vagina", "clitoris", "labia", "cameltoe", "pubic_hair", "anus",
        "huge_penis", "monster_penis", "horse_penis", "tentacle_penetration", "multiple_penises", "futanari",
        "holding_penis", "rubbing_penis", "fucking_machine", "glory_hole", "crotch",
        "nipples", "erect_nipples", "areola", "ass", "asshole", "butt",
        "spread_pussy", "gaping", "cleft_of_venus", "wet_shiny_vagina", "cervix",
        "urethra", "groin_tendon", "clitoral_hood", "erect_clitoris", "clitoris_slip",
        "puffy_nipples", "inverted_nipples", "presenting_nipples", "presenting_crotch",
        "futa_with_female", "ovum", "fertilization", "sperm_cell"
    },
    "cat_nsfw_mosaic": {
        "uncensored", "censored", "bar_censor", "mosaic_censoring", "censor_steam", "ofuda_on_pussy"
    },
    "cat_meta": {
        "highres", "absurdres", "masterpiece", "best_quality", "re:_quality$", "re:^rating_",
        "re:^score_", "realistic", "anime", "manga", "official_art", "key_visual",
        "traditional_media", "digital_media"
    }
}

# ======================================================================
# タグカテゴリ定数（UIとロジックで共有）
# UI最適化: on_ui_tabs のネストスコープで定義していたローカル変数を
# モジュールレベル定数に昇格させ、クロージャ参照の安全性を確保する
# ======================================================================

_CAT_BASE_KEYS = [
    "cat_composition", "cat_pose", "cat_background",
    "cat_nature", "cat_lighting", "cat_atmosphere", "cat_meta",
]
_CAT_CHAR_KEYS = [
    "cat_char_base", "cat_char_male", "cat_char_hair",
    "cat_char_eyes", "cat_char_face", "cat_char_clothes",
]
_CAT_NSFW_KEYS = [
    "cat_nsfw_action", "cat_nsfw_creature", "cat_nsfw_item",
    "cat_nsfw_focus", "cat_nsfw_fluids", "cat_nsfw_fetish",
    "cat_nsfw_clothes_mess", "cat_nsfw_genitals", "cat_nsfw_mosaic",
]
_DEFAULT_CHAR_CATS = _CAT_CHAR_KEYS[:]  # デフォルト選択状態（Character全選択）


def _get_easy_prompt_tags():
    """sdweb-easy-prompt-selector のタグフォルダから全タグを取得する"""
    tags = set()
    # デフォルトのインストールパスを想定
    easy_prompt_dir = os.path.join(os.path.dirname(EXTENSION_DIR), "sdweb-easy-prompt-selector", "tags")
    
    if not os.path.exists(easy_prompt_dir) or yaml is None:
        return tags

    try:
        for root, _, files in os.walk(easy_prompt_dir):
            for file in files:
                if file.endswith((".yml", ".yaml")):
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                            if isinstance(data, dict):
                                def extract_values(d):
                                    for v in d.values():
                                        if isinstance(v, list):
                                            for item in v:
                                                if isinstance(item, str):
                                                    # LoRAやWildcardは除外
                                                    if not item.startswith(("<lora:", "__")):
                                                        tags.add(item.strip().lower().replace(" ", "_"))
                                        elif isinstance(v, dict):
                                            extract_values(v)
                                extract_values(data)
                    except Exception:
                        continue
    except Exception as e:
        print(f"[Smart Img2Img Composer] EasyPrompt load error: {e}")
    return tags


_compiled_cat_patterns = {}


def _filter_tags(tags: dict, confidence_threshold: float = 0.35, selected_categories=None, protect_easy_prompts: bool = True) -> dict:
    """許可タグカテゴリに含まれるタグのみ残すフィルタ (正規表現をキャッシュ)"""
    global _compiled_cat_patterns
    if not selected_categories:
        selected_categories = list(_TAG_CATEGORIES.keys())

    # Bug Fix #1/#2: filtered を関数冒頭で必ず初期化する（未定義によるNameError修正）
    filtered = {}

    # EasyPromptのタグを取得
    easy_tags = _get_easy_prompt_tags() if protect_easy_prompts else set()

    cache_key = tuple(sorted(selected_categories))
    if cache_key in _compiled_cat_patterns:
        allowed_tags, allowed_patterns = _compiled_cat_patterns[cache_key]
    else:
        allowed_tags = set()
        allowed_patterns = []
        for cat in selected_categories:
            if cat in _TAG_CATEGORIES:
                for item in _TAG_CATEGORIES[cat]:
                    if item.startswith("re:"):
                        allowed_patterns.append(re.compile(item[3:]))
                    else:
                        allowed_tags.add(item)
        _compiled_cat_patterns[cache_key] = (allowed_tags, allowed_patterns)

    # カテゴリごとの上限設定
    CAT_LIMITS = {
        "cat_char_eyes": 6,
        "cat_char_hair": 8,
        "cat_char_face": 6,
        "cat_char_clothes": 12,
        "cat_char_base": 10,
        "cat_nsfw_action": 10,
    }

    # 各カテゴリごとにマッチしたタグを一旦貯める
    cat_matches = {cat: [] for cat in selected_categories}
    # EasyPromptで保護されたタグ（上限計算外）
    easy_protected = {}

    for tag, score in tags.items():
        if score < confidence_threshold:
            continue

        tag_clean = tag.strip().lower().replace(" ", "_")

        # Bug Fix #2: filtered が初期化済みのため EasyPrompt ブランチが正常動作
        # EasyPrompt に含まれるタグは無条件でパス (上限計算外)
        if protect_easy_prompts and tag_clean in easy_tags:
            easy_protected[tag_clean] = score
            continue

        matched_cat = None
        # 直接一致を優先
        if tag_clean in allowed_tags:
            # どのカテゴリに属するか特定
            for cat in selected_categories:
                if cat in _TAG_CATEGORIES and tag_clean in _TAG_CATEGORIES[cat]:
                    matched_cat = cat
                    break
        else:
            # キャッシュ済みパターンで正規表現マッチ
            for cat in selected_categories:
                if cat in _TAG_CATEGORIES:
                    for item in _TAG_CATEGORIES[cat]:
                        if item.startswith("re:"):
                            p = re.compile(item[3:])
                            if p.search(tag_clean):
                                matched_cat = cat
                                break
                    if matched_cat:
                        break

        if matched_cat:
            cat_matches[matched_cat].append((tag_clean, score))
        # Bug Fix #6: カテゴリにマッチしないタグは破棄（フィルタの意図通り）
        # else: 以前は other_matches に入れていたが、フィルタ外タグは除外すべき

    # カテゴリごとに上限を適用して統合
    for cat, matches in cat_matches.items():
        limit = CAT_LIMITS.get(cat, 999)
        sorted_matches = sorted(matches, key=lambda x: x[1], reverse=True)
        for t_clean, s in sorted_matches[:limit]:
            filtered[t_clean] = s

    # EasyPromptで保護されたタグを最後に統合（上限適用外）
    filtered.update(easy_protected)

    return filtered


def _tags_to_prompt(tags: dict) -> str:
    """タグを信頼度順でプロンプト文字列に変換"""
    if not tags:
        return ""
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    return ", ".join(tag.replace("_", " ") for tag, _ in sorted_tags)


def _find_tagger():
    """WD14 Tagger モジュールを検索"""
    try:
        from tagger import interrogator as tagger_mod
        return tagger_mod, None
    except ImportError:
        pass

    try:
        webui_root = os.path.dirname(os.path.dirname(EXTENSION_DIR))
        extensions_dir = os.path.join(webui_root, "extensions")
        if os.path.isdir(extensions_dir):
            for dirname in os.listdir(extensions_dir):
                if "tagger" in dirname.lower() or "wd14" in dirname.lower():
                    tagger_path = os.path.join(extensions_dir, dirname)
                    if tagger_path not in sys.path:
                        sys.path.insert(0, tagger_path)
            try:
                from tagger import interrogator as tagger_mod
                return tagger_mod, None
            except ImportError:
                pass
    except Exception:
        pass

    return None, (
        "❌ WD14 Tagger が見つかりません。\n"
        "stable-diffusion-webui-wd14-tagger をインストールしてください:\n"
        "https://github.com/toriato/stable-diffusion-webui-wd14-tagger"
    )


def _interrogate_image(pil_image, confidence_threshold: float = 0.35, selected_categories=None):
    """WD14 Taggerで画像解析 → フィルタ済みタグを返す"""
    tagger_mod, error = _find_tagger()
    if tagger_mod is None:
        return {}, {}, error

    try:
        all_tags = {}
        success = False

        try:
            from tagger import utils as tagger_utils
            if hasattr(tagger_utils, "interrogators") and isinstance(tagger_utils.interrogators, dict) and tagger_utils.interrogators:
                default_model = "wd14-convnext.v2"
                if default_model in tagger_utils.interrogators:
                    interrogator_obj = tagger_utils.interrogators[default_model]
                else:
                    interrogator_obj = list(tagger_utils.interrogators.values())[0]

                res = interrogator_obj.interrogate(pil_image)
                if isinstance(res, tuple) and len(res) >= 2:
                    all_tags = res[1] if isinstance(res[1], dict) else {}
                    success = True
                elif isinstance(res, dict):
                    all_tags = res
                    success = True
        except ImportError:
            pass
        except Exception as e:
            print(f"[Random Composer] tagger.utils pattern error: {e}")

        if not success:
            try:
                import tagger.api as tagger_api
                if hasattr(tagger_api, "interrogate"):
                    res = tagger_api.interrogate(pil_image)
                    if isinstance(res, dict) and "caption" in res:
                        all_tags = res["caption"]
                        success = True
                    elif isinstance(res, dict):
                        all_tags = res
                        success = True
                    elif isinstance(res, tuple) and len(res) >= 2:
                        all_tags = res[1]
                        success = True
            except Exception:
                pass

        if not success and hasattr(tagger_mod, "Interrogator"):
            cls = tagger_mod.Interrogator
            interrogators_dict = {}
            if hasattr(cls, "get_interrogators"):
                res = cls.get_interrogators()
                if isinstance(res, dict):
                    interrogators_dict = res
            elif hasattr(cls, "interrogators"):
                res = cls.interrogators
                if isinstance(res, dict):
                    interrogators_dict = res

            if interrogators_dict:
                interrogator_obj = list(interrogators_dict.values())[0]
                res = interrogator_obj.interrogate(pil_image)
                if isinstance(res, tuple) and len(res) >= 2:
                    all_tags = res[1] if isinstance(res[1], dict) else {}
                    success = True
                elif isinstance(res, dict):
                    all_tags = res
                    success = True

        if not success:
            return {}, {}, t("msg_tagger_not_found")

        return _filter_tags(all_tags, confidence_threshold, selected_categories), all_tags, None

    except Exception as e:
        return {}, {}, t("msg_tag_fetch_err") + f" {e}\n{traceback.format_exc()}"


# ======================================================================
# プロンプト自動生成
# ======================================================================

def get_stable_dimensions(img, mode="slider", slider_val=1024, min_val=512, max_val=1024):
    """
    画像のアスペクト比を維持しつつ、指定されたモードと範囲に合わせて解像度を返す。
    Bug Fix: min_val/max_val のデフォルト値を SD1.5 向けの 512/1024 に修正。
    """
    if not img:
        return slider_val, slider_val
    w, h = img.size
    aspect = w / h

    new_w, new_h = float(w), float(h)
    max_edge = max(w, h)

    if mode == "slider":
        if w > h:
            new_w = slider_val
            new_h = new_w / aspect
        else:
            new_h = slider_val
            new_w = new_h * aspect
    elif mode == "range":
        if max_edge < min_val:
            scale = min_val / max_edge
            new_w = w * scale
            new_h = h * scale
        elif max_edge > max_val:
            scale = max_val / max_edge
            new_w = w * scale
            new_h = h * scale

    new_w = max(64, round(new_w / 64) * 64)
    new_h = max(64, round(new_h / 64) * 64)
    return new_w, new_h


def autogen_prompt(image, section_name, confidence, pos_prompt, neg_prompt, cat_base, cat_char, cat_nsfw, custom_dict_str, gen_mosaic_auto=False, gen_mosaic_level="Mosaic Med", custom_dict_enabled=True):
    """画像を解析してメモエントリを生成"""
    gen_categories = cat_base + cat_char + cat_nsfw
    if image is None:
        return "", t("msg_no_upload_err"), "", "", "512", "512", ""

    if not section_name or not section_name.strip():
        return "", t("msg_no_section_err"), "", "", "512", "512", ""

    try:
        section_name = section_name.strip()
        pos = pos_prompt.strip() if pos_prompt else ""
        neg = neg_prompt.strip() if neg_prompt else ""

        filtered, all_tags, error = _interrogate_image(image, confidence, gen_categories)
        if error:
            return "", error, "", "", "512", "512", ""

        log_lines = []
        log_lines.append(t("log_all_tags").format(count=len(all_tags)))
        log_lines.append(t("log_filtered_tags").format(count=len(filtered)))

        excluded_count = len(all_tags) - len(filtered)
        if excluded_count > 0:
            log_lines.append(t("log_excluded_tags").format(count=excluded_count))

        # モザイク用プロンプトの自動付加
        mosaic_extra = []
        if gen_mosaic_auto:
            is_mosaic = any(tag in all_tags for tag in ["mosaic_censoring", "censored", "bar_censor"])
            if is_mosaic:
                if gen_mosaic_level == t("mosaic_low") or gen_mosaic_level == "Mosaic Low":
                    mosaic_extra = ["(mosaic_censoring:0.8)", "(light_mosaic:1.1)"]
                elif gen_mosaic_level == t("mosaic_high") or gen_mosaic_level == "Mosaic High":
                    mosaic_extra = ["(mosaic_censoring:1.4)", "(thick_mosaic:1.2)", "(detailed_mosaic:1.1)"]
                else: # Medium
                    mosaic_extra = ["(mosaic_censoring:1.1)", "(detailed_mosaic:1.0)"]
                log_lines.append(f"🧱 Mosaic Auto-Prompt added ({gen_mosaic_level})")

        only_tags_str = ", ".join(filtered)
        matched_custom_prompts = []
        if custom_dict_enabled and custom_dict_str and custom_dict_str.strip():
            for line in custom_dict_str.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                separator = "=>" if "=>" in line else "->" if "->" in line else ">" if ">" in line else None
                if not separator:
                    continue

                left, right = line.split(separator, 1)
                condition_tags = [t_tag.strip().lower().replace(" ", "_") for t_tag in left.split(",")]
                right_prompt = right.strip()

                if not condition_tags or not right_prompt:
                    continue

                match = all(c_tag in all_tags for c_tag in condition_tags)

                if match:
                    matched_custom_prompts.append(right_prompt)
                    log_lines.append(t("log_custom_match").format(cond=left, prompt=right_prompt))

        generated_tags = _tags_to_prompt(filtered)

        components = []
        if pos:
            components.append(pos)
        if mosaic_extra:
            components.extend(mosaic_extra)
        if matched_custom_prompts:
            components.extend(matched_custom_prompts)
        if generated_tags:
            components.append(generated_tags)

        final_positive = ", ".join(components)

        if not final_positive:
            log_lines.append(t("log_no_pos_prompt"))
        else:
            log_lines.append(f"📝 Positive: {final_positive}")

        if neg:
            log_lines.append(f"🚫 Negative: {neg}")

        entry = (
            f"[{section_name}]\n"
            f"positive:\n"
            f"{final_positive}\n"
            f"\n"
            f"negative:\n"
            f"{neg}\n"
        )
        # Bug Fix: autogen_prompt から呼ぶ get_stable_dimensions は range モードで SD1.5 範囲を使用
        w, h = get_stable_dimensions(image, mode="range", min_val=512, max_val=1024)
        return entry, "\n".join(log_lines), final_positive, neg, str(w), str(h), only_tags_str

    except Exception as e:
        return "", f"❌ エラー: {e}\n{traceback.format_exc()}", "", "", "512", "512", ""


def append_to_memo(memo_path, entry):
    """メモファイルにエントリを追記"""
    if not memo_path or not memo_path.strip():
        return "❌ メモファイルパスが未設定です（設定タブで保存してください）"
    if not entry or not entry.strip():
        return "❌ 追記するエントリがありません（まずプロンプトを生成してください）"

    try:
        memo_path = memo_path.strip()
        dirpart = os.path.dirname(memo_path)
        if dirpart:
            os.makedirs(dirpart, exist_ok=True)

        separator = ""
        if os.path.isfile(memo_path):
            with open(memo_path, "r", encoding="utf-8") as f:
                content = f.read()
            if content and not content.endswith("\n"):
                separator = "\n\n"
            elif content:
                separator = "\n"

        with open(memo_path, "a", encoding="utf-8") as f:
            f.write(separator + entry.strip() + "\n")

        return t("msg_memo_appended")
    except IOError as e:
        return t("msg_memo_err") + f" {e}"


# ======================================================================
# img2img フック
# ======================================================================

class RandomComposerScript(scripts.Script):
    sorting_priority = -100

    def title(self):
        return "Smart Img2Img Composer v1.0 (Stable)"

    def show(self, is_img2img):
        return scripts.AlwaysVisible if is_img2img else False

    def ui(self, is_img2img):
        if not is_img2img:
            return []
        with gr.Accordion("🎲 Smart Img2Img Composer", open=False, elem_id="smart_composer_accordion"):
            gr.Markdown(t("accordion_desc"))
            enabled = gr.Checkbox(
                label=t("enable"),
                value=False,
                elem_id="smart_composer_enabled",
            )
            # アセット設定: 視認性向上のためアコーディオンを分けすぎず整理
            with gr.Row():
                with gr.Column(variant="panel"):
                    gr.Markdown(f"**{t('accordion_assets')}**")
                    with gr.Row():
                        en_char = gr.Checkbox(label=t("enable_random_char"), value=False, elem_id="smart_composer_en_char")
                        pos_char = gr.Radio(choices=[t("pos_front"), t("pos_back")], label=t("pos_label"), value=t("pos_back"), scale=0)
                    with gr.Row():
                        en_sit = gr.Checkbox(label=t("enable_random_sit"), value=False, elem_id="smart_composer_en_sit")
                        pos_sit = gr.Radio(choices=[t("pos_front"), t("pos_back")], label=t("pos_label"), value=t("pos_back"), scale=0)
                    with gr.Row():
                        en_w1 = gr.Checkbox(label=t("wildcard_1"), value=False, elem_id="smart_composer_en_w1")
                        pos_w1 = gr.Radio(choices=[t("pos_front"), t("pos_back")], label=t("pos_label"), value=t("pos_back"), scale=0)
                    with gr.Row():
                        en_w2 = gr.Checkbox(label=t("wildcard_2"), value=False, elem_id="smart_composer_en_w2")
                        pos_w2 = gr.Radio(choices=[t("pos_front"), t("pos_back")], label=t("pos_label"), value=t("pos_back"), scale=0)
                    with gr.Row():
                        en_w3 = gr.Checkbox(label=t("wildcard_3"), value=False, elem_id="smart_composer_en_w3")
                        pos_w3 = gr.Radio(choices=[t("pos_front"), t("pos_back")], label=t("pos_label"), value=t("pos_back"), scale=0)

            with gr.Row():
                selection_mode = gr.Radio(
                    label=t("selection_mode"),
                    choices=[(t("sel_random"), "random"), (t("sel_sequential"), "sequential")],
                    value="random",
                    elem_id="smart_composer_selection_mode",
                )
                override_prompt = gr.Checkbox(
                    label=t("overwrite_prompt"),
                    value=True,
                    elem_id="smart_composer_override",
                )

            with gr.Row():
                _resize_choices = [t("resize_none"), t("resize_slider"), t("resize_512"), t("resize_1024"), t("resize_1536")]
                resize_mode = gr.Dropdown(
                    label=t("resize_mode"),
                    choices=_resize_choices,
                    value=_resize_choices[0],
                    elem_id="smart_composer_resize_mode",
                )
                base_resolution = gr.Slider(
                    label=t("base_resolution"),
                    minimum=512, maximum=2048, step=64,
                    value=1024,
                    elem_id="smart_composer_base_resolution",
                )

            with gr.Accordion(t("output_settings"), open=False):
                output_sort_mode = gr.Dropdown(
                    label=t("sort_mode"),
                    choices=[t("sort_none"), t("sort_preset"), t("sort_section"), t("sort_date")],
                    value=t("sort_none")
                )

        return [enabled, override_prompt, resize_mode, base_resolution, selection_mode, en_char, pos_char, en_sit, pos_sit, en_w1, pos_w1, en_w2, pos_w2, en_w3, pos_w3, output_sort_mode]

    def before_process(self, p: processing.StableDiffusionProcessing, enabled, override_prompt, resize_mode, base_resolution, selection_mode, en_char, pos_char, en_sit, pos_sit, en_w1, pos_w1, en_w2, pos_w2, en_w3, pos_w3, output_sort_mode):
        if not enabled:
            return

        if getattr(p, "_smart_composer_processed", False):
            return

        config = load_config()
        # Bug Fix: compose_prompt が matched_section_name も返すよう変更
        selected, positive, negative, log, matched_section_name = compose_prompt(
            config.get("image_folder", ""),
            config.get("memo_file", ""),
            config.get("match_threshold", 0.3),
            selection_mode
        )

        log_list = [log] if log else []

        asset_slots = [
            (en_char, LORA_CHAR_PATH, pos_char, "Char"),
            (en_sit, LORA_SIT_PATH, pos_sit, "Sit"),
            (en_w1, config.get("wildcard_1_path", WILD_1_PATH), pos_w1, "W1"),
            (en_w2, config.get("wildcard_2_path", WILD_2_PATH), pos_w2, "W2"),
            (en_w3, config.get("wildcard_3_path", WILD_3_PATH), pos_w3, "W3"),
        ]

        generation_count = config.get("generation_count", 1)
        if generation_count > p.n_iter:
            p.n_iter = generation_count

        if selected:
            try:
                img = Image.open(selected).convert("RGB")
                p.init_images = [img]

                # Bug Fix #7: インデックスのハードコードを廃止し、文字列キーで直接比較する
                # これにより選択肢の順序変更に対して堅牢になる
                _RESIZE_KEY_NONE   = t("resize_none")
                _RESIZE_KEY_SLIDER = t("resize_slider")
                _RESIZE_KEY_512    = t("resize_512")
                _RESIZE_KEY_1024   = t("resize_1024")
                _RESIZE_KEY_1536   = t("resize_1536")

                if resize_mode == _RESIZE_KEY_SLIDER:
                    s_val = int(base_resolution) if base_resolution else 1024
                    new_w, new_h = get_stable_dimensions(img, "slider", s_val, 512, 1024)
                    p.width = new_w
                    p.height = new_h
                elif resize_mode == _RESIZE_KEY_512:
                    new_w, new_h = get_stable_dimensions(img, "range", 1024, 512, 1024)
                    p.width = new_w
                    p.height = new_h
                elif resize_mode == _RESIZE_KEY_1024:
                    new_w, new_h = get_stable_dimensions(img, "range", 1024, 1024, 1536)
                    p.width = new_w
                    p.height = new_h
                elif resize_mode == _RESIZE_KEY_1536:
                    new_w, new_h = get_stable_dimensions(img, "range", 1536, 1536, 1792)
                    p.width = new_w
                    p.height = new_h
                # _RESIZE_KEY_NONE または未知の値の場合はリサイズしない
            except Exception as e:
                print(f"[Smart Img2Img Composer] 画像読み込み失敗: {selected}, Error: {e}")

        def inject(current_val, new_val, override):
            if override:
                return new_val
            return f"{current_val}, {new_val}" if current_val else new_val

        if positive:
            p.prompt = inject(p.prompt, positive, override_prompt)
        if negative:
            p.negative_prompt = inject(p.negative_prompt, negative, override_prompt)

        f_assets = []
        b_assets = []
        asset_logs = []
        for en, path, pos, name in asset_slots:
            if en:
                line = get_random_asset(path)
                if line:
                    if pos == t("pos_front") or pos == "Front":
                        f_assets.insert(0, line)
                    else:
                        b_assets.append(line)
                    asset_logs.append(f"{name}: {line}")

        parts = []
        if f_assets:
            parts.append(", ".join(f_assets))
        parts.append(p.prompt)
        if b_assets:
            parts.append(", ".join(b_assets))

        p.prompt = _clean_prompt(", ".join(parts))

        # Bug Fix: output_sort_mode の section 振り分けで matched_section_name を使用
        if output_sort_mode and output_sort_mode != t("sort_none") and output_sort_mode != "None":
            try:
                from datetime import datetime
                sub_name = ""
                if output_sort_mode in (t("sort_preset"), "Preset"):
                    sub_name = config.get("last_preset_name", "Default")
                elif output_sort_mode in (t("sort_section"), "Section"):
                    # Bug Fix: locals()['matched'] 参照を廃止し matched_section_name を使用
                    raw_name = matched_section_name or "Default"
                    sub_name = re.sub(r'[\\/:*?"<>|]', '_', raw_name)
                elif output_sort_mode in (t("sort_date"), "Date"):
                    sub_name = datetime.now().strftime("%Y-%m-%d")

                if sub_name:
                    p.outpath_samples = os.path.join(p.outpath_samples, sub_name)
                    os.makedirs(p.outpath_samples, exist_ok=True)
                    log_list.append(f"📁 Output subfolder: {sub_name}")
            except Exception as e:
                print(f"[Smart Img2Img Composer] Folder sorting failed: {e}")

        offset = config.get("lora_offset", 0.0)
        if offset != 0.0:
            def apply_offset(match):
                pre, name, val, post = match.groups()
                try:
                    new_val = float(val) + offset
                    return f"{pre}{name}:{new_val:.2f}{post}"
                except Exception:
                    return match.group(0)

            p.prompt = re.sub(r"(<lora:)([^:]+):([-+]?\d*\.?\d+)(>)", apply_offset, p.prompt)
            p.negative_prompt = re.sub(r"(<lora:)([^:]+):([-+]?\d*\.?\d+)(>)", apply_offset, p.negative_prompt)
            log_list.append(f"⚖️ LoRA Offset applied: {offset:+.2f}")

        if asset_logs:
            log_list.append(f"🎲 Random Assets: {' | '.join(asset_logs)}")

        if p.prompt:
            log_list.append(f"📜 Combined Prompt: {p.prompt}")
        print(f"[Smart Img2Img Composer] Final Prompt: {p.prompt}")

        p._smart_composer_processed = True

        final_log = "\n".join(log_list)
        if final_log:
            print(f"[Smart Img2Img Composer]\n{final_log}")

    def process(self, p, *args):
        pass


# ======================================================================
# 独立タブ UI
# ======================================================================

def on_ui_tabs():
    config = load_config()

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown(
            "# 🎲 Smart Img2Img Composer v1.0 (Stable)\n"
            + t("tab_header")
        )


        def handle_save_preset(name, lang, img_f, memo, threshold, count, fallback, auto_l, offset, w1, w2, w3, sort):
            if not name:
                return "Error: Name required", gr.update()
            config = load_config()
            presets = config.get("presets", {})
            presets[name] = {
                "language": lang,
                "image_folder": _clean_path(img_f),
                "memo_file": _clean_path(memo),
                "match_threshold": threshold,
                "generation_count": count,
                "fallback_enabled": fallback,
                "auto_lora_enabled": auto_l,
                "lora_offset": offset,
                "wildcard_1_path": _clean_path(w1),
                "wildcard_2_path": _clean_path(w2),
                "wildcard_3_path": _clean_path(w3),
                "output_sort_mode": sort,
            }
            config["presets"] = presets
            config["last_preset_name"] = name
            save_config(config)
            return f"✅ Preset '{name}' saved!", gr.update(choices=["Default"] + list(presets.keys()))

        def handle_load_preset(name):
            if name == "Default":
                config = load_config()
                config["last_preset_name"] = "Default"
                save_config(config)
                vals = ("ja", "", "", 0.3, 1, True, True, 0.0, WILD_1_PATH, WILD_2_PATH, WILD_3_PATH, t("sort_none"))
                health = check_individual_health("", "", WILD_1_PATH, WILD_2_PATH, WILD_3_PATH)
                return vals + health
            config = load_config()
            config["last_preset_name"] = name
            save_config(config)
            p = config.get("presets", {}).get(name)
            if not p:
                return (gr.update(),) * (12 + 5)
            vals = (
                p.get("language", "ja"),
                p.get("image_folder", ""),
                p.get("memo_file", ""),
                p.get("match_threshold", 0.3),
                p.get("generation_count", 1),
                p.get("fallback_enabled", True),
                p.get("auto_lora_enabled", True),
                p.get("lora_offset", 0.0),
                p.get("wildcard_1_path", WILD_1_PATH),
                p.get("wildcard_2_path", WILD_2_PATH),
                p.get("wildcard_3_path", WILD_3_PATH),
                p.get("output_sort_mode", t("sort_none")),
            )
            health = check_individual_health(
                p.get("image_folder", ""), p.get("memo_file", ""),
                p.get("wildcard_1_path", WILD_1_PATH), p.get("wildcard_2_path", WILD_2_PATH), p.get("wildcard_3_path", WILD_3_PATH)
            )
            return vals + health

        def handle_delete_preset(name):
            if not name or name == "Default":
                return "Cannot delete Default", gr.update()
            config = load_config()
            presets = config.get("presets", {})
            if name in presets:
                del presets[name]
                config["presets"] = presets
                save_config(config)
                return f"🗑️ Deleted '{name}'", gr.update(choices=["Default"] + list(presets.keys()), value="Default")
            return "Not found", gr.update()

        # Helper for initial labels
        initial_config = load_config()
        def get_init_label(key, ptype, label_base):
            path = initial_config.get(key, "")
            if not path: return label_base
            path = _clean_path(path)
            exists = False
            if ptype == "dir": exists = os.path.isdir(path)
            elif ptype == "file": exists = os.path.isfile(path)
            else: exists = os.path.exists(path)
            return f"✅ {label_base}" if exists else f"❌ {label_base}"

        with gr.Tabs() as tabs_root:
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
                                    scale=2
                                )
                                preset_name_input = gr.Textbox(placeholder=t("preset_ph"), label=None, scale=1)
                            with gr.Row():
                                save_preset_btn = gr.Button(t("btn_save_preset"), variant="secondary", scale=1)
                                delete_preset_btn = gr.Button(t("btn_delete_preset"), variant="secondary", scale=0)

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

                    with gr.Column(scale=1):
                        gr.Markdown(t("h_preview"))
                        preview_image = gr.Image(label=t("selected_image"), type="pil", interactive=False)
                        # Bug Fix: 変数名を preview_positive / preview_negative に統一
                        preview_positive = gr.Textbox(label=t("positive_prompt"), interactive=False, lines=3)
                        preview_negative = gr.Textbox(label=t("negative_prompt"), interactive=False, lines=2)
                        preview_log = gr.Textbox(label=t("log"), interactive=False, lines=6)

            # ─── プロンプト自動生成 ───
            with gr.Tab(t("tab_prompt_gen")):
                gr.Markdown(t("prompt_gen_desc"))

                with gr.Row():
                    with gr.Column(scale=1):
                        gen_image = gr.Image(
                            label=t("target_image"),
                            type="pil",
                            interactive=True,
                        )
                        gen_section = gr.Textbox(
                            label=t("section_name"),
                            placeholder=t("section_ph"),
                            info=t("section_info"),
                        )
                        _cat_base = _CAT_BASE_KEYS
                        _cat_char = _CAT_CHAR_KEYS
                        _cat_nsfw = _CAT_NSFW_KEYS

                        gr.Markdown(t("h_categories"))
                        with gr.Row():
                            gen_btn_toggle_all_cats = gr.Button(t("btn_toggle_all_cats"), size="sm", variant="secondary", scale=0)
                            gr.Markdown("") # Spacer

                        DEFAULT_CHAR_CATS = _DEFAULT_CHAR_CATS
                        
                        with gr.Accordion(t("cat_base"), open=True):
                            gen_base_toggle = gr.Button(t("btn_toggle_all"), size="sm", variant="secondary")
                            gen_cat_base = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_base],
                                value=lambda: [c for c in (load_config().get("gen_categories") or list(_TAG_CATEGORIES.keys())) if c in _cat_base],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_char"), open=False):
                            gen_char_toggle = gr.Button(t("btn_toggle_all"), size="sm", variant="secondary")
                            gen_cat_char = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_char],
                                value=lambda: [c for c in (load_config().get("gen_categories") or DEFAULT_CHAR_CATS) if c in _cat_char],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_nsfw"), open=False):
                            gen_nsfw_toggle = gr.Button(t("btn_toggle_all"), size="sm", variant="secondary")
                            gen_cat_nsfw = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_nsfw],
                                value=lambda: [c for c in (load_config().get("gen_categories") or list(_TAG_CATEGORIES.keys())) if c in _cat_nsfw],
                                show_label=False
                            )

                        gen_confidence = gr.Slider(
                            label=t("confidence"),
                            minimum=0.1, maximum=0.9, step=0.05,
                            value=lambda: load_config().get("gen_confidence", 0.35),
                            info=t("confidence_info"),
                        )
                        gen_positive = gr.Textbox(
                            label=t("default_positive"),
                            value=lambda: load_config().get("gen_positive", "(masterpiece:1.1), (best quality:1.0), "),
                            lines=2,
                            info=t("default_positive_info"),
                        )
                        gen_negative = gr.Textbox(
                            label=t("default_negative"),
                            value=lambda: load_config().get("gen_negative", "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts"),
                            lines=2,
                            info=t("default_negative_info"),
                        )
                        with gr.Accordion(t("custom_dict"), open=False):
                            gen_custom_dict_enabled = gr.Checkbox(
                                label=t("gen_custom_dict_enabled"),
                                value=lambda: load_config().get("gen_custom_dict_enabled", False),
                            )
                            gen_custom_dict = gr.Textbox(
                                label=None,
                                value=lambda: load_config().get("gen_custom_dict", "night, city > cyberpunk cityscape, neon lights, highly detailed, vivid colors\n1girl, smile > beautiful detailed eyes, glowing smile"),
                                lines=3,
                                info=t("custom_dict_info"),
                                show_label=False
                            )
                        with gr.Accordion(t("h_mosaic_settings"), open=False):
                            with gr.Row():
                                gen_mosaic_auto = gr.Checkbox(
                                    label=t("gen_mosaic_auto"),
                                    value=lambda: load_config().get("gen_mosaic_auto", False),
                                )
                                gen_mosaic_level = gr.Radio(
                                    choices=[t("mosaic_low"), t("mosaic_med"), t("mosaic_high")],
                                    label=t("gen_mosaic_level"),
                                    value=lambda: load_config().get("gen_mosaic_level", t("mosaic_med")),
                                )
                        with gr.Row():
                            gen_btn = gr.Button(t("btn_gen_tags"), variant="primary")
                            send_to_img2img_btn = gr.Button(t("btn_send_img2img"), variant="primary")
                        with gr.Row():
                            append_btn = gr.Button(t("btn_append_memo"), variant="secondary")
                            gen_save_btn = gr.Button(t("btn_save_settings"), variant="secondary")

                    try:
                        from modules import generation_parameters_copypaste as params_copypaste
                        params_copypaste.register_paste_params_button(
                            params_copypaste.ParamBinding(
                                paste_button=send_to_img2img_btn, tabname="img2img", source_image_component=gen_image
                            )
                        )
                    except Exception as e:
                        print(f"[Smart Img2Img Composer] Image copypaste binding disabled: {e}")

                    with gr.Column(scale=1):
                        # Bug Fix: t("generated_entry") キーが追加されたため正しく表示される
                        gen_output = gr.Textbox(
                            label=t("generated_entry"),
                            interactive=True,
                            lines=10,
                            info=t("generated_entry_info"),
                        )
                        # Bug Fix: t("analysis_log") キーが追加されたため正しく表示される
                        gen_log = gr.Textbox(
                            label=t("analysis_log"),
                            interactive=False,
                            lines=8,
                        )
                        gen_only_tags = gr.Textbox(
                            label=t("h_extracted_tags"),
                            interactive=True,
                            lines=5,
                        )
                        with gr.Row():
                            append_status = gr.Textbox(
                                label=t("append_status"),
                                interactive=False,
                                max_lines=1,
                            )
                            gen_save_status = gr.Textbox(
                                label=t("status"),
                                interactive=False,
                                max_lines=1,
                            )
                        hidden_gen_pos = gr.Textbox(visible=False)
                        hidden_gen_neg = gr.Textbox(visible=False)
                        hidden_gen_w = gr.Textbox(visible=False)
                        hidden_gen_h = gr.Textbox(visible=False)

            # ─── LoRAマネージャー ───
            with gr.Tab(t("tab_lora_manager")):
                def get_mgr_path(mgr_label):
                    config = load_config()
                    label_to_key = {
                        t("lora_type_char"): "char",
                        t("lora_type_sit"): "sit",
                        t("wildcard_1"): "w1",
                        t("wildcard_2"): "w2",
                        t("wildcard_3"): "w3",
                    }
                    mgr_key = label_to_key.get(mgr_label, "char")
                    mapping = {
                        "char": LORA_CHAR_PATH,
                        "sit": LORA_SIT_PATH,
                        "w1": config.get("wildcard_1_path") or WILD_1_PATH,
                        "w2": config.get("wildcard_2_path") or WILD_2_PATH,
                        "w3": config.get("wildcard_3_path") or WILD_3_PATH,
                    }
                    res = mapping.get(mgr_key)
                    if not res:
                        print(f"[Smart Img2Img Composer] Manager path resolution failed for: {mgr_key}")
                    else:
                        print(f"[Smart Img2Img Composer] Manager path resolved ({mgr_key}): {res}")
                    return res

                def load_lora_list(mgr_label):
                    if mgr_label is None:
                        return gr.update()
                    path = get_mgr_path(mgr_label)
                    if path and os.path.exists(path):
                        # Bug Fix #5: except のネスト構文エラーを修正
                        # try/except を正しいフラットな構造に書き直す
                        for enc in ("utf-8", "utf-8-sig", "cp932"):
                            try:
                                with open(path, "r", encoding=enc,
                                          errors=("ignore" if enc == "cp932" else "strict")) as f:
                                    return f.read()
                            except (UnicodeDecodeError, LookupError):
                                continue
                            except Exception:
                                break
                    return ""

                def load_lora_with_baseline(mgr_label):
                    content = load_lora_list(mgr_label)
                    if mgr_label is None:
                        return gr.update(), gr.update()
                    return content, content

                def save_lora_list(mgr_label, content):
                    path = get_mgr_path(mgr_label)
                    if path:
                        dir_name = os.path.dirname(path)
                        if dir_name:
                            os.makedirs(dir_name, exist_ok=True)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(content)
                        return t("msg_lora_saved"), content
                    return "Error", gr.update()

                def append_lora_list(mgr_label, input_text):
                    if not input_text or not input_text.strip():
                        content = load_lora_list(mgr_label)
                        return content, "", content

                    path = get_mgr_path(mgr_label)
                    if not path:
                        return "Error: Path not defined", ""

                    current_content = ""
                    if os.path.exists(path):
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                current_content = f.read()
                        except UnicodeDecodeError:
                            with open(path, "r", encoding="cp932", errors="ignore") as f:
                                current_content = f.read()
                        except Exception:
                            pass

                    new_line = input_text.strip()
                    if current_content and not current_content.endswith("\n"):
                        current_content += "\n"
                    current_content += new_line + "\n"

                    with open(path, "w", encoding="utf-8") as f:
                        f.write(current_content)

                    return current_content, "", current_content

                gr.Markdown(t("lora_manager_desc"))

                with gr.Row():
                    lora_mgr_type = gr.Dropdown(
                        label=t("lora_type"),
                        choices=[
                            t("lora_type_char"),
                            t("lora_type_sit"),
                            t("wildcard_1"),
                            t("wildcard_2"),
                            t("wildcard_3"),
                        ],
                        value=lambda: t("lora_type_char")
                    )

                with gr.Row():
                    lora_mgr_input = gr.Textbox(
                        label=t("lora_input_label"),
                        placeholder="<lora:my_lora:0.8>, 1girl, ...",
                        lines=2
                    )
                    append_lora_btn = gr.Button(t("btn_append_lora"), variant="primary")

                lora_mgr_content = gr.Textbox(
                    label=t("lora_list_label"),
                    lines=15,
                    placeholder="<lora:my_lora:0.8>, 1girl, ...",
                    value=lambda: load_lora_list(t("lora_type_char")),
                    elem_id="smart_composer_lora_mgr_content"
                )
                lora_mgr_baseline = gr.Textbox(
                    value=lambda: load_lora_list(t("lora_type_char")),
                    visible=False,
                    elem_id="smart_composer_lora_baseline"
                )

                # JavaScript for unsaved changes warning
                gr.HTML(f"""
                    <script>
                    function smart_composer_lora_change(type, content, baseline) {{
                        if (content !== baseline) {{
                            if (!confirm("{t('lora_unsaved_warning')}")) {{
                                return [type, content, baseline];
                            }}
                        }}
                        return [type, content, baseline];
                    }}
                    </script>
                """)

                with gr.Row():
                    save_lora_mgr_btn = gr.Button(t("btn_save_lora_list"), variant="primary")
                    lora_mgr_msg = gr.Markdown("")

                # Bug Fix #3: load_lora_with_baseline(mgr_label) は引数1個のため inputs を1個に修正
                # _js で content/baseline を受け取る確認ダイアログは JS 側でのみ処理する
                lora_mgr_type.change(
                    fn=load_lora_with_baseline,
                    inputs=[lora_mgr_type],
                    outputs=[lora_mgr_content, lora_mgr_baseline],
                    _js="(type, content, baseline) => smart_composer_lora_change(type, content, baseline)"
                )
                save_lora_mgr_btn.click(
                    fn=save_lora_list,
                    inputs=[lora_mgr_type, lora_mgr_content],
                    outputs=[lora_mgr_msg, lora_mgr_baseline]
                )
                append_lora_btn.click(
                    fn=append_lora_list,
                    inputs=[lora_mgr_type, lora_mgr_input],
                    outputs=[lora_mgr_content, lora_mgr_input, lora_mgr_baseline]
                )

            # ─── 使い方 ───
            with gr.Tab(t("tab_usage")):
                gr.Markdown(t("usage_md"))

        # ─── イベントハンドラ ───

        _health_inputs = [image_folder, memo_file, w1_path, w2_path, w3_path]
        _preset_inputs = [
            language_selector, image_folder, memo_file, match_threshold, generation_count,
            fallback_enabled, auto_lora_enabled, lora_offset_slider,
            w1_path, w2_path, w3_path, output_sort_selector
        ]

        preset_dropdown.change(
            fn=handle_load_preset,
            inputs=[preset_dropdown],
            outputs=_preset_inputs + _health_inputs
        )
        save_preset_btn.click(
            fn=handle_save_preset,
            inputs=[preset_name_input] + _preset_inputs,
            outputs=[save_status, preset_dropdown]
        )
        delete_preset_btn.click(
            fn=handle_delete_preset,
            inputs=[preset_dropdown],
            outputs=[save_status, preset_dropdown]
        )

        _common_save_inputs = [
            language_selector, image_folder, memo_file, match_threshold, generation_count, fallback_enabled, auto_lora_enabled,
            gen_confidence, gen_positive, gen_negative, gen_custom_dict, gen_cat_base, gen_cat_char, gen_cat_nsfw,
            w1_path, w2_path, w3_path, lora_offset_slider, output_sort_selector,
            gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled
        ]


        save_btn.click(
            fn=lambda *args: (save_all_settings(*args), *check_individual_health(*[args[i] for i in [1, 2, 14, 15, 16]])),
            inputs=_common_save_inputs,
            outputs=[save_status] + _health_inputs,
        )
        # Bug Fix: outputs の変数名を preview_positive / preview_negative に修正
        reload_btn.click(
            fn=preview_compose,
            inputs=[image_folder, memo_file, match_threshold],
            outputs=[preview_image, preview_positive, preview_negative, preview_log],
        )
        preview_btn.click(
            fn=preview_compose,
            inputs=[image_folder, memo_file, match_threshold],
            outputs=[preview_image, preview_positive, preview_negative, preview_log],
        )
        gen_save_btn.click(
            fn=lambda *args: (save_all_settings(*args), *check_individual_health(*[args[i] for i in [1, 2, 14, 15, 16]])),
            inputs=_common_save_inputs,
            outputs=[gen_save_status] + _health_inputs,
        )
        append_btn.click(
            fn=lambda entry: append_to_memo(load_config().get("memo_file", ""), entry),
            inputs=[gen_output],
            outputs=[append_status],
        )
        gen_btn.click(
            fn=autogen_prompt,
            inputs=[
                gen_image, gen_section, gen_confidence, gen_positive, gen_negative,
                gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_custom_dict,
                gen_mosaic_auto, gen_mosaic_level, gen_custom_dict_enabled
            ],
            outputs=[gen_output, gen_log, hidden_gen_pos, hidden_gen_neg, hidden_gen_w, hidden_gen_h, gen_only_tags],
        )

        # ─── トグル/一括操作ロジック ───
        # 全カテゴリ一括選択/解除: いずれかが選択済みなら全解除、全未選択なら全選択
        gen_btn_toggle_all_cats.click(
            fn=lambda cb, cc, cn: (
                [] if (cb or cc or cn) else (_cat_base, _cat_char, _cat_nsfw)
            ),
            inputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw],
            outputs=[gen_cat_base, gen_cat_char, gen_cat_nsfw]
        )
        gen_base_toggle.click(
            fn=lambda x: _cat_base if not x else [],
            inputs=[gen_cat_base],
            outputs=gen_cat_base
        )
        gen_char_toggle.click(
            fn=lambda x: _cat_char if not x else [],
            inputs=[gen_cat_char],
            outputs=gen_cat_char
        )
        gen_nsfw_toggle.click(
            fn=lambda x: _cat_nsfw if not x else [],
            inputs=[gen_cat_nsfw],
            outputs=gen_cat_nsfw
        )

        send_to_img2img_btn.click(
            fn=None,
            _js="""
            function(pos, neg, w, h) {
                const q = (sel) => gradioApp().querySelector(sel);
                const setVal = (sel, val) => {
                    let el = q(sel);
                    if(el) { el.value = val; updateInput(el); }
                };

                setVal('#img2img_prompt textarea', pos);
                setVal('#img2img_neg_prompt textarea', neg);

                if (w && h) {
                    ['input[type="number"]', 'input[type="range"]'].forEach(sel => {
                        setVal('#img2img_width ' + sel, w);
                        setVal('#img2img_height ' + sel, h);
                    });
                }

                const tabs = gradioApp().querySelectorAll('#tabs > div > button');
                if (tabs) {
                    for(let i=0; i<tabs.length; i++){
                        if(tabs[i].innerText.includes('img2img')) {
                            tabs[i].click();
                            break;
                        }
                    }
                }
                return [];
            }
            """,
            inputs=[hidden_gen_pos, hidden_gen_neg, hidden_gen_w, hidden_gen_h],
            outputs=None,
        )

    return [(tab, "Smart Img2Img Composer", "smart_composer_tabs_root")]


script_callbacks.on_ui_tabs(on_ui_tabs)
