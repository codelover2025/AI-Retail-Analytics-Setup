import type { Metadata } from "next";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import "./globals.css";

export const metadata: Metadata = {
  title: "Orzen Vision — Store Analytics",
  description: "Retail AI analytics dashboard",
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
