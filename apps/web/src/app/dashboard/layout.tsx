import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { DashboardSidebar } from "@/components/DashboardSidebar";
import { DashboardTopbar } from "@/components/DashboardTopbar";
import { GenderProvider } from "@/context/GenderContext";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <GenderProvider>
      <div className="flex h-[calc(100vh-4rem)] overflow-hidden">
        <DashboardSidebar />
        <div className="flex flex-1 flex-col overflow-hidden">
          <DashboardTopbar
            userEmail={user.email ?? "User"}
            pageTitle="Dashboard"
          />
          <main className="flex-1 overflow-y-auto bg-app-bg p-6">
            {children}
          </main>
        </div>
      </div>
    </GenderProvider>
  );
}
