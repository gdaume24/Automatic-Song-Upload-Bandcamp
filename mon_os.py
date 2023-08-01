import os


# folder_path = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon"
# chemin_fichier = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon\Archie Bell & The Drells - Dont Let Love Get You Down.wav"
# chemin_image = r"C:\Users\geoff\OneDrive - yncréa\Documents\pro\ordi manu\essai musique pithon\Archie Bell & The Drells - Dont Let Love Get You Down .jpg"
# track_name = "Archie Bell & The Drells - Dont Let Love Get You Down"
# artiste = "Archie Bell & The Drells"



def listage_wav_jpg(chemin_dossier):
   
    liste_fichiers = os.listdir(chemin_dossier)
    liste_wav = [file for file in liste_fichiers if file.endswith('.wav')]
    liste_jpg = [file for file in liste_fichiers if file.endswith('.jpg')] 
    liste_wav.sort()
    liste_jpg.sort()
   
    if len(liste_wav) != len(liste_jpg):

        print(*liste_wav, sep = "\n")
        print("\n"*4)
        print(*liste_jpg, sep = "\n")

        raise Exception(f"Erreur. Nombre de fichiers .wav et .jpg différent dans le dossier, \n longueur liste .wav = {len(liste_wav)} \n longueur liste .jpg = {len(liste_jpg)}")

    return liste_wav, liste_jpg


