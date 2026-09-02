"""Configurable pilot universe for the first real-data prototype.

The list is intentionally treated as a technical pilot universe, not a claim about
historical WIG20 membership. Historical membership should be loaded separately into
core.index_membership from GPW/GPW Benchmark source material.
"""

PILOT_COMPANIES = [
    {"ticker": "PKO", "yahoo": "PKO.WA", "bankier": "PKOBP", "name": "PKO Bank Polski", "sector": "Banks", "is_financial": True},
    {"ticker": "PEO", "yahoo": "PEO.WA", "bankier": "PEKAO", "name": "Bank Pekao", "sector": "Banks", "is_financial": True},
    {"ticker": "SPL", "yahoo": "SPL.WA", "bankier": "SANPL", "name": "Santander Bank Polska", "sector": "Banks", "is_financial": True},
    {"ticker": "MBK", "yahoo": "MBK.WA", "bankier": "MBANK", "name": "mBank", "sector": "Banks", "is_financial": True},
    {"ticker": "PZU", "yahoo": "PZU.WA", "bankier": "PZU", "name": "PZU", "sector": "Insurance", "is_financial": True},
    {"ticker": "ORL", "yahoo": "PKN.WA", "bankier": "PKNORLEN", "name": "ORLEN", "sector": "Energy", "is_financial": False},
    {"ticker": "KGH", "yahoo": "KGH.WA", "bankier": "KGHM", "name": "KGHM Polska Miedź", "sector": "Mining", "is_financial": False},
    {"ticker": "CDR", "yahoo": "CDR.WA", "bankier": "CDPROJEKT", "name": "CD Projekt", "sector": "Gaming", "is_financial": False},
    {"ticker": "DNP", "yahoo": "DNP.WA", "bankier": "DINOPL", "name": "Dino Polska", "sector": "Retail", "is_financial": False},
    {"ticker": "LPP", "yahoo": "LPP.WA", "bankier": "LPP", "name": "LPP", "sector": "Retail", "is_financial": False},
    {"ticker": "CCC", "yahoo": "CCC.WA", "bankier": "CCC", "name": "CCC", "sector": "Retail", "is_financial": False},
    {"ticker": "ALE", "yahoo": "ALE.WA", "bankier": "ALLEGRO", "name": "Allegro.eu", "sector": "E-commerce", "is_financial": False},
    {"ticker": "XTB", "yahoo": "XTB.WA", "bankier": "XTB", "name": "XTB", "sector": "Financial services", "is_financial": True},
]
