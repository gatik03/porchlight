import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Porchlight",
  description: "Smart doorbell visual chime and caretaking",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
