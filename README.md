# <img src="docs/images/icon.jpg" width="36" style="border-radius: 8px; vertical-align: bottom;" /> Smart Img2Img Composer v1.2 Stable

[日本語版 (README_ja.md)](README_ja.md)

![Smart Img2Img Composer Overview](docs/images/en1.png)

## Overview
**Smart Img2Img Composer** is an advanced prompt construction and asset management architecture for the AUTOMATIC1111 Stable Diffusion WebUI, designed to control and deeply automate your img2img workflows.

Equipped with autonomous tag analysis from reference images, memo file synchronization, a unique lottery system for LoRAs and wildcards (Inventory feature), and model-specific prompt optimization. It fully automates tedious batch processing and prompt building, drastically improving creative efficiency and generation quality.

---

## 📥 Installation

1. Open the `Extensions` tab in your AUTOMATIC1111 WebUI.
2. Select the `Install from URL` tab.
3. Paste the following **Repository URL** into the URL field:
   ```text
   https://github.com/MaxwelI-st/smart-img2img-composer
   ```
4. Click the `Install` button.
5. After installation succeeds, go to the `Installed` tab and click `Apply and restart UI`.

*(Note: To use the Auto-Prompt Generator feature, the "WD14 Tagger" extension must be installed and active beforehand.)*

---

## ✨ Full Features of v1.2

### 🧠 Autonomous Analysis & Prompt Generator (Tagger Analyzer)
![Tag Analysis and Auto Prompt Gen](docs/images/en2.png)
*   **Auto Tag Extraction**: In the `Prompt Generator` tab, it integrates with WD14 Tagger to extract high-precision tags from uploaded images using deep learning.
*   **Category Controls**: Individual sliders for categories (Composition, Background, Character, NSFW, etc.) allow fine-tuned control over "Confidence Thresholds," giving you only the tags you want.
*   **Mosaic Auto-Detection**: Automatically detects mosaic/censored attributes in images and injects corresponding protective tags (e.g., `censored`).
*   **🚀 1-Click Warp**: Once you are satisfied with your extracted prompt, click the dedicated button to **warp directly to the img2img tab** with all prompt data and images fully intact, enabling an immediate start to your generation.

### 🔗 Filename-Driven Automatic Prompt Synchronization (Memo Sync)
![Memo Synchronization System](docs/images/en3.png)
*   **Auto Matching**: Automatically matches filenames in the `Reference Image Folder` with manually written section tags (e.g., `[image_01]`) in your `Memo File` (.txt).
*   **Match Threshold**: The UI slider allows for flexible fuzzy-matching, ensuring seamless application of image-specific unique prompts even during massive bulk generation runs.

### 🛡️ Model-Specific Prompt Optimization (Smart Negative & Polish)
![Smart Negative Feature](docs/images/en4.png)
*   **Smart Negative**: By selecting your target model architecture (SDXL, Pony, Illustrious, Animagine, etc.) from the `Active Profile`, the system automatically injects or overwrites the absolute optimal negative prompts to maximize that model's potential.
*   **Prompt Order Optimization**: Automatically sorts the generated tags based on your selected profile. For Pony lineages, critical quality items like `score_9, score_8_up...` are forced to the front.
*   **Prompt Polish**: Effortlessly cleans up syntax errors right before generation, such as duplicate tags, trailing spaces, and double commas (`, , `), while completely protecting your intentional LoRA weights.

### 📦 Bias-Prevention Autonomous Inventory Control (Inventory Logic)
![Inventory Control System](docs/images/en5.png)
*   **Asset Management**: Manage custom lists of Character LoRAs, Situation LoRAs, and Wildcards directly from the WebUI inside the `Asset Lists` tab.
*   **Inventory Control**: The robust lottery logic remembers the "usage history" of assets during randomized generation. It heavily prioritizes **"assets that have never been used"** or **"assets with the lowest usage counts."** This entirely eliminates repetitive "LoRA fatigue" during mass productions.

### 🪄 Auto-Syntax Repair & Custom Dictionary
*   Setup simple shortcuts like `night, city > cyberpunk cityscape, neon lights...` in the Custom Dictionary. Short memo keywords will be beautifully expanded into rich, descriptive prompts automatically.

### 🎛️ Output Organization & High-Density UI
![Streamlined Professional UI Design](docs/images/en6.png)
*   **Health Check (Fail-Safe)**: Real-time path validation for folders and text files with ✅ / ❌ indicators on the UI to prevent silly execution crashes.
*   **Auto-Filename**: Automatically renames output images (e.g., `masterpiece-1girl-smile_0001.png`) by combining the core extracted prompt tags.
*   **Smart Output Sorting**: Change the `Sort Mode` to automatically create clean subfolders organized by "Preset Name," "Section Name," or "Date" without breaking standard save settings.

---

## 📖 Quick Start Usage

1. **Global Settings**: In the `Smart Img2Img Composer` tab under `Settings & Preview`, enter your `Reference Image Folder` and (optional) `Memo File` path.
2. **Options**: Check `Auto-Optimize Prompt` and `Smart Negative`, then select your `Active Profile`.
3. **Save Preset**: Once configured, type a name and click "Save Settings" to store your Preset.
4. **Execute**: Open the `img2img` tab, expand the accordion, check `Enable`, and hit "Generate." The extension will automatically batch-process everything in the folder using your synced memos, optimized prompts, and random inventories!

---
*Developed by Antigravity / Images generated by Gemini*
