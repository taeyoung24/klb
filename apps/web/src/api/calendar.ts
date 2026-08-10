import client from './client';

export interface CalendarEvent {
  date: string; // YYYY-MM-DD
  sim_day: number;
  label: string;
  event_type: string;
}

export async function getCalendarEvents(year?: number): Promise<CalendarEvent[]> {
  try {
    const params = year ? { year } : {};
    const response = await client.get<CalendarEvent[]>('/matches/calendar-events', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching calendar events:', error);
    return [];
  }
}
