/* Renders every icon and link-preview card for markfaizi.dev.
   Needs: playwright, and @fontsource/{chakra-petch,newsreader,ibm-plex-mono,spectral} in node_modules.
   Usage: node render-assets.cjs <repo-root> <fontsource-node_modules>                                   */
const fs = require('fs'), path = require('path');
const PW = process.env.PW || 'playwright';
const { chromium } = require(PW);
const REPO = path.resolve(process.argv[2]);
const NM = path.resolve(process.argv[3]);
const font = (pkg, file) => 'file://' + path.join(NM, '@fontsource', pkg, 'files', file);

/* ---------------- marks (64×64 viewBox) ---------------- */
const ARROW = [
  "X...........","XX..........","XoX.........","XooX........","XoooX.......","XooooX......",
  "XoooooX.....","XooooooX....","XoooooooX...","XooooooooX..","XoooooooooX.","XoooooXXXXXX",
  "XooXooX.....","XoX.XooX....","XX..XooX....","X....XooX...",".....XooX...","......XX...."];
function pixels(map, ch){ let d=''; map.forEach((r,y)=>[...r].forEach((c,x)=>{ if(c===ch) d+=`M${x} ${y}h1v1h-1z`; })); return d; }
function arrowSVG(x, y, s, ink, fill){
  return `<g transform="translate(${x} ${y}) scale(${s})" shape-rendering="crispEdges">
    <path d="${pixels(ARROW,'o')}" fill="${fill}"/><path d="${pixels(ARROW,'X')}" fill="${ink}"/></g>`;
}
const MARKS = {
  site: { bg:'#2E3F6B', draw: () => arrowSVG(18.5, 7.5, 2.75, '#16161A', '#FFFFFF') },
  signal: { bg:'#8E1F2F', draw: () => {
    const c = '#F3EEEA', arcs = [[16,1],[26,.72],[36,.46]].map(([r,o]) =>
      `<path d="M14 ${50-r}A${r} ${r} 0 0 1 ${14+r} 50" fill="none" stroke="${c}" stroke-width="5.5" stroke-linecap="round" opacity="${o}"/>`).join('');
    return arcs + `<circle cx="14" cy="50" r="6.5" fill="${c}"/>`; } },
  kabulledger: { bg:'#1F4E9C', draw: () =>
    `<circle cx="32" cy="32" r="24" fill="none" stroke="#EEEAE1" stroke-width="3" opacity=".5"/>
     <polygon points="32,8 42,32 22,32" fill="#EEEAE1"/><polygon points="22,32 42,32 32,56" fill="#E0AE62"/>
     <circle cx="32" cy="32" r="3.2" fill="#1F4E9C"/>` },
  loadfactor: { bg:'#1D5A43', draw: () => {
    let s=''; for (let r=0;r<3;r++) for (let c=0;c<3;c++){
      const x = 9 + c*17, y = 9 + r*17, empty = (r===2 && c>0);
      s += empty ? `<rect x="${x+1.25}" y="${y+1.25}" width="11.5" height="11.5" rx="2.5" fill="none" stroke="#ECEDE9" stroke-width="2.5" opacity=".7"/>`
                 : `<rect x="${x}" y="${y}" width="14" height="14" rx="3" fill="${c===0&&r===0?'#E0B45C':'#ECEDE9'}"/>`;
    } return s; } },
};
function markSVG(key, rounded){
  const m = MARKS[key];
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="${rounded?14:0}" fill="${m.bg}"/>${m.draw()}</svg>`;
}

/* ---------------- link-preview cards (1200×630) ---------------- */
const CARDS = {
  site: { paper:'#ECEBE6', ink:'#16161A', soft:'#55545C', accent:'#2E3F6B',
    eyebrow:'Market data analyst', word:['Mark','Faizi'],
    stand:'Competitor analysis, CRM and automation that saves businesses time and money.',
    url:'markfaizi.dev', note:'CV · Projects · Writing',
    motif: () => `<svg viewBox="0 0 12 18" width="192" height="288" shape-rendering="crispEdges">
      <path d="${pixels(ARROW,'o')}" fill="#FFFFFF"/><path d="${pixels(ARROW,'X')}" fill="#16161A"/></svg>` },
  signal: { paper:'#EDEAE7', ink:'#17110F', soft:'#4A403C', accent:'#8E1F2F',
    eyebrow:'Technology · AI · Markets', word:['Signal'],
    stand:'What happened in tech, AI and finance, and why the numbers mean what they mean.',
    url:'markfaizi.dev/signal', note:'Mondays & Thursdays',
    motif: () => `<svg viewBox="0 0 64 64" width="330" height="330">
      ${[[16,1],[26,.62],[36,.34],[46,.16]].map(([r,o],i)=>`<path d="M10 ${54-r}A${r} ${r} 0 0 1 ${10+r} 54" fill="none" stroke="${i?'#17110F':'#8E1F2F'}" stroke-width="3.2" stroke-linecap="round" opacity="${i?o:1}"/>`).join('')}
      <circle cx="10" cy="54" r="5" fill="#8E1F2F"/></svg>` },
  kabulledger: { paper:'#EEEAE1', ink:'#16130E', soft:'#5B5346', accent:'#1F4E9C', second:'#A8701E',
    eyebrow:"The Kabul Ledger · Weekly", word:['Kabul','Ledger'],
    stand:"A weekly reading of Afghanistan's economy for people who live outside it.",
    url:'markfaizi.dev/kabulledger', note:'Every Sunday',
    motif: () => `<svg viewBox="0 0 64 64" width="320" height="320">
      <circle cx="32" cy="32" r="28" fill="none" stroke="#16130E" stroke-width="1.2" opacity=".35"/>
      <circle cx="32" cy="32" r="22" fill="none" stroke="#16130E" stroke-width=".6" opacity=".3" stroke-dasharray="1 2.2"/>
      <polygon points="32,6 40,32 24,32" fill="#1F4E9C"/><polygon points="24,32 40,32 32,58" fill="#A8701E"/>
      <circle cx="32" cy="32" r="2.6" fill="#EEEAE1"/></svg>` },
  loadfactor: { paper:'#ECEDE9', ink:'#131714', soft:'#4F5650', accent:'#1D5A43', second:'#B07A16',
    eyebrow:'Escorted touring · Fortnightly', word:['Load','Factor'],
    stand:'The business of escorted touring: who makes money, how, and where the risk sits.',
    url:'markfaizi.dev/loadfactor', note:'1st & 15th of the month',
    motif: () => { let s='', n=0;
      for (let r=0;r<5;r++) for (let c=0;c<4;c++){ n++;
        const x = c*62 + (c>1?22:0), y = r*56, empty = n>16;
        s += empty ? `<rect x="${x+2}" y="${y+2}" width="42" height="38" rx="7" fill="none" stroke="#131714" stroke-width="3" opacity=".35"/>`
                   : `<rect x="${x}" y="${y}" width="46" height="42" rx="8" fill="${n===1?'#B07A16':'#1D5A43'}"/>`; }
      return `<div style="display:grid;gap:16px;justify-items:center"><svg viewBox="0 0 270 266" width="270" height="266">${s}</svg>
        <div style="font:500 21px/1 'Plex';letter-spacing:.08em;color:#4F5650;white-space:nowrap">16 OF 20 SEATS SOLD</div></div>`; } },
};
function cardHTML(c){
  const big = c.word.length > 1 ? 150 : 168;
  return `<!doctype html><html><head><meta charset="utf-8"><style>
  @font-face{font-family:Disp;src:url(${font('chakra-petch','chakra-petch-latin-700-normal.woff2')})}
  @font-face{font-family:Ital;font-style:italic;src:url(${font('spectral','spectral-latin-400-italic.woff2')})}
  @font-face{font-family:Plex;font-weight:500;src:url(${font('ibm-plex-mono','ibm-plex-mono-latin-500-normal.woff2')})}
  @font-face{font-family:Plex;font-weight:600;src:url(${font('ibm-plex-mono','ibm-plex-mono-latin-600-normal.woff2')})}
  *{box-sizing:border-box}html,body{margin:0}
  body{width:1200px;height:630px;background:${c.paper};color:${c.ink};overflow:hidden;position:relative}
  .main{position:absolute;left:76px;top:70px;width:700px;display:grid;gap:26px}
  .eb{font:600 23px/1 Plex;letter-spacing:.16em;text-transform:uppercase;color:${c.accent}}
  .w{font:700 ${big}px/.84 Disp;text-transform:uppercase;letter-spacing:.02em;margin:0}
  .st{font:400 34px/1.3 Ital;font-style:italic;color:${c.soft};max-width:640px;margin:6px 0 0}
  .motif{position:absolute;right:80px;top:0;bottom:96px;width:360px;display:flex;align-items:center;justify-content:center}
  .foot{position:absolute;left:76px;right:76px;bottom:44px;border-top:4px solid ${c.ink};padding-top:20px;
    display:flex;justify-content:space-between;font:500 24px/1 Plex;letter-spacing:.06em}
  .foot b{font-weight:600;color:${c.accent}}
  </style></head><body>
  <div class="main"><div class="eb">${c.eyebrow}</div><h1 class="w">${c.word.join('<br>')}</h1><p class="st">${c.stand}</p></div>
  <div class="motif">${c.motif()}</div>
  <div class="foot"><b>${c.url}</b><span>${c.note}</span></div></body></html>`;
}

(async () => {
  const tmp = fs.mkdtempSync(path.join(require('os').tmpdir(), 'mf-'));
  const b = await chromium.launch();
  const p = await b.newPage();
  for (const key of Object.keys(MARKS)){
    const dir = path.join(REPO, 'assets', key); fs.mkdirSync(dir, { recursive:true });
    fs.writeFileSync(path.join(dir, 'icon.svg'), markSVG(key, true) + '\n');
    const shots = [['icon-32.png',32,true],['apple-touch-icon.png',180,false]];
    if (key === 'site') shots.push(['icon-192.png',192,false],['icon-512.png',512,false],['ico-16.png',16,true],['ico-48.png',48,true]);
    for (const [name, size, rounded] of shots){
      const f = path.join(tmp, `${key}-${size}.html`);
      fs.writeFileSync(f, `<!doctype html><html><body style="margin:0;background:transparent">
        <div id="m" style="width:${size}px;height:${size}px">${markSVG(key, rounded).replace('<svg ', `<svg width="${size}" height="${size}" `)}</div></body></html>`);
      await p.setViewportSize({ width: size, height: size });
      await p.goto('file://' + f);
      await p.locator('#m').screenshot({ path: path.join(dir, name), omitBackground: true });
    }
    const f = path.join(tmp, `${key}-og.html`);
    fs.writeFileSync(f, cardHTML(CARDS[key]));
    await p.setViewportSize({ width: 1200, height: 630 });
    await p.goto('file://' + f);
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(dir, 'og.png') });
    console.log('rendered', key);
  }
  await b.close();
})();
