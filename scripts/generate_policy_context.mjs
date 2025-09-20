import fs from "node:fs";
import { diffStats, depList, secretScan } from "./policy_utils.mjs";

const ctx = {
  pr: {
    ...diffStats(),
    new_dependencies: depList(),
    contains_secrets: secretScan()
  }
};

fs.writeFileSync("policies/context.json", JSON.stringify(ctx, null, 2));
console.log("Policy context written to policies/context.json");
