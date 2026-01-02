import { prisma } from '@/lib/prisma'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { CoinSettingsForm } from './coin-settings-form'
import { ReferralSettingsForm } from './referral-settings-form'
import { PaymentMethodsForm } from './payment-methods-form'

async function getSettings() {
  const [coinSettings, referralSetting, paymentMethods] = await Promise.all([
    prisma.coinSetting.findMany({ orderBy: { coinSymbol: 'asc' } }),
    prisma.referralSetting.findFirst(),
    prisma.paymentMethod.findMany({ orderBy: { name: 'asc' } }),
  ])

  const serializedCoinSettings = coinSettings.map(s => ({
    id: s.id,
    coinSymbol: s.coinSymbol,
    network: s.network,
    buyMargin: Number(s.buyMargin),
    sellMargin: Number(s.sellMargin),
    minBuy: Number(s.minBuy),
    maxBuy: Number(s.maxBuy),
    minSell: Number(s.minSell),
    maxSell: Number(s.maxSell),
    isActive: s.isActive,
  }))

  const serializedReferralSetting = referralSetting ? {
    id: referralSetting.id,
    referrerBonus: Number(referralSetting.referrerBonus),
    refereeBonus: Number(referralSetting.refereeBonus),
    isActive: referralSetting.isActive,
  } : null

  return { 
    coinSettings: serializedCoinSettings, 
    referralSetting: serializedReferralSetting, 
    paymentMethods 
  }
}

export default async function SettingsPage() {
  const { coinSettings, referralSetting, paymentMethods } = await getSettings()

  return (
    <div className="space-y-4 md:space-y-6">
      <h1 className="text-xl md:text-2xl font-bold tracking-tight">Settings</h1>
      
      <div className="grid gap-4 md:gap-6">
        <Card className="transition-smooth">
          <CardHeader className="pb-3 md:pb-4">
            <CardTitle className="text-base md:text-lg">Coin Margins</CardTitle>
          </CardHeader>
          <CardContent className="p-4 md:p-6 pt-0 md:pt-0">
            <CoinSettingsForm settings={coinSettings} />
          </CardContent>
        </Card>

        <Card className="transition-smooth">
          <CardHeader className="pb-3 md:pb-4">
            <CardTitle className="text-base md:text-lg">Referral Bonus</CardTitle>
          </CardHeader>
          <CardContent className="p-4 md:p-6 pt-0 md:pt-0">
            <ReferralSettingsForm setting={referralSetting} />
          </CardContent>
        </Card>

        <Card className="transition-smooth">
          <CardHeader className="pb-3 md:pb-4">
            <CardTitle className="text-base md:text-lg">Payment Methods</CardTitle>
          </CardHeader>
          <CardContent className="p-4 md:p-6 pt-0 md:pt-0">
            <PaymentMethodsForm methods={paymentMethods} />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
