(() => {
  const toast = document.getElementById('toast');
  let timer;
  function show(hex, text) {
    toast.querySelector('i').style.background = '#' + hex;
    toast.querySelector('span').textContent = text;
    toast.classList.add('show');
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove('show'), 1600);
  }
  function fallback(text) {
    const ta = document.createElement('textarea');
    ta.value = text; ta.setAttribute('readonly', ''); ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    let ok = false; try { ok = document.execCommand('copy'); } catch {}
    ta.remove(); return ok;
  }
  // トップページと同じ履歴に足す
  function remember(hex) {
    try {
      const h = JSON.parse(localStorage.getItem('cc-history') || '[]');
      localStorage.setItem('cc-history', JSON.stringify([hex, ...h.filter(x => x !== hex)].slice(0, 30)));
    } catch {}
  }
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-copy]');
    if (!b) return;
    const text = b.dataset.copy, hex = b.dataset.hex;
    const done = () => { show(hex, text + ' をコピーしました'); remember(hex); };
    const fail = () => fallback(text) ? done() : show(hex, 'コピーできませんでした。' + text + ' を手で選んでください');
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fail);
    else fail();
  });
  // 一覧ページの絞り込み
  const q = document.getElementById('q');
  if (q) {
    const toKata = s => s.replace(/[ぁ-ゖ]/g, c => String.fromCharCode(c.charCodeAt(0) + 0x60));
    q.addEventListener('input', () => {
      const v = q.value.trim().replace(/^#/, '').toLowerCase();
      let hits = 0;
      document.querySelectorAll('.fam').forEach(sec => {
        let n = 0;
        sec.querySelectorAll('.card').forEach(c => {
          const hay = c.dataset.q.toLowerCase();
          const ok = !v || hay.includes(v) || toKata(hay).includes(toKata(v));
          c.hidden = !ok; if (ok) n++;
        });
        sec.hidden = n === 0; hits += n;
      });
      document.getElementById('none').hidden = hits > 0;
    });
  }
})();
