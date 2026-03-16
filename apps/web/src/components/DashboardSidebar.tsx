"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Calendar,
  Users,
  BarChart3,
  Settings,
  ChevronLeft,
  ChevronRight,
  Trophy,
  Building2,
  UserCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { GenderSwitch } from "@/components/GenderSwitch";
import { useState } from "react";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
}

const myTeamItems: NavItem[] = [
  { label: "War Room", href: "/dashboard", icon: LayoutDashboard },
  { label: "Schedule", href: "/dashboard/games", icon: Calendar },
  { label: "Roster", href: "/dashboard/players", icon: Users },
  { label: "Analytics", href: "/dashboard/analytics", icon: BarChart3 },
];

const exploreItems: NavItem[] = [
  { label: "Conference", href: "/conference/gac", icon: Trophy },
  { label: "Teams", href: "/explore/teams", icon: Building2 },
  { label: "Players", href: "/explore/players", icon: UserCircle },
];

const settingsItem: NavItem = {
  label: "Settings",
  href: "/dashboard/settings",
  icon: Settings,
};

function NavLink({
  item,
  pathname,
  collapsed,
}: {
  item: NavItem;
  pathname: string;
  collapsed: boolean;
}) {
  const isActive =
    item.href === "/dashboard"
      ? pathname === "/dashboard"
      : pathname.startsWith(item.href);

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "border-l-4 border-data-primary bg-surface-muted text-slate-900 font-semibold pl-2"
          : "text-slate-600 hover:bg-surface-muted hover:text-slate-900",
        collapsed && "justify-center px-2 border-l-0 pl-2"
      )}
      title={collapsed ? item.label : undefined}
    >
      <item.icon className="h-5 w-5 shrink-0" />
      {!collapsed && <span>{item.label}</span>}
    </Link>
  );
}

export function DashboardSidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col border-r bg-white transition-all duration-200",
        collapsed ? "w-16" : "w-60"
      )}
    >
      {/* Gender Switch */}
      <div className="flex items-center justify-between border-b px-3 py-4">
        {!collapsed && <GenderSwitch />}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 shrink-0"
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </Button>
      </div>

      <nav className="flex-1 px-2 py-3">
        {/* MY TEAM section */}
        {!collapsed && (
          <span className="stat-label px-3 mb-2 block">My Team</span>
        )}
        <div className="space-y-1 mb-4">
          {myTeamItems.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              pathname={pathname}
              collapsed={collapsed}
            />
          ))}
        </div>

        {/* EXPLORE section */}
        {!collapsed && (
          <span className="stat-label px-3 mb-2 block">Explore</span>
        )}
        <div className="space-y-1 mb-4">
          {exploreItems.map((item) => (
            <NavLink
              key={item.href}
              item={item}
              pathname={pathname}
              collapsed={collapsed}
            />
          ))}
        </div>

        {/* Divider */}
        <div className="border-t my-2" />

        {/* SETTINGS */}
        <div className="space-y-1">
          <NavLink
            item={settingsItem}
            pathname={pathname}
            collapsed={collapsed}
          />
        </div>
      </nav>
    </aside>
  );
}
