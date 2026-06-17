<script setup>
defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  hint: {
    type: String,
    default: ''
  },
  highlight: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <article class="metric-card" :class="{ 'metric-highlight': highlight }">
    <span>{{ label }}</span>
    <strong>{{ value }}</strong>
    <small>{{ hint }}</small>
  </article>
</template>

<style scoped>
.metric-highlight {
  border-color: #c45f35;
  box-shadow: 0 10px 26px rgba(196, 95, 53, 0.15);
}

.metric-highlight strong {
  color: #c45f35;
}
</style>
