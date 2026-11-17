import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { AppQueryProvider } from "@/components/query-provider";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "StegaShield — Academic Authenticated Steganography & Steganalysis Laboratory",
  description:
    "Production-grade platform for authenticated encrypted LSB steganography, quantitative image distortion metrics, and empirical steganalysis detection.",
  keywords: [
    "steganography",
    "steganalysis",
    "AES-256-GCM",
    "Scrypt",
    "LSB matching",
    "chi-square",
    "RS analysis",
    "image security",
  ],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Geist+Mono:wght@300;400;500;600;700&family=Geist:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="font-sans antialiased bg-abyss text-frost min-h-screen flex flex-col selection:bg-teal-liquid/30 selection:text-white">
        <AppQueryProvider>
          <Navbar />
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 pt-6 pb-16">
            {children}
          </main>
          <Footer />
          <Toaster
            position="top-right"
            toastOptions={{
              className: "glass-deep text-frost border border-teal-liquid/30 shadow-glass-lg",
              style: {
                background: "rgba(16, 38, 49, 0.9)",
                color: "#E5F1F3",
                border: "1px solid rgba(54, 214, 195, 0.3)",
              },
            }}
          />
        </AppQueryProvider>
      </body>
    </html>
  );
}
