export interface School {
  id: number;
  name: string;
  abbreviation: string;
  conference: string | null;
  mascot: string | null;
  gender: string | null;
  enabled: boolean | null;
}

export interface GameSummary {
  game_id: number;
  school_id: number;
  season_year: number;
  date: string | null;
  venue: string | null;
  home_team: string | null;
  away_team: string | null;
  home_score: number | null;
  away_score: number | null;
}

export interface PaginatedGames {
  items: GameSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface TeamGameStatsResponse {
  id: number;
  game_id: number;
  school_id: number;
  team: string | null;
  is_home: boolean | null;
  shots: number | null;
  shots_on_goal: number | null;
  goals: number | null;
  corners: number | null;
  saves: number | null;
}

export interface PlayerGameStatsResponse {
  id: number;
  game_id: number;
  school_id: number;
  team: string | null;
  jersey_number: string | null;
  player_name: string | null;
  position: string | null;
  is_starter: boolean | null;
  minutes: number | null;
  shots: number | null;
  shots_on_goal: number | null;
  goals: number | null;
  assists: number | null;
}

export interface GameEventResponse {
  id: number;
  game_id: number;
  school_id: number;
  event_type: string | null;
  clock: string | null;
  team: string | null;
  player: string | null;
  assist1: string | null;
  assist2: string | null;
  description: string | null;
}

export interface GameDetail {
  game_id: number;
  school_id: number;
  season_year: number;
  source_url: string | null;
  date: string | null;
  venue: string | null;
  attendance: number | null;
  home_team: string | null;
  away_team: string | null;
  home_score: number | null;
  away_score: number | null;
  team_stats: TeamGameStatsResponse[];
  player_stats: PlayerGameStatsResponse[];
  events: GameEventResponse[];
}

export interface TeamStatsAggregation {
  school_id: number;
  school_name: string;
  season_year: number;
  games_played: number;
  total_goals: number;
  total_shots: number;
  total_shots_on_goal: number;
  total_corners: number;
  total_saves: number;
}

export interface PlayerLeaderboard {
  player_name: string;
  school_id: number;
  school_name: string;
  school_abbreviation: string;
  games_played: number;
  total_goals: number;
  total_assists: number;
  total_shots: number;
  total_shots_on_goal: number;
  total_minutes: number;
}

export interface PaginatedPlayers {
  items: PlayerLeaderboard[];
  total: number;
  limit: number;
  offset: number;
}

export interface FormResult {
  result: "W" | "L" | "D";
  game_id: number;
}

export interface ConferenceStanding {
  school_id: number;
  school_name: string;
  abbreviation: string;
  gender: string;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  ppg: number;
  form: FormResult[];
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getSchools(params?: {
  gender?: string;
  conference?: string;
}): Promise<School[]> {
  try {
    const query = new URLSearchParams();
    if (params?.gender) query.set("gender", params.gender);
    if (params?.conference) query.set("conference", params.conference);
    const url = `${API_BASE_URL}/api/schools${query.toString() ? `?${query}` : ""}`;
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to fetch schools: ${res.status}`);
    }
    return (await res.json()) as School[];
  } catch (error) {
    console.error("Error fetching schools:", error);
    return [];
  }
}

export async function getGames(
  school: string,
  season: number,
  limit = 20,
  offset = 0
): Promise<PaginatedGames> {
  try {
    const params = new URLSearchParams({
      school,
      season: String(season),
      limit: String(limit),
      offset: String(offset),
    });
    const res = await fetch(`${API_BASE_URL}/api/games?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch games: ${res.status}`);
    }
    return (await res.json()) as PaginatedGames;
  } catch (error) {
    console.error("Error fetching games:", error);
    return { items: [], total: 0, limit, offset };
  }
}

export async function getGameDetail(
  gameId: number
): Promise<GameDetail | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/games/${gameId}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch game detail: ${res.status}`);
    }
    return (await res.json()) as GameDetail;
  } catch (error) {
    console.error("Error fetching game detail:", error);
    return null;
  }
}

export async function getGamesBySchoolId(
  schoolId: number,
  season?: number,
  limit = 100,
  offset = 0
): Promise<PaginatedGames> {
  try {
    const params = new URLSearchParams({
      school_id: String(schoolId),
      limit: String(limit),
      offset: String(offset),
    });
    if (season != null) {
      params.set("season", String(season));
    }
    const res = await fetch(`${API_BASE_URL}/api/games?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch games by school ID: ${res.status}`);
    }
    return (await res.json()) as PaginatedGames;
  } catch (error) {
    console.error("Error fetching games by school ID:", error);
    return { items: [], total: 0, limit, offset };
  }
}

export async function getTeamStats(
  school: string,
  season: number
): Promise<TeamStatsAggregation[]> {
  try {
    const params = new URLSearchParams({
      school,
      season: String(season),
    });
    const res = await fetch(`${API_BASE_URL}/api/stats/team?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch team stats: ${res.status}`);
    }
    return (await res.json()) as TeamStatsAggregation[];
  } catch (error) {
    console.error("Error fetching team stats:", error);
    return [];
  }
}

export async function getAllSeasonTeamStats(
  school: string
): Promise<TeamStatsAggregation[]> {
  try {
    const params = new URLSearchParams({ school });
    const res = await fetch(`${API_BASE_URL}/api/stats/team?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch all-season team stats: ${res.status}`);
    }
    return (await res.json()) as TeamStatsAggregation[];
  } catch (error) {
    console.error("Error fetching all-season team stats:", error);
    return [];
  }
}

export async function getPlayerLeaderboard(
  school: string,
  season: number,
  sortBy = "goals",
  limit = 20,
  offset = 0
): Promise<PaginatedPlayers> {
  try {
    const params = new URLSearchParams({
      season: String(season),
      sort: sortBy,
      limit: String(limit),
      offset: String(offset),
    });
    if (school) params.set("school", school);
    const res = await fetch(`${API_BASE_URL}/api/stats/players?${params}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch player leaderboard: ${res.status}`);
    }
    return (await res.json()) as PaginatedPlayers;
  } catch (error) {
    console.error("Error fetching player leaderboard:", error);
    return { items: [], total: 0, limit, offset };
  }
}

export interface ConferenceAverages {
  conference: string;
  gender: string;
  season: number;
  schools_count: number;
  avg_goals_per_game: number;
  avg_shot_conversion: number;
  avg_clean_sheet_pct: number;
  avg_shots_per_game: number;
  avg_sog_per_game: number;
}

export async function getConferenceAverages(
  abbr: string,
  season: number,
  gender: string = "men"
): Promise<ConferenceAverages | null> {
  try {
    const params = new URLSearchParams({ season: String(season), gender });
    const res = await fetch(`${API_BASE_URL}/api/conferences/${abbr}/averages?${params}`);
    if (!res.ok) return null;
    return (await res.json()) as ConferenceAverages;
  } catch {
    return null;
  }
}

export async function getConferenceStandings(
  abbr: string,
  season: number,
  gender: string = "men"
): Promise<ConferenceStanding[]> {
  try {
    const params = new URLSearchParams({ season: String(season), gender });
    const res = await fetch(`${API_BASE_URL}/api/conferences/${abbr}/standings?${params}`);
    if (!res.ok) throw new Error(`Failed to fetch standings: ${res.status}`);
    return (await res.json()) as ConferenceStanding[];
  } catch (error) {
    console.error("Error fetching conference standings:", error);
    return [];
  }
}

// --- Team Profile ---

export interface TeamProfileGameResult {
  game_id: number;
  date: string | null;
  opponent: string;
  home_away: string;
  home_score: number;
  away_score: number;
  goals_for: number;
  goals_against: number;
  result: string;
}

export interface TeamProfileTopScorer {
  player_name: string;
  goals: number;
  assists: number;
  games_played: number;
  goals_per_game: number;
}

export interface TeamProfileKPIs {
  goals_per_game: number;
  goals_per_game_delta: number;
  shot_conversion: number;
  shot_conversion_delta: number;
  goals_against_per_game: number;
  goals_against_per_game_delta: number;
  clean_sheets: number;
  conf_avg_goals_per_game: number;
  conf_avg_shot_conversion: number;
  conf_avg_goals_against_per_game: number;
}

export interface TeamProfileSeason {
  year: number;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  goals_for: number;
  goals_against: number;
  goal_diff: number;
  points: number;
  ppg: number;
  form: FormResult[];
  conf_rank: number;
}

export interface TeamProfile {
  abbreviation: string;
  name: string;
  mascot: string;
  gender: string;
  conference: string;
  season: TeamProfileSeason;
  kpis: TeamProfileKPIs;
  results_by_game: TeamProfileGameResult[];
  top_scorers: TeamProfileTopScorer[];
  available_seasons: number[];
}

export async function getTeamProfile(
  abbr: string,
  season?: number
): Promise<TeamProfile | null> {
  try {
    const params = new URLSearchParams();
    if (season != null) params.set("season", String(season));
    const qs = params.toString();
    const res = await fetch(
      `${API_BASE_URL}/api/teams/${abbr}/profile${qs ? `?${qs}` : ""}`
    );
    if (!res.ok) return null;
    return (await res.json()) as TeamProfile;
  } catch {
    return null;
  }
}

// --- Player Profile ---

export interface PlayerProfileCareer {
  seasons: number;
  games_played: number;
  goals: number;
  assists: number;
  shots: number;
  shots_on_goal: number;
}

export interface PlayerProfileSeason {
  season_year: number;
  games_played: number;
  goals: number;
  assists: number;
  shots: number;
  shots_on_goal: number;
  goals_per_90: number;
  shot_conversion: number;
  sog_accuracy: number;
}

export interface PlayerProfileGameLog {
  game_id: number;
  date: string | null;
  opponent: string;
  home_away: string;
  result: string;
  score: string;
  goals: number;
  assists: number;
  shots: number;
  shots_on_goal: number;
  minutes: number;
  is_starter: boolean;
}

export interface PlayerProfileConfAverages {
  season_year: number;
  goals_per_game: number;
  shot_conversion: number;
  sog_accuracy: number;
  assists_per_game: number;
  shots_per_game: number;
}

export interface PlayerProfileRadar {
  goals_pct: number;
  assists_pct: number;
  shots_pct: number;
  sog_pct: number;
  shot_conversion_pct: number;
}

export interface PlayerProfile {
  player_name: string;
  school_abbreviation: string;
  school_name: string;
  gender: string;
  career: PlayerProfileCareer;
  seasons: PlayerProfileSeason[];
  game_log: PlayerProfileGameLog[];
  conf_averages: PlayerProfileConfAverages | null;
  radar: PlayerProfileRadar | null;
}

export async function getPlayerProfile(
  school: string,
  name: string,
  season?: number
): Promise<PlayerProfile | null> {
  try {
    const params = new URLSearchParams({ school, name });
    if (season != null) params.set("season", String(season));
    const res = await fetch(`${API_BASE_URL}/api/players/profile?${params}`);
    if (!res.ok) return null;
    return (await res.json()) as PlayerProfile;
  } catch {
    return null;
  }
}
