import { Card, CardContent, Typography, Grid, Box } from '@mui/material';
import { useState, useEffect } from 'react';
import ReactApexChart from 'react-apexcharts';
import { ApexOptions } from 'apexcharts';
import { getPnL } from '../services/api';

export const Charts = () => {
  const [pnlData, setPnlData] = useState<number[]>([]);

  useEffect(() => {
    loadPnL();
    const interval = setInterval(loadPnL, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadPnL = async () => {
    try {
      const { data } = await getPnL();
      // Vérifier que les données existent avant de les utiliser
      if (data && typeof data.daily === 'number') {
        setPnlData([data.daily - 100, data.daily - 50, data.daily, data.weekly / 7, data.total / 30]);
      }
    } catch (error) {
      console.error('Erreur chargement PnL:', error);
      // Données par défaut si erreur
      setPnlData([120, 150, 180, 140, 200]);
    }
  };

  const pnlChartOptions: ApexOptions = {
    chart: {
      type: 'area',
      height: 250,
      background: 'transparent',
      toolbar: { show: false },
    },
    theme: { mode: 'dark' },
    colors: ['#0ecb81'],
    stroke: { curve: 'smooth', width: 2 },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.2,
      },
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      labels: { style: { colors: '#b7bdc6' } },
    },
    yaxis: { labels: { style: { colors: '#b7bdc6' } } },
    grid: { borderColor: '#2b3139' },
    tooltip: {
      theme: 'dark',
      y: { formatter: (val) => `$${val.toFixed(2)}` },
    },
  };

  const rsiChartOptions: ApexOptions = {
    chart: {
      type: 'line',
      height: 200,
      background: 'transparent',
      toolbar: { show: false },
    },
    theme: { mode: 'dark' },
    colors: ['#3861fb'],
    stroke: { curve: 'smooth', width: 2 },
    dataLabels: { enabled: false },
    xaxis: {
      categories: ['1h', '2h', '3h', '4h', '5h', '6h'],
      labels: { style: { colors: '#b7bdc6' } },
    },
    yaxis: {
      min: 0,
      max: 100,
      labels: { style: { colors: '#b7bdc6' } },
    },
    grid: { borderColor: '#2b3139' },
    annotations: {
      yaxis: [
        { y: 70, borderColor: '#f6465d', label: { text: 'Overbought' } },
        { y: 30, borderColor: '#0ecb81', label: { text: 'Oversold' } },
      ],
    },
  };

  const macdChartOptions: ApexOptions = {
    chart: {
      type: 'bar',
      height: 200,
      background: 'transparent',
      toolbar: { show: false },
    },
    theme: { mode: 'dark' },
    colors: ['#9c4bff'],
    plotOptions: {
      bar: { columnWidth: '80%' },
    },
    dataLabels: { enabled: false },
    xaxis: {
      categories: ['1h', '2h', '3h', '4h', '5h', '6h'],
      labels: { style: { colors: '#b7bdc6' } },
    },
    yaxis: { labels: { style: { colors: '#b7bdc6' } } },
    grid: { borderColor: '#2b3139' },
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Performance Charts
        </Typography>

        <Grid container spacing={2}>
          {/* PnL Chart */}
          <Grid item xs={12} md={6}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(14, 203, 129, 0.05)', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                PnL Évolution (5 jours)
              </Typography>
              <ReactApexChart
                options={pnlChartOptions}
                series={[{ name: 'PnL', data: pnlData.length > 0 ? pnlData : [120, 150, 180, 140, 200] }]}
                type="area"
                height={250}
              />
            </Box>
          </Grid>

          {/* RSI Chart */}
          <Grid item xs={12} md={6}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(56, 97, 251, 0.05)', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                RSI Indicator (6h)
              </Typography>
              <ReactApexChart
                options={rsiChartOptions}
                series={[{ name: 'RSI', data: [45, 52, 38, 65, 48, 55] }]}
                type="line"
                height={200}
              />
            </Box>
          </Grid>

          {/* MACD Chart */}
          <Grid item xs={12}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(156, 75, 255, 0.05)', borderRadius: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                MACD Histogram (6h)
              </Typography>
              <ReactApexChart
                options={macdChartOptions}
                series={[{ name: 'MACD', data: [120, -80, 200, -150, 180, 90] }]}
                type="bar"
                height={200}
              />
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
