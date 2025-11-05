import { Card, CardContent, Typography, Table, TableBody, TableCell, TableHead, TableRow, Chip, Alert, Tabs, Tab } from '@mui/material';
import { useState, useEffect } from 'react';
import { getPositions, getAIDecisions } from '../services/api';
import type { Position, AIDecision } from '../types';

export const PositionsTable = () => {
  const [positions, setPositions] = useState<Position[]>([]);
  const [aiDecisions, setAiDecisions] = useState<AIDecision[]>([]);
  const [tab, setTab] = useState(0);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [posRes, aiRes] = await Promise.all([getPositions(), getAIDecisions()]);
      setPositions(posRes.data.positions);
      setAiDecisions(aiRes.data.decisions);
    } catch (error) {
      console.error('Erreur chargement positions:', error);
    }
  };

  const spotPositions = positions.filter((p) => p.mode === 'spot');
  const futuresPositions = positions.filter((p) => p.mode === 'futures');

  const getDecisionForPosition = (symbol: string, side: string, entry: number) => {
    return aiDecisions.find((d) => d.symbol === symbol && d.side === side && Math.abs(d.entry_price - entry) < 1);
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Positions
        </Typography>
        <Tabs value={tab} onChange={(_e, v) => setTab(v)} sx={{ mb: 2 }}>
          <Tab label={`Spot (${spotPositions.length})`} />
          <Tab label={`Futures (${futuresPositions.length})`} />
        </Tabs>

        {tab === 0 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Current</TableCell>
                <TableCell align="right">PnL %</TableCell>
                <TableCell align="right">PnL USDT</TableCell>
                <TableCell>AI Recommendation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {spotPositions.map((pos, i) => {
                const decision = getDecisionForPosition(pos.symbol, pos.side, pos.entry_price);
                return (
                  <TableRow key={i}>
                    <TableCell sx={{ fontWeight: 600 }}>{pos.symbol}</TableCell>
                    <TableCell>
                      <Chip label={pos.side} size="small" color={pos.side === 'BUY' ? 'success' : 'error'} />
                    </TableCell>
                    <TableCell align="right">${pos.entry_price.toFixed(2)}</TableCell>
                    <TableCell align="right">${pos.current_price.toFixed(2)}</TableCell>
                    <TableCell align="right">
                      <Chip label={`${pos.pnl_pct >= 0 ? '+' : ''}${pos.pnl_pct.toFixed(2)}%`} size="small" color={pos.pnl_pct >= 0 ? 'success' : 'error'} />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color={pos.pnl_usdt >= 0 ? 'success.main' : 'error.main'} fontWeight={600}>
                        ${pos.pnl_usdt.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {decision && (
                        <Alert severity={decision.urgency === 'HIGH' ? 'error' : decision.urgency === 'MEDIUM' ? 'warning' : 'info'} sx={{ py: 0 }}>
                          <Typography variant="caption">
                            {decision.action} - {decision.reason} (Conf: {(decision.confidence * 100).toFixed(0)}%)
                          </Typography>
                        </Alert>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}

        {tab === 1 && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Symbol</TableCell>
                <TableCell>Side</TableCell>
                <TableCell align="right">Entry</TableCell>
                <TableCell align="right">Current</TableCell>
                <TableCell align="right">Liq. Price</TableCell>
                <TableCell align="right">PnL %</TableCell>
                <TableCell align="right">PnL USDT</TableCell>
                <TableCell>AI Recommendation</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {futuresPositions.map((pos, i) => {
                const decision = getDecisionForPosition(pos.symbol, pos.side, pos.entry_price);
                return (
                  <TableRow key={i}>
                    <TableCell sx={{ fontWeight: 600 }}>{pos.symbol}</TableCell>
                    <TableCell>
                      <Chip label={pos.side} size="small" color={pos.side === 'BUY' ? 'success' : 'error'} />
                    </TableCell>
                    <TableCell align="right">${pos.entry_price.toFixed(2)}</TableCell>
                    <TableCell align="right">${pos.current_price.toFixed(2)}</TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color="warning.main">
                        ${pos.liquidation_price?.toFixed(2) || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell align="right">
                      <Chip label={`${pos.pnl_pct >= 0 ? '+' : ''}${pos.pnl_pct.toFixed(2)}%`} size="small" color={pos.pnl_pct >= 0 ? 'success' : 'error'} />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body2" color={pos.pnl_usdt >= 0 ? 'success.main' : 'error.main'} fontWeight={600}>
                        ${pos.pnl_usdt.toFixed(2)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {decision && (
                        <Alert severity={decision.urgency === 'HIGH' ? 'error' : decision.urgency === 'MEDIUM' ? 'warning' : 'info'} sx={{ py: 0 }}>
                          <Typography variant="caption">
                            {decision.action} - {decision.reason} (Conf: {(decision.confidence * 100).toFixed(0)}%)
                          </Typography>
                        </Alert>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
};
