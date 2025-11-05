#!/usr/bin/env python3
import os

os.chdir("/opt/smartorder-pro/dashboard-nextjs/src/app/dashboard")

page_code = '''import ModeSelector from "@/components/smartorder/ModeSelector";
import RiskPanel from "@/components/smartorder/RiskPanel";
import WalletUnified from "@/components/smartorder/WalletUnified";
import ExchangeSelector from "@/components/smartorder/ExchangeSelector";
import StrategiesPanel from "@/components/smartorder/StrategiesPanel";
import PositionsTable from "@/components/smartorder/PositionsTable";

export default function DashboardPage() {
  return (
    <div className="space-y-6 p-6 bg-smartorder-bg min-h-screen">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold text-white">SmartOrder PRO AI v3.0</h1>
          <p className="text-gray-400 mt-1">by MAIGA ABOUBAKAR - SAFELOGIC Engineering</p>
        </div>
        <ModeSelector />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RiskPanel />
        <WalletUnified />
      </div>

      <ExchangeSelector />
      <StrategiesPanel />
      <PositionsTable />
    </div>
  );
}
'''

with open("page.tsx", "w", encoding="utf-8") as f:
    f.write(page_code)

print("✅ Dashboard page.tsx créé")
