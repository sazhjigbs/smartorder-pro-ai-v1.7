import { Button, Dialog, DialogTitle, DialogContent, DialogActions, Typography } from '@mui/material';
import { Warning } from '@mui/icons-material';
import { useState } from 'react';
import { emergencyStop } from '../services/api';

export const EmergencyStop = () => {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleStop = async () => {
    setLoading(true);
    try {
      await emergencyStop();
      alert('✅ Emergency Stop activé avec succès');
      setOpen(false);
    } catch (error) {
      console.error('Erreur emergency stop:', error);
      alert('❌ Erreur lors de l\'arrêt d\'urgence');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button variant="contained" color="error" startIcon={<Warning />} onClick={() => setOpen(true)} size="large" sx={{ fontWeight: 700 }}>
        EMERGENCY STOP
      </Button>

      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle sx={{ color: 'error.main', fontWeight: 700 }}>⚠️ Confirmation Arrêt d'Urgence</DialogTitle>
        <DialogContent>
          <Typography>Êtes-vous sûr de vouloir activer l'Emergency Stop ?</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Toutes les stratégies seront désactivées immédiatement.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)} disabled={loading}>
            Annuler
          </Button>
          <Button variant="contained" color="error" onClick={handleStop} disabled={loading}>
            Confirmer Stop
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};
