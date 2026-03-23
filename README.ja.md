# 🎲 Smart Img2Img Composer

![Smart Img2Img Composer バナー](docs/images/hero_banner_ja.png)

AUTOMATIC1111 Stable Diffusion WebUI 用拡張機能。ランダムに画像を選び、関連するプロンプトを自動取得して img2img を実行します。

![機能一覧](docs/images/feature_overview_ja.png)

### 動作の仕組み

![ワークフロー](docs/images/workflow_diagram_ja.png)

## 🌟 主な機能

1. **ランダム画像＆プロンプト取得**: 指定フォルダ内の画像からランダムに選び、メモファイルに紐づいたプロンプトを適用してimg2img実行。
2. **ネガティブプロンプト対応**: `positive:` と `negative:` に分けて細かくプロンプトを設定可能。
3. **画像サイズの自動調整機能**: SDXL (1024〜1536px) や SD1.5 (512px) など、モデルに合わせて元画像のアスペクト比を維持したまま自動で解像度を最適化。
4. **WD14 Tagger連携（プロンプト自動生成）**: 画像を解析し、構図やシーンのタグだけを抽出してメモファイル用のプロンプトを全自動生成。
5. **好みのプロンプト置き場**: 条件に合致したタグが画像から検出された際に、好みのプロンプトを自動でブレンド。

## 📸 スクリーンショット

### ⚙️ 設定 & プレビュー
画像フォルダ、メモファイル、一致率の設定と、プレビュー結果の確認画面。

![設定 & プレビュー](docs/images/ui_settings.png)

### 🏷️ プロンプト自動生成（WD14 Tagger連携）
画像をアップロードするだけで、構図・ポーズ・照明・NSFWなどスマートにカテゴリ別フィルタリングしてタグを抽出。

![プロンプト自動生成](docs/images/ui_prompt_gen.png)

### 🎲 img2img 連携
img2imgタブ内のチェックボックス1つで有効化。他のスクリプトとも共存可能。
画像サイズの「自動調整ON/OFF」や「スライダーによるベース解像度指定（512px〜2048px）」を設定できます。

![img2img 連携](docs/images/ui_img2img.png)

---

## 🛠️ インストール

`smart-img2img-composer` フォルダを `stable-diffusion-webui/extensions/` に配置して WebUI を再起動してください。
※プロンプト自動生成機能を利用するには [stable-diffusion-webui-wd14-tagger](https://github.com/toriato/stable-diffusion-webui-wd14-tagger) がインストールされている必要があります。

---

## 📖 使い方 (基本編)

### 1. メモファイルを作る

テキストファイルを作成して以下の形式で書きます：

```text
[タイトル1]
positive:
(masterpiece:1.1), 1girl, portrait

negative:
lowres, blurry, artifact

lora:
add_detail:0.8

[city]
positive:
skyline, sunset, cinematic lighting

[default]
positive:
1girl, simple background

# コメント行（#で始まる行や空行は無視されます）
# positive/negativeの指定がない場合は全体がpositiveとして扱われます。
```

📝 **新機能 Tips:**
* **`[default]` セクション**: ファイル名に合致するセクションがない場合の「フォールバック」として使用されます（設定の「fallback有効化」がONの場合）。
* **`lora:` 指定**: `lora:` の下に `LoRA名:強度` を書くと、自動でインストール済みのLoRAか検証し `<lora:add_detail:0.8>` の形でプロンプト先頭へ追加してくれます。未インストールの場合は無視されるのでエラーになりません！

### 2. img2img で生成

1. 「**🎲 Random Composer**」タブの「⚙️ 設定 & プレビュー」で画像フォルダとメモファイルのパスを入力して **保存**。
2. **img2img** タブを開き、下部の「**🎲 Random Composer**」を展開して「**有効化**」にチェック。
3. Generateボタンを押すと、自動で画像が切り替わりながら生成されます！

---

## ✨ 使い方 (プロンプト自動生成機能)

メモファイルを手作業で作るのが大変な場合は、**🏷️ プロンプト自動生成** タブを使って画像を解析できます。

1. 画像をアップロードし、セクション名（例： `タイトル1`）を入力。
2. **🏷️ 抽出するタグの種類** で、残したいタグのカテゴリ（構図、キャラ属性、NSFWなど）を選択します。
   * 🔞 **強力なNSFW・フェティッシュタグ抽出**: 一般的な抽出ツールでは弾かれがちなマニアックな体位、フェティッシュ状態、局所・モザイク指定、体液などの詳細なR-18タグも、専用カテゴリ（「行為・アクション」「体液・汚れ系」「局所・モザイク」など）で漏らさず網羅して抽出可能です！
3. **✨ デフォルトポジティブ** / **🚫 デフォルトネガティブ** に毎回付与したい画質向上タグなどを入力。
4. **📚 好みのプロンプト置き場（条件付与）** に、以下のように条件タグと追加したいプロンプトを書いておくと、画像にその要素があるときだけ自動で追加されます！
   ```text
   night, city > cyberpunk cityscape, neon lights, cinematic lighting, rain reflections, highly detailed
   sunset, skyline > golden hour lighting, dramatic sky colors, atmospheric perspective
   1girl, smile > beautiful detailed eyes, soft lighting, expressive face, warm atmosphere
   outdoors, wind > flowing hair, dynamic pose, motion blur, cinematic composition
   street, night > urban photography style, moody shadows, film grain, realistic lighting
   ```
5. **🏷️ タグ解析＆生成** を押し、結果が良ければ **📝 メモファイルに追記** ボタンで保存します。

📝 **Tips**: 入力した設定（タグ種類や辞書など）は「💾 設定を保存」ボタンを押すことで、次回以降も保持されます！

---

## ⚙️ 互換性

ADetailer / ControlNet / WD14 Tagger / Tag Autocomplete / FABRIC 等と競合せず、すべて同時に適用可能です。

## 📦 依存関係 (Dependencies)

オプション機能（プロンプト自動生成など）は WD14 Tagger などの既存の拡張機能に依存しています。本拡張機能自体がサードパーティのモデルやコードを再配布することはありません。
