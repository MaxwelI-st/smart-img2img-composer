# <img src="docs/images/icon.jpg" width="36" style="border-radius: 8px; vertical-align: bottom;" /> Smart Img2Img Composer v1.2 Stable

[English Version (README.md)](README.md)

![Smart Img2Img Composer 全体概要](docs/images/ja1.png)

## 概要 (Overview)
**Smart Img2Img Composer** は、AUTOMATIC1111 Stable Diffusion WebUI 向けの、img2imgワークフローを統合的に制御・自動化するための高度な拡張機能です。

参照画像の自律タグ解析、メモファイルとのプロンプト同期、LoRAやワイルドカードの独自の抽選システム（インベントリ機能）、そしてモデル固有のプロンプト最適化機能を備えています。煩雑なimg2imgの大量バッチ処理やプロンプト構築作業を全自動化し、作業効率と生成品質を飛躍的に向上させます。

---

## 📥 インストール方法 (Installation)

1. AUTOMATIC1111 WebUIの `Extensions` タブを開きます。
2. `Install from URL` タブを選択します。
3. 以下の**リポジトリURL**を入力欄にペーストします：
   ```text
   https://github.com/MaxwelI-st/smart-img2img-composer
   ```
4. `Install` ボタンをクリックします。
5. インストール完了後、`Installed` タブへ移動し `Apply and restart UI` をクリックしてWebUIを再起動してください。

*(※タグ解析機能を使用する場合、あらかじめ「WD14 Tagger」拡張機能がインストールされ有効になっている必要があります。)*

---

## ✨ v1.2 の全機能紹介 (Full Features)

### 🧠 参照画像の自律解析とプロンプト構築 (Tagger Analyzer)
![タグ解析とプロンプト自動生成](docs/images/ja2.png)
* **自動タグ抽出**: `Prompt Generator` タブにて、WD14 Taggerと連携し、深層学習を用いてアップロードされた画像から高精度なタグを抽出します。
* **カテゴリ別コントロール**: 構図、背景、人物、NSFW要素など、細分化されたカテゴリごとに「信頼度（Confidence）のしきい値」を個別に設定し、必要なタグだけを厳選できます。
* **モザイク自動検知**: 画像からモザイク・検閲属性を検知し、適切なタグ（`censored` 等）を自動で付与します。
* **🚀 1クリック・ワープ**: 納得のいくプロンプトが抽出できたら、専用ボタンを押すだけで**プロンプトと画像を保持したまま自動的に img2img タブへ画面遷移**し、即座に生成を開始できます。

### 🔗 ファイル名駆動型のプロンプト自動同期 (Memo Sync)
![メモ同期機能](docs/images/ja3.png)
* **自動紐付け**: `Reference Image Folder`（参照画像フォルダ）内のファイル名と、`Memo File`（.txt）内に記述したセクション名（例：`[image_01]`）を自動でマッチングします。
* **Match Threshold（一致度設定）**: スライダーを設定することで、完全一致でなくても柔軟に紐付けることができ、大量のバッチ処理時にも「画像ごとの固有プロンプト」をシームレスに適用します。

### 🛡️ モデル別プロンプト自動最適化 (Smart Negative & Polish)
![スマート・ネガティブ機能](docs/images/ja4.png)
* **Smart Negative（ネガティブ補強）**: `Active Profile` から使用するモデル体系（SDXL, Pony, Illustrious, Animagineなど）を選択すると、そのモデルのポテンシャルを最大限に引き出す必須ネガティブプロンプトが自動で追加・上書きされます。
* **プロンプト並び順の最適化**: 選択したプロファイルに合わせてプロンプトの順序をソートします。例えばPony系なら `score_9, score_8_up...` 等の品質タグを自動で最前列へ移動させます。
* **Prompt Polish（プロンプト整形）**: 重複した不要なタグや、連続するカンマ（`, , `）、無駄な空白を生成直前に完璧にクリーンアップします。（※意図的なLoRAウェイトは保護されます）

### 📦 資産の偏りを防ぐ自律型インベントリ制御 (Inventory Logic)
![インベントリ制御システム](docs/images/ja5.png)
* **アセット管理**: `Asset Lists` タブで、ランダム生成に使用するキャラクターLoRA、シチュエーションLoRA、ワイルドカードのリストをWebUI上から直接管理できます。
* **Inventory Control（在庫管理）**: ランダム生成時にアイテムの「使用回数履歴」を記憶し、**「まだ一度も使われていないアセット」や「使用回数が少ないアセット」を優先的に高確率で選出**する独自の抽選ロジックが働きます。これにより「同じLoRAばかりが選ばれる」マンネリ化を完全に防止します。

### 🪄 独自辞書によるタグ展開 (Custom Dictionary)
* `night, city > cyberpunk cityscape, neon lights...` のように辞書登録しておくことで、短いメモ書きをリッチな長文プロンプトへ全自動で変換・展開します。

### 🎛️ 出力整理と高密度UI設計 (Output Organization & UI)
![操作を快適にする洗練された設計](docs/images/ja6.png)
* **Health Check（フェイルセーフ）**: 設定したフォルダやテキストファイルのパスが存在するかをリアルタイムに検証し、UI上に ✅ / ❌ で表示します。
* **Auto-Filename（自動命名）**: 抽出された重要なプロンプトタグを組み合わせて、出力画像ファイルの名前（例：`masterpiece-1girl-smile_0001.png`）を自動生成します。
* **Smart Output Sorting**: 保存先サブフォルダを「指定したプリセット名」や「セクション名」「日付」ごとに自動作成・仕分けし、出力結果を綺麗に整理できます。

---

## 📖 使い方 (Quick Start)

1. **基本設定**: `Smart Img2Img Composer` タブの `Settings & Preview` で、画像の入ったフォルダとメモファイル（任意）のパスを指定します。
2. **生成オプション**: `Auto-Optimize Prompt` や `Smart Negative` にチェックを入れ、プロファイルを指定します。
3. **プリセット保存**: 設定が完了したら名前を付けて「Save Settings」でプリセットとして保存します。
4. **img2img の実行**: `img2img` タブを開き、アコーディオン内の `Enable` にチェックを入れて「Generate」ボタンを押すと、フォルダ内の画像に対して自動でプロンプト処理と画像生成が連続実行されます！

---
*Developed by Antigravity / 画像生成 by Gemini*
