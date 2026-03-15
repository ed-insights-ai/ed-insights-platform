import { Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function TeamsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Teams</h2>
        <p className="text-muted-foreground">
          Manage and analyze your athletic teams
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col items-center py-12">
          <Users className="h-12 w-12 text-muted-foreground mb-4" />
          <CardTitle>Coming Soon</CardTitle>
        </CardHeader>
        <CardContent className="text-center pb-12">
          <p className="text-muted-foreground">
            Team management and performance analytics are being developed. Check
            back soon for roster views, win/loss records, and comparative team
            analysis.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
