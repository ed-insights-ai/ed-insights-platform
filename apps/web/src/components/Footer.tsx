import Link from "next/link";
import { GraduationCap } from "lucide-react";

export function Footer() {
  return (
    <footer className="border-t bg-primary-900 dark:bg-gray-950 text-white">
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex flex-col space-y-2">
            <div className="flex items-center space-x-2">
              <GraduationCap className="h-5 w-5" />
              <span className="text-lg font-bold">EDInsights</span>
            </div>
            <p className="text-sm text-gray-300">
              Data-driven insights for higher education athletics.
            </p>
          </div>

          <div className="flex flex-col space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider">
              Quick Links
            </h3>
            <Link
              href="/about"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              About
            </Link>
            <Link
              href="/dashboard"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Dashboard
            </Link>
          </div>

          <div className="flex flex-col space-y-2">
            <h3 className="text-sm font-semibold uppercase tracking-wider">
              Account
            </h3>
            <Link
              href="/login"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="text-sm text-gray-300 hover:text-white transition-colors"
            >
              Sign Up
            </Link>
          </div>
        </div>

        <div className="mt-8 border-t border-gray-700 pt-4 text-center text-sm text-gray-400">
          &copy; {new Date().getFullYear()} EDInsights.AI. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
