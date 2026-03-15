import { UserCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function PlayersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Players</h2>
        <p className="text-muted-foreground">
          Individual athlete profiles and statistics
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col items-center py-12">
          <UserCircle className="h-12 w-12 text-muted-foreground mb-4" />
          <CardTitle>Coming Soon</CardTitle>
        </CardHeader>
        <CardContent className="text-center pb-12">
          <p className="text-muted-foreground">
            Player profiles with individual performance metrics, eligibility
            tracking, and career progression analytics are on the way.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
