import { http } from './http'

export const loyaltyApi = {
  dashboard: () => http.get('/members/dashboard'),
  members: () => http.get('/members'),
  createMember: (payload) => http.post('/members', payload),
  rules: () => http.get('/points/rules'),
  earnPoints: (payload) => http.post('/points/earn', payload),
  transactions: () => http.get('/points/transactions'),
  gifts: () => http.get('/gifts'),
  redeemGift: (payload) => http.post('/gifts/redeem', payload),
  tiers: () => http.get('/tiers'),
  vouchers: () => http.get('/vouchers'),
  issueBirthdayVouchers: () => http.post('/vouchers/birthday/issue', {})
}
