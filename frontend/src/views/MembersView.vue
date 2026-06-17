<script setup>
import { onMounted, reactive, ref } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, createMember, loadMemberDetail } = useLoyaltyData()
const form = reactive({ name: '', phone: '', birthday: '2000-01-01' })
const selectedMemberId = ref(null)

onMounted(refreshAll)

async function submitMember() {
  await createMember({ ...form })
  Object.assign(form, { name: '', phone: '', birthday: '2000-01-01' })
}

async function selectMember(member) {
  if (selectedMemberId.value === member.id) {
    selectedMemberId.value = null
    return
  }
  selectedMemberId.value = member.id
  await loadMemberDetail(member.id)
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.slice(0, 10)
}

function getExpiryWarning(member) {
  if (!member.expiring_soon_points) return null
  const days = Math.ceil(
    (new Date(member.next_expiration_date) - new Date()) / (1000 * 60 * 60 * 24)
  )
  if (days <= 7) return { class: 'badge-danger', text: `${member.expiring_soon_points}积分${days}天后过期` }
  if (days <= 30) return { class: 'badge-warning', text: `${member.expiring_soon_points}积分${days}天后过期` }
  return { class: 'badge-warning', text: `${member.expiring_soon_points}积分即将过期` }
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
          <div
            v-for="member in state.members"
            :key="member.id"
            class="table-row member-row"
            :class="{ 'row-selected': selectedMemberId === member.id }"
            @click="selectMember(member)">
            <span>
              {{ member.name }}
              <small>{{ member.phone }}</small>
              <span
                v-if="getExpiryWarning(member)"
                :class="['expiry-badge', getExpiryWarning(member).class]">
                {{ getExpiryWarning(member).text }}
              </span>
            </span>
            <span>{{ member.tier_name }}</span>
            <span>
              <strong>{{ member.points }}</strong>
            </span>
            <span>{{ member.benefits.join('、') }}</span>
          </div>
        </div>
      </section>
    </div>

    <section v-if="state.selectedMember" class="panel">
      <div class="panel-header">
        <h3>会员积分详情 - {{ state.selectedMember.name }}</h3>
      </div>
      <div class="member-detail-grid">
        <div class="detail-card">
          <span>总积分</span>
          <strong>{{ state.selectedMember.points }}</strong>
          <small>当前可用</small>
        </div>
        <div class="detail-card" v-if="state.selectedMember.expiring_soon_points">
          <span>即将过期</span>
          <strong class="text-warning">{{ state.selectedMember.expiring_soon_points }}</strong>
          <small>
            {{ formatDate(state.selectedMember.next_expiration_date) }} 到期
          </small>
        </div>
        <div class="detail-card">
          <span>会员等级</span>
          <strong>{{ state.selectedMember.tier_name }}</strong>
          <small>{{ state.selectedMember.discount_percent }}% 折扣</small>
        </div>
        <div class="detail-card">
          <span>注册日期</span>
          <strong>{{ formatDate(state.selectedMember.created_at) }}</strong>
          <small>生日：{{ state.selectedMember.birthday }}</small>
        </div>
      </div>

      <h4 style="margin-top: 24px;">积分批次明细</h4>
      <div class="data-table">
        <div class="table-head">
          <span>获得时间</span>
          <span>原始积分</span>
          <span>剩余积分</span>
          <span>到期时间</span>
          <span>状态</span>
        </div>
        <div v-for="batch in state.selectedMemberBatches" :key="batch.id" class="table-row">
          <span>{{ formatDate(batch.earned_at) }}</span>
          <span>{{ batch.original_points }}</span>
          <span :class="batch.remaining_points > 0 ? '' : 'points-used'">
            {{ batch.remaining_points }}
          </span>
          <span>{{ formatDate(batch.expires_at) }}</span>
          <span>
            <span
              :class="{
                'status-expired': batch.expired,
                'status-danger': !batch.expired && batch.days_until_expiry <= 7,
                'status-warning': !batch.expired && batch.days_until_expiry > 7 && batch.days_until_expiry <= 30,
                'status-normal': !batch.expired && batch.days_until_expiry > 30
              }">
              {{ batch.expired ? '已过期' : `${batch.days_until_expiry}天后过期` }}
            </span>
          </span>
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.member-row {
  cursor: pointer;
  transition: all 0.2s;
}

.member-row:hover {
  background: #f5eadb;
}

.row-selected {
  background: #fff4e0 !important;
  border-color: #c57d46;
}

.expiry-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 700;
  margin-top: 4px;
}

.badge-warning {
  background: var(--warning-bg);
  color: var(--warning-text);
}

.badge-danger {
  background: var(--danger-bg);
  color: var(--danger-text);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.panel-header h3 {
  margin: 0;
}

.member-detail-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.detail-card {
  background: #fbf6ee;
  border-radius: 8px;
  padding: 16px;
  display: grid;
  gap: 6px;
}

.detail-card span {
  font-size: 13px;
  color: var(--muted-text);
  font-weight: 700;
}

.detail-card strong {
  font-size: 24px;
  color: #19312d;
}

.detail-card small {
  font-size: 12px;
  color: var(--muted-text);
}

.text-warning {
  color: var(--warning-text) !important;
}

.status-expired {
  color: var(--danger-text);
  font-weight: 500;
}

.status-danger {
  color: var(--danger-text);
  font-weight: 500;
}

.status-warning {
  color: var(--warning-text);
  font-weight: 500;
}

.status-normal {
  color: var(--success-text);
  font-weight: 500;
}

.points-used {
  color: var(--muted-text);
  text-decoration: line-through;
}

@media (max-width: 980px) {
  .member-detail-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
