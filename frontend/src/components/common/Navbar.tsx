import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Sun,
  Menu,
  X,
  ArrowRight,
  ShieldCheck,
  User as UserIcon,
  LogOut,
  LayoutDashboard,
  Settings,
  ChevronDown
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Navbar: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userDropdownOpen, setUserDropdownOpen] = useState(false);
  const location = useLocation();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'Solar Assessment', path: '/assessment' },
    { name: 'Generation AI', path: '/generation' },
    { name: 'Dust Detection', path: '/dust' },
    { name: 'Battery Backup', path: '/battery' },
    { name: 'System Status', path: '/status' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = async () => {
    setUserDropdownOpen(false);
    setMobileMenuOpen(false);
    await logout();
  };

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-3 group">
            <div className="w-10 h-10 rounded-xl bg-forest-900 flex items-center justify-center text-solar-400 shadow-md group-hover:bg-forest-800 transition-colors">
              <Sun className="w-6 h-6 animate-[spin_12s_linear_infinite]" />
            </div>
            <div className="flex flex-col">
              <span className="font-extrabold text-xl tracking-tight text-forest-950 font-sans">
                Roofwise<span className="text-solar-500">BD</span>
              </span>
              <span className="text-[10px] uppercase font-bold tracking-widest text-forest-700">
                Bangladesh Solar AI
              </span>
            </div>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive(link.path)
                    ? 'bg-forest-50 text-forest-900 font-semibold border-b-2 border-forest-700'
                    : 'text-slate-600 hover:text-forest-900 hover:bg-slate-100'
                }`}
              >
                {link.name}
              </Link>
            ))}
          </nav>

          {/* User Auth Section & CTA */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {isAuthenticated && user ? (
              <div className="relative">
                <button
                  onClick={() => setUserDropdownOpen(!userDropdownOpen)}
                  className="flex items-center space-x-2 px-3 py-1.5 rounded-xl border border-slate-200 hover:bg-slate-50 transition-colors cursor-pointer text-sm font-medium text-slate-800"
                >
                  <div className="w-7 h-7 rounded-lg bg-forest-900 text-solar-400 flex items-center justify-center font-bold text-xs">
                    {user.full_name.charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden sm:inline max-w-[120px] truncate">{user.full_name}</span>
                  <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                </button>

                {userDropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-fade-in text-sm">
                    <div className="px-4 py-2 border-b border-slate-100">
                      <p className="font-bold text-forest-950 truncate">{user.full_name}</p>
                      <p className="text-xs text-slate-400 truncate">{user.email}</p>
                      {isAdmin && (
                        <span className="inline-flex items-center mt-1 px-2 py-0.5 rounded text-[10px] font-extrabold uppercase tracking-wider bg-amber-100 text-amber-800">
                          <ShieldCheck className="w-3 h-3 mr-1" />
                          Admin
                        </span>
                      )}
                    </div>

                    <Link
                      to="/dashboard"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center px-4 py-2 text-slate-700 hover:bg-slate-50 hover:text-forest-900 transition-colors"
                    >
                      <LayoutDashboard className="w-4 h-4 mr-2.5 text-slate-400" />
                      <span>My Dashboard</span>
                    </Link>

                    <Link
                      to="/profile"
                      onClick={() => setUserDropdownOpen(false)}
                      className="flex items-center px-4 py-2 text-slate-700 hover:bg-slate-50 hover:text-forest-900 transition-colors"
                    >
                      <Settings className="w-4 h-4 mr-2.5 text-slate-400" />
                      <span>Account Settings</span>
                    </Link>

                    {isAdmin && (
                      <Link
                        to="/admin/dashboard"
                        onClick={() => setUserDropdownOpen(false)}
                        className="flex items-center px-4 py-2 text-amber-700 hover:bg-amber-50 font-semibold transition-colors"
                      >
                        <ShieldCheck className="w-4 h-4 mr-2.5 text-amber-500" />
                        <span>Admin Console</span>
                      </Link>
                    )}

                    <div className="border-t border-slate-100 my-1"></div>

                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center px-4 py-2 text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer text-left"
                    >
                      <LogOut className="w-4 h-4 mr-2.5" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-1.5 sm:space-x-2">
                <Link
                  to="/login"
                  className="px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold text-slate-700 hover:text-forest-950 hover:bg-slate-100 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="hidden sm:inline-flex px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold bg-forest-50 text-forest-900 hover:bg-forest-100 border border-forest-200 transition-colors"
                >
                  Register
                </Link>
              </div>
            )}

            <Link
              to="/assessment"
              className="hidden lg:inline-flex items-center px-4 py-2 rounded-xl text-sm font-semibold bg-forest-900 text-white hover:bg-forest-800 transition-all shadow-sm hover:shadow"
            >
              <span>Calculate</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </Link>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 px-4 pt-2 pb-4 space-y-1 shadow-lg">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2.5 rounded-lg text-base font-medium ${
                isActive(link.path)
                  ? 'bg-forest-50 text-forest-900 font-semibold'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              {link.name}
            </Link>
          ))}

          <div className="pt-3 border-t border-slate-100 space-y-2">
            {isAuthenticated && user ? (
              <>
                <Link
                  to="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center px-3 py-2 text-sm font-semibold text-forest-900"
                >
                  <LayoutDashboard className="w-4 h-4 mr-2" />
                  <span>My Dashboard</span>
                </Link>
                {isAdmin && (
                  <Link
                    to="/admin/dashboard"
                    onClick={() => setMobileMenuOpen(false)}
                    className="flex items-center px-3 py-2 text-sm font-semibold text-amber-700"
                  >
                    <ShieldCheck className="w-4 h-4 mr-2" />
                    <span>Admin Portal</span>
                  </Link>
                )}
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center px-3 py-2 text-sm font-semibold text-rose-600 text-left"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  <span>Sign Out</span>
                </button>
              </>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center py-2 px-3 rounded-lg text-sm font-bold border border-slate-200 text-slate-800"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex items-center justify-center py-2 px-3 rounded-lg text-sm font-bold bg-forest-50 text-forest-900 border border-forest-200"
                >
                  Register
                </Link>
              </div>
            )}
            <Link
              to="/assessment"
              onClick={() => setMobileMenuOpen(false)}
              className="w-full flex items-center justify-center px-4 py-2.5 rounded-xl text-base font-semibold bg-forest-900 text-white hover:bg-forest-800"
            >
              <span>Start Solar Assessment</span>
              <ArrowRight className="w-4 h-4 ml-2" />
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
