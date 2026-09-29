import { useMemo, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import TableSortLabel from '@mui/material/TableSortLabel';
import TablePagination from '@mui/material/TablePagination';
import IconButton from '@mui/material/IconButton';
import Tooltip from '@mui/material/Tooltip';
import Paper from '@mui/material/Paper';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import type { Device } from '../../types/device';
import { DeviceStatusChip } from './DeviceStatusChip';

type SortableColumn = 'id' | 'sohPercent' | 'predictedRulCycles' | 'temperatureMean30d' | 'cycleCount';
type SortDirection = 'asc' | 'desc';

interface DeviceTableProps {
  devices: Device[];
}

const COLUMNS: { key: SortableColumn; label: string }[] = [
  { key: 'id', label: 'Dispositivo' },
  { key: 'sohPercent', label: 'SoH' },
  { key: 'predictedRulCycles', label: 'RUL previsto' },
  { key: 'temperatureMean30d', label: 'Temperatura média' },
  { key: 'cycleCount', label: 'Ciclos' },
];

function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const diffMinutes = Math.round((Date.now() - date.getTime()) / 60_000);

  if (diffMinutes < 60) return `Há ${diffMinutes} min`;
  const diffHours = Math.round(diffMinutes / 60);
  if (diffHours < 24) return `Hoje ${date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })}`;
  const diffDays = Math.round(diffHours / 24);
  return `Há ${diffDays} dia${diffDays > 1 ? 's' : ''}`;
}

export function DeviceTable({ devices }: DeviceTableProps) {
  const [orderBy, setOrderBy] = useState<SortableColumn>('id');
  const [order, setOrder] = useState<SortDirection>('asc');
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);

  const sortedDevices = useMemo(() => {
    const sorted = [...devices].sort((a, b) => {
      const aValue = a[orderBy];
      const bValue = b[orderBy];
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return aValue.localeCompare(bValue);
      }
      return Number(aValue) - Number(bValue);
    });
    return order === 'asc' ? sorted : sorted.reverse();
  }, [devices, orderBy, order]);

  const paginatedDevices = sortedDevices.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage);

  function handleSort(column: SortableColumn) {
    if (orderBy === column) {
      setOrder((prev) => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setOrderBy(column);
      setOrder('asc');
    }
  }

  return (
    <Paper variant="outlined">
      <TableContainer>
        <Table size="small">
          <TableHead>
            <TableRow>
              {COLUMNS.map((column) => (
                <TableCell key={column.key}>
                  <TableSortLabel
                    active={orderBy === column.key}
                    direction={orderBy === column.key ? order : 'asc'}
                    onClick={() => handleSort(column.key)}
                  >
                    {column.label}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell>Status</TableCell>
              <TableCell>Descargas profundas</TableCell>
              <TableCell>Última leitura</TableCell>
              <TableCell align="right">Ações</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedDevices.map((device) => (
              <TableRow key={device.id} hover>
                <TableCell sx={{ fontWeight: 600 }}>{device.id}</TableCell>
                <TableCell>{device.sohPercent}%</TableCell>
                <TableCell>{device.predictedRulCycles.toLocaleString('pt-BR')}</TableCell>
                <TableCell>{device.temperatureMean30d}°C</TableCell>
                <TableCell>{device.cycleCount.toLocaleString('pt-BR')}</TableCell>
                <TableCell>
                  <DeviceStatusChip status={device.status} />
                </TableCell>
                <TableCell>{device.deepDischargeEvents30d}</TableCell>
                <TableCell>{formatRelativeTime(device.lastTelemetryAt)}</TableCell>
                <TableCell align="right">
                  <Tooltip title="Visualizar detalhes">
                    <IconButton component={RouterLink} to={`/devices/${device.id}`} size="small">
                      <VisibilityOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {paginatedDevices.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                  Nenhum dispositivo encontrado para os filtros aplicados.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </TableContainer>
      <TablePagination
        component="div"
        count={sortedDevices.length}
        page={page}
        onPageChange={(_, newPage) => setPage(newPage)}
        rowsPerPage={rowsPerPage}
        onRowsPerPageChange={(event) => {
          setRowsPerPage(parseInt(event.target.value, 10));
          setPage(0);
        }}
        rowsPerPageOptions={[10, 25, 50]}
        labelRowsPerPage="Linhas por página"
        labelDisplayedRows={({ from, to, count }) => `${from}–${to} de ${count}`}
      />
    </Paper>
  );
}
