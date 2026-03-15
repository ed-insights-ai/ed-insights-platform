"use client";

import { useEffect, useState } from "react";
import { getSchools } from "@/lib/api";
import type { School } from "@/lib/api";

const SEASONS = Array.from({ length: 10 }, (_, i) => 2025 - i);

interface SchoolSeasonSelectorProps {
  onSelectionChange: (school: string, season: number, schoolName: string) => void;
}

export function SchoolSeasonSelector({
  onSelectionChange,
}: SchoolSeasonSelectorProps) {
  const [schools, setSchools] = useState<School[]>([]);
  const [selectedSchool, setSelectedSchool] = useState("");
  const [selectedSeason, setSelectedSeason] = useState(SEASONS[0]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSchools().then((data) => {
      setSchools(data);
      if (data.length > 0) {
        setSelectedSchool(data[0].abbreviation);
        onSelectionChange(data[0].abbreviation, selectedSeason, data[0].name);
      }
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSchoolChange = (abbr: string) => {
    setSelectedSchool(abbr);
    const schoolName = schools.find((s) => s.abbreviation === abbr)?.name ?? abbr;
    onSelectionChange(abbr, selectedSeason, schoolName);
  };

  const handleSeasonChange = (season: number) => {
    setSelectedSeason(season);
    const schoolName = schools.find((s) => s.abbreviation === selectedSchool)?.name ?? selectedSchool;
    onSelectionChange(selectedSchool, season, schoolName);
  };

  if (loading) {
    return (
      <div className="flex gap-3">
        <div className="h-10 w-40 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
        <div className="h-10 w-32 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-3">
      <select
        value={selectedSchool}
        onChange={(e) => handleSchoolChange(e.target.value)}
        className="rounded-lg border bg-card px-3 py-2 text-sm font-medium text-primary-900 dark:text-white dark:border-gray-700 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        {schools.map((s) => (
          <option key={s.id} value={s.abbreviation}>
            {s.name} ({s.abbreviation})
          </option>
        ))}
      </select>

      <select
        value={selectedSeason}
        onChange={(e) => handleSeasonChange(Number(e.target.value))}
        className="rounded-lg border bg-card px-3 py-2 text-sm font-medium text-primary-900 dark:text-white dark:border-gray-700 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-primary-500"
      >
        {SEASONS.map((y) => (
          <option key={y} value={y}>
            {y - 1}&ndash;{y}
          </option>
        ))}
      </select>
    </div>
  );
}
