<script setup>
import { onMounted, ref } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, issueBirthdayVouchers } = useLoyaltyData()
const issuedCount = ref(null)

onMounted(refreshAll)

async function submitIssue() {
  const vouchers = await issueBirthdayVouchers()
  issuedCount.value = vouchers.length
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Birthday</p>
        <h2>生日礼券发放</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="toolbar-panel">
      <button class="primary-button" type="button" @click="submitIssue">发放今日生日礼券</button>
      <span v-if="issuedCount !== null">本次发放 {{ issuedCount }} 张</span>
    </div>

    <section class="panel">
      <h3>礼券记录</h3>
      <div class="data-table">
        <div class="table-head voucher-cols">
          <span>会员</span>
          <span>礼券</span>
          <span>内容</span>
          <span>有效期</span>
          <span>状态</span>
        </div>
        <div v-for="voucher in state.vouchers" :key="voucher.id" class="table-row voucher-cols">
          <span>{{ voucher.member_name }}</span>
          <span>{{ voucher.title }}</span>
          <span>{{ voucher.value }}</span>
          <span>{{ voucher.expires_at }}</span>
          <span>{{ voucher.status }}</span>
        </div>
      </div>
    </section>
  </section>
</template>
