
import path from "node:path";
import { fileURLToPath } from "node:url";
import { buildIslands } from "@framework/ui/vite/island";

const root = path.dirname(fileURLToPath(import.meta.url));

await buildIslands({
    app: "one_compliance",
    root,
    entries: {
        "one_compliance.employee_dashboard":
            "src/islands/employee_dashboard.js"
    },
    production: process.argv.includes("--production"),
    watch: process.argv.includes("--watch")
});
