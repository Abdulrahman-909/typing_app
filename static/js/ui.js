const root = document.documentElement;
root.dataset.theme = localStorage.getItem('theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.getElementById('theme')?.addEventListener('click', () => {
  root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
  localStorage.setItem('theme', root.dataset.theme)
});
for (const form of document.querySelectorAll('form[method=get]')) {
  const params = new URLSearchParams(location.search);
  for (const control of form.elements) {
    if (params.has(control.name)) control.value = params.get(control.name)
  }
}
