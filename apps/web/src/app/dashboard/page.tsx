import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { createClient } from "@/lib/supabase/server";
import { DashboardStats } from "@/components/DashboardStats";

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Overview</h2>
        <p className="text-muted-foreground">
          Welcome back, {user?.email ?? "User"}
        </p>
      </div>

      <DashboardStats />

      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Select a school and season above to explore team performance, player
            statistics, and game-by-game analytics. Use the navigation sidebar
            to dive deeper into teams, players, and advanced analytics.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
