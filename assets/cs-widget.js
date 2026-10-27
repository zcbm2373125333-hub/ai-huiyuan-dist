/**
 * AI会员充值站 · 导购站自动接待与多店分流挂件（纯前端关键词规则，无付费 API）
 * 预留：window.__CS_LLM_HOOK__ = async (text, ctx) => string|null  未命中规则时可异步调用
 */
(function () {
  const CFG = window.__CS_CONFIG__ || {};
  const FAQ = window.__CS_FAQ__ || { intents: [], quick: [], fallback: '' };
  const SHOP1 = CFG.shopUrl || 'https://catfk.com/shop/IW58ZQO9';
  const SHOP2 = CFG.shop2Url || 'https://wzyp.cn/shop/XIK4BB7S';
  const SHOP3 = CFG.shop3Url || 'https://www.16688.com.cn/shop/S385728';
  const ORD1 = CFG.orderUrl || 'https://catfk.com/order';
  const ORD2 = CFG.order2Url || 'https://wzyp.cn/order';
  const ORD3 = CFG.order3Url || 'https://www.16688.com.cn/order';

  function fill(tpl) {
    return String(tpl || '')
      .replaceAll('{shopUrl}', SHOP1)
      .replaceAll('{shop2Url}', SHOP2)
      .replaceAll('{shop3Url}', SHOP3)
      .replaceAll('{orderUrl}', ORD1)
      .replaceAll('{order2Url}', ORD2)
      .replaceAll('{order3Url}', ORD3)
      .replaceAll('{wechat}', CFG.wechat || '店铺商品页「联系TA」站内留言')
      .replaceAll('{hours}', CFG.hours || '留言后尽快回复')
      .replaceAll('{brand}', CFG.brand || 'AI会员充值站');
  }

  function score(text, keywords) {
    const t = text.toLowerCase();
    let s = 0;
    for (const k of keywords) {
      const kk = String(k).toLowerCase();
      if (!kk) continue;
      if (t.includes(kk)) s += kk.length >= 2 ? 2 : 1;
    }
    return s;
  }

  function matchIntent(text) {
    let best = null;
    let bestScore = 0;
    for (const intent of FAQ.intents || []) {
      const s = score(text, intent.keywords || []);
      if (s > bestScore) {
        bestScore = s;
        best = intent;
      }
    }
    return bestScore > 0 ? best : null;
  }

  async function reply(text) {
    const intent = matchIntent(text);
    if (intent) return { text: fill(intent.answer), intent: intent.id, source: 'rules' };
    if (typeof window.__CS_LLM_HOOK__ === 'function') {
      try {
        const alt = await window.__CS_LLM_HOOK__(text, { cfg: CFG, faq: FAQ });
        if (alt) return { text: String(alt), intent: 'llm', source: 'llm' };
      } catch (_) {}
    }
    return { text: fill(FAQ.fallback || '暂时无法回答，请联系人工客服。'), intent: null, source: 'fallback' };
  }

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function linkify(text) {
    return fill(text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener nofollow">$1</a>')
      .replace(/\n/g, '<br>');
  }

  function ensureMultiShopUI() {
    if (!document.querySelector('.notice')) {
      const hd = document.querySelector('header.top');
      if (hd && hd.parentNode) {
        const bar = el('div', 'notice', `<div class="wrap" style="padding:8px 20px;display:flex;flex-wrap:wrap;align-items:center;gap:8px"><strong>多店分流 · 微信/支付宝任选：</strong><a href="${SHOP1}" target="_blank" rel="nofollow sponsored noopener" style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:6px;font-weight:700;text-decoration:none">通道一：云猫主店（支付宝·45款全系）</a><a href="${SHOP2}" target="_blank" rel="nofollow sponsored noopener" style="background:#059669;color:#fff;padding:2px 8px;border-radius:6px;font-weight:700;text-decoration:none">通道二：链动分店（支持微信支付+支付宝·35款）</a><a href="${SHOP3}" target="_blank" rel="nofollow sponsored noopener" style="background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:6px;font-weight:700;text-decoration:none">通道三：16688分店（含Codex 250 ¥88.9/备用自动发卡）</a></div>`);
        hd.insertAdjacentElement('afterend', bar);
      }
    }
    if (!document.querySelector('.float-bar')) {
      const fb = el('div', 'float-bar', `<div class="wrap" style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px"><span style="font-weight:700;color:#e2e8f0">多店自动发卡通道：</span><div style="display:flex;flex-wrap:wrap;gap:6px"><a href="${SHOP1}" target="_blank" rel="nofollow sponsored noopener" style="background:#1d4ed8;color:#fff;padding:5px 10px;border-radius:8px;font-weight:700;font-size:12px;text-decoration:none">通道一：云猫主店（支付宝·45款）</a><a href="${SHOP2}" target="_blank" rel="nofollow sponsored noopener" style="background:#059669;color:#fff;padding:5px 10px;border-radius:8px;font-weight:700;font-size:12px;text-decoration:none">通道二：链动分店（支持微信支付+支付宝·35款）</a><a href="${SHOP3}" target="_blank" rel="nofollow sponsored noopener" style="background:#d97706;color:#fff;padding:5px 10px;border-radius:8px;font-weight:700;font-size:12px;text-decoration:none">通道三：16688分店（Codex ¥88.9/备用）</a></div></div>`);
      fb.style.cssText = 'position:fixed;left:0;right:0;bottom:0;z-index:9990;background:rgba(15,23,42,.96);color:#f8fafc;border-top:1px solid rgba(255,255,255,.15);padding:8px 14px;font-size:13px';
      document.body.style.paddingBottom = '60px';
      document.body.appendChild(fb);
    }
    document.querySelectorAll('.cta-box').forEach((box) => {
      if (!box.querySelector('.cta-shops')) {
        const d = el('div', 'cta-shops', `<a href="${SHOP2}" target="_blank" rel="nofollow sponsored noopener" style="flex:1;min-width:180px;text-align:center;padding:9px 10px;border-radius:8px;font-size:13px;font-weight:700;background:#059669;color:#fff;text-decoration:none">通道二：链动分店（支持微信支付+支付宝·35款） →</a><a href="${SHOP1}" target="_blank" rel="nofollow sponsored noopener" style="flex:1;min-width:160px;text-align:center;padding:9px 10px;border-radius:8px;font-size:13px;font-weight:700;background:#fff;border:1px solid #93c5fd;color:#1e40af;text-decoration:none">通道一：云猫主店（支付宝·45款全系）</a><a href="${SHOP3}" target="_blank" rel="nofollow sponsored noopener" style="flex:1;min-width:160px;text-align:center;padding:9px 10px;border-radius:8px;font-size:13px;font-weight:700;background:#fff;border:1px solid #fcd34d;color:#92400e;text-decoration:none">通道三：16688分店（含Codex 250 ¥88.9）</a>`);
        d.style.cssText = 'display:flex;flex-wrap:wrap;gap:8px;margin-top:4px;padding-top:8px;border-top:1px dashed #bfdbfe';
        box.appendChild(d);
      }
    });
  }

  function mount() {
    ensureMultiShopUI();
    const root = el('div', 'cs-root');
    root.style.bottom = '64px';
    root.innerHTML = `
      <button type="button" class="cs-fab" aria-label="打开客服">客服</button>
      <div class="cs-panel" hidden>
        <div class="cs-hd">
          <div>
            <strong>${(CFG.brand || '自动客服').replace(/</g, '')}</strong>
            <span>自动接待 · 多店24h自动发卡</span>
          </div>
          <button type="button" class="cs-x" aria-label="关闭">×</button>
        </div>
        <div class="cs-bd" role="log" aria-live="polite"></div>
        <div class="cs-quick"></div>
        <form class="cs-ft">
          <input type="text" name="q" placeholder="例如：微信支付、怎么买、查订单…" maxlength="200" autocomplete="off" />
          <button type="submit">发送</button>
        </form>
      </div>`;
    document.body.appendChild(root);

    const fab = root.querySelector('.cs-fab');
    const panel = root.querySelector('.cs-panel');
    const bd = root.querySelector('.cs-bd');
    const quick = root.querySelector('.cs-quick');
    const form = root.querySelector('.cs-ft');
    const input = form.querySelector('input');

    function add(role, text) {
      const row = el('div', 'cs-msg cs-' + role);
      row.innerHTML = linkify(text);
      bd.appendChild(row);
      bd.scrollTop = bd.scrollHeight;
    }

    function open() {
      panel.hidden = false;
      fab.setAttribute('aria-expanded', 'true');
      if (!bd.dataset.greeted) {
        bd.dataset.greeted = '1';
        add(
          'bot',
          fill(
            '你好，我是{brand}自动接待。\n可点下方快捷问题，或直接选择下单通道：\n• 通道一（云猫主店·支付宝·45款）：{shopUrl}\n• 通道二（链动分店·支持微信支付+支付宝·35款）：{shop2Url}\n• 通道三（16688分店·含Codex 250 ¥88.9）：{shop3Url}'
          )
        );
      }
      input.focus();
    }
    function close() {
      panel.hidden = true;
      fab.setAttribute('aria-expanded', 'false');
    }

    fab.addEventListener('click', () => (panel.hidden ? open() : close()));
    root.querySelector('.cs-x').addEventListener('click', close);

    const quickList = (FAQ.quick && FAQ.quick.some(x => x.intent === 'wxpay'))
      ? FAQ.quick
      : [{ label: '微信支付/分店', intent: 'wxpay' }, ...(FAQ.quick || [])];

    quickList.forEach((q) => {
      const b = el('button', 'cs-chip');
      b.type = 'button';
      b.textContent = q.label;
      b.addEventListener('click', async () => {
        add('user', q.label);
        if (q.intent === 'wxpay') {
          add('bot', fill('本站三大自动发卡店铺通道（习惯用微信付款请进通道二）：\n• 通道一：云猫主店（支付宝·45款全系）：{shopUrl}\n• 通道二：链动分店（支持微信支付+支付宝·35款）：{shop2Url}\n• 通道三：16688分店（含Codex 250 ¥88.9/备用自动发卡）：{shop3Url}\n• Codex 250 额度卡 ¥88.9 直达：https://www.16688.com.cn/goods/G76223428'));
          return;
        }
        const intent = (FAQ.intents || []).find((i) => i.id === q.intent);
        const text = intent ? fill(intent.answer) : (await reply(q.label)).text;
        add('bot', text);
      });
      quick.appendChild(b);
    });

    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      const v = (input.value || '').trim();
      if (!v) return;
      input.value = '';
      add('user', v);
      const r = await reply(v);
      add('bot', r.text);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount);
  else mount();
})();
