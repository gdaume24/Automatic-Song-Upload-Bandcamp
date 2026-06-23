"""
Connexion unique a Bandcamp.

A lancer UNE fois : une fenetre Firefox s'ouvre, tu te connectes a la main
(et tu resous le CAPTCHA). La session (cookies) est ensuite enregistree dans
.bandcamp_cookies.json. L'application rechargera cette session, ce qui evite
de se reconnecter / repasser le CAPTCHA a chaque lancement.

    python3 login_once.py
"""

import os
import json
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

# Fichier de session, range a cote du projet (ignore par git : contient le
# jeton d'authentification, a ne jamais committer).
FICHIER_COOKIES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".bandcamp_cookies.json"
)


def ouvrir_firefox():
    options = Options()
    options.set_preference("intl.accept_languages", "fr")
    return webdriver.Firefox(options=options)


def accepter_cookies(driver, timeout=20):
    # La banniere cookies (Shadow DOM de <menu-bar>) gene la connexion : on
    # clique "Tout accepter" via JS des qu'elle apparait.
    click_js = r"""
    function walk(root){
      for(const el of root.querySelectorAll('*')){
        if(el.shadowRoot){
          for(const b of el.shadowRoot.querySelectorAll('button')){
            if((b.textContent||'').trim().startsWith('Tout accepter')){ b.click(); return true; }
          }
          if(walk(el.shadowRoot)) return true;
        }
      }
      return false;
    }
    return walk(document);
    """
    from time import time as maintenant
    fin = maintenant() + timeout
    while maintenant() < fin:
        try:
            if driver.execute_script(click_js):
                return True
        except Exception:
            pass
        sleep(0.5)
    return False


if __name__ == "__main__":

    driver = ouvrir_firefox()
    driver.get("https://bandcamp.com/login")

    accepter_cookies(driver)

    print("Connecte-toi a Bandcamp dans la fenetre Firefox (resous le CAPTCHA).")
    print("J'attends la connexion...")

    try:
        connecte = False
        for _ in range(600):                    # jusqu'a 10 minutes
            try:
                # La page de login (Vue) se recharge / redirige : le contexte
                # surveille peut etre "jete". On se raccroche a une fenetre
                # valide a chaque tour et on ignore les erreurs transitoires.
                handles = driver.window_handles
                if handles:
                    driver.switch_to.window(handles[0])
                if driver.get_cookie("identity"):   # cookie pose une fois connecte
                    connecte = True
                    break
            except Exception:
                pass
            sleep(1)

        if connecte:
            with open(FICHIER_COOKIES, "w") as f:
                json.dump(driver.get_cookies(), f)
            print(f">>> Connexion detectee ! Session enregistree dans {os.path.basename(FICHIER_COOKIES)}.")
            print(">>> Tu peux fermer la fenetre. L'app reutilisera cette session.")
        else:
            print("Timeout : aucune connexion detectee.")

        sleep(2)
    finally:
        driver.quit()
