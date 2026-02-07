import React, { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/lib/auth';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn, getRoleDisplayName } from '@/lib/utils';
import {
  Activity, LayoutDashboard, Users, FileText, Calendar,
  ClipboardList, Settings, LogOut, ChevronLeft, ChevronRight,
  Pill, AlertTriangle, Stethoscope, BarChart3, Heart, UserCog, Shield, Video,
  Building2, Globe, CreditCard, Share2, ShieldCheck, FileSearch, Layers,
  Menu, X, Bell, Search, Sun, Moon, HelpCircle, Bed, Scan, Ambulance, Package
} from 'lucide-react';

const navItems = [
  // ========== PLATFORM LEVEL (Super Admin Only) ==========
  { 
    to: '/platform/super-admin', 
    icon: Globe, 
    label: 'Platform Admin', 
    roles: ['super_admin'],
    description: 'Manage hospitals and platform',
    color: 'text-purple-500'
  },
  
  // ========== HOSPITAL LEVEL ==========
  { 
    to: '/it-admin', 
    icon: UserCog, 
    label: 'IT Admin', 
    roles: ['hospital_it_admin'],
    description: 'Staff account management',
    color: 'text-indigo-500'
  },
  { 
    to: '/admin-dashboard', 
    icon: Building2, 
    label: 'Hospital Admin', 
    roles: ['hospital_admin'],
    description: 'Hospital administration',
    color: 'text-blue-500'
  },
  { 
    to: '/facility-admin', 
    icon: Layers, 
    label: 'Facility Admin', 
    roles: ['facility_admin'],
    description: 'Local facility management',
    color: 'text-cyan-500'
  },
  
  // ========== CLINICAL PORTALS ==========
  { 
    to: '/dashboard', 
    icon: LayoutDashboard, 
    label: 'Physician Portal', 
    roles: ['physician'],
    description: 'Clinical dashboard',
    color: 'text-emerald-500'
  },
  { 
    to: '/nurse-station', 
    icon: Heart, 
    label: 'Nurse Station', 
    roles: ['nurse'],
    description: 'Nursing care portal',
    color: 'text-rose-500'
  },
  { 
    to: '/nursing-supervisor', 
    icon: Heart, 
    label: 'Nursing Supervisor', 
    roles: ['nursing_supervisor', 'floor_supervisor'],
    description: 'Nursing supervision',
    color: 'text-rose-600'
  },
  
  // ========== OPERATIONAL PORTALS ==========
  { 
    to: '/scheduling', 
    icon: Calendar, 
    label: 'Scheduler', 
    roles: ['scheduler'],
    description: 'Appointment scheduling',
    color: 'text-amber-500'
  },
  { 
    to: '/billing', 
    icon: CreditCard, 
    label: 'Billing Portal', 
    roles: ['biller'],
    description: 'Financial administration',
    color: 'text-green-500'
  },
  { 
    to: '/pharmacy', 
    icon: Pill, 
    label: 'Pharmacy Portal', 
    roles: ['pharmacist', 'pharmacy_tech', 'hospital_admin'],
    description: 'Dispensing, inventory & NHIS claims',
    color: 'text-emerald-500'
  },
  { 
    to: '/radiology', 
    icon: Scan, 
    label: 'Radiology', 
    roles: ['radiology_staff', 'radiologist', 'hospital_admin'],
    description: 'Imaging orders & reports',
    color: 'text-purple-500'
  },
  { 
    to: '/bed-management', 
    icon: Bed, 
    label: 'Bed Management', 
    roles: ['bed_manager', 'nurse', 'nursing_supervisor', 'floor_supervisor', 'hospital_admin'],
    description: 'Ward census & admissions',
    color: 'text-sky-500'
  },
  { 
    to: '/department', 
    icon: Layers, 
    label: 'Department Portal', 
    roles: ['records_officer', 'department_staff'],
    description: 'Department operations',
    color: 'text-teal-500'
  },
  { 
    to: '/ambulance', 
    icon: Ambulance, 
    label: 'Ambulance', 
    roles: ['nurse', 'nursing_supervisor', 'floor_supervisor', 'hospital_admin'],
    description: 'Emergency transport',
    color: 'text-red-500'
  },
  
  // ========== SHARED CLINICAL PAGES (Based on Permissions) ==========
  { 
    to: '/patients', 
    icon: Users, 
    label: 'Patients', 
    roles: ['physician', 'nurse', 'scheduler', 'hospital_admin', 'records_officer'],
    color: 'text-sky-500'
  },
  { 
    to: '/appointments', 
    icon: Calendar, 
    label: 'Appointments', 
    roles: ['physician', 'nurse', 'scheduler', 'hospital_admin'],
    color: 'text-violet-500'
  },
  { 
    to: '/orders', 
    icon: ClipboardList, 
    label: 'Orders', 
    roles: ['physician', 'nurse', 'hospital_admin'],
    color: 'text-orange-500'
  },
  { 
    to: '/telehealth', 
    icon: Video, 
    label: 'Telehealth', 
    roles: ['physician', 'nurse', 'hospital_admin'],
    color: 'text-pink-500'
  },
  { 
    to: '/records-sharing', 
    icon: Share2, 
    label: 'Records Sharing', 
    roles: ['physician', 'hospital_admin'],
    color: 'text-lime-500'
  },
  { 
    to: '/analytics', 
    icon: BarChart3, 
    label: 'Analytics', 
    roles: ['physician', 'hospital_admin'],
    color: 'text-cyan-500'
  },
  
  // ========== AUDIT (Limited Access) ==========
  { 
    to: '/audit-logs', 
    icon: FileSearch, 
    label: 'Audit Logs', 
    roles: ['hospital_admin'],
    color: 'text-slate-500'
  },
];

// Loading skeleton component
function LoadingSkeleton() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-sky-50 to-slate-100">
      <div className="flex flex-col items-center gap-6">
        <div className="relative">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-sky-500 to-sky-600 flex items-center justify-center shadow-xl animate-pulse">
            <Activity className="w-10 h-10 text-white" />
          </div>
          <div className="absolute -bottom-1 -right-1 w-6 h-6 rounded-full bg-emerald-500 border-4 border-white animate-bounce" />
        </div>
        <div className="text-center space-y-2">
          <p className="text-xl font-semibold text-slate-700" style={{ fontFamily: 'Manrope' }}>
            Yacco EMR
          </p>
          <p className="text-slate-500 text-sm">Loading your workspace...</p>
        </div>
        <div className="flex gap-1">
          <div className="w-2 h-2 rounded-full bg-sky-500 animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-2 h-2 rounded-full bg-sky-500 animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-2 h-2 rounded-full bg-sky-500 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

export default function Layout() {
  const { user, logout, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [pageLoading, setPageLoading] = useState(false);

  // Handle route changes with loading state - using ref to track pathname
  const prevPathname = React.useRef(location.pathname);
  useEffect(() => {
    if (prevPathname.current !== location.pathname) {
      prevPathname.current = location.pathname;
      // Use timeout to avoid synchronous state updates
      const timer = setTimeout(() => {
        setPageLoading(true);
        setTimeout(() => setPageLoading(false), 300);
      }, 0);
      return () => clearTimeout(timer);
    }
  }, [location.pathname]);

  // Close mobile menu on route change - using callback ref
  const prevPathnameForMenu = React.useRef(location.pathname);
  useEffect(() => {
    if (prevPathnameForMenu.current !== location.pathname) {
      prevPathnameForMenu.current = location.pathname;
      // Delay to avoid synchronous setState in effect
      const timer = setTimeout(() => setMobileMenuOpen(false), 0);
      return () => clearTimeout(timer);
    }
  }, [location.pathname]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  if (loading) {
    return <LoadingSkeleton />;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const userNavItems = navItems.filter(item => item.roles.includes(user.role));

  // Get current page title
  const getCurrentPageTitle = () => {
    const currentItem = userNavItems.find(item => location.pathname.startsWith(item.to));
    return currentItem?.label || 'Clinical Workspace';
  };

  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50/30 to-slate-100" data-testid="main-layout">
        {/* Mobile Menu Overlay */}
        {mobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-black/50 z-40 lg:hidden backdrop-blur-sm transition-opacity duration-300"
            onClick={() => setMobileMenuOpen(false)}
          />
        )}

        {/* Sidebar */}
        <aside 
          className={cn(
            "fixed top-0 left-0 h-full bg-gradient-to-b from-slate-900 via-slate-900 to-slate-800 text-white flex flex-col transition-all duration-300 ease-in-out z-50",
            collapsed ? "w-[72px]" : "w-64",
            mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
          )}
        >
          {/* Logo */}
          <div className="h-16 flex items-center px-4 border-b border-slate-700/50">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-sky-400 to-sky-600 flex items-center justify-center flex-shrink-0 shadow-lg shadow-sky-500/30 transition-transform hover:scale-105">
                <Activity className="w-5 h-5" />
              </div>
              {!collapsed && (
                <div className="overflow-hidden">
                  <span className="text-xl font-bold tracking-tight whitespace-nowrap" style={{ fontFamily: 'Manrope' }}>
                    Yacco EMR
                  </span>
                  <p className="text-xs text-slate-400 -mt-0.5">Healthcare Platform</p>
                </div>
              )}
            </div>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="space-y-1 px-3">
              {userNavItems.map((item, index) => (
                <Tooltip key={item.to} delayDuration={collapsed ? 0 : 1000}>
                  <TooltipTrigger asChild>
                    <NavLink
                      to={item.to}
                      data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                      className={({ isActive }) => cn(
                        "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group",
                        isActive 
                          ? "bg-gradient-to-r from-sky-500 to-sky-600 text-white shadow-lg shadow-sky-500/25" 
                          : "text-slate-400 hover:text-white hover:bg-slate-800/70"
                      )}
                      style={{ animationDelay: `${index * 50}ms` }}
                    >
                      <item.icon className={cn(
                        "w-5 h-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-110",
                        !collapsed && item.color
                      )} />
                      {!collapsed && (
                        <span className="font-medium truncate">{item.label}</span>
                      )}
                    </NavLink>
                  </TooltipTrigger>
                  {collapsed && (
                    <TooltipContent side="right" className="bg-slate-800 text-white border-slate-700">
                      <p className="font-medium">{item.label}</p>
                      {item.description && (
                        <p className="text-xs text-slate-400">{item.description}</p>
                      )}
                    </TooltipContent>
                  )}
                </Tooltip>
              ))}
            </nav>
          </ScrollArea>

          {/* Collapse Toggle - Desktop only */}
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex absolute -right-3 top-20 w-6 h-6 bg-slate-700 rounded-full items-center justify-center hover:bg-sky-600 transition-all duration-200 shadow-lg hover:scale-110"
            data-testid="sidebar-toggle"
          >
            {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>

          {/* User Profile in Sidebar */}
          <div className="p-4 border-t border-slate-700/50">
            <div className={cn("flex items-center gap-3", collapsed && "justify-center")}>
              <Avatar className="h-10 w-10 border-2 border-sky-500/50 ring-2 ring-sky-500/20 transition-all hover:ring-sky-500/40">
                <AvatarFallback className="bg-gradient-to-br from-sky-500 to-sky-600 text-white text-sm font-semibold">
                  {user.first_name?.[0]}{user.last_name?.[0]}
                </AvatarFallback>
              </Avatar>
              {!collapsed && (
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{user.first_name} {user.last_name}</p>
                  <Badge variant="secondary" className="bg-slate-700/50 text-slate-300 text-xs mt-0.5">
                    {getRoleDisplayName(user.role)}
                  </Badge>
                </div>
              )}
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <div className={cn(
          "flex-1 transition-all duration-300 ease-in-out",
          collapsed ? "lg:ml-[72px]" : "lg:ml-64"
        )}>
          {/* Top Header */}
          <header className="h-16 glass-header sticky top-0 z-30 flex items-center justify-between px-4 lg:px-6">
            {/* Left side - Mobile menu + Page title */}
            <div className="flex items-center gap-4">
              {/* Mobile Menu Button */}
              <Button
                variant="ghost"
                size="icon"
                className="lg:hidden"
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </Button>
              
              <div className="flex items-center gap-3">
                <h1 className="text-lg font-semibold text-slate-900 hidden sm:block" style={{ fontFamily: 'Manrope' }}>
                  {getCurrentPageTitle()}
                </h1>
                {pageLoading && (
                  <div className="w-4 h-4 border-2 border-sky-500 border-t-transparent rounded-full animate-spin" />
                )}
              </div>
            </div>
            
            {/* Right side - Actions */}
            <div className="flex items-center gap-2 lg:gap-4">
              {/* Quick Actions - Hidden on mobile */}
              <div className="hidden md:flex items-center gap-2">
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="text-slate-600 hover:text-sky-600">
                      <Search className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Search</TooltipContent>
                </Tooltip>
                
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="text-slate-600 hover:text-sky-600 relative">
                      <Bell className="w-4 h-4" />
                      <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Notifications</TooltipContent>
                </Tooltip>
                
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button variant="ghost" size="icon" className="text-slate-600 hover:text-sky-600">
                      <HelpCircle className="w-4 h-4" />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Help & Support</TooltipContent>
                </Tooltip>
              </div>

              <div className="h-6 w-px bg-slate-200 hidden md:block" />
              
              {/* User Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center gap-2 px-2 lg:px-3 hover:bg-sky-50" data-testid="user-menu-trigger">
                    <Avatar className="h-8 w-8 border border-sky-200">
                      <AvatarFallback className="bg-gradient-to-br from-sky-100 to-sky-200 text-sky-700 text-sm font-semibold">
                        {user.first_name?.[0]}{user.last_name?.[0]}
                      </AvatarFallback>
                    </Avatar>
                    <div className="text-left hidden sm:block">
                      <span className="text-sm font-medium text-slate-700 block">
                        {user.first_name} {user.last_name}
                      </span>
                      <span className="text-xs text-slate-500">
                        {getRoleDisplayName(user.role)}
                      </span>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-400 rotate-90 hidden sm:block" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex items-center gap-3">
                      <Avatar className="h-10 w-10">
                        <AvatarFallback className="bg-gradient-to-br from-sky-100 to-sky-200 text-sky-700">
                          {user.first_name?.[0]}{user.last_name?.[0]}
                        </AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{user.first_name} {user.last_name}</p>
                        <p className="text-xs text-slate-500 truncate">{user.email}</p>
                      </div>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={() => navigate('/security')} className="cursor-pointer">
                    <ShieldCheck className="w-4 h-4 mr-2 text-slate-500" />
                    Security Settings
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer">
                    <Settings className="w-4 h-4 mr-2 text-slate-500" />
                    Preferences
                  </DropdownMenuItem>
                  <DropdownMenuItem className="cursor-pointer">
                    <HelpCircle className="w-4 h-4 mr-2 text-slate-500" />
                    Help & Support
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout} className="cursor-pointer text-red-600 focus:text-red-600 focus:bg-red-50" data-testid="logout-btn">
                    <LogOut className="w-4 h-4 mr-2" />
                    Sign Out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </header>

          {/* Page Content */}
          <main className={cn(
            "p-4 lg:p-6 transition-opacity duration-300",
            pageLoading ? "opacity-50" : "opacity-100"
          )}>
            <div className="animate-fade-in">
              <Outlet />
            </div>
          </main>

          {/* Footer */}
          <footer className="px-4 lg:px-6 py-4 border-t border-slate-200/50 bg-white/50">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-slate-500">
              <p>© 2026 Yacco EMR. All rights reserved.</p>
              <div className="flex items-center gap-4">
                <a href="#" className="hover:text-sky-600 transition-colors">Privacy Policy</a>
                <a href="#" className="hover:text-sky-600 transition-colors">Terms of Service</a>
                <a href="#" className="hover:text-sky-600 transition-colors">Support</a>
              </div>
            </div>
          </footer>
        </div>
      </div>
    </TooltipProvider>
  );
}
