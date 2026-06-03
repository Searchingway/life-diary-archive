import { NavLink } from "react-router";
import { cn } from "../ui/utils";
import {
  LayoutDashboard,
  BookOpen,
  MapPin,
  Lightbulb,
  Target,
  Brain,
  ClipboardList,
  Scale,
  FileText,
  Eye,
  AlertTriangle,
  User,
  Film,
  Database,
  Settings,
} from "lucide-react";

interface NavItem {
  label: string;
  path: string;
  icon: React.ComponentType<{ className?: string }>;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

const navGroups: NavGroup[] = [
  {
    title: "总览",
    items: [
      { label: "工作台", path: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "日常记录",
    items: [
      { label: "日记", path: "/diary", icon: BookOpen },
      { label: "足迹", path: "/footprints", icon: MapPin },
      { label: "自我观察", path: "/self-observation", icon: Eye },
    ],
  },
  {
    title: "思考与反思",
    items: [
      { label: "轻思考", path: "/light-thought", icon: Lightbulb },
      { label: "轻资源", path: "/light-resource", icon: Scale },
      { label: "教训与反思", path: "/lessons-reflection", icon: AlertTriangle },
      { label: "自我分析", path: "/self-analysis", icon: User },
    ],
  },
  {
    title: "计划与执行",
    items: [
      { label: "轻计划", path: "/light-plan", icon: Target },
      { label: "行动计划", path: "/action-plan", icon: Brain },
    ],
  },
  {
    title: "信息与作品",
    items: [
      { label: "接单备忘", path: "/order-memo", icon: ClipboardList },
      { label: "信息备忘", path: "/info-memo", icon: FileText },
      { label: "作品感悟", path: "/works-reflection", icon: Film },
    ],
  },
  {
    title: "系统",
    items: [
      { label: "数据管理", path: "/data-management", icon: Database },
      { label: "AI 设置", path: "/ai-settings", icon: Settings },
    ],
  },
];

export function Sidebar() {
  return (
    <aside className="w-64 border-r bg-card flex flex-col">
      <div className="p-6 border-b">
        <h1 className="text-xl font-semibold">人生档案 Diary</h1>
        <p className="text-xs text-muted-foreground mt-1">本地优先个人档案</p>
      </div>

      <nav className="flex-1 overflow-y-auto p-4 space-y-6">
        {navGroups.map((group) => (
          <div key={group.title}>
            <h2 className="text-xs font-semibold text-muted-foreground uppercase mb-2 px-3">
              {group.title}
            </h2>
            <div className="space-y-1">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
                      isActive
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-accent text-muted-foreground hover:text-foreground"
                    )
                  }
                >
                  <item.icon className="size-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-4 border-t text-xs text-muted-foreground">
        <div className="flex items-center justify-between">
          <span>本地数据</span>
          <span className="text-green-600">正常</span>
        </div>
      </div>
    </aside>
  );
}
