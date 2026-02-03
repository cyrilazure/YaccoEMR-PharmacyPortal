import { useState } from 'react';
import { Outlet, NavLink, useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn, getRoleDisplayName } from '@/lib/utils';
import {
  Activity, LayoutDashboard, Users, FileText, Calendar,
  ClipboardList, Settings, LogOut, ChevronLeft, ChevronRight,
  Pill, AlertTriangle, Stethoscope, BarChart3, Heart, UserCog, Shield, Video,
  Building2, Globe, CreditCard, Share2
} from 'lucide-react';

const navItems = [
  // Super Admin
  { to: '/platform-admin', icon: Globe, label: 'Platform Admin', roles: ['super_admin'] },
  // Hospital Admin
  { to: '/hospital-settings', icon: Building2, label: 'Hospital Settings', roles: ['hospital_admin'] },
  // Role-specific dashboards
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', roles: ['physician', 'hospital_admin'] },
  { to: '/nurse-station', icon: Heart, label: 'Nurse Station', roles: ['nurse'] },
  { to: '/scheduling', icon: Calendar, label: 'Scheduling', roles: ['scheduler'] },
  { to: '/admin', icon: Shield, label: 'Admin Center', roles: ['admin'] },
  // Shared pages
  { to: '/patients', icon: Users, label: 'Patients', roles: ['physician', 'nurse', 'scheduler', 'admin', 'hospital_admin', 'super_admin'] },
  { to: '/appointments', icon: Calendar, label: 'Appointments', roles: ['physician', 'nurse', 'scheduler', 'admin', 'hospital_admin'] },
  { to: '/orders', icon: ClipboardList, label: 'Orders', roles: ['physician', 'nurse', 'admin', 'hospital_admin'] },
  { to: '/telehealth', icon: Video, label: 'Telehealth', roles: ['physician', 'nurse', 'admin', 'hospital_admin'] },
  { to: '/records-sharing', icon: Share2, label: 'Records Sharing', roles: ['physician', 'hospital_admin'] },
  { to: '/billing', icon: CreditCard, label: 'Billing', roles: ['physician', 'admin', 'hospital_admin'] },
  { to: '/analytics', icon: BarChart3, label: 'Analytics', roles: ['physician', 'admin', 'hospital_admin', 'super_admin'] },
];

export default function Layout() {
  const { user, logout, loading } = useAuth();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <Activity className="w-12 h-12 text-sky-600 animate-pulse" />
          <p className="text-slate-600">Loading Yacco EMR...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userNavItems = navItems.filter(item => item.roles.includes(user.role));

  return (
    <div className="min-h-screen bg-slate-50 flex" data-testid="main-layout">
      {/* Sidebar */}
      <aside 
        className={cn(
          "fixed top-0 left-0 h-full bg-slate-900 text-white flex flex-col transition-all duration-300 z-40",
          collapsed ? "w-[72px]" : "w-64"
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center px-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-sky-500 flex items-center justify-center flex-shrink-0">
              <Activity className="w-5 h-5" />
            </div>
            {!collapsed && (
              <span className="text-xl font-bold tracking-tight" style={{ fontFamily: 'Manrope' }}>
                Yacco EMR
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="space-y-1 px-3">
            {userNavItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                data-testid={`nav-${item.label.toLowerCase()}`}
                className={({ isActive }) => cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                  isActive 
                    ? "bg-sky-500 text-white" 
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                )}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                {!collapsed && <span className="font-medium">{item.label}</span>}
              </NavLink>
            ))}
          </nav>
        </ScrollArea>

        {/* Collapse Toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-20 w-6 h-6 bg-slate-700 rounded-full flex items-center justify-center hover:bg-slate-600 transition-colors"
          data-testid="sidebar-toggle"
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>

        {/* User */}
        <div className="p-4 border-t border-slate-800">
          <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
            <Avatar className="h-9 w-9 border border-slate-700">
              <AvatarFallback className="bg-sky-600 text-white text-sm">
                {user.first_name?.[0]}{user.last_name?.[0]}
              </AvatarFallback>
            </Avatar>
            {!collapsed && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user.first_name} {user.last_name}</p>
                <p className="text-xs text-slate-400 truncate">{getRoleDisplayName(user.role)}</p>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className={cn("flex-1 transition-all duration-300", collapsed ? "ml-[72px]" : "ml-64")}>
        {/* Top Header */}
        <header className="h-16 glass-header sticky top-0 z-30 flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'Manrope' }}>
              Clinical Workspace
            </h1>
          </div>
          
          <div className="flex items-center gap-4">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2" data-testid="user-menu-trigger">
                  <Avatar className="h-8 w-8">
                    <AvatarFallback className="bg-sky-100 text-sky-700 text-sm">
                      {user.first_name?.[0]}{user.last_name?.[0]}
                    </AvatarFallback>
                  </Avatar>
                  <span className="text-sm font-medium text-slate-700 hidden sm:inline">
                    {user.first_name} {user.last_name}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div>
                    <p className="font-medium">{user.first_name} {user.last_name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem className="cursor-pointer">
                  <Settings className="w-4 h-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600" data-testid="logout-btn">
                  <LogOut className="w-4 h-4 mr-2" />
                  Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
