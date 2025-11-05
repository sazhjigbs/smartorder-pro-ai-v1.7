import { Card, CardContent, Typography, Box, Chip, Grid, LinearProgress } from '@mui/material';
import { Psychology } from '@mui/icons-material';
import { useState, useEffect } from 'react';
import { getAIFusionStatus } from '../services/api';
import type { AIFusion } from '../types';

export const AIFusionStatus = () => {
  const [fusion, setFusion] = useState<AIFusion | null>(null);

  useEffect(() => {
    loadFusion();
    const interval = setInterval(loadFusion, 8000);
    return () => clearInterval(interval);
  }, []);

  const loadFusion = async () => {
    try {
      const { data } = await getAIFusionStatus();
      setFusion(data);
    } catch (error) {
      console.error('Erreur AI Fusion:', error);
    }
  };

  if (!fusion) return null;

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Psychology color="secondary" />
            <Typography variant="h6">AI Fusion Layer</Typography>
          </Box>
          <Chip label={fusion.fusion_active ? 'ACTIVE' : 'INACTIVE'} color={fusion.fusion_active ? 'success' : 'default'} />
        </Box>

        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Trust Score
          </Typography>
          <Typography variant="h4" fontWeight={700} color="secondary.main">
            {(fusion.trust_score * 100).toFixed(0)}%
          </Typography>
          <LinearProgress variant="determinate" value={fusion.trust_score * 100} color="secondary" sx={{ mt: 1, height: 8, borderRadius: 4 }} />
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(56, 97, 251, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="primary" fontWeight={600}>
                LEARNER AI
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {fusion.learner.patterns_learned} patterns
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Accuracy: {(fusion.learner.accuracy * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(240, 185, 11, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="warning.main" fontWeight={600}>
                GENETIC AI
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                Gen {fusion.genetic.generation}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Fitness: {(fusion.genetic.best_fitness * 100).toFixed(0)}%
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(14, 203, 129, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="success.main" fontWeight={600}>
                REINFORCEMENT AI
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {fusion.reinforcement.total_episodes} episodes
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Avg Reward: ${fusion.reinforcement.avg_reward.toFixed(0)}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={6} sm={3}>
            <Box sx={{ p: 1.5, backgroundColor: 'rgba(156, 75, 255, 0.1)', borderRadius: 2 }}>
              <Typography variant="caption" color="secondary.main" fontWeight={600}>
                BEHAVIOR AI
              </Typography>
              <Typography variant="body2" sx={{ mt: 0.5 }}>
                {fusion.behavior.market_emotion}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Fear/Greed: {fusion.behavior.fear_greed_index}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};
