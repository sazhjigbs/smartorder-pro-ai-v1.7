import paramiko

# Components code
COMPONENTS = {
    "ExchangeSelector.tsx": '''use client';
import { useEffect, useState } from 'react';
import { Activity } from 'lucide-react';
import { API_CONFIG, safe } from '@/lib/smartorder-api';

interface Exchange {
  exchange_id: string;
  name: string;
  status: string;
  latency_ms: number | null;
}

export default function ExchangeSelector() {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.EXCHANGES_STATUS}`);
        const data = await res.json();
        setExchanges(data.exchanges || []);
      } catch (e) { }
      finally { setLoading(false); }
    };
    fetchData();
    const i = setInterval(fetchData, 5000);
    return () => clearInterval(i);
  }, []);

  if (loading) return <div className="glassmorphism p-6 rounded-xl animate-pulse"><div className="h-8 bg-gray-700/50 rounded"></div></div>;

  return (
    <div className="glassmorphism p-6 rounded-xl">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2"><Activity className="w-6 h-6 text-blue-500"/>Exchanges</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {exchanges.map(ex => (
          <div key={ex.exchange_id} className="glassmorphism p-4 rounded-lg">
            <h3 className="font-bold text-white">{ex.name}</h3>
            <div className="text-xs text-gray-400">Latency: {safe(ex.latency_ms, 0)}ms</div>
          </div>
        ))}
      </div>
    </div>
  );
}
''',
    "AIDecisionsBadge.tsx": '''use client';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

interface Props {
  action: 'BUY' | 'SELL' | 'HOLD' | null;
  confidence: number | null;
  reasoning?: string;
  size?: 'sm' | 'md';
}

export default function AIDecisionsBadge({ action, confidence, reasoning, size = 'md' }: Props) {
  if (!action) return null;
  const colors = { BUY: 'bg-green-500/20 text-green-400', SELL: 'bg-red-500/20 text-red-400', HOLD: 'bg-yellow-500/20 text-yellow-400' };
  const icons = { BUY: TrendingUp, SELL: TrendingDown, HOLD: Minus };
  const Icon = icons[action];
  return (
    <div className={`inline-flex items-center gap-1 rounded px-2 py-1 text-xs ${colors[action]}`} title={reasoning}>
      <Icon className="w-3 h-3"/><span>{action}</span>
      {confidence && <span className="opacity-75">{Math.round(confidence)}%</span>}
    </div>
  );
}
''',
    "StrategiesPanel.tsx": '''use client';
import { useEffect, useState } from 'react';
import { Brain } from 'lucide-react';
import { API_CONFIG, safe, formatPercent } from '@/lib/smartorder-api';

interface Strategy {
  strategy_id: string;
  name: string;
  active: boolean | null;
  score: number | null;
  performance_24h: number | null;
}

export default function StrategiesPanel() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.STRATEGIES}`);
        const data = await res.json();
        setStrategies(data.strategies || []);
      } catch (e) { }
      finally { setLoading(false); }
    };
    fetchData();
    const i = setInterval(fetchData, 5000);
    return () => clearInterval(i);
  }, []);

  if (loading) return <div className="glassmorphism p-6 rounded-xl animate-pulse"><div className="h-8 bg-gray-700/50 rounded"></div></div>;

  return (
    <div className="glassmorphism p-6 rounded-xl">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2"><Brain className="w-6 h-6 text-purple-500"/>Strategies ({strategies.length})</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {strategies.map(s => {
          const score = safe(s.score, 0);
          const perf = safe(s.performance_24h, 0);
          return (
            <div key={s.strategy_id} className="glassmorphism p-4 rounded-lg">
              <h3 className="font-bold text-white mb-2">{s.name}</h3>
              <div className="mb-2"><span className="text-gray-400 text-sm">Score:</span> <span className="text-white font-bold">{score}/100</span></div>
              <div className="w-full bg-gray-700 rounded-full h-2"><div className="bg-purple-500 h-2 rounded-full" style={{width: `${score}%`}}></div></div>
              <div className="mt-2 text-xs text-gray-400">24h: <span className={perf >= 0 ? 'text-green-400' : 'text-red-400'}>{formatPercent(perf)}</span></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
''',
    "PositionsTable.tsx": '''use client';
import { useEffect, useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { API_CONFIG, safe, formatCurrency } from '@/lib/smartorder-api';
import AIDecisionsBadge from './AIDecisionsBadge';

interface Position {
  position_id: string;
  symbol: string;
  side: string;
  size: number | null;
  entry_price: number | null;
  current_price: number | null;
  unrealized_pnl: number | null;
  ai_recommendation?: { action: 'BUY' | 'SELL' | 'HOLD'; confidence: number; reasoning: string; };
}

export default function PositionsTable() {
  const [positions, setPositions] = useState<Position[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.POSITIONS}`);
        const data = await res.json();
        setPositions(data.futures || []);
      } catch (e) { }
      finally { setLoading(false); }
    };
    fetchData();
    const i = setInterval(fetchData, 3000);
    return () => clearInterval(i);
  }, []);

  if (loading) return <div className="glassmorphism p-6 rounded-xl animate-pulse"><div className="h-64 bg-gray-700/50 rounded"></div></div>;

  return (
    <div className="glassmorphism p-6 rounded-xl">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-2"><BarChart3 className="w-6 h-6 text-blue-500"/>Positions ({positions.length})</h2>
      {positions.length === 0 ? (
        <div className="text-center py-12 text-gray-400">No open positions</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
                <th className="pb-3 px-2">Symbol</th>
                <th className="pb-3 px-2">Side</th>
                <th className="pb-3 px-2">Size</th>
                <th className="pb-3 px-2">Entry</th>
                <th className="pb-3 px-2">Current</th>
                <th className="pb-3 px-2">PnL</th>
                <th className="pb-3 px-2">AI</th>
              </tr>
            </thead>
            <tbody>
              {positions.map(p => {
                const pnl = safe(p.unrealized_pnl, 0);
                return (
                  <tr key={p.position_id} className="border-b border-gray-700/30">
                    <td className="py-4 px-2 font-bold text-white">{p.symbol}</td>
                    <td className="py-4 px-2"><span className={`px-2 py-1 rounded text-xs ${p.side === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{p.side}</span></td>
                    <td className="py-4 px-2 text-white font-mono">{safe(p.size, 0).toFixed(4)}</td>
                    <td className="py-4 px-2 text-gray-300">{formatCurrency(p.entry_price)}</td>
                    <td className="py-4 px-2 text-white">{formatCurrency(p.current_price)}</td>
                    <td className="py-4 px-2"><div className={`font-bold ${pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>{pnl >= 0 ? '+' : ''}{formatCurrency(pnl)}</div></td>
                    <td className="py-4 px-2">{p.ai_recommendation ? <AIDecisionsBadge action={p.ai_recommendation.action} confidence={p.ai_recommendation.confidence} reasoning={p.ai_recommendation.reasoning} size="sm"/> : <span className="text-gray-500 text-xs">-</span>}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
'''
}

# SSH connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('107.189.22.255', username='root')

base_path = '/opt/smartorder-pro/dashboard-nextjs/src/components/smartorder'

for filename, content in COMPONENTS.items():
    full_path = f'{base_path}/{filename}'
    command = f"cat > {full_path} << 'ENDFILE'\n{content}\nENDFILE"
    stdin, stdout, stderr = ssh.exec_command(command)
    stdout.channel.recv_exit_status()
    print(f'✅ {filename}')

ssh.close()
print('\n✅ All components deployed!')
