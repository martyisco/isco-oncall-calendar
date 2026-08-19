import { resolveTheme, setTheme } from "./theme.mjs";

const timeZone = "America/New_York";
const storageKey = "isco-oncall-theme";

function updateThemeToggle(theme) {
  const button = document.getElementById("theme-toggle");
  const icon = document.getElementById("theme-icon");
  const nextTheme = theme === "dark" ? "light" : "dark";
  button.setAttribute("aria-pressed", String(theme === "dark"));
  button.setAttribute("aria-label", `Switch to ${nextTheme} mode`);
  icon.textContent = theme === "dark" ? "☀" : "☾";
}

function initializeTheme() {
  const theme = setTheme(
    document,
    resolveTheme(localStorage.getItem(storageKey), window.matchMedia("(prefers-color-scheme: dark)").matches),
  );
  updateThemeToggle(theme);
  document.getElementById("theme-toggle").addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(document, nextTheme);
    localStorage.setItem(storageKey, nextTheme);
    updateThemeToggle(nextTheme);
  });
}

initializeTheme();

function parse(dateTime) {
  return new Date(dateTime);
}

function dateText(dateTime, options = { month: "short", day: "numeric" }) {
  return new Intl.DateTimeFormat("en-US", { ...options, timeZone }).format(parse(dateTime));
}

function rangeText(block) {
  return `${dateText(block.start)} at 8:00 AM – ${dateText(block.end)} at 8:00 AM ET`;
}

function isCurrent(block, now = new Date()) {
  return parse(block.start) <= now && now < parse(block.end);
}

function monthKey(block) {
  return new Intl.DateTimeFormat("en-US", { month: "long", year: "numeric", timeZone }).format(parse(block.start));
}

function renderBlock(block) {
  const classes = ["block"];
  if (block.override) classes.push("override");
  if (isCurrent(block)) classes.push("current");
  const note = block.note ? `<span class="block-note">${escapeHtml(block.note)}</span>` : "";
  return `<article class="${classes.join(" ")}"><span class="block-primary">${escapeHtml(block.primary)}</span><span class="block-range">${rangeText(block)}</span>${note}</article>`;
}

function escapeHtml(value) {
  const node = document.createElement("span");
  node.textContent = value;
  return node.innerHTML;
}

function render(schedule) {
  document.title = schedule.service;
  document.getElementById("timezone").textContent = "All rotation boundaries are Monday at 8:00 AM Eastern Time.";
  document.getElementById("coverage-through").textContent = `Published through ${dateText(schedule.coverage_through, { month: "long", day: "numeric", year: "numeric" })}`;
  document.getElementById("generated-at").textContent = `Schedule generated ${schedule.generated_at}`;

  const current = schedule.blocks.find((block) => isCurrent(block)) || schedule.blocks[0];
  document.getElementById("current-primary").textContent = current.primary;
  document.getElementById("current-range").textContent = rangeText(current);

  const months = new Map();
  for (const block of schedule.blocks) {
    const key = monthKey(block);
    months.set(key, [...(months.get(key) || []), block]);
  }
  document.getElementById("schedule").innerHTML = [...months.entries()]
    .map(([month, blocks]) => `<section class="month"><h3>${month}</h3><div class="blocks">${blocks.map(renderBlock).join("")}</div></section>`)
    .join("");
}

fetch("/api/schedule", { cache: "no-store", credentials: "same-origin" })
  .then((response) => response.ok ? response.json() : Promise.reject(new Error(`HTTP ${response.status}`)))
  .then(render)
  .catch(() => {
    document.getElementById("schedule").innerHTML = '<p class="error">The published on-call schedule is temporarily unavailable.</p>';
    document.getElementById("timezone").textContent = "Schedule unavailable";
  });
