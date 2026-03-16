"use client";

import { useEffect, useState } from "react";
import { useGender } from "@/context/GenderContext";
import { getSchools } from "@/lib/api";
import type { School } from "@/lib/api";

const SEASONS = Array.from({ length: 10 }, (_, i) => 2025 - i);

interface SchoolSeasonSelectorProps {
  onSelectionChange: (school: string, season: number, schoolName: string) => void;
}

export function SchoolSeasonSelector({
  onSelectionChange,
}: SchoolSeasonSelectorProps) {
  const { gender } = useGender();
  const [schools, setSchools] = useState<School[]>([]);
  const [selectedSchool, setSelectedSchool] = useState("");
  const [selectedSchoolName, setSelectedSchoolName] = useState("");
  const [selectedSeason, setSelectedSeason] = useState(SEASONS[0]);
  const [loading, setLoading] = useState(true);

  // Re-fetch schools when gender changes
  useEffect(() => {
    setLoading(true);
    getSchools({ gender, conference: "GAC" }).then((data) => {
      setSchools(data);
      if (data.length > 0) {
        setSelectedSchool(data[0].abbreviation);
        setSelectedSchoolName(data[0].name);
        onSelectionChange(data[0].abbreviation, selectedSeason, data[0].name);
      } else {
        setSelectedSchool("");
        setSelectedSchoolName("");
      }
      setLoading(false);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gender]);

  const handleSchoolChange = (abbr: string) => {
    setSelectedSchool(abbr);
    const schoolName = schools.find((s) => s.abbreviation === abbr)?.name ?? abbr;
    setSelectedSchoolName(schoolName);
    onSelectionChange(abbr, selectedSeason, schoolName);
  };

  const handleSeasonChange = (season: number) => {
    setSelectedSeason(season);
    onSelectionChange(selectedSchool, season, selectedSchoolName);
  };

  if (loading) {
    return (
      <div className="flex gap-3">
        <div className="h-10 w-16 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
        <div className="h-10 w-40 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
        <div className="h-10 w-32 animate-pulse rounded-lg bg-gray-200 dark:bg-gray-700" />
      </div>
    );
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <span className="inline-flex items-center gap-1 rounded-md bg-surface-muted px-2 py-1.5 text-xs font-semibold text-slate-600">
        GAC
      </span>

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
