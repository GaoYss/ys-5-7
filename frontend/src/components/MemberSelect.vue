<script setup>
defineProps({
  members: {
    type: Array,
    required: true
  },
  modelValue: {
    type: [String, Number],
    default: ''
  }
})

defineEmits(['update:modelValue'])
</script>

<template>
  <select :value="modelValue" @change="$emit('update:modelValue', Number($event.target.value))">
    <option disabled value="">选择会员</option>
    <option v-for="member in members" :key="member.id" :value="member.id">
      {{ member.name }} · {{ member.tier_name }} · {{ member.points }}分
    </option>
  </select>
</template>
