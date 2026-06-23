"""
Interface graphique de l'outil d'upload automatique Bandcamp.

- choix du dossier a importer (avec bouton Parcourir) ;
- valeurs par defaut pour le prix et les tags (modifiables) ;
- journal d'avancement en direct dans la fenetre (plus besoin de la console) ;
- barre de progression et etat de session.

La connexion se fait par cookies (voir login_once.py) : il n'y a plus de
champ email / mot de passe.
"""

import os
import sys
import json
import queue
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext

from mon_os import listage_wav_jpg
from mon_selenium import Pilotage, FICHIER_COOKIES
from selenium import webdriver


# --- Valeurs par defaut (modifiables dans l'interface) ---------------------
DEFAULT_PRIX = "0"
DEFAULT_TAGS = "electronic, lo-fi, instrumental"
DOSSIER_TEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test", "dossier_test")

# Preferences memorisees entre deux sessions (chemin, prix, tags, mode demo).
# Fichier local non versionne (chemins personnels) -> voir .gitignore.
FICHIER_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".bandcamp_config.json")


def charger_config():
    try:
        with open(FICHIER_CONFIG) as f:
            return json.load(f)
    except Exception:
        return {}

# Couleurs (theme sombre, plus "produit").
BG = "#1e1f26"
BG_CARD = "#2a2c36"
FG = "#e8e8ec"
FG_DIM = "#9aa0ad"
ACCENT = "#ffd200"
OK = "#5fd38a"
ERR = "#ff6b6b"


class Application:


    def __init__(self):

        self.evenements = queue.Queue()      # messages (log/progress/etat) du thread de travail
        self.file_dossiers = []              # dossiers en attente (clics pendant un traitement)
        self.traitement_en_cours = False
        self.config = charger_config()       # preferences de la session precedente

        self._construire_fenetre()
        self._verifier_session()
        self.fenetre.protocol("WM_DELETE_WINDOW", self._fermer)
        self.fenetre.after(100, self._vider_la_file)

    # ----------------------------------------------------------------- UI ---

    def _construire_fenetre(self):

        self.fenetre = tk.Tk()
        self.fenetre.title("Bandcamp Auto-Upload")
        self.fenetre.geometry("760x640")
        self.fenetre.minsize(680, 560)
        self.fenetre.configure(bg = BG)

        style = ttk.Style(self.fenetre)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background = BG)
        style.configure("Card.TFrame", background = BG_CARD)
        style.configure("TLabel", background = BG, foreground = FG, font = ("Helvetica", 12))
        style.configure("Dim.TLabel", background = BG, foreground = FG_DIM, font = ("Helvetica", 10))
        style.configure("Title.TLabel", background = BG, foreground = FG, font = ("Helvetica", 20, "bold"))
        style.configure("Sub.TLabel", background = BG, foreground = FG_DIM, font = ("Helvetica", 11))
        style.configure("TEntry", fieldbackground = "#3a3d49", foreground = FG, insertcolor = FG)
        style.configure("TCheckbutton", background = BG, foreground = FG_DIM, font = ("Helvetica", 10))
        style.map("TCheckbutton", background = [("active", BG)])
        style.configure("Accent.TButton", font = ("Helvetica", 13, "bold"), padding = 10)
        style.configure("Link.TButton", font = ("Helvetica", 10), padding = 4)
        style.configure("Bar.Horizontal.TProgressbar", troughcolor = BG_CARD, background = ACCENT)

        cont = ttk.Frame(self.fenetre, padding = 20)
        cont.pack(fill = "both", expand = True)
        cont.columnconfigure(0, weight = 1)

        # En-tete
        ttk.Label(cont, text = "Bandcamp Auto-Upload", style = "Title.TLabel").grid(row = 0, column = 0, sticky = "w")
        ttk.Label(cont, text = "Publie tout un dossier de morceaux sur Bandcamp, automatiquement.",
                  style = "Sub.TLabel").grid(row = 1, column = 0, sticky = "w", pady = (2, 14))

        # Etat de session
        self.lbl_session = ttk.Label(cont, text = "Session : verification...", style = "Dim.TLabel")
        self.lbl_session.grid(row = 2, column = 0, sticky = "w")
        self.btn_login = ttk.Button(cont, text = "Se connecter (1re fois)", style = "Link.TButton",
                                    command = self._lancer_login)
        self.btn_login.grid(row = 2, column = 0, sticky = "e")

        # Carte des champs
        carte = ttk.Frame(cont, style = "Card.TFrame", padding = 16)
        carte.grid(row = 3, column = 0, sticky = "ew", pady = 14)
        carte.columnconfigure(1, weight = 1)

        def _lbl(row, txt):
            tk.Label(carte, text = txt, bg = BG_CARD, fg = FG, font = ("Helvetica", 12, "bold")
                     ).grid(row = row, column = 0, sticky = "w", pady = 6, padx = (0, 12))

        # Dossier
        _lbl(0, "Dossier")
        self.var_chemin = tk.StringVar(value = self.config.get("chemin", DOSSIER_TEST))
        ttk.Entry(carte, textvariable = self.var_chemin).grid(row = 0, column = 1, sticky = "ew")
        ttk.Button(carte, text = "Parcourir", style = "Link.TButton",
                   command = self._choisir_dossier).grid(row = 0, column = 2, padx = (8, 0))

        # Prix
        _lbl(1, "Prix (€)")
        self.var_prix = tk.StringVar(value = self.config.get("prix", DEFAULT_PRIX))
        ttk.Entry(carte, textvariable = self.var_prix, width = 10).grid(row = 1, column = 1, sticky = "w")

        # Tags
        _lbl(2, "Tags")
        self.var_tags = tk.StringVar(value = self.config.get("tags", DEFAULT_TAGS))
        ttk.Entry(carte, textvariable = self.var_tags).grid(row = 2, column = 1, columnspan = 2, sticky = "ew")

        # Mode demo (ralenti)
        self.var_demo = tk.BooleanVar(value = self.config.get("demo", True))
        ttk.Checkbutton(carte, text = "Mode démo : ralenti + surbrillance (on voit chaque champ se remplir)",
                        variable = self.var_demo).grid(row = 3, column = 1, columnspan = 2, sticky = "w", pady = (8, 0))

        # Bouton principal + progression
        barre = ttk.Frame(cont)
        barre.grid(row = 4, column = 0, sticky = "ew")
        barre.columnconfigure(1, weight = 1)

        self.btn_lancer = ttk.Button(barre, text = "▶  Lancer l'upload", style = "Accent.TButton",
                                     command = self._lancer)
        self.btn_lancer.grid(row = 0, column = 0, sticky = "w")

        self.progress = ttk.Progressbar(barre, style = "Bar.Horizontal.TProgressbar",
                                        mode = "determinate")
        self.progress.grid(row = 0, column = 1, sticky = "ew", padx = (14, 0))

        self.lbl_etat = ttk.Label(cont, text = "Prêt.", style = "Dim.TLabel")
        self.lbl_etat.grid(row = 5, column = 0, sticky = "w", pady = (8, 4))

        # Journal
        self.journal = scrolledtext.ScrolledText(cont, height = 12, bg = "#15161b", fg = FG,
                                                  insertbackground = FG, relief = "flat",
                                                  font = ("Menlo", 10), state = "disabled")
        self.journal.grid(row = 6, column = 0, sticky = "nsew")
        self.journal.tag_config("ok", foreground = OK)
        self.journal.tag_config("err", foreground = ERR)
        self.journal.tag_config("accent", foreground = ACCENT)
        cont.rowconfigure(6, weight = 1)

    # -------------------------------------------------------------- actions -

    def _choisir_dossier(self):
        chemin = filedialog.askdirectory(title = "Choisir le dossier à importer")
        if chemin:
            self.var_chemin.set(chemin)

    def _sauver_config(self):
        # Memorise les champs pour la prochaine session.
        try:
            with open(FICHIER_CONFIG, "w") as f:
                json.dump({
                    "chemin": self.var_chemin.get().strip(),
                    "prix": self.var_prix.get().strip(),
                    "tags": self.var_tags.get().strip(),
                    "demo": bool(self.var_demo.get()),
                }, f, indent = 2)
        except Exception:
            pass

    def _fermer(self):
        self._sauver_config()
        self.fenetre.destroy()

    def _verifier_session(self):
        if os.path.exists(FICHIER_COOKIES):
            self.lbl_session.configure(text = "Session : ✓ connectée (cookies enregistrés)", foreground = OK)
        else:
            self.lbl_session.configure(text = "Session : ✗ aucune — clique « Se connecter » d'abord", foreground = ERR)

    def _lancer_login(self):
        # Lance login_once.py dans un sous-processus (Firefox s'ouvre, connexion manuelle).
        self._log("Ouverture de la connexion manuelle (login_once.py)...", "accent")
        script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "login_once.py")

        def run():
            try:
                subprocess.run([sys.executable, script], check = False)
            finally:
                self.evenements.put(("session", None))

        threading.Thread(target = run, daemon = True).start()

    def _lancer(self):
        chemin = self.var_chemin.get().strip()
        if not chemin or not os.path.isdir(chemin):
            self._log("Dossier introuvable : vérifie le chemin.", "err")
            return

        dossier = {
            "chemin": chemin,
            "prix": self.var_prix.get().strip(),
            "tags": self.var_tags.get().strip(),
            "pause": 1.1 if self.var_demo.get() else 0.25,
        }

        self._sauver_config()

        if self.traitement_en_cours:
            self.file_dossiers.append(dossier)
            self._log(f"Ajouté à la file d'attente : {chemin}", "accent")
            return

        self.traitement_en_cours = True
        self.btn_lancer.configure(state = "disabled")
        self.lbl_etat.configure(text = "Démarrage du navigateur...")
        threading.Thread(target = self._worker, args = (dossier,), daemon = True).start()

    # ----------------------------------------------------- thread de travail

    def _worker(self, premier_dossier):

        # Tout ce qui est imprime ici (y compris par mon_selenium) part dans le
        # journal de l'interface via la redirection de stdout ci-dessous.
        ancien_stdout = sys.stdout
        sys.stdout = _RedirectionVersFile(self.evenements, ancien_stdout)

        driver = None
        try:
            driver = webdriver.Firefox()
            pilote = Pilotage(driver, pause = premier_dossier["pause"])

            self._traiter(pilote, premier_dossier)
            while self.file_dossiers:
                self._traiter(pilote, self.file_dossiers.pop(0))

            self.evenements.put(("done", "Terminé ✓"))

        except Exception as e:
            self.file_dossiers.clear()
            self.evenements.put(("error", f"Interrompu ({type(e).__name__}). File d'attente annulée."))
        finally:
            sys.stdout = ancien_stdout
            if driver is not None:
                try:
                    driver.quit()
                except Exception:
                    pass
            self.evenements.put(("ready", None))

    def _traiter(self, pilote, dossier):
        pilote.pause = dossier["pause"]
        liste_wav, liste_jpg = listage_wav_jpg(chemin_dossier = dossier["chemin"])
        total = len(liste_wav)
        self.evenements.put(("progress", 0, total))
        print(f"Dossier : {dossier['chemin']}  ({total} morceaux)")

        for i in range(total):
            nom_wav, nom_jpg = liste_wav[i], liste_jpg[i]
            print(f"[{i + 1}/{total}] {nom_wav}")
            pilote.loop(dossier["chemin"], nom_wav, nom_jpg,
                        prix = dossier["prix"], tags = dossier["tags"])
            self.evenements.put(("progress", i + 1, total))

    # ------------------------------------------------ boucle de l'interface -

    def _vider_la_file(self):
        try:
            while True:
                ev = self.evenements.get_nowait()
                self._traiter_evenement(ev)
        except queue.Empty:
            pass
        self.fenetre.after(100, self._vider_la_file)

    def _traiter_evenement(self, ev):
        type_ev = ev[0]
        if type_ev == "log":
            self._log(ev[1])
        elif type_ev == "progress":
            fait, total = ev[1], ev[2]
            self.progress.configure(maximum = max(total, 1), value = fait)
            self.lbl_etat.configure(text = f"Upload {fait}/{total}")
        elif type_ev == "done":
            self._log(ev[1], "ok")
            self.lbl_etat.configure(text = ev[1])
        elif type_ev == "error":
            self._log(ev[1], "err")
            self.lbl_etat.configure(text = ev[1])
        elif type_ev == "ready":
            self.traitement_en_cours = False
            self.btn_lancer.configure(state = "normal")
        elif type_ev == "session":
            self._verifier_session()

    def _log(self, texte, tag = None):
        self.journal.configure(state = "normal")
        self.journal.insert("end", texte.rstrip("\n") + "\n", tag or ())
        self.journal.see("end")
        self.journal.configure(state = "disabled")

    def run(self):
        self.fenetre.mainloop()


class _RedirectionVersFile:
    """Capture les print() du thread de travail et les envoie au journal."""

    def __init__(self, file_evenements, stdout_reel):
        self.file = file_evenements
        self.stdout_reel = stdout_reel
        self._tampon = ""

    def write(self, texte):
        self.stdout_reel.write(texte)
        self._tampon += texte
        while "\n" in self._tampon:
            ligne, self._tampon = self._tampon.split("\n", 1)
            if ligne.strip():
                self.file.put(("log", ligne))

    def flush(self):
        self.stdout_reel.flush()


if __name__ == "__main__":
    Application().run()
