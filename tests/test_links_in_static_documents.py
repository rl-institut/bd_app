import logging

import requests

# Liste der Urls, alphabetisch sortiert
urls = [
    "https://deneff.org/sanierungssprint-legt-los-immer-mehr-regionen-setzen-auf-tempo-bei-der-gebaeudesanierung/",
    "https://energieberatung-wissen.de/energieeffizienz-berechnen-die-wichtigsten-formeln/",
    "https://sanierungsrechner.kfw.de/",
    "https://verbraucherzentrale-energieberatung.de/",
    "https://verbraucherzentrale-energieberatung.de/heizen/neue-heiztechnik/elektrische-direktheizung/",
    "https://verbraucherzentrale-energieberatung.de/heizen/neue-heiztechnik/gasheizung",
    "https://verbraucherzentrale-energieberatung.de/heizen/neue-heiztechnik/oelheizung/",
    "https://webtool.building-typology.eu/#bm",
    "https://www.agfw.de/energiewirtschaft-recht-politik/energiewende-politik/ueberblick-fakten-und-antworten-zu-fernwaerme",
    "https://www.agfw.de/energiewirtschaft-recht-politik/recht/anschluss-und-benutzungszwang",
    "https://www.bafa.de/DE/Energie/Effiziente_Gebaeude/Foerderprogramm_im_Ueberblick/foerderprogramm_im_ueberblick_node.html",
    "https://www.bafa.de/SharedDocs/Downloads/DE/Energie/beg_merkblatt_allgemein_antragstellung.pdf?__blob=publicationFile&v=10",
    "https://www.bbsr-geg.bund.de/GEGPortal/DE/GEGRegelungen/Anlagen_EE/Beratungspflicht/Beratungspflicht.html",
    "https://www.bbsr.bund.de/BBSR/DE/veroeffentlichungen/sonderveroeffentlichungen/2024/geg.html",
    "https://www.berlin.de/solarcity/solarzentrum/",
    "https://www.bundesfinanzministerium.de/Content/DE/Standardartikel/Themen/Schlaglichter/Nachhaltigkeitsstrategie/steuerliche-foerderung-energetischer-gebaeudesanierungen.html",
    "https://www.bundesregierung.de/breg-de/aktuelles/neues-gebaeudeenergiegesetz-2184942",
    "https://www.co2online.de/energie-sparen/heizenergie-sparen/lueften-lueftungsanlagen-fenster/fenster-tauschen/",
    "https://www.co2online.de/modernisieren-und-bauen/blockheizkraftwerk-kraft-waerme-kopplung/blockheizkraftwerk-funktionsweise-wirkungsgrad/",
    "https://www.co2online.de/modernisieren-und-bauen/daemmung/dachdaemmung/",
    "https://www.co2online.de/modernisieren-und-bauen/daemmung/daemmung-der-obersten-geschossdecke/",
    "https://www.co2online.de/modernisieren-und-bauen/daemmung/fassadendaemmung/",
    "https://www.co2online.de/modernisieren-und-bauen/daemmung/kellerdeckendaemmung/",
    "https://www.co2online.de/modernisieren-und-bauen/heizung/gasheizung/",
    "https://www.co2online.de/modernisieren-und-bauen/heizung/heizungsarten-im-vergleich/",
    "https://www.co2online.de/modernisieren-und-bauen/heizung/pelletheizung/",
    "https://www.co2online.de/modernisieren-und-bauen/photovoltaik/pv-heizstab/",
    "https://www.co2online.de/modernisieren-und-bauen/photovoltaik/pv-heizstab/",
    "https://www.co2online.de/modernisieren-und-bauen/solarthermie/",
    "https://www.co2online.de/service/energiesparchecks/foerdermittelcheck/",
    "https://www.co2online.de/service/energiesparchecks/heizcheck/",
    "https://www.co2online.de/service/energiesparchecks/modernisierungscheck/",
    "https://www.co2online.de/service/energiesparchecks/waermepumpencheck/",
    "https://www.co2online.de/service/handwerkerangebote-einholen/",
    "https://www.dena.de/fileadmin/dena/Publikationen/PDFs/2018/2024_Modernisierungsratgeber_Energie.pdf",
    "https://www.energie-effizienz-experten.de/",
    "https://www.energiewechsel.de/KAENEF/Redaktion/DE/FAQ/GEG/faq-geg.html",
    "https://www.gebaeudeforum.de/realisieren/heizungstechnik/nt-ready/",
    "https://www.hwk-berlin.de/downloads/broschuere-sanierung-von-kastenfenstern-eine-entscheidungshilfe-91,650.pdf",
    "https://www.ifeu.de/gebaeudecheck-waermepumpe#/",
    "https://www.ioew.de/publikation/energiewende_in_der_lausitz_regionaloekonomische_effekte_relevanter_technologien",
    "https://www.ioew.de/publikation/geschaeftsmodelle_fuer_die_waermewende_im_quartier",
    "https://www.ioew.de/publikation/kommunale_waermewende_strategisch_planen",
    "https://www.kfw.de/inlandsfoerderung/Privatpersonen/Bestandsimmobilie/F%C3%B6rderprodukte/F%C3%B6rderprodukte-f%C3%BCr-Bestandsimmobilien.html",
    "https://www.raum-analyse.de/waermedaemmung/daemmstoffdicke-berechnen/",
    "https://www.raum-analyse.de/waermedaemmung/daemmstoffdicke-berechnen/",
    "https://www.sfv.de/solaranlagenberatung-1",
    "https://www.umweltbundesamt.de/publikationen/heizen-holz",
    "https://www.umweltbundesamt.de/umwelttipps-fuer-den-alltag/heizen-bauen/sanierung#hintergrund",
    "https://www.unendlich-viel-energie.de/wertschoepfungsrechner",
    "https://www.verbraucherzentrale-rlp.de/sites/default/files/2024-07/240612_bhp_vz_keller_06.pdf",
    "https://www.verbraucherzentrale-saarland.de/pressemeldungen/energie/daemmen-der-obersten-geschossdecke-59258",
    "https://www.verbraucherzentrale.bayern/pressemeldungen/energie/dachdaemmung-schuetzt-vor-hitze-und-energieverlust-109975",
    "https://www.verbraucherzentrale.de/wissen/energie/energetische-sanierung/fenster-sanieren-oder-austauschen-darauf-sollten-sie-achten-13878",
    "https://www.verbraucherzentrale.de/wissen/energie/energetische-sanierung/geg-was-steht-im-gebaeudeenergiegesetz-13886",
    "https://www.verbraucherzentrale.de/wissen/energie/energetische-sanierung/hauseingang-schoen-sicher-und-energiesparend-gestalten-9-tipps-11449",
    "https://www.verbraucherzentrale.de/wissen/energie/energetische-sanierung/rechenbeispiel-fuer-eine-fassadendaemmung-8192",
    "https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/heizungsfoerderung-fuer-bestandsgebaeude-heizen-mit-erneuerbaren-energien-10773",
    "https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/photovoltaik-was-bei-der-planung-einer-solaranlage-wichtig-ist-5574",
    "https://www.verbraucherzentrale.de/wissen/energie/erneuerbare-energien/solarthermie-solarenergie-fuer-heizung-und-warmwasser-nutzen-5568",
    "https://www.verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/fernwaerme-kosten-sparen-und-gleichzeitig-das-klima-schonen-34038",
    "https://www.verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/heizung-tauschen-so-gehts-schritt-fuer-schritt-30045?",
    "https://verbraucherzentrale-energieberatung.de/heizen/neue-heiztechnik/blockheizkraftwerk/",
    "https://www.verbraucherzentrale.de/wissen/energie/heizen-und-warmwasser/waermepumpe-alles-was-sie-wissen-muessen-5439",
    "https://www.waermepumpe.de/",
    "https://www.waermepumpe.de/fachpartner/planungstools/",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9",
}


def check_url(url):
    """
    Prüft, ob eine URL erreichbar ist.
    Gibt ein Tuple zurück: (True/False, StatusCode oder Fehlertext)
    Status-Codes: https://de.wikipedia.org/wiki/HTTP-Statuscode
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # currently no redirecting is allowed. to do so: allow_redirects=True
        statuscode = response.status_code
    except requests.RequestException as exc:
        logging.warning("Request failed: %s -> %s", url, exc)
        # exceptions in doc https://requests.readthedocs.io/en/latest/_modules/requests/exceptions/#RequestException
        return False, str(exc)
    else:
        # 200 oder 2xx (Erfolgreiche Operation) akzeptieren
        statuscode_min = 200
        statuscode_max = 300
        ok = statuscode_min <= statuscode < statuscode_max
        return ok, statuscode


# Test with pytest: needs approx. 20-35 seconds to run
def test_urls_are_working():
    """
    Test that checks all URLS in list urls for reachability.
    Every status between 200 and 299 is accepted as working.

    Broken URLs at the moment:
    https://www.baunetzwissen.de/nachhaltig-bauen/fachwissen/regelwerke/
    berechnungsgrundlagen-fuer-energiebilanzen-830569 ; status code: 403
    """
    broken_urls = []
    for url in urls:
        ok, status = check_url(url)
        if not ok:
            broken_urls.append((url, status))

    assert not broken_urls, f"{len(broken_urls)} URLs failed:\n" + "\n".join(
        f"- {url} (Status: {status})" for url, status in broken_urls
    )
