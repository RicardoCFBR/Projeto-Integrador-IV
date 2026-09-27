import { create } from 'zustand';
import type { Device, DeviceStatus } from '../types/device';
import { getDevices } from '../services/api';

export type RulRangeFilter = 'all' | 'low' | 'medium' | 'high';
export type StatusFilter = DeviceStatus | 'all';

interface DeviceFilters {
  search: string;
  status: StatusFilter;
  rulRange: RulRangeFilter;
}

interface DeviceStoreState {
  devices: Device[];
  isLoading: boolean;
  hasLoaded: boolean;
  filters: DeviceFilters;
  fetchDevices: () => Promise<void>;
  setSearch: (search: string) => void;
  setStatusFilter: (status: StatusFilter) => void;
  setRulRangeFilter: (range: RulRangeFilter) => void;
}

export const useDeviceStore = create<DeviceStoreState>((set, get) => ({
  devices: [],
  isLoading: false,
  hasLoaded: false,
  filters: {
    search: '',
    status: 'all',
    rulRange: 'all',
  },
  fetchDevices: async () => {
    if (get().hasLoaded || get().isLoading) return;
    set({ isLoading: true });
    const devices = await getDevices();
    set({ devices, isLoading: false, hasLoaded: true });
  },
  setSearch: (search) => set((state) => ({ filters: { ...state.filters, search } })),
  setStatusFilter: (status) => set((state) => ({ filters: { ...state.filters, status } })),
  setRulRangeFilter: (rulRange) => set((state) => ({ filters: { ...state.filters, rulRange } })),
}));

export function matchesRulRange(predictedRulCycles: number, range: RulRangeFilter): boolean {
  if (range === 'all') return true;
  if (range === 'low') return predictedRulCycles < 700;
  if (range === 'medium') return predictedRulCycles >= 700 && predictedRulCycles <= 1200;
  return predictedRulCycles > 1200;
}
