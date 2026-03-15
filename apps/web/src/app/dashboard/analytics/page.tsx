import { BarChart3 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Analytics</h2>
        <p className="text-muted-foreground">
          In-depth program analytics and reporting
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col items-center py-12">
          <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
          <CardTitle>Coming Soon</CardTitle>
        </CardHeader>
        <CardContent className="text-center pb-12">
          <p className="text-muted-foreground">
            Advanced analytics dashboards with trend analysis, predictive
            insights, and custom reporting tools will be available here.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
