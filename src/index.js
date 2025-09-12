import http from "http";
const port = process.env.PORT || 3000;
const server = http.createServer((_, res) => {
  res.writeHead(200, {"Content-Type": "application/json"});
  res.end(JSON.stringify({ ok: true, service: "rika-guardrail", ts: Date.now() }));
});
server.listen(port, () => console.log("Rika guardrail stub listening on", port));
