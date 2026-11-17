# Projectnotities voor Claude

- Site: https://welkedresscode.nl (Netlify, publiceert automatisch de map `site/` bij elke push naar `main`).
- Bron: `src/app.html` bevat alles: de lijst `CODES` (naam `n`, Engelse naam `ne`, zoektermen `a`, teksten `nl`/`en` = [uitleg, mannen, vrouwen]), `LOOKS` (outfits voor de illustraties, per naam) en de app-logica.
- Elke dresscode in `CODES` moet een item in `LOOKS` hebben met dezelfde `n`.
- Bouwen na elke wijziging (uitkomst wordt meegecommit):
  1. `node tools/build.mjs` → maakt `site/` met homepage NL (`/`) en EN (`/en/`), een pagina per dresscode per taal (`/black-tie/`, `/en/black-tie/`), overzichtspagina's, 404, sitemap.xml en robots.txt.
  2. `python3 tools/og.py` → deelplaatjes in `site/og/` (alleen nodig als namen of illustraties veranderen).
  3. `python3 tools/pins.py` → Pinterest-plaatjes in `site/pins/` en upload-bestanden `pinterest/pinterest-nl.csv` en `-en.csv` (idem).
- Bewerk nooit bestanden in `site/` met de hand.
- Bezoekersteller: GoatCounter (welkedresscode.goatcounter.com). Getypte zoekopdrachten tellen als paginaweergave (gevonden), of als gebeurtenis `niet-gevonden: …` / `bedoel-je: …`; de deelknop als `gedeeld: …`.
- Gelegenheidspagina's (bruiloft, gala, …) staan in `src/occasions.json`; dresscodenamen daarin moeten exact overeenkomen met `CODES`.
- Ontwerp: één zoekvak, NL/EN-schakelaar en één deelknop onder de kaart (op verzoek van de gebruiker); verder geen extra knoppen. Retro-illustraties (pastel, rasterpunten). Geen andere stijl zonder overleg.
- Gebruiker communiceert in het Nederlands, wil korte uitleg en niet-technische stappen. "Bouw maar" = wijzigingen doorvoeren, bouwen, testen en pushen naar `main`.
- Na wijzigingen: test zoeken (typfouten), check beide talen, controleer illustraties op telefoonformaat.
