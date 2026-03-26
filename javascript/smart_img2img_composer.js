function sc_send_to_img2img(image, prompt) {
    if (!image) return;

    // 1. Switch to img2img tab
    if (typeof switch_to_img2img === 'function') {
        switch_to_img2img();
    } else {
        const tabs = document.querySelectorAll('#tabs > div > button');
        tabs.forEach(tab => {
            if (tab.innerText.trim() === 'img2img') {
                tab.click();
            }
        });
    }

    // 2. Find img2img components
    const img2img_prompt = document.querySelector('#img2img_prompt textarea');
    const img2img_image = document.querySelector('#img2img_image input[type="file"]');
    
    if (img2img_prompt) {
        img2img_prompt.value = prompt;
        updateInput(img2img_prompt);
    }

    if (img2img_image && image) {
        fetch(image)
            .then(res => res.blob())
            .then(blob => {
                const file = new File([blob], "image.png", { type: "image/png" });
                const dt = new DataTransfer();
                dt.items.add(file);
                img2img_image.files = dt.files;
                img2img_image.dispatchEvent(new Event('change', { bubbles: true }));
            });
    }

    console.log("Smart Composer: Sent prompt and image to img2img.");
}

// Helper to trigger Gradio's change detection
function updateInput(target) {
    let event = new Event('input', { bubbles: true });
    target.dispatchEvent(event);
    event = new Event('change', { bubbles: true });
    target.dispatchEvent(event);
}
