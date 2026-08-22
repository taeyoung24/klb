import React, { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { getSystemInfo } from '../api/system';
import { getClubs, type Club } from '../api/clubs';

interface SystemContextType {
  seasonYear: number | null;
  currentDate: Date;
  scheduleDate: Date;
  hostLeagueName: string | null;
  hostLeagueId: number;
  clubsMap: Record<number, Club>;
  isLoaded: boolean;
  setScheduleDate: React.Dispatch<React.SetStateAction<Date>>;
  handleScheduleDateChange: (days: number) => void;
}

const SystemContext = createContext<SystemContextType | undefined>(undefined);

export function SystemProvider({ children }: { children: ReactNode }) {
  const [seasonYear, setSeasonYear] = useState<number | null>(null);
  const [currentDate, setCurrentDate] = useState<Date>(new Date("1953-01-01"));
  const [scheduleDate, setScheduleDate] = useState<Date>(new Date("1953-01-01"));
  const [hostLeagueName, setHostLeagueName] = useState<string | null>(null);
  const [hostLeagueId, setHostLeagueId] = useState<number>(1);
  const [clubsMap, setClubsMap] = useState<Record<number, Club>>({});
  const [isLoaded, setIsLoaded] = useState<boolean>(false);

  useEffect(() => {
    Promise.all([getSystemInfo(), getClubs()])
      .then(([info, clubs]) => {
        setSeasonYear(info.season_year);
        if (info.host_league_name) setHostLeagueName(info.host_league_name);
        if (info.host_league_id) setHostLeagueId(info.host_league_id);

        const [y, m, d] = info.current_date.split('-');
        const sysDate = new Date(Number(y), Number(m) - 1, Number(d));
        setCurrentDate(sysDate);
        setScheduleDate(sysDate);

        const map: Record<number, Club> = {};
        clubs.forEach(c => {
          map[c.id] = c;
        });
        setClubsMap(map);
        setIsLoaded(true);
      })
      .catch(e => {
        console.error("Failed to load initial system context data", e);
        setSeasonYear(1953);
        setIsLoaded(true);
      });
  }, []);

  const handleScheduleDateChange = (days: number) => {
    setScheduleDate(prev => {
      const nextDate = new Date(prev);
      nextDate.setDate(nextDate.getDate() + days);
      return nextDate;
    });
  };

  return (
    <SystemContext.Provider
      value={{
        seasonYear,
        currentDate,
        scheduleDate,
        hostLeagueName,
        hostLeagueId,
        clubsMap,
        isLoaded,
        setScheduleDate,
        handleScheduleDateChange,
      }}
    >
      {children}
    </SystemContext.Provider>
  );
}

export function useSystemContext() {
  const context = useContext(SystemContext);
  if (!context) {
    throw new Error('useSystemContext must be used within a SystemProvider');
  }
  return context;
}
