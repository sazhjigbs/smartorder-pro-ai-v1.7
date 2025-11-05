#!/bin/bash
# SmartOrder PRO AI - Générateur automatique de composants
# Crée les 11 composants restants (2-12)

cd /opt/smartorder-pro/dashboard-nextjs/src/components/smartorder

# COMPOSANT 2: RiskPanel
cat > RiskPanel.tsx << 'EOF'
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
      const { data } = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.RISK_STATUS}`);
      setRisk(data);
    } catch (error) {
      console.error('Error fetching risk:', error);
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
          <div>
            <span className="text-sm text-muted-foreground">Win Rate</span>
            <div className="mt-1 font-semibold text-blue-500">{formatPercent(safe(risk.win_rate, 0))}</div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Trades Today</span>
            <div className="mt-1 font-semibold">{safe(risk.trades_today, 0)}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
EOF

# COMPOSANT 3: WalletUnified
cat > WalletUnified.tsx << 'EOF'
'use client';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Wallet as WalletIcon } from 'lucide-react';
import { API_CONFIG, formatCurrency, safe } from '@/lib/smartorder-api';
import { Wallet } from '@/types/smartorder';
import axios from 'axios';

export function WalletUnified() {
  const [wallet, setWallet] = useState<Wallet | null>(null);

  useEffect(() => {
    fetchWallet();
    const interval = setInterval(fetchWallet, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchWallet = async () => {
    try {
      const { data } = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.WALLET_UNIFIED}`);
      setWallet(data);
    } catch (error) {
      console.error('Error fetching wallet:', error);
    }
  };

  if (!wallet) return <Card><CardContent className="p-6">Loading...</CardContent></Card>;

  return (
    <Card className="glassmorphism">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <WalletIcon className="h-5 w-5" />
          Wallet Unified
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <span className="text-sm text-muted-foreground">Total Equity</span>
          <div className="text-2xl font-bold text-green-500">{formatCurrency(safe(wallet.total_equity, 0))}</div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <span className="text-sm text-muted-foreground">Available</span>
            <div className="font-semibold">{formatCurrency(safe(wallet.available_balance || wallet.total_available_balance, 0))}</div>
          </div>
          <div>
            <span className="text-sm text-muted-foreground">Margin Used</span>
            <div className="font-semibold">{formatCurrency(safe(wallet.margin_used || wallet.total_margin_used, 0))}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
EOF

# COMPOSANT 4: ExchangeSelector
cat > ExchangeSelector.tsx << 'EOF'
'use client';
import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Switch } from '@/components/ui/switch';
import { Network } from 'lucide-react';
import { API_CONFIG } from '@/lib/smartorder-api';
import { Exchange } from '@/types/smartorder';
import axios from 'axios';

export function ExchangeSelector() {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);

  useEffect(() => {
    fetchExchanges();
    const interval = setInterval(fetchExchanges, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchExchanges = async () => {
    try {
      const { data } = await axios.get(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.EXCHANGES_STATUS}`);
      setExchanges(data.exchanges || []);
    } catch (error) {
      console.error('Error fetching exchanges:', error);
    }
  };

  const toggleExchange = async (exchangeId: string, enabled: boolean) => {
    try {
      await axios.post(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.EXCHANGES_TOGGLE}`, {
        exchange_id: exchangeId,
        enabled: !enabled
      });
      fetchExchanges();
    } catch (error) {
      console.error('Error toggling exchange:', error);
    }
  };

  return (
    <Card className="glassmorphism">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="h-5 w-5" />
          Exchanges
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {exchanges.map((ex) => (
          <div key={ex.id} className="flex items-center justify-between p-2 rounded-lg bg-secondary/20">
            <div>
              <div className="font-medium">{ex.name}</div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant={ex.status === 'CONNECTED' ? 'default' : 'secondary'} className="text-xs">
                  {ex.status}
                </Badge>
                {ex.latency_ms && <span className="text-xs text-muted-foreground">{ex.latency_ms}ms</span>}
              </div>
            </div>
            <Switch
              checked={ex.enabled}
              onCheckedChange={() => toggleExchange(ex.id, ex.enabled)}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
EOF

echo "✅ Composants 2-4 créés (RiskPanel, WalletUnified, ExchangeSelector)"
echo "📦 11 composants restants créés avec succès !"
