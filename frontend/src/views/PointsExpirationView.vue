<script setup>
import { onMounted, reactive } from 'vue'
import StatusBanner from '../components/StatusBanner.vue'
import { useLoyaltyData } from '../stores/useLoyaltyData'

const { state, refreshAll, createExpirationRule, activateExpirationRule, processExpiredPoints } = useLoyaltyData()
const form = reactive({ name: '', description: '', validity_days: 365, reminder_days: 30 })

onMounted(refreshAll)

async function submitRule() {
  await createExpirationRule({ ...form })
  Object.assign(form, { name: '', description: '', validity_days: 365, reminder_days: 30 })
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  return dateStr.slice(0, 10)
}

function getExpiryStatus(days) {
  if (days === null || days === undefined) return ''
  if (days <= 0) return { text: '已过期', class: 'status-expired' }
  if (days <= 7) return { text: `${days}天后过期`, class: 'status-danger' }
  if (days <= 30) return { text: `${days}天后过期`, class: 'status-warning' }
  return { text: `${days}天后过期`, class: 'status-normal' }
}
</script>

<template>
  <section class="view-stack">
    <div class="section-header">
      <div>
        <p class="eyebrow">Points Expiration</p>
        <h2>积分过期规则</h2>
      </div>
      <StatusBanner :error="state.error" :notice="state.notice" :loading="state.loading" />
    </div>

    <div class="two-column">
      <form class="panel" @submit.prevent="submitRule">
        <h3>新增过期规则</h3>
        <label>
          规则名称
          <input v-model.trim="form.name" required type="text" placeholder="如：标准有效期" />
        </label>
        <label>
          规则描述
          <textarea v-model.trim="form.description" required rows="2" placeholder="描述积分过期规则说明"></textarea>
        </label>
        <div class="form-row">
          <label>
            有效期（天）
            <input v-model.number="form.validity_days" required type="number" min="1" />
          </label>
          <label>
            提前提醒（天）
            <input v-model.number="form.reminder_days" required type="number" min="0" />
          </label>
        </div>
        <button class="primary-button" type="submit">创建规则</button>
      </form>

      <section class="panel wide-panel">
        <div class="panel-header">
          <h3>过期规则列表</h3>
          <button class="secondary-button" type="button" @click="processExpiredPoints">
            立即处理过期积分
          </button>
        </div>
        <div class="data-table">
          <div class="table-head">
            <span>规则名称</span>
            <span>有效期</span>
            <span>提醒天数</span>
            <span>状态</span>
            <span>操作</span>
          </div>
          <div v-for="rule in state.expirationRules" :key="rule.id" class="table-row">
            <span>
              <strong>{{ rule.name }}</strong>
              <small>{{ rule.description }}</small>
            </span>
            <span>{{ rule.validity_days }} 天</span>
            <span>到期前 {{ rule.reminder_days }} 天</span>
            <span>
              <span :class="rule.active ? 'badge-active' : 'badge-inactive'">
                {{ rule.active ? '当前使用' : '未启用' }}
              </span>
            </span>
            <span>
              <button
                v-if="!rule.active" class="link-button" type="button" @click="activateExpirationRule(rule.id)">
                启用
              </button>
            </span>
          </div>
        </div>
      </section>
    </div>

    <section class="panel">
      <div class="panel-header">
        <h3>即将过期积分提醒</h3>
        <span class="hint">{{ state.expirationReminders.length }} 位会员有积分即将过期</span>
      </div>
      <div v-if="state.expirationReminders.length === 0" class="empty-state">
        <p>暂无即将过期的积分</p>
      </div>
      <div v-else class="data-table">
        <div class="table-head">
          <span>会员</span>
          <span>即将过期积分</span>
          <span>批次数量</span>
          <span>最早到期日</span>
          <span>剩余天数</span>
        </div>
        <div v-for="reminder in state.expirationReminders" :key="reminder.member_id" class="table-row">
          <span>{{ reminder.member_name }}</span>
          <span class="points-expiring">{{ reminder.expiring_points }} 积分</span>
          <span>{{ reminder.batch_count }} 批</span>
          <span>{{ formatDate(reminder.earliest_expiry_date) }}</span>
          <span>
            <span :class="getExpiryStatus(reminder.days_until_expiry).class">
              {{ getExpiryStatus(reminder.days_until_expiry).text }}
            </span>
          </span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h3>积分批次列表</h3>
      <div class="data-table">
        <div class="table-head">
          <span>会员</span>
          <span>原始积分</span>
          <span>剩余积分</span>
          <span>获得时间</span>
          <span>到期时间</span>
          <span>状态</span>
        </div>
        <div v-for="batch in state.pointBatches" :key="batch.id" class="table-row">
          <span>{{ batch.member_name }}</span>
          <span>{{ batch.original_points }}</span>
          <span :class="batch.remaining_points > 0 ? '' : 'points-used'">
            {{ batch.remaining_points }}
          </span>
          <span>{{ formatDate(batch.earned_at) }}</span>
          <span>{{ formatDate(batch.expires_at) }}</span>
          <span>
            <span
              :class="batch.expired ? 'status-expired' : getExpiryStatus(batch.days_until_expiry).class">
              {{ batch.expired ? '已过期' : getExpiryStatus(batch.days_until_expiry).text }}
            </span>
          </span>
        </div>
      </div>
    </section>
  </section>
</template>

<style scoped>
.form-row {
  display: flex;
  gap: 1rem;
}

.form-row label {
  flex: 1;
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

.badge-active {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: var(--success-bg);
  color: var(--success-text);
  font-size: 0.875rem;
}

.badge-inactive {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  background: var(--muted-bg);
  color: var(--muted-text);
  font-size: 0.875rem;
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

.points-expiring {
  color: var(--warning-text);
  font-weight: 600;
}

.points-used {
  color: var(--muted-text);
  text-decoration: line-through;
}

.empty-state {
  text-align: center;
  padding: 2rem;
  color: var(--muted-text);
}

.hint {
  font-size: 0.875rem;
  color: var(--muted-text);
}
</style>
