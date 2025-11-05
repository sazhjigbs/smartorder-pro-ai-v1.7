'use client';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Shield } from 'lucide-react';
import { API_CONFIG, formatPercent, safe } from '@/lib/smartorder-api';
import { RiskData } from '@/types/smartorder';
import axios from 'axios';

export function RiskPanel() {
  const [risk, setRisk] = useState<RiskData | null>(null);

  useEffect(() => {
    fetchRisk();
    const interval = setInterval(fetchRisk, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchRisk = async () => {
    try {
      const url = `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.RISK_STATUS}`;
      const { data } = await axios.get(url);
      setRisk(data);
    } catch (err) {
      console.error('Risk fetch error:', err);
    }
  };

  if (!risk) return <Card><CardContent className="p-6">Loading...</CardContent></Card>;

  const reliability = safe(risk.reliability_score, 0);

  return (
    <Card className="glassmorphism">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Risk Management
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <div className="flex justify-between mb-2">
            <span className="text-sm text-muted-foreground">Market Reliability</span>
            <span className="text-lg font-bold text-green-500">{reliability}%</span>
          </div>
          <Progress value={reliability} className="h-2" />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-muted-foreground">Mode</span>
            <div className="mt-1">
              <Badge variant="outline">{risk.current_mode || 'N/A'}</Badge>
            </div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Drawdown</span>
            <div className="mt-1 font-semibold">{formatPercent(safe(risk.drawdown_day_pct, 0))}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
