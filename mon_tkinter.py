import tkinter as tk
from tkinter import ttk
from mon_os import listage_wav_jpg
from mon_selenium import Pilotage
from selenium import webdriver
import uuid
import threading

_1 = "geoffroy.daumer@outlook.fr"
_2 = "kirbycath61"
_3 = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon"
folder_dict = {}
folder_list = []
Dossier_en_cours = False
isconnected = False

def tkinter():


    def liste_dattente():


        pass

    def recolte_donnees():
        
        EMAIL = email.get()
        MDP = mdp.get()
        chemin_dossier = rf"{chemin.get()}"

        
        return EMAIL, MDP, chemin_dossier


    class Dossier:


        def __init__(self, email, mdp, chemin):


            self.email = email
            self.mdp = mdp
            self.chemin = chemin

        def mettre_en_liste_attente(self):

            pass

        def traiter_le_dossier(self, pilote):


            Dossier_en_cours = True

            label5 = tk.Label(text = f"Dossier en cours de traitement... Email = {self.email}, Chemin_dossier = {self.chemin}")
            label5.grid(row = 5, column = 0, columnspan = 5)

            liste_wav, liste_jpg = listage_wav_jpg(chemin_dossier = self.chemin)

            a = 0

            for i in range(len(liste_wav)):
                

                nom_wav = liste_wav[i]
                nom_jpg = liste_jpg[i]
                
                pilote.loop(self.chemin, nom_wav, nom_jpg)
                a += 1 

            label5.destroy()

            dossier_en_cours = False
            
                

    def convert():
        

        # Récupération des données
        
        EMAIL, MDP, chemin_dossier = recolte_donnees()


        # Instanciation d'une classe dossier

        dossier_name = str(uuid.uuid4())
        folder_dict[dossier_name] = Dossier(EMAIL, MDP, chemin_dossier)


        # Est-ce qu'il y a un dossier en cours de traitement ?

        if Dossier_en_cours:
            

            # Mise à jour de la liste d'attente

            folder_list.append(folder_dict[dossier_name])
            

            # Liste d'attente

            
            if bool(folder_list):
                

                label8 = tk.Label(text = "Liste d'attente")
                label8.grid(row = 8, columnspan = 5)
                
                i = 9

                for folder in folder_list:

                    my_label = tk.Label(text = f"Dossier : {folder.chemin_dossier}, Email : {folder.email}")
                    my_label.grid(row = i, columnspan = 5)
                    
                    i += 1




        else:

            
            # Connexion

            driver = webdriver.Firefox()
            connector_bandcamp = Pilotage(driver, email = folder_dict[dossier_name].email, mdp = folder_dict[dossier_name].mdp)


            # Traitement du dossier

            folder_dict[dossier_name].traiter_le_dossier(connector_bandcamp) # On est connecté
            email_avant = folder_dict[dossier_name].email


            # Check si la liste d'attente est encore remplie

            while folder_list:


                # On prend le premier élément de la liste

                dossier_a_traiter = folder_list.pop(0)

                if dossier_a_traiter.email == email_avant:


                    dossier_a_traiter.traiter_le_dossier(connector_bandcamp)

                else:
                    
                    driver = webdriver.Firefox()
                    connector_bandcamp = Pilotage(driver, email = folder_dict[dossier_name].email, mdp = folder_dict[dossier_name].mdp)

                    dossier_a_traiter.traiter_le_dossier(connector_bandcamp)






    # Create a window

    window = tk.Tk()
    window.title("Insertion Bandcamp automatique")
    window.geometry("1200x800")


    label1 = tk.Label(text = "Entrez vos identifiants Bandcamp", font = ("Arial Bold", 15))
    label1.grid(row = 0, column = 0)


    # Email

    email = tk.StringVar()
    label2 = tk.Label(text = "Email", font = ("Arial Bold", 11))
    label2.grid(row = 1, column = 0, sticky = "w")

    entry2 = tk.Entry(font = 1, textvariable = email, width = 35)
    entry2.grid(row = 1, column = 1, stick = "w")


    #  MDP

    mdp = tk.StringVar()
    label3 = tk.Label(text = "Mot de passe", font = ("Arial Bold", 11))
    label3.grid(row = 2, column = 0, sticky = "w")

    entry3 = tk.Entry(font = 15, textvariable = mdp, width = 35, show = "*",)
    entry3.grid(row = 2, column = 1, sticky = "w")


    # Chemin dossier

    chemin = tk.StringVar() 
    label4 = tk.Label(text = "Veuillez insérer le chemin du dossier à importer", font = ("Arial Bold", 15))
    label4.grid(row = 3, column = 0)

    entry4 = tk.Entry(font = 15, textvariable = chemin, width = 60)
    entry4.grid(row = 3, column = 1)


    # Boutton

    button = tk.Button(text = "Entrer", command = threading.Thread(target = convert).start)
    button.grid(row = 4, column = 0)

    # Run

    window.mainloop()


# EMAIL = "geoffroy.daumer@outlook.fr"
# MDP = "kirbycath61"

# chemin_dossier = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon"

tkinter()