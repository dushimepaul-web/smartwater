/* SmartWater IoT – scripts de l'interface */
(function () {
  'use strict';
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => Array.from(el.querySelectorAll(s));

  // Menu mobile
  $('.burger')?.addEventListener('click', () => $('.sidebar').classList.toggle('open'));

  // Onglets (page Paramètres) ; l'onglet peut aussi venir de l'ancre (#notifications)
  function ouvrirOnglet(id) {
    if (!document.getElementById(id)) return;
    $$('.tabs button,.pane').forEach(e => e.classList.remove('on'));
    $(`.tabs button[data-pane="${id}"]`)?.classList.add('on');
    document.getElementById(id).classList.add('on');
  }
  $$('.tabs button').forEach(b => b.addEventListener('click', () => ouvrirOnglet(b.dataset.pane)));
  if (location.hash) ouvrirOnglet(location.hash.slice(1));

  // Modales
  $$('[data-open]').forEach(b => b.addEventListener('click', () => document.getElementById(b.dataset.open).classList.add('open')));
  $$('[data-close]').forEach(b => b.addEventListener('click', e => { e.preventDefault(); b.closest('.modal').classList.remove('open'); }));
  $$('.modal').forEach(m => m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); }));

  // Confirmation avant suppression
  $$('form[data-confirm]').forEach(f => f.addEventListener('submit', e => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));

  // Afficher / masquer le mot de passe
  $$('.pw-toggle').forEach(btn => btn.addEventListener('click', e => {
    e.preventDefault();
    const input = btn.parentElement.querySelector('input');
    input.type = input.type === 'password' ? 'text' : 'password';
  }));

  /* ---------- Graphique SVG (sans bibliothèque) ---------- */
  const W = 640, H = 250, X0 = 46, X1 = 626, Y0 = 220, Y1 = 12;
  const NS = 'http://www.w3.org/2000/svg';
  function el(nom, attrs, texte) {
    const n = document.createElementNS(NS, nom);
    for (const k in attrs) n.setAttribute(k, attrs[k]);
    if (texte !== undefined) n.textContent = texte;
    return n;
  }
  function etiquette(date, dureeMs) {
    if (dureeMs > 2 * 86400000) return date.toLocaleDateString('fr-FR', { weekday: 'short', day: '2-digit' });
    return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  }
  function dessinerGraphique(svg, serie, seuils) {
    if (!svg) return;
    svg.innerHTML = '';
    const debut = new Date(serie?.debut || Date.now() - 86400000).getTime();
    const fin = new Date(serie?.fin || Date.now()).getTime();
    const duree = Math.max(1, fin - debut);
    const x = t => X0 + (X1 - X0) * (t - debut) / duree;
    const y = v => Y0 - (Y0 - Y1) * v / 100;
    const defs = el('defs', {});
    const g = el('linearGradient', { id: 'grad-niveau', x1: 0, y1: 0, x2: 0, y2: 1 });
    g.append(el('stop', { offset: 0, 'stop-color': '#1e6fe8', 'stop-opacity': '.22' }),
      el('stop', { offset: 1, 'stop-color': '#1e6fe8', 'stop-opacity': '.02' }));
    defs.append(g); svg.append(defs);
    [0, 25, 50, 75, 100].forEach(v => {
      svg.append(el('line', { x1: X0, x2: X1, y1: y(v), y2: y(v), stroke: '#e6edf7' }));
      svg.append(el('text', { x: 38, y: y(v) + 4, 'text-anchor': 'end' }, v + '%'));
    });
    for (let i = 0; i <= 4; i++) {
      const t = debut + duree * i / 4;
      svg.append(el('text', { x: x(t), y: 242, 'text-anchor': i === 0 ? 'start' : i === 4 ? 'end' : 'middle' }, etiquette(new Date(t), duree)));
    }
    if (seuils) {
      [['seuil_bas', '#dc2626'], ['seuil_haut', '#f08a1c']].forEach(([k, c]) => {
        if (seuils[k] != null) svg.append(el('line', { x1: X0, x2: X1, y1: y(seuils[k]), y2: y(seuils[k]), stroke: c, 'stroke-dasharray': '4 4', 'stroke-opacity': '.7' }));
      });
    }
    const pts = (serie?.points || []).map(p => [x(new Date(p.t).getTime()), y(p.niveau), p]);
    if (!pts.length) {
      svg.append(el('text', { x: (X0 + X1) / 2, y: 120, 'text-anchor': 'middle', class: 'nodata' }, 'Aucune mesure sur cette période'));
      return;
    }
    const ligne = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ');
    svg.append(el('path', { d: `${ligne} L${pts[pts.length - 1][0].toFixed(1)} ${Y0} L${pts[0][0].toFixed(1)} ${Y0} Z`, fill: 'url(#grad-niveau)' }));
    svg.append(el('path', { d: ligne, fill: 'none', stroke: '#1e6fe8', 'stroke-width': 2.2 }));
    if (pts.length <= 100) pts.forEach(([cx, cy, p]) => {
      const c = el('circle', { cx, cy, r: 3, fill: '#fff', stroke: '#1e6fe8', 'stroke-width': 1.8 });
      c.append(el('title', {}, `${new Date(p.t).toLocaleString('fr-FR')} : ${p.niveau} %`));
      svg.append(c);
    });
  }
  const lireJSON = id => { const n = document.getElementById(id); return n ? JSON.parse(n.textContent) : null; };

  // Page Historique
  const serieHist = lireJSON('serie-initiale');
  if (serieHist !== null && !$('#dashboard')) dessinerGraphique($('#chart'), serieHist);

  /* ---------- Tableau de bord en temps réel ---------- */
  const dash = $('#dashboard');
  if (dash) {
    const set = (k, v) => { const n = $(`[data-k="${k}"]`, dash); if (n) n.textContent = v; };
    let dernierEtat = null;
    function afficher(d) {
      const r = d.reservoir, g = d.global;
      if (!r) return;
      const niv = r.niveau_pct;
      set('niveau', niv == null ? '—' : Math.round(niv) + ' %');
      set('donut_txt', niv == null ? '—' : Math.round(niv) + '%');
      $('[data-k="donut"]', dash)?.style.setProperty('--p', niv == null ? 0 : Math.round(niv));
      set('capacite', g.capacite_totale.toLocaleString('fr-FR') + ' L');
      set('en_ligne', `${g.nb_en_ligne} / ${g.nb_reservoirs}`);
      set('alertes', g.alertes_non_lues);
      set('volume', r.volume_litres == null ? '' : `≈ ${r.volume_litres.toLocaleString('fr-FR')} L`);
      set('maj', r.date_mesure ? 'Mesure : ' + new Date(r.date_mesure).toLocaleTimeString('fr-FR') : '');
      set('titre', r.message_titre); set('message', r.message);
      const box = $('[data-k="etat"]', dash);
      if (box) {
        box.className = 'okb' + (r.etat === 'bas' ? ' bad' : (r.etat === 'haut' || r.etat === 'inconnu') ? ' warn' : '');
        box.querySelector('use').setAttribute('href', r.etat === 'normal' ? '#i-okc' : '#i-err');
      }
      const compteur = $('.sidebar .count');
      if (compteur) compteur.textContent = g.alertes_non_lues;
      dessinerGraphique($('#chart'), d.serie, r);
      if (dernierEtat && dernierEtat !== r.etat && (r.etat === 'bas' || r.etat === 'haut')) notifier(r);
      dernierEtat = r.etat;
    }
    function notifier(r) {
      const prefs = window.SMARTWATER_PREFS || {};
      if (prefs.son) { try { const a = new AudioContext(), o = a.createOscillator(); o.connect(a.destination); o.frequency.value = 880; o.start(); o.stop(a.currentTime + 0.4); } catch (e) { /* navigateur sans audio */ } }
      if (prefs.push && 'Notification' in window && Notification.permission === 'granted') new Notification('SmartWater IoT', { body: `${r.message_titre} (${Math.round(r.niveau_pct)} %) – ${r.nom}` });
    }
    if ((window.SMARTWATER_PREFS || {}).push && 'Notification' in window && Notification.permission === 'default') Notification.requestPermission();
    const init = lireJSON('donnees-initiales');
    if (init) { afficher(init); dernierEtat = init.reservoir?.etat; }
    const url = `${dash.dataset.api}?reservoir=${dash.dataset.reservoir}&periode=${dash.dataset.periode}`;
    async function rafraichir() {
      if (document.hidden) return;
      try {
        const rep = await fetch(url, { headers: { Accept: 'application/json' }, credentials: 'same-origin' });
        if (rep.ok) afficher(await rep.json());
      } catch (e) { /* réseau momentanément indisponible */ }
    }
    setInterval(rafraichir, 5000);
  }
})();
