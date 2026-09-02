export type Company = {
  ticker: string;
  name: string;
  sector: string;
  group: 'financial' | 'non-financial';
  note: string;
};

export type QuarterPoint = {
  quarter: string;
  actual: number;
  predicted: number;
};

export type ModelRow = {
  name: string;
  family: string;
  mae: number;
  rmse: number;
  smape: number;
  status: 'baseline' | 'candidate' | 'champion';
};

// Lista demonstracyjna do warstwy UI. Docelowo ma być pobierana z core.index_membership.
// Skład indeksu zmienia się w czasie, dlatego w pracy badawczej nie wolno traktować tej tablicy jako źródła historycznego.
export const companies: Company[] = [
  { ticker: 'ALE', name: 'Allegro.eu', sector: 'Handel / e-commerce', group: 'non-financial', note: 'Sprzedaż internetowa i marketplace' },
  { ticker: 'BDX', name: 'Budimex', sector: 'Budownictwo', group: 'non-financial', note: 'Generalne wykonawstwo i infrastruktura' },
  { ticker: 'CDR', name: 'CD Projekt', sector: 'Gry', group: 'non-financial', note: 'Produkcja i dystrybucja gier' },
  { ticker: 'CCC', name: 'CCC', sector: 'Handel detaliczny', group: 'non-financial', note: 'Obuwie i fashion retail' },
  { ticker: 'DNP', name: 'Dino Polska', sector: 'Handel detaliczny', group: 'non-financial', note: 'Sieć sklepów spożywczych' },
  { ticker: 'KTY', name: 'Grupa Kęty', sector: 'Przemysł', group: 'non-financial', note: 'Przetwórstwo aluminium' },
  { ticker: 'KGH', name: 'KGHM Polska Miedź', sector: 'Surowce', group: 'non-financial', note: 'Miedź, srebro i metale' },
  { ticker: 'KRU', name: 'Kruk', sector: 'Finanse', group: 'financial', note: 'Zarządzanie wierzytelnościami' },
  { ticker: 'LPP', name: 'LPP', sector: 'Odzież', group: 'non-financial', note: 'Projektowanie i sprzedaż odzieży' },
  { ticker: 'MBK', name: 'mBank', sector: 'Banki', group: 'financial', note: 'Bankowość detaliczna i korporacyjna' },
  { ticker: 'OPL', name: 'Orange Polska', sector: 'Telekomunikacja', group: 'non-financial', note: 'Telekomunikacja i usługi cyfrowe' },
  { ticker: 'ORL', name: 'ORLEN', sector: 'Energia', group: 'non-financial', note: 'Energetyka, paliwa i petrochemia' },
  { ticker: 'PEO', name: 'Bank Pekao', sector: 'Banki', group: 'financial', note: 'Bankowość uniwersalna' },
  { ticker: 'PCO', name: 'Pepco Group', sector: 'Handel detaliczny', group: 'non-financial', note: 'Sieć sklepów dyskontowych' },
  { ticker: 'PKO', name: 'PKO Bank Polski', sector: 'Banki', group: 'financial', note: 'Bankowość uniwersalna' },
  { ticker: 'PZU', name: 'PZU', sector: 'Ubezpieczenia', group: 'financial', note: 'Ubezpieczenia i usługi finansowe' },
  { ticker: 'SPL', name: 'Santander Bank Polska', sector: 'Banki', group: 'financial', note: 'Bankowość detaliczna i korporacyjna' },
  { ticker: 'TPE', name: 'Tauron Polska Energia', sector: 'Energia', group: 'non-financial', note: 'Wytwarzanie i dystrybucja energii' },
  { ticker: 'ZAB', name: 'Żabka Group', sector: 'Handel detaliczny', group: 'non-financial', note: 'Sieć convenience' },
  { ticker: 'XTB', name: 'XTB', sector: 'Finanse', group: 'financial', note: 'Usługi maklerskie i inwestycyjne' },
];

export const companySeries: QuarterPoint[] = [
  { quarter: '2024 Q1', actual: 2.18, predicted: 2.05 },
  { quarter: '2024 Q2', actual: 2.42, predicted: 2.31 },
  { quarter: '2024 Q3', actual: 2.30, predicted: 2.36 },
  { quarter: '2024 Q4', actual: 2.73, predicted: 2.61 },
  { quarter: '2025 Q1', actual: 2.56, predicted: 2.49 },
  { quarter: '2025 Q2', actual: 2.84, predicted: 2.72 },
  { quarter: '2025 Q3', actual: 3.04, predicted: 2.91 },
  { quarter: '2025 Q4', actual: 3.18, predicted: 3.11 },
];

export const modelRows: ModelRow[] = [
  { name: 'Seasonal naive', family: 'Baseline', mae: 0.42, rmse: 0.58, smape: 15.9, status: 'baseline' },
  { name: 'Last value', family: 'Baseline', mae: 0.39, rmse: 0.54, smape: 14.7, status: 'baseline' },
  { name: 'Ridge', family: 'Regresja', mae: 0.31, rmse: 0.45, smape: 11.8, status: 'candidate' },
  { name: 'HistGradientBoosting', family: 'Boosting', mae: 0.27, rmse: 0.39, smape: 10.2, status: 'champion' },
];

export const featureDrivers = [
  { label: 'Zysk netto t-4', value: 100 },
  { label: 'Zysk netto t-1', value: 86 },
  { label: 'Zmiana przychodów r/r', value: 69 },
  { label: 'Stopa referencyjna NBP', value: 48 },
  { label: 'Zwrot 60 sesji', value: 36 },
];
