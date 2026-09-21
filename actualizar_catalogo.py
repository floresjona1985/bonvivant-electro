#!/usr/bin/env python3
"""Baja el catálogo vivo de Printech11 y reemplaza products.json.
Los productos que ya no están en el proveedor se eliminan.
Los nuevos se agregan. Los precios de costo se actualizan.
"""
import json, os, re, sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup

BASE = "https://www.printech11.com"
CLAVE = os.environ.get("PRINTECH_CLAVE", "th11")
OUT = Path(__file__).resolve().parent / "products.json"

MAP = {
    "AURICULAR BLUETHOOTH": "AURICULARES",
    "AURICULAR EARPHONE": "AURICULARES",
    "AURICULAR VINCHA": "AURICULARES",
    "CABLES DATOS CARGA Y AUDIO": "CABLES",
    "JOYSTICK/TECLADO Y MOUSE": "GAMING",
    "PEGAMENTOS Y ADHESIVO": "PEGAMENTOS",
    "TERMOS - MATES": "TERMOS",
    "HERRAMIENTAS ELECTRICAS": "HERRAMIENTAS",
    "MEMORIA Y PENDRIVE": "MEMORIAS",
    "SOLO ADULTOS": "ADULTOS",
}

def parse_price(txt):
    n = re.sub(r"[^\d]", "", txt or "")
    return int(n) if n else 0

def norm_cat(c):
    c = (c or "VARIOS").strip().upper()
    return MAP.get(c, c if c else "VARIOS")

def scrape():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 BonvivantElectroCatalog/1.0"
    s.post(f"{BASE}/index.php", data={"clave": CLAVE, "enviar": "Ingresar"}, timeout=40)
    r = s.get(f"{BASE}/catalogo2024.php?rub=99999", timeout=90)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    items = []
    seen = set()
    for el in soup.select(".caja_producto"):
        form = el.find("form")
        code = ""
        if form and form.get("action"):
            m = re.search(r"cod=([^&]+)", form.get("action"))
            if m:
                code = m.group(1).strip()
        if not code:
            a = el.find("a", id=True)
            code = (a.get("id") if a else "") or ""
        name_el = el.find("h1")
        name = name_el.get_text(" ", strip=True) if name_el else ""
        rub = el.select_one(".rubro_centrado")
        cat = norm_cat(rub.get_text(" ", strip=True) if rub else "")
        price_el = el.select_one(".datos")
        cost = parse_price(price_el.get_text() if price_el else "")
        img = ""
        im = el.find("img")
        if im and im.get("src"):
            src = im["src"]
            img = src if src.startswith("http") else f"{BASE}/{src.lstrip('/')}"
        if not code or not name or cost <= 0 or cost > 2_000_000:
            continue
        if code in seen:
            continue
        seen.add(code)
        items.append({
            "id": code,
            "name": name,
            "cost": cost,
            "price": cost * 2,
            "img": img,
            "category": cat,
        })
    if len(items) < 50:
        raise SystemExit(f"Catálogo demasiado chico ({len(items)}). No se guarda para no borrar la tienda.")
    return items

def main():
    items = scrape()
    OUT.write_text(json.dumps(items, ensure_ascii=False), encoding="utf-8")
    print(f"OK {len(items)} productos -> {OUT}")

if __name__ == "__main__":
    main()
