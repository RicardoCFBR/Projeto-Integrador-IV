import { useParams } from 'react-router-dom';
import Typography from '@mui/material/Typography';

export function DeviceDetailPage() {
  const { id } = useParams<{ id: string }>();
  return <Typography variant="h5">Detalhe do dispositivo {id}</Typography>;
}
