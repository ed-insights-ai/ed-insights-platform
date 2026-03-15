import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type LucideIcon } from "lucide-react";

interface ValueCardProps {
  icon: LucideIcon;
  title: string;
  stat: string;
  description: string;
  className?: string;
}

export function ValueCard({
  icon: Icon,
  title,
  stat,
  description,
  className,
}: ValueCardProps) {
  return (
    <Card
      className={cn(
        "text-center overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 dark:bg-gray-800 dark:border-gray-700",
        className
      )}
    >
      <div className="h-1 bg-gradient-to-r from-secondary via-accent to-primary" />
      <CardHeader className="pb-2">
        <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-secondary/10 dark:bg-secondary/20">
          <Icon className="h-7 w-7 text-secondary" />
        </div>
        <CardTitle className="text-lg dark:text-white">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold text-accent mb-2">{stat}</p>
        <p className="text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}
