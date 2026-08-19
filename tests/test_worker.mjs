import assert from "node:assert/strict";
import test from "node:test";
import { handleSchedule } from "../worker/index.mjs";

test("returns a private no-store JSON schedule from KV", async () => {
  const schedule = { service: "Test rotation", blocks: [] };
  const response = await handleSchedule({
    ONCALL_SCHEDULE: { get: async (key, type) => {
      assert.equal(key, "schedule");
      assert.equal(type, "json");
      return schedule;
    } },
  });

  assert.equal(response.status, 200);
  assert.equal(response.headers.get("Cache-Control"), "private, no-store");
  assert.deepEqual(await response.json(), schedule);
});

test("returns 503 when no schedule has been published", async () => {
  const response = await handleSchedule({
    ONCALL_SCHEDULE: { get: async () => null },
  });

  assert.equal(response.status, 503);
  assert.equal((await response.json()).error, "The on-call schedule has not been published yet.");
});
