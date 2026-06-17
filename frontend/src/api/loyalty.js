import { http } from './http'

export const loyaltyApi = {
  dashboard: () => http.get('/members/dashboard'),
  members: () => http.get('/members'),
  member: (id) => http.get(`/members/${id}`),
  memberTransactions: (id) => http.get(`/members/${id}/transactions`),
  createMember: (payload) => http.post('/members', payload),
  rules: () => http.get('/points/rules'),
  earnPoints: (payload) => http.post('/points/earn', payload),
  transactions: () => http.get('/points/transactions'),
  pointBatches: (memberId, includeExpired = false) => {
    const params = new URLSearchParams()
    if (memberId) params.append('member_id', memberId)
    if (includeExpired) params.append('include_expired', 'true')
    return http.get(`/points/batches${params.toString() ? '?' + params.toString() : ''}`)
  },
  memberPointBatches: (memberId, includeExpired = false) => {
    return http.get(`/points/batches/${memberId}?include_expired=${includeExpired}`)
  },
  processExpiredPoints: () => http.post('/points/expire/process', {}),
  expirationRules: () => http.get('/expiration/rules'),
  activeExpirationRule: () => http.get('/expiration/rules/active'),
  createExpirationRule: (payload) => http.post('/expiration/rules', payload),
  activateExpirationRule: (ruleId) => http.post(`/expiration/rules/${ruleId}/activate`, {}),
  expirationReminders: () => http.get('/expiration/reminders'),
  gifts: () => http.get('/gifts'),
  redeemGift: (payload) => http.post('/gifts/redeem', payload),
  tiers: () => http.get('/tiers'),
  vouchers: () => http.get('/vouchers'),
  issueBirthdayVouchers: () => http.post('/vouchers/birthday/issue', {})
}
