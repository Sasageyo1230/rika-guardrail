import http from "node:http";

const target = process.env.CANARY_URL || "http://localhost:3000";
const timeoutMs = 2000;

const req = http.get(target, res => {
  console.log("HTTP", res.statusCode);
  if (res.statusCode >= 500) process.exit(1);
  process.exit(0);
});
req.setTimeout(timeoutMs, () => {
  console.error("timeout");
  req.destroy();
  process.exit(1);
});
req.on("error", e => {
  console.error("error", e.message);
  process.exit(1);
});
