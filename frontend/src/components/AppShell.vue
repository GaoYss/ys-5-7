<script setup>
defineProps({
  tabs: {
    type: Array,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  }
})

defineEmits(['update:activeTab'])
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div>
        <p class="eyebrow">Milk Tea Club</p>
        <h1>奶茶店会员积分系统</h1>
      </div>
      <nav class="nav-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="{ active: tab.key === activeTab }"
          type="button"
          @click="$emit('update:activeTab', tab.key)"
        >
          {{ tab.label }}
        </button>
      </nav>
    </aside>

    <main class="content">
      <slot />
    </main>
  </div>
</template>
