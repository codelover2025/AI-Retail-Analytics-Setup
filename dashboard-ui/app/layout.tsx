import type { Metadata } from "next";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orzen Vision — Enterprise Analytics",
  description: "Enterprise retail AI analytics — multi-store, realtime, reports",
  icons: {
    icon: "/branding/orzen-icon.png",
    apple: "/branding/orzen-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased" suppressHydrationWarning>
        <DashboardLayout>{children}</DashboardLayout>
      </body>
    </html>
  );
}
