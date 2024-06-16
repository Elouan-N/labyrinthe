from math import *
from random import *
import pyxel

pyxel.init(528, 528, "LABYRINTHE")
pyxel.load("res.pyxres")

#############
# variables #
#############

# variables de système
hold_time = 6  # frames
repeat_time = 2  # frames

# variables de jeu
speleo_x = 1
speleo_y = 1

fenetre_x = 0
fenetre_y = 0
fenetre_w = 528
fenetre_h = 528

monstre_liste = []
pioche_liste = []  # TODO: ajouter des pioches pour casser des murs

muter_laby = False  # TODO: ajouter la possibilité de modifier le labyrinthe pour le rendre imparfait
laby = []

##############################
# fonctions d'initialisation #
##############################


def laby_init(w: int, h: int) -> list[list[int]]:
    """Cette fonction genere un labyrinthe parfait.
    Entree : les dimensions w et h en cases du labyrinthe
    Sortie : la liste de listes avec un indice d'etat pour chaque case
        - 0 : couloir
        - 1 : mur
        - 2 : porte de sortie"""

    laby = [[1 for _ in range(w)] for _ in range(h)]

    x, y = 0, 0
    target = (0, 0)
    deplacements_possibles = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    deplacements_faisables = []
    for _ in range((w // 2) * (h // 2) - 1):
        laby[y * 2 + 1][x * 2 + 1] = 0
        deplacements_faisables = []
        for deplacement in deplacements_possibles:
            if (
                x + deplacement[0] in range(w // 2)
                and y + deplacement[1] in range(h // 2)
                and laby[(y + deplacement[1]) * 2 + 1][(x + deplacement[0]) * 2 + 1]
                == 1
            ):
                deplacements_faisables.append(deplacement)
        if deplacements_faisables != []:
            target = choice(deplacements_faisables)
            laby[y * 2 + 1 + target[1]][x * 2 + 1 + target[0]] = 0
            x += target[0]
            y += target[1]
        else:
            x, y = 0, 0
            while laby[y * 2 + 1][x * 2 + 1] != 1:
                x += 1
                if x == w // 2:
                    x = 0
                    y += 1
            if x == 0:
                laby[y * 2][x * 2 + 1] = 0
            elif y == 0:
                laby[y * 2 + 1][x * 2] = 0
            else:
                target = choice([(-1, 0), (0, -1)])
                laby[y * 2 + 1 + target[1]][x * 2 + 1 + target[0]] = 0
        laby[y * 2 + 1][x * 2 + 1] = 0
    laby[h - 2][w - 2] = 2
    return laby


############################
# fonctions intermediaires #
############################


def speleo_mvt(x, y):
    if pyxel.btnp(pyxel.KEY_RIGHT, hold_time, repeat_time):
        if x + 1 in range(fenetre_w) and laby[y][x + 1] == 0:
            x += 1
    if pyxel.btnp(pyxel.KEY_LEFT, hold_time, repeat_time):
        if x - 1 in range(fenetre_w) and laby[y][x - 1] == 0:
            x -= 1
    if pyxel.btnp(pyxel.KEY_DOWN, hold_time, repeat_time):
        if y + 1 in range(fenetre_h) and laby[y + 1][x] == 0:
            y += 1
    if pyxel.btnp(pyxel.KEY_UP, hold_time, repeat_time):
        if y - 1 in range(fenetre_h) and laby[y - 1][x] == 0:
            y -= 1
    return (x, y)


def fenetre_mvt(fenetre_x, fenetre_y):
    return (fenetre_x, fenetre_y)


#########################
#  fonctions de dessin  #
#########################


def dessin_perso():
    pyxel.rect(speleo_x * 16, speleo_y * 16, 16, 16, 11)
    pyxel.blt(
        speleo_x * 16 + fenetre_x, speleo_y * 16 + fenetre_x * 16, 0, 0, 48, 16, 16
    )


def dessin_pioche(x, y):
    pyxel.blt(x * 16 + fenetre_x, y * 16 + fenetre_x * 16, 0, 0, 64, 16, 16)


def dessin_mur(x, y):
    pyxel.rect(x * 16, y * 16, 16, 16, 0)
    pyxel.blt(x * 16, y * 16, 0, 0, 0, 16, 16)


def dessin_couloir(x, y):
    pyxel.rect(x * 16, y * 16, 16, 16, 7)
    pyxel.blt(x * 16, y * 16, 0, 0, 16, 16, 16)


def dessin_porte(x, y):
    pyxel.rect(x * 16, y * 16, 16, 16, 10)
    pyxel.blt(x * 16, y * 16, 0, (9 - (pyxel.frame_count // 2 % 10)) * 16, 32, 16, 16)


#########################
# fonctions principales #
#########################


def update():
    """mise a jour des variables 30 fois par seconde (toutes les frames)"""

    # pour avoir le droit de modifier les variables
    global speleo_x, speleo_y, fenetre_x, fenetre_y

    # mise a jour de la position du speleologue avec les fleches du clavier
    speleo_x, speleo_y = speleo_mvt(speleo_x, speleo_y)
    fenetre_x, fenetre_y = fenetre_mvt(fenetre_x, fenetre_y)


def draw():
    """dessin 30 fois par seconde (toutes les frames)"""

    # on remet l'ecran tout noir
    pyxel.cls(0)

    # pour chaque case de laby visible dans la fenetre, on dessine un carre et une image
    w = fenetre_w // 16
    h = fenetre_h // 16
    for i in range(h):
        for j in range(w):
            if laby[i + fenetre_y][j + fenetre_x] == 0:  # couloir
                dessin_couloir(j, i)
            elif laby[i + fenetre_y][j + fenetre_x] == 1:  # mur
                dessin_mur(j, i)
            elif laby[i + fenetre_y][j + fenetre_x] == 2:  # porte de sortie
                dessin_porte(j, i)

    # on dessine le personnage (carre et image), pour l'instant decorrele de la fenetre
    dessin_perso()


# initialisation du labyrinthe
laby = laby_init(33, 33)

# fonction qui fait tourner le jeu
pyxel.run(update, draw)
