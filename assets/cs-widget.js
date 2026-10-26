/**
 * AI会员充值站 · 导购站自动接待（纯前端关键词规则，无付费 API）
 * 预留：window.__CS_LLM_HOOK__ = async (text, ctx) => string|null  未命中规则时可异步调用
 */
(function () {
  const CFG = window.__CS_CONFIG__ || {};
  const FAQ = window.__CS_FAQ__ || { intents: [], quick: [], fallback: '' };

  function fill(tpl) {
    return String(tpl || '')
      .replaceAll('{shopUrl}', CFG.shopUrl || '')
      .replaceAll('{orderUrl}', CFG.orderUrl || '')
      .replaceAll('{wechat}', CFG.wechat || '【待填微信号】')
      .replaceAll('{hours}', CFG.hours || '【待填客服时间】')
      .replaceAll('{brand}', CFG.brand || '本站');
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

  function mount() {
    const root = el('div', 'cs-root');
    root.innerHTML = `
      <button type="button" class="cs-fab" aria-label="打开客服">客服</button>
      <div class="cs-panel" hidden>
        <div class="cs-hd">
          <div>
            <strong>${(CFG.brand || '自动客服').replace(/</g, '')}</strong>
            <span>自动接待 · 非厂商厂商</span>
          </div>
          <button type="button" class="cs-x" aria-label="关闭">×</button>
        </div>
        <div class="cs-bd" role="log" aria-live="polite"></div>
        <div class="cs-quick"></div>
        <form class="cs-ft">
          <input type="text" name="q" placeholder="例如：怎么买、查订单、质保…" maxlength="200" autocomplete="off" />
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
            '你好，我是{brand}自动接待。\n可点下方快捷问题，或直接输入。\n店铺：{shopUrl}\n查单：{orderUrl}'
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

    (FAQ.quick || []).forEach((q) => {
      const b = el('button', 'cs-chip');
      b.type = 'button';
      b.textContent = q.label;
      b.addEventListener('click', async () => {
        add('user', q.label);
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
