import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration.
 *
 * webServer block starts:
 *   1. The FastAPI backend  (port 8000)  with TEST_MODE=1 so the /seed-test-quiz
 *      endpoint is active and no Gemini key is needed.
 *   2. The Vite frontend    (port 5173)
 *
 * reuseExistingServer=!process.env.CI means:
 *   - Locally: reuse already-running servers (faster dev loop)
 *   - CI:      always start fresh servers
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,   // tests share the same backend DB — run sequentially
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    headless: true,
  },

  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
  ],

  webServer: [
    {
      // Backend: FastAPI via uvicorn
      // - CI (Linux): 'python' from PATH via setup-python action
      // - Local (Windows): explicit venv path (system Python has no uvicorn)
      command: [
        process.env.CI
          ? "python"
          : "..\\\\backend\\\\.venv\\\\Scripts\\\\python.exe",
        "-m uvicorn app.main:app",
        "--host 127.0.0.1",
        "--port 8000",
      ].join(" "),
      cwd: "../backend",
      port: 8000,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
      env: {
        TEST_MODE:    "1",
        GEMINI_API_KEY: "e2e-dummy-key-tests-do-not-call-gemini",
        SECRET_KEY:   "e2e-test-secret-key",
        DATABASE_URL: "sqlite:///./e2e_test.db",
      },
    },
    {
      // Frontend: Vite dev server
      command: "npm run dev",
      port: 5173,
      reuseExistingServer: !process.env.CI,
      timeout: 30_000,
    },
  ],
});
