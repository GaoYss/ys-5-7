<script setup>
import { onMounted } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll } = useLoyaltyData()

onMounted(refreshAll)
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Tier Benefits</p>
        <h2>等级权益</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="tier-timeline">
      <article v-for="tier in state.tiers" :key="tier.id" class="tier-item">
        <div>
          <h3>{{ tier.name }}</h3>
          <p>{{ tier.min_points }} 积分起</p>
        </div>
        <strong>{{ tier.discount_percent ? `${100 - tier.discount_percent}折` : '原价' }}</strong>
        <span>生日加赠 {{ tier.birthday_bonus }} 积分</span>
        <ul>
          <li v-for="benefit in tier.benefits" :key="benefit">{{ benefit }}</li>
        </ul>
      </article>
    </div>
  </section>
</template>
