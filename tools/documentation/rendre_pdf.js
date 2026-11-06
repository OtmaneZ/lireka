// Usage interne ZineInsights. Lit sur l'entrée standard la liste des pages HTML à rendre en PDF (voir generer_pdf.py).
const { chromium } = require('playwright');

(async () => {
  let entree = '';
  for await (const morceau of process.stdin) entree += morceau;
  const taches = JSON.parse(entree);
  const navigateur = await chromium.launch();
  for (const t of taches) {
    const onglet = await navigateur.newPage();
    await onglet.goto('file://' + t.html, { waitUntil: 'networkidle' });
    await onglet.pdf({
      path: t.pdf, format: 'A4', printBackground: true, displayHeaderFooter: true,
      headerTemplate: '<span></span>', footerTemplate: t.pied,
      margin: { top: '18mm', bottom: '18mm', left: '18mm', right: '18mm' },
    });
    await onglet.close();
    console.log(t.pdf.split('/').pop());
  }
  await navigateur.close();
})();
