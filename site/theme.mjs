const themes = new Set(["light", "dark"]);

export function resolveTheme(savedTheme, systemPrefersDark) {
  if (themes.has(savedTheme)) return savedTheme;
  return systemPrefersDark ? "dark" : "light";
}

export function setTheme(document, theme) {
  document.documentElement.dataset.theme = theme;
  return theme;
}
