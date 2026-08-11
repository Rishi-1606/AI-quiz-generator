import { test, expect, type APIRequestContext } from "@playwright/test";

/**
 * Sprint 8 - Gap 3: Critical-path E2E test
 *
 * Flow:
 *   1.  Sign up a fresh user via API
 *   2.  Seed a 2-question MCQ quiz via /api/quizzes/seed-test-quiz (TEST_MODE=1)
 *   3.  Log in through the UI  (/login)
 *   4.  Navigate directly to the quiz page  (/quiz/:id)
 *   5.  Answer both questions
 *   6.  Click "Submit Quiz" → confirm dialog → "Yes, Submit"
 *   7.  Assert results page shows the score heading (100%)
 *
 * Gemini is never called — the seed endpoint creates hardcoded questions.
 */

const API = "http://localhost:8000/api";

// Unique email per run so parallel CI jobs don't collide
// NOTE: @playwright.test is an RFC 2606 reserved TLD — Pydantic's EmailStr rejects it.
// Use a real-looking (but non-deliverable) domain instead.
const E2E_EMAIL    = `e2e-${Date.now()}@e2e-playwright.io`;
const E2E_PASSWORD = "e2ePassword123";
const E2E_NAME     = "E2E User";

async function apiSignupAndSeed(
  request: APIRequestContext
): Promise<{ token: string; quizId: number }> {
  // 1. Sign up — must send JSON (not form-encoded)
  const signupResp = await request.post(`${API}/auth/signup`, {
    headers: { "Content-Type": "application/json" },
    data: JSON.stringify({ name: E2E_NAME, email: E2E_EMAIL, password: E2E_PASSWORD, role: "student" }),
  });
  expect(signupResp.status()).toBe(201);
  const { access_token } = await signupResp.json();

  // 2. Seed quiz (requires auth)
  const seedResp = await request.post(`${API}/quizzes/seed-test-quiz`, {
    headers: { Authorization: `Bearer ${access_token}` },
  });
  expect(seedResp.status()).toBe(201);
  const quiz = await seedResp.json();

  return { token: access_token, quizId: quiz.id };
}


test.describe("Critical path: login → take quiz → results", () => {
  let quizId: number;

  test.beforeAll(async ({ request }) => {
    const { quizId: id } = await apiSignupAndSeed(request);
    quizId = id;
  });

  test("1. Login via the UI and land on dashboard", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel("Email")).toBeVisible();

    await page.getByLabel("Email").fill(E2E_EMAIL);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    await page.getByRole("button", { name: "Sign In" }).click();

    // Should redirect to /dashboard
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("2. Navigate to quiz and answer all questions", async ({ page }) => {
    // Log in first (each test gets a fresh page)
    await page.goto("/login");
    await page.getByLabel("Email").fill(E2E_EMAIL);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    // Go directly to the seeded quiz
    await page.goto(`/quiz/${quizId}`);

    // Q1: "What is 2 + 2?" — correct answer is "4" (option D, index 3)
    await expect(page.getByText("What is 2 + 2?")).toBeVisible({ timeout: 15_000 });
    await page.getByText("4").first().click();

    // Navigate to Q2 via "Next" button (or the question is on same page)
    const nextBtn = page.getByRole("button", { name: /next/i });
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
    }

    // Q2: "What is the capital of France?" — correct answer is "Paris" (index 2)
    await expect(page.getByText("What is the capital of France?")).toBeVisible();
    await page.getByText("Paris").first().click();
  });

  test("3. Submit quiz and verify results page shows 100%", async ({ page }) => {
    // Full flow in one test to verify end-to-end navigation
    await page.goto("/login");
    await page.getByLabel("Email").fill(E2E_EMAIL);
    await page.getByLabel("Password").fill(E2E_PASSWORD);
    await page.getByRole("button", { name: "Sign In" }).click();
    await expect(page).toHaveURL(/\/dashboard/);

    await page.goto(`/quiz/${quizId}`);
    await expect(page.getByText("What is 2 + 2?")).toBeVisible({ timeout: 15_000 });

    // Answer Q1
    await page.getByText("4").first().click();

    // Navigate to Q2 if paginated
    const nextBtn = page.getByRole("button", { name: /next/i });
    if (await nextBtn.isVisible()) {
      await nextBtn.click();
    }

    // Answer Q2
    await expect(page.getByText("What is the capital of France?")).toBeVisible();
    await page.getByText("Paris").first().click();

    // Submit — the header button text is just "Submit" (not "Submit Quiz")
    await page.getByRole("button", { name: /^Submit$/ }).click();

    // Confirm dialog
    await expect(page.getByText("Submit Quiz?")).toBeVisible();
    await page.getByRole("button", { name: /yes, submit/i }).click();

    // Wait for results page
    await expect(page).toHaveURL(/\/quiz\/\d+\/results/, { timeout: 20_000 });

    // Score heading — results page shows {Math.round(attempt.percentage)}%
    await expect(page.getByText("100%")).toBeVisible({ timeout: 15_000 });
  });
});
