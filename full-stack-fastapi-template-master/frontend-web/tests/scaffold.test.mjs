import { existsSync, readFileSync } from "node:fs"
import { join } from "node:path"
import { cwd, exit } from "node:process"

const root = cwd()
const frontendWebRoot = join(root, "frontend-web")

const requiredFiles = [
  "frontend-web/index.html",
  "frontend-web/package.json",
  "frontend-web/tsconfig.json",
  "frontend-web/tsconfig.node.json",
  "frontend-web/vite.config.ts",
  "frontend-web/src/main.ts",
  "frontend-web/src/app/App.vue",
  "frontend-web/src/app/config.ts",
  "frontend-web/src/router/index.ts",
  "frontend-web/src/router/guards.ts",
  "frontend-web/src/layouts/AppShell.vue",
  "frontend-web/src/layouts/EmptyLayout.vue",
  "frontend-web/src/pages/LibraryPage.vue",
  "frontend-web/src/pages/EditorPage.vue",
  "frontend-web/src/pages/LoginPage.vue",
  "frontend-web/src/pages/NotFoundPage.vue",
  "frontend-web/src/features/notes/index.ts",
  "frontend-web/src/features/conversations/index.ts",
  "frontend-web/src/features/documents/index.ts",
  "frontend-web/src/features/editor/index.ts",
  "frontend-web/src/features/agent/index.ts",
  "frontend-web/src/shared/api/index.ts",
  "frontend-web/src/shared/ui/index.ts",
  "frontend-web/src/shared/composables/index.ts",
  "frontend-web/src/shared/utils/index.ts",
  "frontend-web/src/shared/constants/index.ts",
  "frontend-web/src/client/.gitkeep",
  "frontend-web/src/assets/.gitkeep",
  "frontend-web/src/styles/index.css",
]

const failures = []

for (const file of requiredFiles) {
  if (!existsSync(join(root, file))) {
    failures.push(`Missing required file: ${file}`)
  }
}

if (existsSync(join(root, "package.json"))) {
  const rootPackage = JSON.parse(readFileSync(join(root, "package.json"), "utf8"))
  if (!rootPackage.workspaces?.includes("frontend-web")) {
    failures.push("Root package.json must include frontend-web in workspaces")
  }
  for (const scriptName of ["dev:web", "build:web", "lint:web", "test:web:structure"]) {
    if (!rootPackage.scripts?.[scriptName]) {
      failures.push(`Root package.json must define script: ${scriptName}`)
    }
  }
}

if (existsSync(join(frontendWebRoot, "package.json"))) {
  const webPackage = JSON.parse(
    readFileSync(join(frontendWebRoot, "package.json"), "utf8"),
  )
  for (const scriptName of ["dev", "build", "lint", "preview", "test:structure"]) {
    if (!webPackage.scripts?.[scriptName]) {
      failures.push(`frontend-web package.json must define script: ${scriptName}`)
    }
  }
  for (const depName of ["@vitejs/plugin-vue", "typescript", "vite", "vue", "vue-router", "pinia"]) {
    if (!webPackage.dependencies?.[depName] && !webPackage.devDependencies?.[depName]) {
      failures.push(`frontend-web package.json must include dependency: ${depName}`)
    }
  }
}

if (failures.length > 0) {
  console.error(failures.join("\n"))
  exit(1)
}

console.log("frontend-web scaffold is present")
