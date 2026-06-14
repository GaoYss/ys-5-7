<script setup>
defineProps({
  error: {
    type: String,
    default: ''
  },
  notice: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  }
})
</script>

<template>
  <div v-if="error || notice || loading" class="status-row">
    <span v-if="loading" class="status neutral">加载中</span>
    <span v-if="notice" class="status success">{{ notice }}</span>
    <span v-if="error" class="status danger">{{ error }}</span>
  </div>
</template>
