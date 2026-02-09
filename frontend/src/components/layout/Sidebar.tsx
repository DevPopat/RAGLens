import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  MessageSquare,
  ClipboardCheck,
  FileText,
  Target,
} from 'lucide-react';

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/chat', icon: MessageSquare, label: 'Chat' },
  { to: '/evaluations', icon: ClipboardCheck, label: 'Evaluations' },
  { to: '/golden-sets', icon: FileText, label: 'Golden Sets' },
];

export default function Sidebar() {
  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <Target className="w-8 h-8 text-primary-600" />
          <span className="text-xl font-bold text-gray-900">RAGLens</span>
        </div>
        <p className="text-xs text-gray-500 mt-1">RAG Evaluation & Diagnostics</p>
      </div>
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-2.5 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`
                }
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}
