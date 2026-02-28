const { chromium } = require('playwright');

const SEEDS = [67, 68, 69, 70, 71, 72, 73, 74, 75, 76];

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let grandTotal = 0;

  for (const seed of SEEDS) {
    const url = `https://sanand0.github.io/tdsdata/js_table/?seed=${seed}`;
    await page.goto(url, { waitUntil: 'networkidle' });
    await page.waitForSelector('table');

    const seedSum = await page.evaluate(() => {
      let sum = 0;
      document.querySelectorAll('table td, table th').forEach(cell => {
        const val = parseFloat(cell.innerText.trim());
        if (!isNaN(val)) sum += val;
      });
      return sum;
    });

    console.log(`Seed ${seed}: ${seedSum}`);
    grandTotal += seedSum;
  }

  await browser.close();
  console.log(`Total sum: ${grandTotal}`);
})();
