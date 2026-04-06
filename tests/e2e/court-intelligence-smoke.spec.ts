import { expect, test } from "@playwright/test";

test("court intelligence vertical slice smoke", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo@legalos.local");
  await page.getByLabel("Password").fill("DemoPass123!");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL(/\/matters/);
  await page.getByRole("link", { name: "Open matter" }).click();
  const matterUrl = page.url();

  await page.goto(`${matterUrl}/intelligence`);
  await page.getByLabel("Official artifact file").setInputFiles(
    "tests/fixtures/public_court/district_ecourts_case_history.html"
  );
  await page.getByRole("button", { name: "Import official artifact" }).click();
  await expect(page.getByText(/Imported W\.P\.\(Crl\.\) 1542\/2026/)).toBeVisible();
  await expect(page.getByText("W.P.(Crl.) 1542/2026")).toBeVisible();
  await expect(page.getByRole("button", { name: "Case Memory" })).toBeVisible();

  await page.getByRole("button", { name: "Party Memory" }).click();
  await expect(page.getByText("Litigant Memory")).toBeVisible();

  await page.getByRole("button", { name: "Connected Matters" }).click();
  await page.getByPlaceholder("Search across public and private artifacts").fill(
    "production delay"
  );
  await page.getByRole("button", { name: "Hybrid search" }).click();
  await expect(page.getByText(/score/i)).toBeVisible();
});
