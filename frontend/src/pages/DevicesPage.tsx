import { useEffect, useMemo } from 'react';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import MenuItem from '@mui/material/MenuItem';
import InputAdornment from '@mui/material/InputAdornment';
import CircularProgress from '@mui/material/CircularProgress';
import Typography from '@mui/material/Typography';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import { DeviceTable } from '../components/devices/DeviceTable';
import { matchesRulRange, useDeviceStore, type RulRangeFilter, type StatusFilter } from '../stores/deviceStore';

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: 'all', label: 'Todos os status' },
  { value: 'healthy', label: 'Saudável' },
  { value: 'attention', label: 'Atenção' },
  { value: 'risk', label: 'Risco' },
];

const RUL_RANGE_OPTIONS: { value: RulRangeFilter; label: string }[] = [
  { value: 'all', label: 'Todas as faixas de RUL' },
  { value: 'low', label: 'RUL baixo (< 700)' },
  { value: 'medium', label: 'RUL intermediário (700–1200)' },
  { value: 'high', label: 'RUL alto (> 1200)' },
];

export function DevicesPage() {
  const { devices, isLoading, filters, fetchDevices, setSearch, setStatusFilter, setRulRangeFilter } =
    useDeviceStore();

  useEffect(() => {
    fetchDevices();
  }, [fetchDevices]);

  const filteredDevices = useMemo(() => {
    const search = filters.search.trim().toLowerCase();
    return devices.filter((device) => {
      const matchesSearch = search.length === 0 || device.id.toLowerCase().includes(search);
      const matchesStatus = filters.status === 'all' || device.status === filters.status;
      const matchesRul = matchesRulRange(device.predictedRulCycles, filters.rulRange);
      return matchesSearch && matchesStatus && matchesRul;
    });
  }, [devices, filters]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box>
        <Typography variant="h5">Dispositivos</Typography>
        <Typography variant="body2" color="text.secondary">
          {devices.length.toLocaleString('pt-BR')} dispositivos monitorados na frota.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          placeholder="Buscar por ID (ex: DEVICE-0125)"
          size="small"
          value={filters.search}
          onChange={(event) => setSearch(event.target.value)}
          sx={{ minWidth: 260 }}
          slotProps={{
            input: {
              startAdornment: (
                <InputAdornment position="start">
                  <SearchOutlinedIcon fontSize="small" />
                </InputAdornment>
              ),
            },
          }}
        />
        <TextField
          select
          size="small"
          label="Status"
          value={filters.status}
          onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
          sx={{ minWidth: 190 }}
        >
          {STATUS_OPTIONS.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          size="small"
          label="Faixa de RUL"
          value={filters.rulRange}
          onChange={(event) => setRulRangeFilter(event.target.value as RulRangeFilter)}
          sx={{ minWidth: 220 }}
        >
          {RUL_RANGE_OPTIONS.map((option) => (
            <MenuItem key={option.value} value={option.value}>
              {option.label}
            </MenuItem>
          ))}
        </TextField>
      </Box>

      {isLoading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : (
        <DeviceTable devices={filteredDevices} />
      )}
    </Box>
  );
}
