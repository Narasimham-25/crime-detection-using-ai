const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const fs = require('fs');

const html = fs.readFileSync('hotspot_report.html', 'utf8');
const virtualConsole = new jsdom.VirtualConsole();
virtualConsole.on("error", (error) => {
  console.error("error:", error);
});

virtualConsole.on("jsdomError", (error) => {
  console.error("JSDOM ERROR:", error.stack || error);
});

process.on("unhandledRejection", (reason, p) => {
  console.error("Unhandled Rejection at:", p, "reason:", reason);
  process.exit(1);
});

console.log("Starting JSDOM...");
try {
    const dom = new JSDOM(html, { runScripts: "dangerously", virtualConsole, url: "http://localhost/" });
    console.log("JSDOM Loaded.");
} catch (e) {
    console.error("Exception loading dom:", e);
}
