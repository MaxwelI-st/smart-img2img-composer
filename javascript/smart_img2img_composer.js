/**
 * Smart Img2Img Composer - JavaScript Helper
 *
 * 【初回だけプロンプトが届かない問題の原因と解決策】
 *
 * 旧実装の問題:
 *   プロンプト即時転送 → タブ切り替え(250ms後) の順だったため、
 *   初回は img2img タブが未初期化で textarea が DOM に存在せず空振り。
 *   2回目以降は DOM が既に存在するので届く。
 *
 * 新実装の順序:
 *   250ms後: タブ切り替え（先にDOMを確実に出現させる）+ 画像転送開始
 *   450ms後: プロンプトセット（DOM描画完了を待つ）+ リトライ付き
 */

/** Gradio Shadow DOM / 通常 DOM 両対応 querySelector */
function scApp() {
    if (typeof gradioApp === 'function') return gradioApp();
    return document.querySelector('gradio-app') || document;
}

/** テキストエリアに値をセット + Gradio 変更検知トリガー */
function scSetTextarea(selector, value) {
    var app = scApp();
    var area = app.querySelector(selector + ' textarea');
    if (!area) return false;
    var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
    setter.call(area, value);
    area.dispatchEvent(new Event('input',  { bubbles: true }));
    area.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
}

/** img2img タブへ切り替え（即時） */
function scSwitchToImg2img() {
    if (typeof switch_to_img2img === 'function') {
        try { switch_to_img2img(); return true; } catch(e) {}
    }
    var app = scApp();
    var tabs = app.querySelectorAll('#tabs > div > button');
    var found = false;
    tabs.forEach(function(btn) {
        var txt = (btn.innerText || btn.textContent || '').toLowerCase().trim();
        if (!found && txt.indexOf('img2img') !== -1 && txt.indexOf('settings') === -1) {
            btn.click();
            found = true;
        }
    });
    if (found) return true;
    if (tabs.length > 1) { tabs[1].click(); return true; }
    return false;
}

/**
 * プロンプトセット（リトライ付き）
 * タブ切り替え直後は textarea がまだ描画中のことがあるため
 * 最大 retries 回、100ms 間隔で再試行する
 */
function scSetPromptsWithRetry(pos, neg, delay_ms, retries) {
    setTimeout(function() {
        var ok = scSetTextarea('#img2img_prompt', pos);
        scSetTextarea('#img2img_neg_prompt', neg);
        if (!ok && retries > 1) {
            scSetPromptsWithRetry(pos, neg, 100, retries - 1);
        }
    }, delay_ms);
}

/** 画像を fetch して img2img の file input に流し込む */
function scTransferImage(imgUrl) {
    fetch(imgUrl)
        .then(function(r) { return r.blob(); })
        .then(function(blob) {
            var file = new File([blob], 'sc_image.png', { type: blob.type || 'image/png' });
            var app = scApp();
            [
                app.querySelector('#img2img_image'),
                app.querySelector('#img2img_sketch'),
                app.querySelector('[data-testid="img2img"]'),
            ].forEach(function(c) {
                if (!c) return;
                var inp = c.querySelector('input[type="file"]');
                if (!inp) return;
                var dt = new DataTransfer();
                dt.items.add(file);
                inp.files = dt.files;
                inp.dispatchEvent(new Event('change', { bubbles: true }));
            });
        })
        .catch(function(e) { console.warn('[SC] Image fetch failed:', e); });
}

/**
 * メインハンドラ
 *
 * タイムライン:
 *   0ms    : 関数呼び出し（Gradio _js 後処理待ちのため即時操作はしない）
 *   250ms  : ① タブ切り替え（DOMを出現させる）  ② 画像転送開始
 *   450ms  : ③ プロンプトセット（リトライ最大5回 × 100ms）
 *
 * ポイント: タブを先に切り替えることで初回でも textarea が存在する状態を作る
 */
function scSendToImg2img(img, entry, default_neg) {
    // ── プロンプト解析 ──
    var pos = '';
    var neg = (default_neg && typeof default_neg === 'string') ? default_neg.trim() : '';

    if (entry && typeof entry === 'string') {
        var posMarker = 'positive:\n';
        var negMarker = '\n\nnegative:\n';
        var pi = entry.indexOf(posMarker);
        if (pi !== -1) {
            var after = entry.substring(pi + posMarker.length);
            var ni = after.indexOf(negMarker);
            if (ni !== -1) {
                pos = after.substring(0, ni).trim();
                neg = after.substring(ni + negMarker.length).trim();
            } else {
                pos = after.trim();
            }
        } else {
            pos = entry.trim();
        }
    }

    // ── 画像URL解決 ──
    var imgUrl = null;
    if (img) {
        if (typeof img === 'string' && img.length > 0)        { imgUrl = img; }
        else if (img.data)                                     { imgUrl = img.data; }
        else if (img.path)                                     { imgUrl = img.path; }
        else if (Array.isArray(img) && img[0] && img[0].data) { imgUrl = img[0].data; }
    }

    // ── Step 1 (250ms後): タブ切り替え ＋ 画像転送 ──
    setTimeout(function() {
        scSwitchToImg2img();
        if (imgUrl) scTransferImage(imgUrl);

        // ── Step 2 (さらに200ms後): プロンプトセット ──
        // タブを開いた後 textarea の描画を待ってからセット、最大5回リトライ
        scSetPromptsWithRetry(pos, neg, 200, 5);

    }, 250);
}
