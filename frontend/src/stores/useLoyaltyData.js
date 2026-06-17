import { reactive } from 'vue'
import { loyaltyApi } from '../api/loyalty'

const state = reactive({
  loading: false,
  error: '',
  notice: '',
  dashboard: null,
  members: [],
  rules: [],
  gifts: [],
  tiers: [],
  vouchers: [],
  transactions: [],
  pointBatches: [],
  expirationRules: [],
  activeExpirationRule: null,
  expirationReminders: [],
  selectedMember: null,
  selectedMemberBatches: []
})

async function run(action, successMessage = '') {
  state.loading = true
  state.error = ''
  try {
    const result = await action()
    state.notice = successMessage
    return result
  } catch (error) {
    state.error = error.message
    throw error
  } finally {
    state.loading = false
  }
}

async function refreshAll() {
  state.loading = true
  state.error = ''
  try {
    const [dashboard, members, rules, gifts, tiers, vouchers, transactions, expirationRules, activeRule, reminders] = await Promise.all([
      loyaltyApi.dashboard(),
      loyaltyApi.members(),
      loyaltyApi.rules(),
      loyaltyApi.gifts(),
      loyaltyApi.tiers(),
      loyaltyApi.vouchers(),
      loyaltyApi.transactions(),
      loyaltyApi.expirationRules(),
      loyaltyApi.activeExpirationRule().catch(() => null),
      loyaltyApi.expirationReminders()
    ])
    Object.assign(state, {
      dashboard,
      members,
      rules,
      gifts,
      tiers,
      vouchers,
      transactions,
      expirationRules,
      activeExpirationRule: activeRule,
      expirationReminders: reminders
    })
  } catch (error) {
    state.error = error.message
  } finally {
    state.loading = false
  }
}

export function useLoyaltyData() {
  return {
    state,
    refreshAll,
    async createMember(payload) {
      await run(() => loyaltyApi.createMember(payload), '会员已创建')
      await refreshAll()
    },
    async earnPoints(payload) {
      await run(() => loyaltyApi.earnPoints(payload), '积分已入账')
      await refreshAll()
    },
    async redeemGift(payload) {
      try {
        await run(() => loyaltyApi.redeemGift(payload), '礼品已兑换')
        await refreshAll()
      } catch (e) {
        await refreshAll()
        throw e
      }
    },
    async issueBirthdayVouchers() {
      const vouchers = await run(() => loyaltyApi.issueBirthdayVouchers(), '生日礼券发放完成')
      await refreshAll()
      return vouchers
    },
    async loadMemberDetail(memberId) {
      const [member, batches] = await Promise.all([
        loyaltyApi.member(memberId),
        loyaltyApi.memberPointBatches(memberId)
      ])
      state.selectedMember = member
      state.selectedMemberBatches = batches
      return { member, batches }
    },
    async loadPointBatches(memberId = null, includeExpired = false) {
      state.pointBatches = await run(() => loyaltyApi.pointBatches(memberId, includeExpired))
      return state.pointBatches
    },
    async createExpirationRule(payload) {
      const rule = await run(() => loyaltyApi.createExpirationRule(payload), '过期规则已创建')
      await refreshAll()
      return rule
    },
    async activateExpirationRule(ruleId) {
      await run(() => loyaltyApi.activateExpirationRule(ruleId), '已设为当前规则')
      await refreshAll()
    },
    async processExpiredPoints() {
      const result = await run(() => loyaltyApi.processExpiredPoints(), '过期积分已处理')
      await refreshAll()
      return result
    },
    async loadExpirationReminders() {
      state.expirationReminders = await run(() => loyaltyApi.expirationReminders())
      return state.expirationReminders
    }
  }
}
