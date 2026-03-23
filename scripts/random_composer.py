# -*- coding: utf-8 -*-
"""
Random Img2Img Composer
AUTOMATIC1111 Stable Diffusion WebUI 拡張機能

img2img生成時に、指定フォルダからランダム画像を選択し、
メモファイルから対応プロンプト（positive/negative）を自動取得して投入する。
WD14 Tagger連携でプロンプトの自動生成も可能。
"""

import os
import sys
import json
import random
import re
import traceback
import gradio as gr
from PIL import Image

from modules import script_callbacks, processing, scripts

# ======================================================================
# 定数
# ======================================================================

EXTENSION_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(EXTENSION_DIR, "config.json")

DEFAULT_CONFIG = {
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
    "gen_categories": [], # _TAG_CATEGORIES初期化時に後でセットするか、Noneで扱う
    "fallback_enabled": True,
    "auto_lora_enabled": True,
}

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


# ======================================================================
# i18n 翻訳辞書
# ======================================================================

_I18N = {
    # --- img2img アコーディオン ---
    "accordion_desc": {
        "en": "**Check Enable → Click Generate.** Settings are saved in 'Smart Img2Img Composer' tab.",
        "ja": "**有効化 → Generate で自動実行。** 設定は「Smart Img2Img Composer」タブで保存。",
    },
    "enable": {
        "en": "✅ Enable (Auto-inject image & prompt)",
        "ja": "✅ 有効化（生成時に自動で画像＋プロンプト投入）",
    },
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
        "en": "💾 Save",
        "ja": "💾 保存",
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
        "en": "🔞 NSFW & Fetish (Actions, Fluids)",
        "ja": "🔞 特殊・NSFWカテゴリ (行為・アイテム等)",
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
    
    # --- タグカテゴリ名 ---
    "cat_composition": {"en": "Composition & Camera", "ja": "構図・カメラ"},
    "cat_pose": {"en": "Pose & Action", "ja": "ポーズ・アクション"},
    "cat_background": {"en": "Background & Scene", "ja": "背景・場所"},
    "cat_nature": {"en": "Nature & Weather", "ja": "自然・天候"},
    "cat_lighting": {"en": "Lighting", "ja": "照明"},
    "cat_atmosphere": {"en": "Atmosphere", "ja": "雰囲気"},
    "cat_meta": {"en": "Meta Tags", "ja": "メタタグ"},
    "cat_char_base": {"en": "Character Base", "ja": "人物・基本属性"},
    "cat_char_hair": {"en": "Hair & Face Area", "ja": "髪型・顔周り"},
    "cat_char_face": {"en": "Expression & Mouth", "ja": "表情・口"},
    "cat_char_clothes": {"en": "Clothes & Accessories", "ja": "服装・靴・装飾品"},
    "cat_nsfw_action": {"en": "🎭 Actions", "ja": "🎭 行為・アクション"},
    "cat_nsfw_creature": {"en": "🦑 Creatures", "ja": "🦑 クリーチャー・追加キャラ"},
    "cat_nsfw_item": {"en": "🧸 Toys & Items", "ja": "🧸 アイテム・玩具"},
    "cat_nsfw_focus": {"en": "🔞 Focus & Angles", "ja": "🔞 特殊構図・フォーカス"},
    "cat_nsfw_fluids": {"en": "💦 Fluids & Mess", "ja": "💦 体液・汚れ系"},
    "cat_nsfw_fetish": {"en": "🥵 Fetish States", "ja": "🥵 表情・フェティッシュ状態"},
    "cat_nsfw_clothes_mess": {"en": "👗 Clothes Mess", "ja": "👗 衣服の乱れ・着脱"},
    "cat_nsfw_censored": {"en": "🍆 Censor & Genitals", "ja": "🍆 局所・モザイク"},

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
    "tab_lora_manager": {"en": "🏷️ LoRA Manager", "ja": "🏷️ LoRAマネージャー"},
    "lora_manager_desc": {
        "en": "Register and manage your Character/Situation LoRAs. You can also edit the .txt files directly.",
        "ja": "キャラクターやシチュエーションのLoRAリストを管理します。拡張機能内の.txtファイルを直接編集することも可能です。"
    },
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
    # --- 使い方タブ ---
    "tab_usage": {"en": "📖 Usage", "ja": "📖 使い方"},
    "usage_md": {
        "en": (
            "## How to write Memo File\n"
            "Create a text file and write in the following format:\n"
            "```text\n"
            "[title1]\n"
            "positive:\n"
            "(masterpiece:1.1), 1girl, portrait\n"
            "\n"
            "negative:\n"
            "lowres, blurry, artifact\n"
            "\n"
            "[city]\n"
            "positive:\n"
            "skyline, sunset, cinematic lighting\n"
            "\n"
            "negative:\n"
            "lowres, text, watermark\n"
            "```\n\n"
            "## Rules\n"
            "- `[name]` = Section start\n"
            "- Under `positive:` = Positive prompt\n"
            "- Under `negative:` = Negative prompt\n"
            "- If `positive:`/`negative:` omitted, entire block is positive\n"
            "- `#` = Comment / Empty lines = Ignored\n\n"
            "## Using in img2img\n"
            "1. Save your folder paths in **⚙️ Settings** tab.\n"
            "2. In **img2img** tab, expand **🎲 Smart Composer** and check **Enable**.\n"
            "3. Click **Generate** to start auto-processing.\n\n"
            "## Auto-Prompt Generation\n"
            "1. Upload image to **🏷️ Auto-Prompt Gen** tab.\n"
            "2. Enter section name and click **Generate Tags**.\n"
            "3. Review/edit and click **Append to Memo**.\n"
            "4. Requires WD14 Tagger extension."
        ),
        "ja": (
            "## メモファイルの書き方\n"
            "テキストファイルを作成して以下の形式で書きます：\n"
            "```text\n"
            "[タイトル1]\n"
            "positive:\n"
            "(masterpiece:1.1), 1girl, portrait\n"
            "\n"
            "negative:\n"
            "lowres, blurry, artifact\n"
            "\n"
            "[city]\n"
            "positive:\n"
            "skyline, sunset, cinematic lighting\n"
            "\n"
            "negative:\n"
            "lowres, text, watermark\n"
            "```\n\n"
            "## ルール\n"
            "- `[名前]` = セクション開始\n"
            "- `positive:` の下 = ポジティブプロンプト\n"
            "- `negative:` の下 = ネガティブプロンプト\n"
            "- `positive:` / `negative:` 省略時は全て positive 扱い\n"
            "- `#` = コメント / 空行 = 無視\n\n"
            "## img2img での使い方\n"
            "1. **⚙️ 設定** タブで画像フォルダ・メモファイルを保存\n"
            "2. **img2img** タブで **🎲 Smart Composer** → **有効化**\n"
            "3. **Generate** ボタンで自動実行\n\n"
            "## プロンプト自動生成\n"
            "1. **🏷️ プロンプト自動生成** タブで画像をアップロード\n"
            "2. セクション名を入力して **タグ解析＆生成**\n"
            "3. 結果を確認・編集して **メモファイルに追記**\n"
            "4. WD14 Tagger 拡張が必要です"
        )
    },
}


def _get_lang() -> str:
    """config.jsonからlanguage設定を読み取る (デフォルト: ja)"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f).get("language", "ja")
    except Exception:
        pass
    return "ja"


def t(key: str) -> str:
    """翻訳キーを現在の言語に変換して返す"""
    lang = _get_lang()
    entry = _I18N.get(key, {})
    return entry.get(lang, entry.get("en", key))


# ======================================================================
# 設定管理
# ======================================================================

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except (json.JSONDecodeError, IOError):
            pass
    return dict(DEFAULT_CONFIG)


def save_config(config: dict) -> str:
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return t("msg_settings_saved")
    except IOError as e:
        return f"{t('msg_settings_err')} {e}"


# ======================================================================
# メモファイル解析（positive / negative 対応）
# ======================================================================

def parse_memo_file(memo_path: str) -> dict:
    """
    メモファイルを解析する。
    戻り値: { セクション名: {"positive": "...", "negative": "..."} }
    """
    sections = {}
    if not memo_path or not os.path.isfile(memo_path):
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
        with open(memo_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n\r")
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
    except IOError:
        pass

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
    if not folder or not os.path.isdir(folder):
        return []
    return [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS
    ]


def match_image_to_sections(image_path: str, sections: dict, threshold: float) -> list:
    basename = os.path.splitext(os.path.basename(image_path))[0].lower()
    exact_match = []
    partial_match_candidates = []

    for section_name, data in sections.items():
        # 完全一致（最優先）
        if basename == section_name:
            exact_match.append(data)
            continue
            
        # 部分一致のスコア計算
        score = 0
        if section_name in basename or basename in section_name:
            shorter = min(len(basename), len(section_name))
            longer = max(len(basename), len(section_name))
            if shorter >= 3 and longer > 0:
                score = shorter / longer
        
        # 類似度マッチ（閾値以下の場合のみ試行してスコアを更新）
        if score < 1.0 and threshold < 1.0:
            longer = max(len(basename), len(section_name))
            if longer > 0:
                common = sum(1 for a, b in zip(basename, section_name) if a == b)
                sim_score = common / longer
                if sim_score > score:
                    score = sim_score
        
        if score >= threshold:
            partial_match_candidates.append((score, data))

    # 完全一致があれば完全一致のみ返す
    if exact_match:
        return [exact_match[0]] # 複数あっても1件に絞る（通常は辞書なので1件）
    
    # 部分一致があれば最もスコアが高い1件のみ返す
    if partial_match_candidates:
        partial_match_candidates.sort(key=lambda x: x[0], reverse=True)
        return [partial_match_candidates[0][1]]

    return []


def check_lora_exists(lora_str: str) -> bool:
    parts = lora_str.split(":")
    lora_name = parts[0].strip()
    try:
        import modules.lora
        if hasattr(modules.lora, 'available_loras'):
            return lora_name in modules.lora.available_loras
    except ImportError:
        pass
    return True

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

def compose_prompt(image_folder: str, memo_file: str, match_threshold: float, selection_mode="Random") -> tuple:
    """戻り値: (画像パス, positive, negative, ログ)"""
    log = []
    config = load_config()
    fallback_enabled = config.get("fallback_enabled", True)
    auto_lora_enabled = config.get("auto_lora_enabled", True)

    image_files = get_image_files(image_folder)
    if not image_files:
        return None, "", "", t("msg_no_images")

    if selection_mode == "sequential":
        last_index = config.get("last_sequential_index", 0)
        index = last_index % len(image_files)
        selected = image_files[index]
        config["last_sequential_index"] = index + 1
        save_config(config)
        log.append(t("log_sel_sequential").format(index=index+1, total=len(image_files), filename=os.path.basename(selected)))
    else:
        selected = random.choice(image_files)
        log.append(t("log_sel_random").format(filename=os.path.basename(selected)))

    sections = parse_memo_file(memo_file)
    if not sections:
        log.append(t("log_no_sections"))
        return selected, "", "", "\n".join(log)

    log.append(t("log_sections_count").format(count=len(sections)))
    matched = match_image_to_sections(selected, sections, match_threshold)

    if not matched:
        if fallback_enabled and "default" in sections:
            log.append(t("log_fallback"))
            matched = [sections["default"]]
        else:
            log.append(t("log_no_match"))
            return selected, "", "", "\n".join(log)

    pos_parts, neg_parts, lora_parts = [], [], []
    seen_pos, seen_neg, seen_lora = set(), set(), set()
    for m in matched:
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

    return selected, positive, negative, "\n".join(log)


# ======================================================================
# UI ヘルパー
# ======================================================================

def preview_compose(image_folder, memo_file, match_threshold):
    selected, positive, negative, log = compose_prompt(
        image_folder, memo_file, match_threshold
    )
    img = None
    if selected and os.path.isfile(selected):
        try:
            img = Image.open(selected)
        except Exception:
            pass
    return img, positive, negative, log


def save_all_settings(language, image_folder, memo_file, match_threshold, generation_count, fallback, auto_lora,
                      gen_confidence, gen_positive, gen_negative, gen_custom, cat_base, cat_char, cat_nsfw):
    config = load_config()
    categories = cat_base + cat_char + cat_nsfw
    config.update({
        "language": language,
        "image_folder": image_folder,
        "memo_file": memo_file,
        "match_threshold": match_threshold,
        "generation_count": int(generation_count),
        "fallback_enabled": fallback,
        "auto_lora_enabled": auto_lora,
        "gen_confidence": gen_confidence,
        "gen_positive": gen_positive,
        "gen_negative": gen_negative,
        "gen_custom_dict": gen_custom,
        "gen_categories": categories,
    })
    return save_config(config)


# ======================================================================
# WD14 Tagger 連携 — タグフィルタリング
# ======================================================================
# img2imgで元キャラに干渉しないタグのみ通す（構図/ポーズ/シーン/照明）

# ── 許可タグカテゴリ辞書 ──
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
        "re:^nail", "re:^lip", "ear", "ears", "nose", "mole", "scar", "tattoo", "freckle"
    },
    "cat_char_hair": {
        "re:_hair$", "re:^hair_", "bangs", "ponytail", "twintails", "braid", "ahoge", "sidelocks",
        "bob_cut", "hime_cut", "pixie_cut", "drill_hair", "long_hair", "short_hair", "medium_hair",
        "very_long_hair", "re:_eyes$", "heterochromia", "eyelashes", "pupils"
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
        "self_breast_sucking", "groping", "symmetrical_docking", "torso_grab", "handjob_over_clothes",
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
        "close-up", "macro", "from_below", "from_above", "dutch_angle"
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
    "cat_nsfw_censored": {
        "penis", "balls", "testicles", "erection", "vein", "precum", "foreskin",
        "pussy", "vagina", "clitoris", "labia", "cameltoe", "pubic_hair", "anus",
        "huge_penis", "monster_penis", "horse_penis", "tentacle_penetration", "multiple_penises", "futanari",
        "uncensored", "censored", "bar_censor", "mosaic_censoring", "censor_steam",
        "holding_penis", "rubbing_penis", "fucking_machine", "glory_hole", "crotch",
        "nipples", "erect_nipples", "areola", "ass", "asshole", "butt",
        "spread_pussy", "gaping", "cleft_of_venus", "wet_shiny_vagina", "cervix",
        "urethra", "groin_tendon", "clitoral_hood", "erect_clitoris", "clitoris_slip",
        "puffy_nipples", "inverted_nipples", "presenting_nipples", "presenting_crotch",
        "ofuda_on_pussy", "futa_with_female", "ovum", "fertilization", "sperm_cell"
    },
    "cat_meta": {
        "highres", "absurdres", "masterpiece", "best_quality", "re:_quality$", "re:^rating_",
        "re:^score_", "realistic", "anime", "manga", "official_art", "key_visual",
        "traditional_media", "digital_media"
    }
}


def _filter_tags(tags: dict, confidence_threshold: float = 0.35, selected_categories=None) -> dict:
    """許可タグカテゴリに含まれるタグのみ残すフィルタ"""
    if selected_categories is None:
        selected_categories = list(_TAG_CATEGORIES.keys())

    allowed_tags = set()
    allowed_patterns = []
    
    for cat in selected_categories:
        if cat in _TAG_CATEGORIES:
            for item in _TAG_CATEGORIES[cat]:
                if item.startswith("re:"):
                    allowed_patterns.append(re.compile(item[3:]))
                else:
                    allowed_tags.add(item)

    filtered = {}
    for tag, score in tags.items():
        if score < confidence_threshold:
            continue
            
        tag_clean = tag.strip().lower().replace(" ", "_")
        
        if tag_clean in allowed_tags:
            filtered[tag_clean] = score
            continue
            
        for p in allowed_patterns:
            if p.search(tag_clean):
                filtered[tag_clean] = score
                break
                
    return filtered


def _tags_to_prompt(tags: dict) -> str:
    """タグを信頼度順でプロンプト文字列に変換"""
    if not tags:
        return ""
    sorted_tags = sorted(tags.items(), key=lambda x: x[1], reverse=True)
    return ", ".join(tag.replace("_", " ") for tag, _ in sorted_tags)


def _find_tagger():
    """WD14 Tagger モジュールを検索"""
    # 方法1: 直接import
    try:
        from tagger import interrogator as tagger_mod
        return tagger_mod, None
    except ImportError:
        pass

    # 方法2: extensions ディレクトリを走査して手動追加
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

        # パターン1: 推奨 - tagger.utils.interrogators から実体インスタンスを取得
        try:
            from tagger import utils as tagger_utils
            if hasattr(tagger_utils, "interrogators") and isinstance(tagger_utils.interrogators, dict) and tagger_utils.interrogators:
                # デフォルトモデルを探す、なければ最初のもの
                default_model = "wd14-convnext.v2"
                if default_model in tagger_utils.interrogators:
                    interrogator_obj = tagger_utils.interrogators[default_model]
                else:
                    interrogator_obj = list(tagger_utils.interrogators.values())[0]

                res = interrogator_obj.interrogate(pil_image)
                # res は (rating_dict, tag_dict) のタプル
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

        # パターン2: tagger.api.interrogate (新しいWD14拡張のエンドポイント)
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

        # パターン3: インタロゲータークラスのget_interrogators
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
                
                # 自動ロードを期待してそのままinterrogate
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

def get_stable_dimensions(img, mode="slider", slider_val=1024, min_val=1024, max_val=1536):
    """画像のアスペクト比を維持しつつ、指定されたモードと範囲に合わせて解像度を返す"""
    if not img:
        return slider_val, slider_val
    w, h = img.size
    aspect = w / h
    
    new_w, new_h = w, h
    max_edge = max(w, h)

    if mode == "slider":
        # スライダーの値に長辺を強制
        if w > h:
            new_w = slider_val
            new_h = int(new_w / aspect)
        else:
            new_h = slider_val
            new_w = int(new_h * aspect)
    elif mode == "range":
        # 指定範囲内に長辺を収める
        if max_edge < min_val:
            scale = min_val / max_edge
            new_w = w * scale
            new_h = h * scale
        elif max_edge > max_val:
            scale = max_val / max_edge
            new_w = w * scale
            new_h = h * scale

    # SDで安定しやすいよう64の倍数にスナップ
    new_w = max(64, round(new_w / 64) * 64)
    new_h = max(64, round(new_h / 64) * 64)
    return new_w, new_h

def autogen_prompt(image, section_name, confidence, pos_prompt, neg_prompt, cat_base, cat_char, cat_nsfw, custom_dict_str):
    """画像を解析してメモエントリを生成"""
    gen_categories = cat_base + cat_char + cat_nsfw
    if image is None:
        return "", t("msg_no_upload_err")

    if not section_name or not section_name.strip():
        return "", t("msg_no_section_err")

    try:
        section_name = section_name.strip()
        pos = pos_prompt.strip() if pos_prompt else ""
        neg = neg_prompt.strip() if neg_prompt else ""

        filtered, all_tags, error = _interrogate_image(image, confidence, gen_categories)
        if error:
            return "", error

        log_lines = []
        log_lines.append(t("log_all_tags").format(count=len(all_tags)))
        log_lines.append(t("log_filtered_tags").format(count=len(filtered)))

        excluded_count = len(all_tags) - len(filtered)
        if excluded_count > 0:
            log_lines.append(t("log_excluded_tags").format(count=excluded_count))

        # ==== 好みのプロンプトの条件付与 ====
        matched_custom_prompts = []
        if custom_dict_str and custom_dict_str.strip():
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
                
                # すべての条件タグが抽出された全タグ(all_tags)に含まれているかチェック
                match = True
                for c_tag in condition_tags:
                    if c_tag not in all_tags:
                        match = False
                        break
                
                if match:
                    matched_custom_prompts.append(right_prompt)
                    log_lines.append(t("log_custom_match").format(cond=left, prompt=right_prompt))

        # タグの文字列化
        generated_tags = _tags_to_prompt(filtered)

        # デフォルトポジティブ、カスタムプロンプト、抽出タグを結合
        components = []
        if pos:
            components.append(pos)
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
        w, h = get_stable_dimensions(image)
        return entry, "\n".join(log_lines), final_positive, neg, str(w), str(h)

    except Exception as e:
        return "", f"❌ エラー: {e}\n{traceback.format_exc()}", "", "", "512", "512"


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
    # Dynamic Promptsなどの他スクリプトよりも先に実行させるため、優先度を低く設定
    sorting_priority = -100

    def title(self):
        return "Smart Img2Img Composer"

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
            with gr.Row():
                enable_random_char = gr.Checkbox(
                    label=t("enable_random_char"),
                    value=False,
                    elem_id="smart_composer_random_char",
                )
                enable_random_sit = gr.Checkbox(
                    label=t("enable_random_sit"),
                    value=False,
                    elem_id="smart_composer_random_sit",
                )
            # 画像選択モード: 内部キー "random" / "sequential" を使い、表示は翻訳
            _sel_choices = [(t("sel_random"), "random"), (t("sel_sequential"), "sequential")]
            selection_mode = gr.Radio(
                label=t("selection_mode"),
                choices=_sel_choices,
                value="random",
                elem_id="smart_composer_selection_mode",
            )
            override_prompt = gr.Checkbox(
                label=t("overwrite_prompt"),
                value=True,
                elem_id="smart_composer_override",
            )
            # リサイズモード: 内部判定はインデックスで行う
            _resize_choices = [
                t("resize_none"),
                t("resize_slider"),
                t("resize_512"),
                t("resize_1024"),
                t("resize_1536"),
            ]
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
        return [enabled, override_prompt, resize_mode, base_resolution, selection_mode, enable_random_char, enable_random_sit]

    def before_process(self, p: processing.StableDiffusionProcessing, enabled, override_prompt, resize_mode="", base_resolution=1024, selection_mode="", enable_random_char=False, enable_random_sit=False):
        """before_process メソッドでプロンプト注入を行う。
        getattr(p, '_smart_composer_processed', False) を使って二重実行を防止する。
        """
        if not enabled:
            return

        # すでにこの処理オブジェクトで実行済みならスキップ
        if getattr(p, "_smart_composer_processed", False):
            return

        config = load_config()
        selected, positive, negative, log = compose_prompt(
            config.get("image_folder", ""),
            config.get("memo_file", ""),
            config.get("match_threshold", 0.3),
            selection_mode
        )
        
        log_list = [log] if log else []

        # ランダムLoRAの読み込みと注入
        def get_random_lora(filename):
            path = os.path.join(EXTENSION_DIR, filename)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
                if lines:
                    return random.choice(lines)
            return None

        additional_prompts = []
        if enable_random_char:
            lora = get_random_lora("lora_char.txt")
            if lora:
                additional_prompts.append(lora)
                log_list.append(t("log_random_lora").format(lora=lora))
        
        if enable_random_sit:
            lora = get_random_lora("lora_sit.txt")
            if lora:
                additional_prompts.append(lora)
                log_list.append(t("log_random_lora").format(lora=lora))
        
        if additional_prompts:
            if positive:
                positive = f"{positive}, {', '.join(additional_prompts)}"
            else:
                positive = ", ".join(additional_prompts)

        # 内部的な生成回数（Batch count）の設定
        generation_count = config.get("generation_count", 1)
        if generation_count > p.n_iter:
            p.n_iter = generation_count

        if selected:
            try:
                img = Image.open(selected).convert("RGB")
                p.init_images = [img]
                
                # 画像サイズ自動調整
                _resize_choices = [
                    t("resize_none"),
                    t("resize_slider"),
                    t("resize_512"),
                    t("resize_1024"),
                    t("resize_1536"),
                ]
                resize_idx = -1
                if resize_mode in _resize_choices:
                    resize_idx = _resize_choices.index(resize_mode)
                
                if resize_idx > 0:  # 0 = "Do not resize"
                    mode_flag = "slider"
                    min_v, max_v = 1024, 1536
                    s_val = int(base_resolution) if base_resolution else 1024
                    
                    if resize_idx == 2:  # 512~1024
                        mode_flag = "range"
                        min_v, max_v = 512, 1024
                    elif resize_idx == 3:  # 1024~1536
                        mode_flag = "range"
                        min_v, max_v = 1024, 1536
                    elif resize_idx == 4:  # 1536~1792
                        mode_flag = "range"
                        min_v, max_v = 1536, 1792
                        
                    new_w, new_h = get_stable_dimensions(img, mode_flag, s_val, min_v, max_v)
                    p.width = new_w
                    p.height = new_h
            except Exception as e:
                print(f"[Smart Img2Img Composer] 画像読み込み失敗: {selected}, Error: {e}")

        # プロンプトの注入（p.prompt だけでなく all_prompts も更新する）
        def inject(current_val, new_val, override):
            if override:
                return new_val
            return f"{current_val}, {new_val}" if current_val else new_val

        if positive:
            p.prompt = inject(p.prompt, positive, override_prompt)
            if hasattr(p, "all_prompts") and p.all_prompts:
                p.all_prompts = [inject(x, positive, override_prompt) for x in p.all_prompts]

        if negative:
            p.negative_prompt = inject(p.negative_prompt, negative, override_prompt)
            if hasattr(p, "all_negative_prompts") and p.all_negative_prompts:
                p.all_negative_prompts = [inject(x, negative, override_prompt) for x in p.all_negative_prompts]

        final_log = "\n".join(log_list)
        print(f"[Smart Img2Img Composer]\n{final_log}")
        
        # 実行済みフラグをセット
        setattr(p, "_smart_composer_processed", True)


# ======================================================================
# 独立タブ UI
# ======================================================================

def on_ui_tabs():
    config = load_config()

    with gr.Blocks(analytics_enabled=False) as tab:
        gr.Markdown(
            "# 🎲 Smart Img2Img Composer\n"
            + t("tab_header")
        )

        with gr.Tabs() as tabs_root:
            # ─── 設定 & プレビュー ───
            with gr.Tab(t("tab_settings")):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown(t("h_settings"))
                        # 言語設定
                        language_selector = gr.Radio(
                            label=t("language_label"),
                            choices=["ja", "en"],
                            value=lambda: load_config().get("language", "ja"),
                        )
                        image_folder = gr.Textbox(
                            label=t("image_folder"),
                            placeholder=t("image_folder_ph"),
                            value=lambda: load_config().get("image_folder", ""),
                        )
                        memo_file = gr.Textbox(
                            label=t("memo_file"),
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
                        fallback_enabled = gr.Checkbox(
                            label=t("fallback_enabled"),
                            value=lambda: load_config().get("fallback_enabled", True),
                        )
                        auto_lora_enabled = gr.Checkbox(
                            label=t("auto_lora"),
                            value=lambda: load_config().get("auto_lora_enabled", True),
                        )
                        with gr.Row():
                            save_btn = gr.Button(t("btn_save"), variant="primary")
                            preview_btn = gr.Button(t("btn_preview"), variant="secondary")
                        save_status = gr.Textbox(label=t("status"), interactive=False, max_lines=1)

                    with gr.Column(scale=1):
                        gr.Markdown(t("h_preview"))
                        preview_image = gr.Image(label=t("selected_image"), type="pil", interactive=False)
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
                        # --- アコーディオン化されたタグカテゴリ ---
                        _cat_base = ["cat_composition", "cat_pose", "cat_background", "cat_nature", "cat_lighting", "cat_atmosphere", "cat_meta"]
                        _cat_char = ["cat_char_base", "cat_char_hair", "cat_char_face", "cat_char_clothes"]
                        _cat_nsfw = ["cat_nsfw_action", "cat_nsfw_creature", "cat_nsfw_item", "cat_nsfw_focus", "cat_nsfw_fluids", "cat_nsfw_fetish", "cat_nsfw_clothes_mess", "cat_nsfw_censored"]
                        
                        gr.Markdown(t("h_categories"))
                        with gr.Accordion(t("cat_base"), open=True):
                            gen_cat_base = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_base],
                                value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_base],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_char"), open=False):
                            gen_cat_char = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_char],
                                value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_char],
                                show_label=False
                            )
                        with gr.Accordion(t("cat_nsfw"), open=False):
                            gen_cat_nsfw = gr.CheckboxGroup(
                                choices=[(t(c), c) for c in _cat_nsfw],
                                value=lambda: [c for c in load_config().get("gen_categories", list(_TAG_CATEGORIES.keys())) if c in _cat_nsfw],
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
                        gen_custom_dict = gr.Textbox(
                            label=t("custom_dict"),
                            value=lambda: load_config().get("gen_custom_dict", "night, city > cyberpunk cityscape, neon lights, highly detailed, vivid colors\n1girl, smile > beautiful detailed eyes, glowing smile"),
                            lines=3,
                            info=t("custom_dict_info"),
                        )
                        gen_negative = gr.Textbox(
                            label=t("default_negative"),
                            value=lambda: load_config().get("gen_negative", "lowres, blurry, artifact, bad anatomy, worst quality, low quality, jpeg artifacts"),
                            lines=2,
                            info=t("default_negative_info"),
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
                        gen_output = gr.Textbox(
                            label=t("generated_entry"),
                            interactive=True,
                            lines=10,
                            info=t("generated_entry_info"),
                        )
                        gen_log = gr.Textbox(
                            label=t("analysis_log"),
                            interactive=False,
                            lines=8,
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
                        # 内部保持用の隠しコンポーネント
                        hidden_gen_pos = gr.Textbox(visible=False)
                        hidden_gen_neg = gr.Textbox(visible=False)
                        hidden_gen_w = gr.Textbox(visible=False)
                        hidden_gen_h = gr.Textbox(visible=False)

            # ─── 🏷️ LoRAマネージャー ───
            with gr.Tab(t("tab_lora_manager")):
                def load_lora_list(mgr_type):
                    filename = "lora_char.txt" if mgr_type == "char" else "lora_sit.txt"
                    path = os.path.join(EXTENSION_DIR, filename)
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            return f.read()
                    return ""

                def save_lora_list(mgr_type, content):
                    filename = "lora_char.txt" if mgr_type == "char" else "lora_sit.txt"
                    path = os.path.join(EXTENSION_DIR, filename)
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(content)
                    return t("msg_lora_saved")

                def append_lora_list(mgr_type, input_text):
                    if not input_text or not input_text.strip():
                        return load_lora_list(mgr_type), ""
                    
                    filename = "lora_char.txt" if mgr_type == "char" else "lora_sit.txt"
                    path = os.path.join(EXTENSION_DIR, filename)
                    
                    # 既存の内容を確認し、改行が必要か判断する
                    current_content = ""
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            current_content = f.read()
                    
                    new_line = input_text.strip()
                    # 末尾が改行で終わっていない場合は改行を足す
                    if current_content and not current_content.endswith("\n"):
                        current_content += "\n"
                    
                    current_content += new_line + "\n"
                    
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(current_content)
                    
                    return current_content, "" # 最新リストを返し、入力欄を空にする

                gr.Markdown(t("lora_manager_desc"))
                
                with gr.Row():
                    lora_mgr_type = gr.Radio(
                        label=t("lora_type"),
                        choices=[(t("lora_type_char"), "char"), (t("lora_type_sit"), "sit")],
                        value="char"
                    )
                
                with gr.Row():
                    # １個ずつ追加するための入力エリア
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
                    value=lambda: load_lora_list("char"),
                    elem_id="smart_composer_lora_mgr_content"
                )
                
                with gr.Row():
                    save_lora_mgr_btn = gr.Button(t("btn_save_lora_list"), variant="primary")
                    lora_mgr_msg = gr.Markdown("")

                # イベント
                lora_mgr_type.change(fn=load_lora_list, inputs=[lora_mgr_type], outputs=[lora_mgr_content])
                save_lora_mgr_btn.click(fn=save_lora_list, inputs=[lora_mgr_type, lora_mgr_content], outputs=[lora_mgr_msg])
                append_lora_btn.click(fn=append_lora_list, inputs=[lora_mgr_type, lora_mgr_input], outputs=[lora_mgr_content, lora_mgr_input])

            # ─── 使い方 ───
            with gr.Tab(t("tab_usage")):
                gr.Markdown(t("usage_md"))

        # ─── イベントハンドラ (すべてのコンポーネント定義後に記述) ───
        save_btn.click(
            fn=save_all_settings,
            inputs=[
                language_selector, image_folder, memo_file, match_threshold, generation_count, fallback_enabled, auto_lora_enabled,
                gen_confidence, gen_positive, gen_negative, gen_custom_dict, gen_cat_base, gen_cat_char, gen_cat_nsfw
            ],
            outputs=[save_status],
        )
        preview_btn.click(
            fn=preview_compose,
            inputs=[image_folder, memo_file, match_threshold],
            outputs=[preview_image, preview_positive, preview_negative, preview_log],
        )
        gen_save_btn.click(
            fn=save_all_settings,
            inputs=[
                language_selector, image_folder, memo_file, match_threshold, generation_count, fallback_enabled, auto_lora_enabled,
                gen_confidence, gen_positive, gen_negative, gen_custom_dict, gen_cat_base, gen_cat_char, gen_cat_nsfw
            ],
            outputs=[gen_save_status],
        )
        append_btn.click(
            fn=lambda entry: append_to_memo(load_config().get("memo_file", ""), entry),
            inputs=[gen_output],
            outputs=[append_status],
        )
        gen_btn.click(
            fn=autogen_prompt,
            inputs=[gen_image, gen_section, gen_confidence, gen_positive, gen_negative, gen_cat_base, gen_cat_char, gen_cat_nsfw, gen_custom_dict],
            outputs=[gen_output, gen_log, hidden_gen_pos, hidden_gen_neg, hidden_gen_w, hidden_gen_h],
        )
        
        send_to_img2img_btn.click(
            fn=None,
            _js="""
            function(pos, neg, w, h) {
                var pos_elem = gradioApp().querySelector('#img2img_prompt textarea');
                if (pos_elem) {
                    pos_elem.value = pos;
                    updateInput(pos_elem);
                }
                var neg_elem = gradioApp().querySelector('#img2img_neg_prompt textarea');
                if (neg_elem) {
                    neg_elem.value = neg;
                    updateInput(neg_elem);
                }
                if (w && h) {
                    var w_num = gradioApp().querySelector('#img2img_width input[type="number"]');
                    var w_range = gradioApp().querySelector('#img2img_width input[type="range"]');
                    if (w_num) { w_num.value = w; updateInput(w_num); }
                    if (w_range) { w_range.value = w; updateInput(w_range); }
                    var h_num = gradioApp().querySelector('#img2img_height input[type="number"]');
                    var h_range = gradioApp().querySelector('#img2img_height input[type="range"]');
                    if (h_num) { h_num.value = h; updateInput(h_num); }
                    if (h_range) { h_range.value = h; updateInput(h_range); }
                }
                var tabs = gradioApp().querySelectorAll('#tabs > div > button');
                if (tabs && tabs.length > 0) {
                    for(var i=0; i<tabs.length; i++){
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
