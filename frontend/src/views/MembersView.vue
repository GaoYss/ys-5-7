<script setup>
import { onMounted, reactive } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, createMember } = useLoyaltyData()
const form = reactive({ name: '', phone: '', birthday: '2000-01-01' })

onMounted(refreshAll)

async function submitMember() {
  await createMember({ ...form })
  Object.assign(form, { name: '', phone: '', birthday: '2000-01-01' })
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Members</p>
        <h2>会员管理</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="two-column">
      <form class="panel" @submit.prevent="submitMember">
        <h3>新增会员</h3>
        <label>
          姓名
          <input v-model.trim="form.name" required type="text" />
        </label>
        <label>
          手机号
          <input v-model.trim="form.phone" required type="tel" />
        </label>
        <label>
          生日
          <input v-model="form.birthday" required type="date" />
        </label>
        <button class="primary-button" type="submit">创建会员</button>
      </form>

      <section class="panel wide-panel">
        <h3>会员列表</h3>
        <div class="data-table">
          <div class="table-head">
            <span>会员</span>
            <span>等级</span>
            <span>积分</span>
            <span>权益</span>
          </div>
          <div v-for="member in state.members" :key="member.id" class="table-row">
            <span>{{ member.name }}<small>{{ member.phone }}</small></span>
            <span>{{ member.tier_name }}</span>
            <span>{{ member.points }}</span>
            <span>{{ member.benefits.join('、') }}</span>
          </div>
        </div>
      </section>
    </div>
  </section>
</template>
