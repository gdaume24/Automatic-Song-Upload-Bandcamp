from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import os
import json


# Fichier de session cree par login_once.py (cookies d'authentification).
FICHIER_COOKIES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".bandcamp_cookies.json"
)



def track_artiste_name(nom_wav):


    pattern1 = r"\.wav"
    text_sans_wav = re.sub(pattern1, "", nom_wav)

    pattern2 = r" ?-? \d{4} ?$"
    text_sans_annee = re.sub(pattern2, "", text_sans_wav)

    pattern3 = r" ?-? ?([^-]*$)"
    artiste = re.sub(pattern3, "", text_sans_annee)

    pattern4 = " ?- ?([^-]*$)"
    track_name = re.search(pattern4, text_sans_annee).group(1)


    return track_name, artiste

class Pilotage:

    def __init__(self, driver, pause = 0.8):


        self.driver = driver
        # Temporisation entre chaque action visible (scroll + surbrillance d'un
        # champ avant de le remplir). Rend l'automatisation lisible a l'oeil :
        # on voit defiler les etapes dans l'ordre. Mettre 0 pour aller vite.
        self.pause = pause
        self.connection_bandcamp()

    def accepter_cookies(self, timeout = 25):


        # La bannière de cookies de Bandcamp est rendue dans le Shadow DOM
        # de l'element <menu-bar>, donc on clique le bouton "Tout accepter"
        # via JavaScript (Selenium ne peut pas le cibler en CSS classique).
        # La banniere peut apparaitre avec un leger delai : on attend donc
        # qu'elle soit presente, on clique, puis on la laisse se fermer
        # (sinon l'overlay <menu-bar> bloque le clic du bouton de login).

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

        from time import sleep, time as maintenant
        fin = maintenant() + timeout
        clique = False
        while maintenant() < fin:
            try:
                if self.driver.execute_script(click_js):
                    clique = True
                    break
            except Exception:
                pass
            sleep(0.5)

        if clique:
            sleep(1)   # laisser l'overlay se refermer
        return clique

    def clic(self, by, selector, timeout = 10):


        # Clic robuste : si un overlay (ex : banniere cookies) intercepte le
        # clic, on re-tente apres avoir ferme la banniere, puis en dernier
        # recours on clique via JavaScript.

        element = WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        try:
            element.click()
        except Exception:
            self.accepter_cookies(timeout = 5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
            try:
                element.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", element)
        return element

    def _montrer(self, element, etiquette = None):


        # Rend l'action visible et "humaine" : on amene le champ au centre de
        # l'ecran et on le fait clignoter (contour jaune) avant de le remplir.
        # Ainsi, en regardant Firefox, on suit dans l'ordre quel champ est
        # rempli et quel bouton est cliqué.

        from time import sleep

        if etiquette:
            print(f"      -> {etiquette}")

        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center', behavior:'smooth'});",
                element,
            )
            self.driver.execute_script(
                """
                const el = arguments[0];
                const avant = el.style.outline;
                const fond = el.style.boxShadow;
                el.style.outline = '3px solid #ffd200';
                el.style.boxShadow = '0 0 12px 3px rgba(255,210,0,.8)';
                setTimeout(() => { el.style.outline = avant; el.style.boxShadow = fond; }, 700);
                """,
                element,
            )
        except Exception:
            pass

        sleep(self.pause)
        return element

    def connection_bandcamp(self):


        # On ne se connecte pas via email/mot de passe : Bandcamp sert un
        # CAPTCHA aux navigateurs pilotes. On RECHARGE la session enregistree
        # (cookies). Si elle est absente ou expiree, on bascule sur une
        # connexion manuelle unique (l'utilisateur resout le CAPTCHA a la main)
        # et on sauvegarde la session pour les fois suivantes.

        self.driver.get("https://bandcamp.com/")
        self.accepter_cookies(timeout = 5)

        if os.path.exists(FICHIER_COOKIES):
            with open(FICHIER_COOKIES) as f:
                for cookie in json.load(f):
                    cookie.pop("sameSite", None)
                    try:
                        self.driver.add_cookie(cookie)
                    except Exception:
                        pass
            self.driver.get("https://bandcamp.com/")

        # Pas (ou plus) de session valide -> connexion manuelle.
        if not self.driver.get_cookie("identity"):
            self.connexion_manuelle()

        # Decouvrir le sous-domaine du groupe pour construire l'URL d'ajout
        # de piste (ex : https://blablabla8.bandcamp.com/edit_track).
        self.url_edit_track = self.decouvrir_url_edit_track()

        print(">>> Session Bandcamp chargee. Le traitement du dossier commence.")

    def connexion_manuelle(self, timeout = 600):


        # Ouvre la page de login : l'utilisateur se connecte a la main (et
        # resout le CAPTCHA). On attend l'apparition du cookie de session, puis
        # on le sauvegarde pour ne plus avoir a se reconnecter ensuite.

        self.driver.get("https://bandcamp.com/login")
        self.accepter_cookies(timeout = 10)

        print(">>> Connecte-toi a Bandcamp dans Firefox (resous le CAPTCHA). En attente...")

        from time import sleep, time as maintenant
        fin = maintenant() + timeout
        while maintenant() < fin:
            try:
                if self.driver.get_cookie("identity"):
                    with open(FICHIER_COOKIES, "w") as f:
                        json.dump(self.driver.get_cookies(), f)
                    print(">>> Connexion reussie, session sauvegardee.")
                    self.driver.get("https://bandcamp.com/")
                    return
            except Exception:
                pass
            sleep(1)

        raise Exception("Connexion non detectee (delai depasse). Reessaie.")

    def decouvrir_url_edit_track(self):


        # Ouvre le menu de compte et lit le lien "Outils" du groupe, dont on
        # derive l'URL de la page d'ajout de piste.

        self.clic(By.CSS_SELECTOR, "button[class*='logged-in-nav']")

        lien_outils = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/tools']"))
        )
        base = lien_outils.get_attribute("href").split("/tools")[0]
        return base + "/edit_track"

    def aller_add_track(self):


        # Nouvelle methode : on va directement sur la page de creation de piste
        # (l'ancien menu "+" du menubar n'existe plus).

        self.driver.get(self.url_edit_track)

    def add_audio(self, chemin_fichier_wav):


        # ------------------------------------------------------------------ add audio ------------------------------------------------------------------------------------

        champ_fichier = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".no-audio input[type='file']"))
        )


        # Charger chanson

        print("   1/6  Audio")
        champ_fichier.send_keys(chemin_fichier_wav)


        # Attendre la checkmarque (marqueur de fin d'upload)

        WebDriverWait(self.driver, 800).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span[data-test='track-upload-success-marker']"))
        )

    def ajout_trackname(self, track_name):


        # Ajouter trackname

        print("   2/6  Titre")
        champ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.title_0']"))
        )
        self._montrer(champ, f"Titre : {track_name}")
        champ.send_keys(track_name)

    def ajout_artiste(self, artist_name):


        # Artiste

        print("   3/6  Artiste")
        champ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.artist_0']"))
        )
        self._montrer(champ, f"Artiste : {artist_name}")
        champ.send_keys(artist_name)

    def ajout_tags(self, tags):


        # Tags (liste separee par des virgules). Ignore si vide.

        if not tags:
            return

        print("   4/6  Tags")
        champ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.tags_0']"))
        )
        self._montrer(champ, f"Tags : {tags}")
        champ.send_keys(tags)

    def ajout_prix(self, prix):


        # Prix de la piste. Ignore si vide.

        if prix in (None, ""):
            return

        print("   5/6  Prix")
        champ = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.price_0']"))
        )
        self._montrer(champ, f"Prix : {prix}")
        champ.clear()
        champ.send_keys(str(prix))

    def ajout_image(self, chemin_fichier_jpg):



        # ----------------------------------------------------------------- image ------------------------------------------------------------------------------------------

        print("   6/6  Pochette")
        sous_categorie = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "image-upload-hint"))
        )
        self._montrer(sous_categorie, "Pochette (image)")

        sous_categorie.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(chemin_fichier_jpg)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='art deletableArt']"))
            )
        except:
            print("pas d'élément localisé")

    def publication(self):


        # ----------------------------------------------------------------- finalisation -----------------------------------------------------------------------------------

        print("   ->   Enregistrement du brouillon")
        bouton = self.clic(By.CSS_SELECTOR, "a[data-test='save-draft-button']")
        self._montrer(bouton, "Bouton : Enregistrer le brouillon")

        # Appuyer sur le bouton de publication

        print("   ->   Publication")
        bouton = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-test='publish-tralbum']"))
        )
        self._montrer(bouton, "Bouton : Publier")
        self.clic(By.CSS_SELECTOR, "a[data-test='publish-tralbum']", timeout = 30)

        # On attend le petit message comme quoi c'est publié (tolerant : si le
        # selecteur a change, on n'echoue pas tout le traitement pour autant).

        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='congrats-message']"))
            )
        except Exception:
            print("   (message de confirmation non detecte, on continue)")

    def loop(self, chemin_dossier, nom_wav, nom_jpg, prix = "", tags = ""):


        chemin_musique = os.path.join(chemin_dossier, nom_wav)
        chemin_image = os.path.join(chemin_dossier, nom_jpg)
        track_name, artiste = track_artiste_name(nom_wav)


        self.aller_add_track()
        self.add_audio(chemin_musique)
        self.ajout_trackname(track_name)
        self.ajout_artiste(artist_name = artiste)
        self.ajout_tags(tags)
        self.ajout_prix(prix)
        self.ajout_image(chemin_image)
        self.publication()



if __name__ == "__main__":


    # Test manuel : suppose que login_once.py a deja enregistre la session.
    # La connexion se fait par cookies, l'email/mdp ne sont plus utilises.

    connector = Pilotage(webdriver.Firefox())

    chemin_dossier = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "dossier_test")
    nom_wav = "The Testers - Opening Theme.wav"
    nom_jpg = "The Testers - Opening Theme.jpg"

    connector.loop(chemin_dossier, nom_wav, nom_jpg, prix = "0", tags = "electronic, lo-fi, instrumental")

    









# loop()
















def code_prix():

    """pas besoin"""

    # Prix à 0€
    # WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, "input[class='price']"))
    # ).clear()

    # WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CSS_SELECTOR, "input[class='price']"))
    # ).send_keys(0)

