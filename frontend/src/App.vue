<script setup>
import { ref } from 'vue'
import AppShell from './components/AppShell.vue'
import DashboardView from './views/DashboardView.vue'
import GiftsView from './views/GiftsView.vue'
import MembersView from './views/MembersView.vue'
import TiersView from './views/TiersView.vue'
import VouchersView from './views/VouchersView.vue'

const tabs = [
  { key: 'dashboard', label: '积分工作台', component: DashboardView },
  { key: 'members', label: '会员管理', component: MembersView },
  { key: 'gifts', label: '礼品兑换', component: GiftsView },
  { key: 'tiers', label: '等级权益', component: TiersView },
  { key: 'vouchers', label: '生日礼券', component: VouchersView }
]

const activeTab = ref('dashboard')
</script>

<template>
  <AppShell v-model:active-tab="activeTab" :tabs="tabs">
    <component :is="tabs.find((tab) => tab.key === activeTab).component" />
  </AppShell>
</template>
