import { test, expect } from "@playwright/test";

test("login, upload, and research search flow", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo@legalos.local");
  await page.getByLabel("Password").fill("DemoPass123!");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL(/\/matters/);
  await page.getByRole("link", { name: "Open matter" }).click();

  await page.getByRole("link", { name: "Upload documents" }).click();
  await page.getByLabel("Files").setInputFiles("tests/fixtures/sample_matter/petition_note.txt");
  await page.getByRole("button", { name: /Upload/ }).click();

  const uploadUrl = new URL(page.url());
  await page.goto(`${uploadUrl.origin}${uploadUrl.pathname.replace("/upload", "/research")}`);
  await page.getByLabel("Search query").fill("personal liberty legal aid");
  await page.getByRole("button", { name: /Run search/ }).click();
  await expect(page.getByText("Source spans only")).toBeVisible();
});
