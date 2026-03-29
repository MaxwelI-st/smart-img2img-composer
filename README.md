# Smart Img2Img Composer v1.1.2 Stable

[日本語版 (README_ja.md)](README_ja.md)

![Smart Img2Img Composer Overview](docs/images/1en.png)

## Overview
An advanced prompt construction and asset management architecture for the AUTOMATIC1111 Stable Diffusion WebUI, designed to control and integrate img2img workflows.
Equipped with autonomous tag analysis from reference images, memo file synchronization, and a unique lottery system for LoRAs and wildcards, it automates tedious batch processing and prompt building, drastically improving creative efficiency.

## Key Features

### 🧠 Autonomous Tag Analysis & Prompt Construction (Tagger Analyzer)

![Tag Analysis and Auto Prompt Gen](docs/images/2en.png)

*   In the **Prompt Generator** tab, it integrates with WD14 Tagger to extract high-precision tags using deep learning.
*   Individual sliders for categories such as Composition, Background, Character, and Lighting allow fine-tuned control over "Confidence Thresholds."
*   Automatically detects mosaic attributes in images and injects corresponding tags.
*   Once satisfied with the extracted prompt, use the dedicated button to **warp to the img2img tab** while maintaining all data, enabling an immediate 1-click generation start.

### 🔗 Filename-Driven Automatic Prompt Synchronization

*   Automatically matches filenames in the **Reference Image Folder** with section names (e.g., `[image_01]`) in your **Memo File** (.txt).
*   The **Match Threshold** slider in the UI provides flexibility for non-exact matches, ensuring seamless application of image-specific prompts and targeted LoRAs during bulk processing.

### 🛡️ Profile-Dependent Negative Prompt Optimization (Smart Negative)

![Smart Negative Feature](docs/images/3en.png)

*   Select your target model (SDXL, Pony, Illustrious, etc.) from the **Active Profile** dropdown. When **Smart Negative** is enabled, it automatically adds or overwrites optimal negative prompts for that specific model.
*   The prompt order is also optimized. For example, selecting the Pony profile automatically sorts critical quality tags like `score_9, score_8_up...` to the beginning, boosting overall generation quality.

### 📦 Bias-Prevention Autonomous Inventory Control (Inventory Logic)

![Inventory Control System](docs/images/4en.png)

*   The system monitors usage counts for randomized LoRAs and wildcards registered in the **Asset Lists** tab, visible on the **Inventory** dashboard.
*   The lottery logic prioritizes unused or infrequently used assets during generation, preventing repetitive "LoRA fatigue" and ensuring maximum diversity in large-scale productions.

### 🪄 Auto-Syntax Repair & Custom Dictionary Protocol

*   The **Custom Dictionary** expands short memos like `night, city > cyberpunk cityscape, neon lights...` into rich, descriptive prompts automatically.
*   With **Prompt Polish** enabled, common syntax errors like double commas (`, ,`), stray spaces, or mismatched brackets are automatically cleaned up right before generation.

### 🎛️ Fail-Safe Design & High-Density UI

![Streamlined Professional UI Design](docs/images/5en.png)

*   **Health Check**: Real-time path validation for folders and files with ✅ / ❌ indicators on the UI to prevent execution errors.
*   **Compact UI**: Space-saving optimization of standard Gradio layouts organizes sliders and checkboxes into efficient single-line rows.
*   **Smart Output Sorting**: Change the **Sort Mode** in the **Output Settings** within the img2img tab to automatically create subfolders by "Preset Name" or "Date," keeping outputs organized without breaking standard save paths.

---

## Installation
1. Open the `Extensions` tab in AUTOMATIC1111 WebUI.
2. Go to the `Install from URL` tab and paste this repository's URL.
3. Click "Install" and then "Apply and restart UI."

*Note: The "WD14 Tagger" extension must be installed and active to use the Auto-Prompt Gen feature.*

---

## Usage Workflow
This system coordinates "Preparation & Testing" in a dedicated tab with "Execution" in the img2img tab.

### 1. ⚙️ Global Settings & Preset Management
Navigate to the "Settings & Preview" tab under "Smart Img2Img Composer."
*   **Path Configuration**: Specify paths for the `Reference Image Folder` and `Memo File`. A ✅ health check indicates successful recognition.
*   **Profiles & Optimization**: Choose your `Active Profile` and enable features like `Smart Negative` or `Prompt Polish`.
*   **Saving Presets**: Save your current configuration as a "Preset" to recall environments instantly from the dropdown menu.

### 2. 🏷️ Tag Analysis & 1-Click Warp (Prompt Generator)
Handle individual image analysis and test generates in the "Prompt Generator" tab.
*   Analyze uploaded images using WD14 Tagger and adjust category sliders for optimal tag extraction.
*   Once satisfied, use the dedicated button to **warp to the img2img tab** with all data intact.

### 3. 🎲 Asset Lists & Inventory Control
*   **Asset Lists**: Directly manage and edit lists of Character LoRAs, Situation LoRAs, and Wildcards within the WebUI.
*   **Inventory Control**: When Inventory Mode is enabled, monitor global usage counts (stock) here and reset them as needed.

### 4. 🖼️ Img2Img Execution & Organization
Expand the "Smart Img2Img Composer" accordion in the `img2img` tab.
*   **Enable**: Activate the extension to start automated batch processing with folder monitoring, memo synchronization, and inventory lottery logic.
*   **Random Slots**: Control where random LoRAs are injected (Front, Back, or after specific tags).
*   **Organization (Output Settings)**: Set the `Sort Mode` to "By Preset" or "By Date" for automatic image sorting.
