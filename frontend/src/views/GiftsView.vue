<script setup>
import { onMounted, reactive } from 'vue'
import MemberSelect from '../components/MemberSelect.vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, redeemGift } = useLoyaltyData()
const form = reactive({ member_id: '', gift_id: '' })

onMounted(async () => {
  await refreshAll()
  if (state.members[0]) form.member_id = state.members[0].id
  if (state.gifts[0]) form.gift_id = state.gifts[0].id
})

async function submitRedeem() {
  await redeemGift({ member_id: Number(form.member_id), gift_id: Number(form.gift_id) })
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

    <form class="toolbar-panel" @submit.prevent="submitRedeem">
      <MemberSelect v-model="form.member_id" :members="state.members" />
      <select v-model.number="form.gift_id">
        <option v-for="gift in state.gifts" :key="gift.id" :value="gift.id">
          {{ gift.name }} · {{ gift.points_cost }}分
        </option>
      </select>
      <button class="primary-button" type="submit">兑换</button>
    </form>

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
