import { expect, test } from "@playwright/test";

test("drafting, strategy, and institutional workflow smoke", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo@legalos.local");
  await page.getByLabel("Password").fill("DemoPass123!");
  await page.getByRole("button", { name: "Continue" }).click();

  await expect(page).toHaveURL(/\/matters/);
  await page.getByRole("link", { name: "Open matter" }).click();

  const matterUrl = page.url();

  await page.goto(`${matterUrl}/upload`);
  await page.getByRole("checkbox").uncheck();
  await page.getByLabel("Files").setInputFiles("tests/fixtures/sample_matter/petition_note.txt");
  await page.getByRole("button", { name: "Upload and extract" }).click();
  await expect(page.getByText(/Uploaded 1 document/)).toBeVisible();

  await page.goto(`${matterUrl}/drafting`);
  await page.getByRole("button", { name: "Generate structured draft" }).click();
  await expect(page.getByText("Selected draft")).toBeVisible();
  await expect(page.getByText("Verified authorities")).toBeVisible();

  await page.goto(`${matterUrl}/strategy`);
  await expect(page.getByText("Bounded hearing strategy")).toBeVisible();
  await expect(page.getByText("Sequencing console")).toBeVisible();

  await page.goto(`${matterUrl}/institutional`);
  await expect(page.getByText("Auditability and approvals")).toBeVisible();
  await page.getByRole("button", { name: "Request approval for latest draft" }).click();
  await expect(page.getByText(/Approval requested:/)).toBeVisible();
});
