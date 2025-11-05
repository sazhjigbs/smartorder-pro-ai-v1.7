import { ModeSelector } from '@/components/smartorder/ModeSelector';
import { RiskPanel } from '@/components/smartorder/RiskPanel';

export default function DashboardPage() {
  return (
    <div className="space-y-6 p-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">SmartOrder PRO AI v3.0</h1>
          <p className="text-muted-foreground">by MAIGA ABOUBAKAR - SAFELOGIC Engineering</p>
        </div>
        <ModeSelector />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <RiskPanel />
      </div>
    </div>
  );
}
