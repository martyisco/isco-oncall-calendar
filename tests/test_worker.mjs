import assert from "node:assert/strict";
import test from "node:test";
import worker, { handleSchedule } from "../worker/index.mjs";

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

test("does not expose schedule data on the public workers.dev hostname", async () => {
  const response = await worker.fetch(
    new Request("https://isco-oncall-calendar.isco-tech.workers.dev/api/schedule"),
    { ONCALL_SCHEDULE: { get: async () => ({ service: "Test rotation" }) } },
  );

  assert.equal(response.status, 404);
});
