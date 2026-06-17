<script setup>
import { onMounted, reactive, ref } from 'vue'
import MemberSelect from '../components/MemberSelect.vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, redeemGift } = useLoyaltyData()
const form = reactive({ member_id: '', gift_id: '' })
const redeemError = ref('')
const redeemData = ref(null)

onMounted(async () => {
  await refreshAll()
  if (state.members[0]) form.member_id = state.members[0].id
  if (state.gifts[0]) form.gift_id = state.gifts[0].id
})

async function submitRedeem() {
  redeemError.value = ''
  redeemData.value = null
  try {
    await redeemGift({ member_id: Number(form.member_id), gift_id: Number(form.gift_id) })
  } catch (e) {
    redeemError.value = e.message || '兑换失败'
    const available = typeof e.available_points === 'number' ? e.available_points : null
    const needed = typeof e.needed_points === 'number' ? e.needed_points : null
    const expired = typeof e.expired_points === 'number' ? e.expired_points : null
    if (available !== null || needed !== null || expired !== null) {
      redeemData.value = { available, needed, expired }
    }
  }
}

function getSelectedMember() {
  return state.members.find(m => m.id === Number(form.member_id))
}

function formatDetail(d) {
  const parts = []
  if (d.available !== null) parts.push(`实际可用：${d.available} 积分`)
  if (d.needed !== null && d.needed > 0) parts.push(`需要：${d.needed} 积分`)
  if (d.expired !== null && d.expired > 0) parts.push(`已过期：${d.expired} 积分`)
  return parts.join('｜')
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
      <div v-if="redeemData && (redeemData.available !== null || redeemData.expired > 0)" class="error-detail">
        <div class="detail-grid">
          <div class="detail-item" v-if="redeemData.available !== null">
            <span>实际可用</span>
            <strong class="num-available">{{ redeemData.available }}</strong>
          </div>
          <div class="detail-item" v-if="redeemData.needed !== null && redeemData.needed > 0">
            <span>还需</span>
            <strong class="num-needed">{{ Math.max(0, redeemData.needed - (redeemData.available || 0)) }}</strong>
          </div>
          <div class="detail-item" v-if="redeemData.expired !== null && redeemData.expired > 0">
            <span>已过期</span>
            <strong class="num-expired">{{ redeemData.expired }}</strong>
          </div>
        </div>
        <div v-if="redeemData.available !== null && redeemData.needed !== null && redeemData.needed > redeemData.available" class="gap-hint">
          缺口 {{ redeemData.needed - redeemData.available }} 积分
        </div>
      </div>
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
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid rgba(168, 61, 45, 0.2);
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.detail-item {
  background: #fff;
  border-radius: 6px;
  padding: 8px 10px;
  text-align: center;
}

.detail-item span {
  display: block;
  font-size: 12px;
  color: #6c6258;
  margin-bottom: 4px;
}

.detail-item strong {
  display: block;
  font-size: 20px;
  font-weight: 800;
}

.num-available {
  color: var(--success-text);
}

.num-needed {
  color: #a43d2d;
}

.num-expired {
  color: #a43d2d;
  text-decoration: line-through;
  opacity: 0.8;
}

.gap-hint {
  margin-top: 10px;
  font-size: 13px;
  color: #7a2d20;
  font-weight: 700;
  text-align: center;
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
