import * as bootstrap from 'bootstrap';

// Dynamic dark or light mode
function applyTheme() {
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  document.documentElement.setAttribute('data-bs-theme', prefersDark ? 'dark' : 'light');
}
applyTheme();
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);