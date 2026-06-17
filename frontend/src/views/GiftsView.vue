<script setup>
import { onMounted, reactive, ref } from 'vue'
import MemberSelect from '../components/MemberSelect.vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, redeemGift } = useLoyaltyData()
const form = reactive({ member_id: '', gift_id: '' })
const redeemError = ref('')
const redeemDetail = ref('')

onMounted(async () => {
  await refreshAll()
  if (state.members[0]) form.member_id = state.members[0].id
  if (state.gifts[0]) form.gift_id = state.gifts[0].id
})

async function submitRedeem() {
  redeemError.value = ''
  redeemDetail.value = ''
  try {
    await redeemGift({ member_id: Number(form.member_id), gift_id: Number(form.gift_id) })
  } catch (e) {
    const msg = e.message || ''
    redeemError.value = msg
    const availableMatch = msg.match(/可用\s*(\d+)\s*积分/)
    const expiredMatch = msg.match(/另有\s*(\d+)\s*积分已过期/)
    const needMatch = msg.match(/需\s*(\d+)\s*积分/)
    if (availableMatch || expiredMatch) {
      const parts = []
      if (availableMatch) parts.push(`实际可用：${availableMatch[1]} 积分`)
      if (needMatch) parts.push(`需要：${needMatch[1]} 积分`)
      if (expiredMatch) parts.push(`已过期：${expiredMatch[1]} 积分`)
      redeemDetail.value = parts.join('｜')
    }
  }
}

function getSelectedMember() {
  return state.members.find(m => m.id === Number(form.member_id))
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Rewards</p>
        <h2>礼品兑换</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div v-if="redeemError" class="redeem-error-panel">
      <div class="error-title">{{ redeemError }}</div>
      <div v-if="redeemDetail" class="error-detail">{{ redeemDetail }}</div>
    </div>

    <form class="toolbar-panel" @submit.prevent="submitRedeem">
      <MemberSelect v-model="form.member_id" :members="state.members" />
      <select v-model.number="form.gift_id">
        <option v-for="gift in state.gifts" :key="gift.id" :value="gift.id">
          {{ gift.name }} · {{ gift.points_cost }}分
        </option>
      </select>
      <button class="primary-button" type="submit">兑换</button>
    </form>

    <div v-if="getSelectedMember()" class="member-points-bar">
      <span>
        当前可用积分：<strong>{{ getSelectedMember().points }}</strong>
      </span>
      <span v-if="getSelectedMember().expiring_soon_points" class="expiring-hint">
        （其中 {{ getSelectedMember().expiring_soon_points }} 积分即将过期，到期日 {{ getSelectedMember().next_expiration_date?.slice(0, 10) }}）
      </span>
    </div>

    <div class="gift-grid">
      <article v-for="gift in state.gifts" :key="gift.id" class="gift-card">
        <div>
          <h3>{{ gift.name }}</h3>
          <p>{{ gift.description }}</p>
        </div>
        <footer>
          <strong>{{ gift.points_cost }} 分</strong>
          <span>库存 {{ gift.stock }}</span>
        </footer>
      </article>
    </div>
  </section>
</template>

<style scoped>
.redeem-error-panel {
  background: #f9dfd8;
  border: 1px solid #e8a898;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
}

.error-title {
  color: #a43d2d;
  font-weight: 700;
  font-size: 15px;
}

.error-detail {
  color: #7a2d20;
  font-size: 14px;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(168, 61, 45, 0.2);
  letter-spacing: 0.3px;
}

.member-points-bar {
  background: #fbf6ee;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #4d463f;
}

.member-points-bar strong {
  color: #19312d;
  font-size: 18px;
}

.expiring-hint {
  color: var(--warning-text);
  font-size: 13px;
}
</style>
