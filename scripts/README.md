# MakerWorld Profile Scraper

Script Python per estrarre automaticamente i dati del tuo profilo MakerWorld usando Playwright.

## 🚀 Installazione

```bash
# Installa Playwright
pip3 install playwright

# Installa il browser Chromium
python3 -m playwright install chromium
```

## 📖 Uso

### Comando Base
```bash
python3 scripts/scrape_makerworld_py.py https://makerworld.com/en/@darionji
```

### Con Output Personalizzato
```bash
python3 scripts/scrape_makerworld_py.py https://makerworld.com/en/@darionji --out my_profile.json
```

## 📁 Output

Tutti i file vengono salvati nella cartella `output/` nella root del progetto:

- **`profile_data.json`** - Dati strutturati del profilo (nome, punti, modelli)
- **`page.html`** - HTML completo della pagina
- **`screenshot.png`** - Screenshot dell'intera pagina
- **`diagnostics.json`** - Informazioni tecniche (URL, selettori trovati, dimensione HTML)

## 📊 Formato Dati Estratti

```json
{
  "sourceUrl": "https://makerworld.com/en/@darionji",
  "accountName": "Nome Account",
  "points": 1234,
  "models": {
    "model_id_1": {
      "id": "16023105_position_home_index_0",
      "title": "Titolo Modello",
      "raw_metrics_numbers": ["123", "456"]
    }
  }
}
```

### Cosa viene estratto:
- **accountName**: Nome del profilo (dal tag `<h1>`)
- **points**: Punti/reward del profilo
- **models**: Lista di tutti i modelli con:
  - `id`: Identificativo univoco del modello
  - `title`: Titolo del modello
  - `raw_metrics_numbers`: Numeri trovati (likes, downloads, views, ecc.)

## 🔧 Come Funziona

1. **Avvia browser headless** (Chromium invisibile)
2. **Naviga al profilo** MakerWorld specificato
3. **Aspetta il caricamento** degli elementi con `[data-trackid]`
4. **Cattura HTML e screenshot** della pagina completa
5. **Estrae dati strutturati**:
   - Nome account dal tag `<h1>`
   - Punti da elementi con classi "points" o "reward"
   - Modelli da tutti gli elementi con attributo `data-trackid`
6. **Salva tutto** nella cartella `output/`

## 🐛 Risoluzione Problemi

### Cartella /tmp non visibile su macOS
La cartella `/tmp` su macOS è nascosta. Gli script ora salvano tutto in `output/` nella root del progetto per facilità di accesso.

### Errore "Protocol error Target.activateTarget"
Questo errore era causato da pyppeteer (deprecato). Gli script ora usano Playwright che risolve il problema.

### Browser non si avvia
Assicurati di aver installato Chromium:
```bash
python3 -m playwright install chromium
```

## 💡 Note

- Lo script funziona con **profili pubblici**, non serve autenticazione
- Il browser viene eseguito in **modalità headless** (senza interfaccia grafica)
- Timeout configurabile: 60 secondi per la navigazione, 30 secondi per i selettori
- User-Agent impostato per simulare Chrome su macOS

## 📝 Esempio Completo

```bash
# Esegui lo scraper
python3 scripts/scrape_makerworld_py.py https://makerworld.com/en/@darionji

# Output:
# 📁 Files saved in: /path/to/project/output
#   - profile_data.json (profile data)
#   - page.html (full HTML)
#   - screenshot.png (page screenshot)
#   - diagnostics.json (technical info)
# {"status":"ok","models":4,"points":0,"accountName":"darionji"}

# Apri la cartella output
open output/

# Visualizza i dati estratti
cat output/profile_data.json | python3 -m json.tool