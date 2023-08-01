from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from time import time
from selenium.webdriver.support import expected_conditions as EC
import re



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

    def __init__(self, driver, email, mdp):


        self.driver = driver
        self.email = email
        self.mdp = mdp
        self.connection_bandcamp()

    def connection_bandcamp(self):


        # Ouvrir une URL

        self.driver.get('https://bandcamp.com/login')


        # EMAIL

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "username-field"))
        ).send_keys(self.email)


        # MDP

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "password-field"))
        ).send_keys(self.mdp)


        # Click button

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "buttons"))
        ).click()

    def aller_add_track(self):


        # Click add

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "menubar-add-link"))
        ).click()

        # Click track

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "li[data-test='mb-add-track']"))
        ).click()

    def add_audio(self, chemin_fichier_wav):


        # ------------------------------------------------------------------ add audio ------------------------------------------------------------------------------------

        sous_categorie = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "audio-upload"))
        )


        # Charger chanson

        sous_categorie.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(chemin_fichier_wav)


        # Attendre la checkmarque

        WebDriverWait(self.driver, 800).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span[class='bc-ui checkmark'][data-test='track-upload-success-marker']"))
        )

    def ajout_trackname(self, track_name):


        # Ajouter trackname

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[class='title required force-placeholder-wrapper']"))
        ).send_keys(track_name)

    def ajout_artiste(self, artist_name):


        # Artiste

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.artist_0']"))
        ).send_keys(artist_name)

    def ajout_bandtags(self):


        # bandtags

        balises_span = self.driver.find_elements(By.CSS_SELECTOR, "span[class='bandtag']")

        string = ""
        longueur_tags = len(balises_span)
        i = 1
        for balise in balises_span:
            print()
            string += balise.text
            if i < longueur_tags:
                string += ", "
            i += 1
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='track.tags_0']"))
        ).send_keys(string)

    def ajout_image(self, chemin_fichier_jpg):



        # ----------------------------------------------------------------- image ------------------------------------------------------------------------------------------

        sous_categorie = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "image-upload-hint"))
        )

        sous_categorie.find_element(By.CSS_SELECTOR, "input[type='file']").send_keys(chemin_fichier_jpg)

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='art deletableArt']"))
            )
        except:
            print("pas d'élément localisé")

    def publication(self):


        # ----------------------------------------------------------------- finalisation -----------------------------------------------------------------------------------

        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='button save-draft show-when-dirty save_link']"))
        ).click()

        # Appuyer sur le bouton de publication

        WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a[class='button publish publish_link']"))
        ).click()

        # On attend le petit message comme quoi c'est publié

        WebDriverWait(self.driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div[class='congrats-message']"))
        )

    def loop(self, chemin_dossier, nom_wav, nom_jpg):


        chemin_musique = chemin_dossier + "\\" + nom_wav
        chemin_image = chemin_dossier + "\\" + nom_jpg
        track_name, artiste = track_artiste_name(nom_wav)


        self.aller_add_track()
        self.add_audio(chemin_musique)
        self.ajout_trackname(track_name)
        self.ajout_artiste(artist_name = artiste)
        self.ajout_bandtags()
        self.ajout_image(chemin_image)
        self.publication()



if __name__ == "__main__":


    connector = Pilotage(webdriver.Firefox())


    EMAIL = "geoffroy.daumer@outlook.fr"
    MDP = "kirbycath61"
    chemin_dossier = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon"
    nom_wav = "Ben E. King - Music Trance .wav"
    nom_jpg = "Ben E. King - Music Trance .jpg"

    connector.loop(chemin_dossier, nom_wav, nom_jpg)

    









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

