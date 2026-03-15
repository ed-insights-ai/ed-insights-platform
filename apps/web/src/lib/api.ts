export interface School {
  id: string;
  name: string;
  abbreviation: string;
  conference: string;
  mascot: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getSchools(): Promise<School[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/schools`);
    if (!res.ok) {
      throw new Error(`Failed to fetch schools: ${res.status}`);
    }
    return (await res.json()) as School[];
  } catch (error) {
    console.error("Error fetching schools:", error);
    return [];
  }
}
