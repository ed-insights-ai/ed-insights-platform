"use client";

import { useRouter } from "next/navigation";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { LogOut } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

interface DashboardTopbarProps {
  userEmail: string;
  pageTitle: string;
}

export function DashboardTopbar({ userEmail, pageTitle }: DashboardTopbarProps) {
  const router = useRouter();
  const supabase = createClient();

  const initials = userEmail
    .split("@")[0]
    .slice(0, 2)
    .toUpperCase();

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <header className="flex h-14 items-center justify-between border-b bg-white px-6">
      <h1 className="text-lg font-semibold text-primary-900">{pageTitle}</h1>

      <DropdownMenu>
        <DropdownMenuTrigger className="flex items-center gap-2 rounded-md px-2 py-1 hover:bg-muted transition-colors">
          <span className="hidden text-sm text-muted-foreground sm:inline">
            {userEmail}
          </span>
          <Avatar className="h-8 w-8">
            <AvatarFallback className="bg-primary-100 text-primary-900 text-xs">
              {initials}
            </AvatarFallback>
          </Avatar>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={handleSignOut}>
            <LogOut className="mr-2 h-4 w-4" />
            Sign Out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
