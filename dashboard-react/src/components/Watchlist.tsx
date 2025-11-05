import {
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Box,
  Button,
} from '@mui/material';
import { Delete, Add, TrendingUp } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getWatchlist, manageWatchlist, getGainers } from '../services/api';
import type { WatchlistAsset, Gainer } from '../types';

export const Watchlist = () => {
  const [assets, setAssets] = useState<WatchlistAsset[]>([]);
  const [gainers, setGainers] = useState<Gainer[]>([]);
  const [showGainers, setShowGainers] = useState(false);

  useEffect(() => {
    loadWatchlist();
    const interval = setInterval(loadWatchlist, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadWatchlist = async () => {
    try {
      const { data } = await getWatchlist();
      setAssets(data.assets);
    } catch (error) {
      console.error('Erreur chargement watchlist:', error);
    }
  };

  const loadGainers = async () => {
    try {
      const { data } = await getGainers(5);
      setGainers(data.gainers);
      setShowGainers(true);
    } catch (error) {
      console.error('Erreur chargement gainers:', error);
    }
  };

  const handleRemove = async (symbol: string) => {
    try {
      await manageWatchlist(symbol, 'remove');
      await loadWatchlist();
    } catch (error) {
      console.error('Erreur suppression asset:', error);
    }
  };

  const handleAddGainer = async (symbol: string) => {
    try {
      await manageWatchlist(symbol, 'add');
      await loadWatchlist();
      setShowGainers(false);
    } catch (error) {
      console.error('Erreur ajout gainer:', error);
    }
  };

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Watchlist ({assets.length})</Typography>
          <Button size="small" startIcon={<TrendingUp />} onClick={loadGainers}>
            Top Gainers
          </Button>
        </Box>

        {showGainers && gainers.length > 0 && (
          <Box sx={{ mb: 2, p: 1.5, backgroundColor: 'rgba(14, 203, 129, 0.1)', borderRadius: 2 }}>
            <Typography variant="body2" fontWeight={600} gutterBottom>
              Top Gainers 24h
            </Typography>
            {gainers.map((gainer) => (
              <Box key={gainer.symbol} sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', py: 0.5 }}>
                <Typography variant="body2">{gainer.symbol}</Typography>
                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  <Chip label={`+${gainer.change_24h.toFixed(1)}%`} size="small" color="success" />
                  <IconButton size="small" onClick={() => handleAddGainer(gainer.symbol)}>
                    <Add fontSize="small" />
                  </IconButton>
                </Box>
              </Box>
            ))}
          </Box>
        )}

        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Symbol</TableCell>
              <TableCell align="right">Price</TableCell>
              <TableCell align="right">24h %</TableCell>
              <TableCell align="right">Volume</TableCell>
              <TableCell align="center">Action</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {assets.map((asset) => (
              <TableRow key={asset.symbol}>
                <TableCell>
                  <Typography variant="body2" fontWeight={600}>
                    {asset.symbol}
                  </Typography>
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2">${asset.price.toLocaleString()}</Typography>
                </TableCell>
                <TableCell align="right">
                  <Chip
                    label={`${asset.change_24h > 0 ? '+' : ''}${asset.change_24h.toFixed(2)}%`}
                    size="small"
                    color={asset.change_24h > 0 ? 'success' : 'error'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Typography variant="body2" color="text.secondary">
                    ${(asset.volume / 1000000).toFixed(2)}M
                  </Typography>
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small" onClick={() => handleRemove(asset.symbol)} color="error">
                    <Delete fontSize="small" />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
};
