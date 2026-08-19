import assert from "node:assert/strict";
import test from "node:test";
import { resolveTheme } from "../site/theme.mjs";

test("uses a saved light or dark preference over the system setting", () => {
  assert.equal(resolveTheme("dark", false), "dark");
  assert.equal(resolveTheme("light", true), "light");
});

test("uses system preference when no valid saved choice exists", () => {
  assert.equal(resolveTheme(null, true), "dark");
  assert.equal(resolveTheme("unexpected", false), "light");
});
