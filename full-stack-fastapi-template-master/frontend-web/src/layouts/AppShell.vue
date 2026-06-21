<template>
  <div class="app-shell">
    <aside class="app-shell__sidebar" aria-label="Primary">
      <div class="app-shell__brand">Moss</div>
      <nav class="app-shell__nav">
        <RouterLink to="/library">Library</RouterLink>
        <RouterLink to="/editor">Editor</RouterLink>
      </nav>
    </aside>
    <main class="app-shell__main">
      <RouterView />
    </main>
  </div>
</template>
