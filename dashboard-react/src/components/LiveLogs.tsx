import { Card, CardContent, Typography, Box, Chip, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { Info, Warning, Error, CheckCircle } from '@mui/icons-material';
import { useState, useEffect, useRef } from 'react';
import type { LogEntry } from '../types';

export const LiveLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [filter, setFilter] = useState<string[]>(['info', 'warning', 'error', 'success']);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Simuler des logs (à remplacer par WebSocket ou API)
    const mockLogs: LogEntry[] = [
      { timestamp: new Date().toISOString(), level: 'success', message: 'Strategy RSI_MACD_BB: Signal BUY BTC/USDT @ 108,500', source: 'strategy' },
      { timestamp: new Date().toISOString(), level: 'info', message: 'Position opened: BTC/USDT LONG x3 @ 108,500', source: 'executor' },
      { timestamp: new Date().toISOString(), level: 'warning', message: 'Market Reliability dropped to 65%', source: 'risk' },
      { timestamp: new Date().toISOString(), level: 'info', message: 'AI Fusion: Trust score updated to 84%', source: 'ai' },
      { timestamp: new Date().toISOString(), level: 'error', message: 'Binance API: Rate limit warning (90/120)', source: 'exchange' },
    ];
    setLogs(mockLogs);

    // Auto-scroll
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const handleFilterChange = (_event: React.MouseEvent<HTMLElement>, newFilter: string[]) => {
    if (newFilter.length > 0) {
      setFilter(newFilter);
    }
  };

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'success':
        return <CheckCircle color="success" fontSize="small" />;
      case 'warning':
        return <Warning color="warning" fontSize="small" />;
      case 'error':
        return <Error color="error" fontSize="small" />;
      default:
        return <Info color="info" fontSize="small" />;
    }
  };

  const getLogColor = (level: string) => {
    switch (level) {
      case 'success':
        return 'success.main';
      case 'warning':
        return 'warning.main';
      case 'error':
        return 'error.main';
      default:
        return 'info.main';
    }
  };

  const filteredLogs = logs.filter((log) => filter.includes(log.level));

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Live Logs ({filteredLogs.length})</Typography>
          <ToggleButtonGroup value={filter} onChange={handleFilterChange} size="small" aria-label="log filter">
            <ToggleButton value="info" aria-label="info">
              Info
            </ToggleButton>
            <ToggleButton value="success" aria-label="success">
              Success
            </ToggleButton>
            <ToggleButton value="warning" aria-label="warning">
              Warning
            </ToggleButton>
            <ToggleButton value="error" aria-label="error">
              Error
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        <Box
          sx={{
            maxHeight: 300,
            overflowY: 'auto',
            backgroundColor: 'rgba(0,0,0,0.2)',
            borderRadius: 2,
            p: 1.5,
          }}
        >
          {filteredLogs.map((log, i) => (
            <Box
              key={i}
              sx={{
                display: 'flex',
                gap: 1,
                mb: 1,
                pb: 1,
                borderBottom: i < filteredLogs.length - 1 ? '1px solid rgba(255,255,255,0.05)' : 'none',
              }}
            >
              {getLogIcon(log.level)}
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mb: 0.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </Typography>
                  {log.source && <Chip label={log.source} size="small" sx={{ height: 18, fontSize: '0.65rem' }} />}
                </Box>
                <Typography variant="body2" color={getLogColor(log.level)}>
                  {log.message}
                </Typography>
              </Box>
            </Box>
          ))}
          <div ref={logsEndRef} />
        </Box>
      </CardContent>
    </Card>
  );
};
