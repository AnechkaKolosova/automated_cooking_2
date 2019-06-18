export interface Device {
  id: number;
  description: string;
  status: string;
  temp?: number;
  latitude?: number;
  longitude?: number;
  humidity?: number;
  photo?: string;
}
