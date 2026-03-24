import { cookies } from "next/headers";
import { LegalOsApiClient } from "./client";

export async function createServerApiClient() {
  const token = (await cookies()).get("legalos_token")?.value ?? null;
  return new LegalOsApiClient(
    process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000",
    fetch,
    token
  );
}
