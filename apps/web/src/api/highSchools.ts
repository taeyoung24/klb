import type { Region } from './regions';

export interface HighSchool {
  id: number;
  name: string;
  name_ko: string;
  is_specialized: boolean;
  capacity: number;
  region_id: number;
  region?: Region | null;
}
