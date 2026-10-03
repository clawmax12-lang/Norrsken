import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Preflight — Dashboard",
  description: "Launch videos that are tested before anyone sees them.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
