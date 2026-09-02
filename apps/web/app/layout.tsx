import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'WIG20 Financial Prediction',
  description: 'Prototyp platformy predykcji wyników finansowych spółek WIG20',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pl">
      <body>
        <div className="site-shell">
          <header className="site-header">
            <Link href="/" className="brand-link">
              <span className="brand-mark">FP</span>
              <span><strong>Financial Prediction</strong><small>WIG20 · platforma badawcza</small></span>
            </Link>
            <nav className="main-nav" aria-label="Nawigacja główna">
              <Link href="/">Start</Link>
              <Link href="/review">Review</Link>
              <Link href="/companies">Spółki WIG20</Link>
              <Link href="/data">Jakość danych</Link>
              <Link href="/data-browser">Podgląd danych</Link>
              <Link href="/models">Modele</Link>
              <Link href="/dashboard">Dashboard</Link>
            </nav>
          </header>
          {children}
          <footer className="footer">Model predykcji wyników finansowych spółek giełdowych · v6.0 REVIEW RELEASE</footer>
        </div>
      </body>
    </html>
  );
}
