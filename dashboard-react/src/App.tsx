import { Container, Grid, Box, Typography } from '@mui/material';
import { Header } from './components/Header';
import { ExchangeSelector } from './components/ExchangeSelector';
import { Watchlist } from './components/Watchlist';
import { StrategiesPanel } from './components/StrategiesPanel';
import { RiskPanel } from './components/RiskPanel';
import { PositionsTable } from './components/PositionsTable';
import { AIFusionStatus } from './components/AIFusionStatus';
import { EmergencyStop } from './components/EmergencyStop';
import { SignalValidator } from './components/SignalValidator';
import { LiveLogs } from './components/LiveLogs';
import { Charts } from './components/Charts';
import { useWebSocket } from './hooks/useWebSocket';

const WS_URL = (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8182';

function App() {
  const { isConnected } = useWebSocket({
    url: WS_URL,
    onMessage: (data) => {
      console.log('[WS] Message reçu:', data);
    },
    onConnect: () => console.log('[WS] Connecté au serveur WebSocket'),
    onDisconnect: () => console.log('[WS] Déconnecté du serveur WebSocket'),
  });

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Header />
      
      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Grid container spacing={2.5}>
          {/* Emergency Stop - Full width */}
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <EmergencyStop />
            </Box>
          </Grid>

          {/* Risk Panel - Full width */}
          <Grid item xs={12}>
            <RiskPanel />
          </Grid>

          {/* AI Fusion Status - Full width */}
          <Grid item xs={12}>
            <AIFusionStatus />
          </Grid>

          {/* Exchanges + Watchlist */}
          <Grid item xs={12} md={4}>
            <Grid container spacing={2.5}>
              <Grid item xs={12}>
                <ExchangeSelector />
              </Grid>
              <Grid item xs={12}>
                <Watchlist />
              </Grid>
            </Grid>
          </Grid>

          {/* Strategies Panel */}
          <Grid item xs={12} md={8}>
            <StrategiesPanel />
          </Grid>

          {/* Signal Validator */}
          <Grid item xs={12}>
            <SignalValidator />
          </Grid>

          {/* Positions Table - Full width */}
          <Grid item xs={12}>
            <PositionsTable />
          </Grid>

          {/* Charts */}
          <Grid item xs={12}>
            <Charts />
          </Grid>

          {/* Live Logs */}
          <Grid item xs={12}>
            <LiveLogs />
          </Grid>

          {/* WebSocket Status */}
          <Grid item xs={12}>
            <Box sx={{ textAlign: 'center', py: 1, opacity: 0.5 }}>
              <Typography variant="caption" color={isConnected ? 'success.main' : 'error.main'}>
                WebSocket: {isConnected ? '🟢 Connecté' : '🔴 Déconnecté'}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
