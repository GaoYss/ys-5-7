<script setup>
import { computed, onMounted, reactive } from 'vue'
import MemberSelect from '../components/MemberSelect.vue'
import MetricCard from '../components/MetricCard.vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, earnPoints } = useLoyaltyData()
const form = reactive({ member_id: '', amount: 38, rule_id: '' })

const recentTransactions = computed(() => state.transactions.slice(0, 6))

onMounted(async () => {
  await refreshAll()
  if (state.members[0]) form.member_id = state.members[0].id
  if (state.rules[0]) form.rule_id = state.rules[0].id
})

async function submitEarn() {
  await earnPoints({
    member_id: Number(form.member_id),
    amount: Number(form.amount),
    rule_id: Number(form.rule_id)
  })
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Loyalty Desk</p>
        <h2>积分工作台</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="metrics-grid">
      <MetricCard label="会员数" :value="state.dashboard?.members_count || 0" hint="已登记会员" />
      <MetricCard label="积分池" :value="state.dashboard?.total_points || 0" hint="当前可用积分" />
      <MetricCard label="礼品" :value="state.dashboard?.gifts_count || 0" hint="可兑换项目" />
      <MetricCard label="礼券" :value="state.dashboard?.active_vouchers || 0" hint="未使用生日券" />
    </div>

    <div class="two-column">
      <form class="panel" @submit.prevent="submitEarn">
        <h3>消费入账</h3>
        <label>
          会员
          <MemberSelect v-model="form.member_id" :members="state.members" />
        </label>
        <label>
          消费金额
          <input v-model.number="form.amount" min="1" step="0.01" type="number" />
        </label>
        <label>
          积分规则
          <select v-model.number="form.rule_id">
            <option v-for="rule in state.rules" :key="rule.id" :value="rule.id">
              {{ rule.name }} · x{{ rule.multiplier }}
            </option>
          </select>
        </label>
        <button class="primary-button" type="submit">确认入账</button>
      </form>

      <section class="panel">
        <h3>最近积分流水</h3>
        <div class="list-table">
          <div v-for="tx in recentTransactions" :key="tx.id" class="list-row">
            <div>
              <strong>{{ tx.member_name }}</strong>
              <span>{{ tx.note }}</span>
            </div>
            <b :class="{ negative: tx.points < 0 }">{{ tx.points > 0 ? '+' : '' }}{{ tx.points }}</b>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>
