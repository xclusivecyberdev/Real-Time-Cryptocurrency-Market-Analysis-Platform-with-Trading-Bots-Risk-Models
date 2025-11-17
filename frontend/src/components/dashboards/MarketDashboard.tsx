import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface MarketData {
  symbol: string;
  price: number;
  change24h: number;
  volume: number;
  high24h: number;
  low24h: number;
}

interface IndicatorData {
  rsi: number;
  macd: number;
  signal: number;
}

const MarketDashboard: React.FC = () => {
  const [marketData, setMarketData] = useState<MarketData[]>([]);
  const [indicators, setIndicators] = useState<IndicatorData | null>(null);
  const [priceHistory, setPriceHistory] = useState<number[]>([]);

  useEffect(() => {
    // Fetch market data
    fetchMarketData();
    fetchIndicators();

    // Set up WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws/market');

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateMarketData(data);
    };

    return () => {
      ws.close();
    };
  }, []);

  const fetchMarketData = async () => {
    try {
      const response = await fetch('/api/market/ticker/binance/BTC/USDT');
      const data = await response.json();

      setMarketData([
        {
          symbol: 'BTC/USDT',
          price: data.last,
          change24h: data.change_24h,
          volume: data.volume,
          high24h: data.last * 1.02,
          low24h: data.last * 0.98,
        },
      ]);
    } catch (error) {
      console.error('Error fetching market data:', error);
    }
  };

  const fetchIndicators = async () => {
    try {
      const response = await fetch('/api/analytics/indicators/BTC/USDT');
      const data = await response.json();

      setIndicators({
        rsi: data.indicators.rsi,
        macd: data.indicators.macd.macd,
        signal: data.indicators.macd.signal,
      });
    } catch (error) {
      console.error('Error fetching indicators:', error);
    }
  };

  const updateMarketData = (data: any) => {
    setPriceHistory(prev => [...prev.slice(-100), data.price]);
  };

  const chartData = {
    labels: priceHistory.map((_, i) => i.toString()),
    datasets: [
      {
        label: 'BTC/USDT',
        data: priceHistory,
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'BTC/USDT Price Chart',
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Market Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Price Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Line data={chartData} options={chartOptions} />
          </Paper>
        </Grid>

        {/* Technical Indicators */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Technical Indicators
            </Typography>
            {indicators && (
              <Box>
                <Card sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      RSI
                    </Typography>
                    <Typography variant="h5">
                      {indicators.rsi.toFixed(2)}
                    </Typography>
                    <Typography
                      variant="caption"
                      color={
                        indicators.rsi > 70
                          ? 'error'
                          : indicators.rsi < 30
                          ? 'success'
                          : 'text.secondary'
                      }
                    >
                      {indicators.rsi > 70
                        ? 'Overbought'
                        : indicators.rsi < 30
                        ? 'Oversold'
                        : 'Neutral'}
                    </Typography>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent>
                    <Typography variant="body2" color="text.secondary">
                      MACD
                    </Typography>
                    <Typography variant="h6">
                      {indicators.macd.toFixed(2)}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Signal: {indicators.signal.toFixed(2)}
                    </Typography>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Paper>
        </Grid>

        {/* Market Table */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Market Overview
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Symbol</TableCell>
                    <TableCell align="right">Price</TableCell>
                    <TableCell align="right">24h Change</TableCell>
                    <TableCell align="right">Volume</TableCell>
                    <TableCell align="right">24h High</TableCell>
                    <TableCell align="right">24h Low</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {marketData.map((row) => (
                    <TableRow key={row.symbol}>
                      <TableCell component="th" scope="row">
                        {row.symbol}
                      </TableCell>
                      <TableCell align="right">
                        ${row.price.toLocaleString()}
                      </TableCell>
                      <TableCell
                        align="right"
                        sx={{
                          color: row.change24h >= 0 ? 'success.main' : 'error.main',
                        }}
                      >
                        {row.change24h >= 0 ? '+' : ''}
                        {row.change24h.toFixed(2)}%
                      </TableCell>
                      <TableCell align="right">
                        ${row.volume.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        ${row.high24h.toLocaleString()}
                      </TableCell>
                      <TableCell align="right">
                        ${row.low24h.toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default MarketDashboard;
