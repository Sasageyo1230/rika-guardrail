import fs from "node:fs";

const limit = parseFloat(process.env.BUDGET_LIMIT_USD || "5");      // default per-job budget
const cost  = parseFloat(process.env.JOB_COST_USD || "0");           // pipeline estimates plug in here

console.log(`Budget check: cost=$${cost.toFixed(2)} limit=$${limit.toFixed(2)}`);
if (isNaN(cost) || cost < 0) {
  console.error("JOB_COST_USD not set or invalid; failing closed.");
  process.exit(1);
}
if (cost > limit) {
  console.error(`Budget exceeded by $${(cost - limit).toFixed(2)}.`);
  process.exit(1);
}
console.log("Budget OK.");
