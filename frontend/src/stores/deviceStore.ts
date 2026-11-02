import { create } from 'zustand';
import type { Device, DeviceStatus } from '../types/device';
import { describeApiError, getDevices } from '../services/api';

export type StatusFilter = DeviceStatus | 'all';

interface DeviceFilters {
  search: string;
  status: StatusFilter;
}

interface DeviceStoreState {
  devices: Device[];
  isLoading: boolean;
  hasLoaded: boolean;
  error: string | null;
  filters: DeviceFilters;
  fetchDevices: () => Promise<void>;
  invalidate: () => void;
  setSearch: (search: string) => void;
  setStatusFilter: (status: StatusFilter) => void;
}

export const useDeviceStore = create<DeviceStoreState>((set, get) => ({
  devices: [],
  isLoading: false,
  hasLoaded: false,
  error: null,
  filters: {
    search: '',
    status: 'all',
  },
  fetchDevices: async () => {
    if (get().hasLoaded || get().isLoading) return;
    set({ isLoading: true, error: null });
    try {
      const devices = await getDevices();
      set({ devices, isLoading: false, hasLoaded: true });
    } catch (error) {
      set({ isLoading: false, error: describeApiError(error) });
    }
  },
  invalidate: () => set({ hasLoaded: false }),
  setSearch: (search) => set((state) => ({ filters: { ...state.filters, search } })),
  setStatusFilter: (status) => set((state) => ({ filters: { ...state.filters, status } })),
}));
