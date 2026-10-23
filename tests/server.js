// Tiny static file server for the browser tests (no dependencies).
// Serves the repository root, supports Range requests so <audio> can stream and seek.
"use strict";
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(process.env.SITE_ROOT || path.join(__dirname, ".."));
const PORT = +process.env.PORT || 4173;
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
  ".json": "application/json", ".mp3": "audio/mpeg", ".png": "image/png", ".svg": "image/svg+xml",
  ".txt": "text/plain; charset=utf-8", ".ico": "image/x-icon"
};

const server = http.createServer((req, res) => {
  let rel;
  try { rel = decodeURIComponent(new URL(req.url, "http://x").pathname); } catch (e) { res.writeHead(400); return res.end(); }
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.join(ROOT, rel);
  if (!file.startsWith(ROOT + path.sep)) { res.writeHead(403); return res.end(); }
  fs.stat(file, (err, st) => {
    if (err || !st.isFile()) { res.writeHead(404, { "Content-Type": "text/plain" }); return res.end("not found"); }
    const headers = { "Content-Type": TYPES[path.extname(file)] || "application/octet-stream", "Accept-Ranges": "bytes", "Cache-Control": "no-store" };
    const m = /^bytes=(\d*)-(\d*)$/.exec(req.headers.range || "");
    if (m) {
      const start = m[1] ? +m[1] : Math.max(0, st.size - +m[2]);
      const end = m[1] && m[2] ? Math.min(+m[2], st.size - 1) : st.size - 1;
      if (start > end || start >= st.size) { res.writeHead(416, { "Content-Range": `bytes */${st.size}` }); return res.end(); }
      res.writeHead(206, { ...headers, "Content-Range": `bytes ${start}-${end}/${st.size}`, "Content-Length": end - start + 1 });
      return req.method === "HEAD" ? res.end() : fs.createReadStream(file, { start, end }).pipe(res);
    }
    res.writeHead(200, { ...headers, "Content-Length": st.size });
    return req.method === "HEAD" ? res.end() : fs.createReadStream(file).pipe(res);
  });
});
server.on("error", e => {
  if (e.code !== "EADDRINUSE") throw e;
  console.error(`Port ${PORT} is already in use, so the site may already be running: open http://127.0.0.1:${PORT}/`);
  console.error(`To use another port: set PORT first (PowerShell: $env:PORT=4174; npm run serve   bash: PORT=4174 npm run serve).`);
  process.exit(1);
});
server.listen(PORT, "127.0.0.1", () => {
  console.log(`serving ${ROOT} at http://127.0.0.1:${PORT}/`);
  console.log(`try the task without uploading anything: http://127.0.0.1:${PORT}/index.html?nosave=1&fast=1   (Ctrl+C stops)`);
});
