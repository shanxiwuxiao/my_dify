<template>
  <div class="app-shell">
    <header class="topbar">
      <RouterLink class="brand" to="/apps">my_dify</RouterLink>
      <span class="subtitle">用自己的代码理解 LLM 应用</span>
    </header>
    <main class="page-container"><RouterView /></main>
  </div>
</template>
