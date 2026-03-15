import { Settings } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-primary-900">Settings</h2>
        <p className="text-muted-foreground">
          Configure your dashboard preferences
        </p>
      </div>

      <Card>
        <CardHeader className="flex flex-col items-center py-12">
          <Settings className="h-12 w-12 text-muted-foreground mb-4" />
          <CardTitle>Coming Soon</CardTitle>
        </CardHeader>
        <CardContent className="text-center pb-12">
          <p className="text-muted-foreground">
            Dashboard settings and customization options are being developed.
            Check back soon for theme preferences, notification controls, and
            account configuration.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
