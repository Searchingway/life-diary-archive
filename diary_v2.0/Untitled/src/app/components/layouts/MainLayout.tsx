import { Outlet } from "react-router";
import { Sidebar } from "./Sidebar";

export function MainLayout() {
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      <Sidebar />
      <main id="main-content" className="min-w-0 flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
