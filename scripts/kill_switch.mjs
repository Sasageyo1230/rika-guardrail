import fs from "node:fs";

const ffPath = "feature_flags/config.yaml";
if (!fs.existsSync(ffPath)) {
  console.error("feature_flags/config.yaml not found");
  process.exit(1);
}
let text = fs.readFileSync(ffPath, "utf8");

// Brutal but effective: set all "default:" to false
text = text.replace(/default:\s*true/gi, "default: false");

fs.writeFileSync(ffPath, text, "utf8");
fs.writeFileSync("KILL_SWITCH.ACTIVE", `at=${new Date().toISOString()}\n`, "utf8");
console.log("Kill switch engaged: all defaults false, marker file created.");
