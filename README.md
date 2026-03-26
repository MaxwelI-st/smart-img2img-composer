# 🎲 Smart Img2Img Composer v1.1 Stable

[日本語版はこちら (README_ja.md)](README_ja.md)

![Smart Img2Img Composer Banner](docs/images/hero_banner.png)

### **"Mass Production, Met Art Quality."**
**The ultimate batch generation and management solution for YouTube Shorts, TikTok, and SNS content creators.**

A professional-grade extension for AUTOMATIC1111 Stable Diffusion WebUI. Automate the combination of massive image assets and prompts, reducing creative workload by up to 80%.

---

## 🌟 What's New in v1.1
Version 1.1.2 introduces enhanced UI organization, a dedicated inventory management system, and significantly expanded specialized tag libraries.

### 📦 Dedicated Inventory Management Tab
Total control over randomization variety. A new standalone tab allows you to monitor usage counts for every LoRA and wildcard asset. This ensures maximum diversity in large-scale generations by prioritizing underused items. Features real-time stock checking and granular reset options.

### 🚀 Improved img2img Synchronization
The integration is now truly bi-directional. The "Send to img2img" button now transfers **both the generated prompt and the source image** directly into the main img2img generation tab with a single click, eliminating manual file uploads.

### 🔞 Expanded NSFW & Fetish Tag Library
Massively expanded specialized tag definitions including machine FET (milking, breast pumps), fluids, and detailed fetish states. Complemented by **📏 Group-Based Tag Limits** (Base, Character, NSFW) to maintain perfect prompt balance.

### 🧱 Intelligent Mosaic Auto-Prompting
Automatically detects censorship in uploaded images and injects weight-adjusted mosaic prompts (Low/Med/High) to ensure consistency in generated results.

---

## 🛠️ Powerful Core Systems

### 1. 📂 Advanced Preset Management
Save and load complex configurations — including folder paths, thresholds, and resolutions — as "Presets". Seamlessly switch between different projects or characters with a single click.

### 2. 🧬 High-Precision LoRA Global Tuning
Fine-tune the weights of all active LoRAs simultaneously using a global slider with **0.05 increments**. Achieve the perfect balance and stylistic nuance for every batch.

### 3. 📁 Intelligent Output Sorting
Automatically organize your generated masterpieces into subfolders based on Preset Name, Section Name, or Date. Eliminate the chaos of "mixed-output" directories forever.

---

## ✨ Cutting-Edge Auto-Prompting (WD14 Tagger)

Powered by deep integration with WD14 Tagger.

- **Categorized Smart Extraction**: Filter tags precisely by Composition, Pose, Lighting, NSFW, and more.
- **Global Category Toggle**: Instantly select or deselect groups of tags with one click.
- **Custom Dictionary Translation**: Automatically transform raw extracted tags into your preferred descriptive style or highly-detailed phrases.

---

## 🎲 Seamless img2img Integration

Located natively at the bottom of the img2img tab. Designed to work in perfect harmony with ADetailer, ControlNet, and other popular extensions.

- **Random Injection Slots**: Manage 5 slots (Character, Situation, and 3 Wildcards) for dynamic randomization.
- **Strategic Prompt Positioning**: Choose to inject your random prompts either "Before" or "After" the main prompt for maximum architectural control.

---

## 📖 Quick Start Guide

A comprehensive manual is built directly into the UI via the "**📖 User Manual**" tab.

1.  **Configure**: Set your Image Folder and Memo File in the "⚙️ Settings & Preview" tab.
2.  **Verify**: Save your Preset and ensure all Health Check icons are **✅**.
3.  **Generate**: Enable the extension in the img2img tab and press "Generate".

---

## 📦 Built for Reliability
- **Complete Internationalization (i18n)**: Fully supported in Japanese and English.
- **Enterprise-Grade Compatibility**: Works alongside ADetailer, ControlNet, Dynamic Prompts, and FABRIC.
- **State Persistence**: Securely stores settings in `config.json`.

---

Licensed under the MIT License. Developed for Professional Creators.
