from math import *
from random import *
from typing import *
import pyxel, os


# Calcul de la taille de l'écran
with os.popen("xwininfo -root | grep -Po '(Width|Height): \K.*'", "r") as f:
    l = list(map(lambda x: x.strip(), f.readlines()))
    if len(l) == 0:
        # Ca n'a pas marché
        SCREEN_W = 1900
        SCREEN_H = 980
    else:
        SCREEN_W = int(l[0]) - 20
        SCREEN_H = int(l[1]) - 100


#############
# variables #
#############

# variables de système
hold_time = 6  # frames
repeat_time = 2  # frames

# variables de jeu

# SPELEOLOGUE
periode_flash_perso = 3
# coordonees du speleologue (en croisements de couloirs)
speleo_x = 0
speleo_y = 0

# dimensions du labyrinthe (en croisements de couloirs)
W = 16
H = 16

# coordonnees de la fenetre dans le labyrinthe (en cases)
fenetre_x = 0
fenetre_y = 0
# ratio d'agrandissement
fenetre_ratio = 2
# taille de la fenetre (en px)
fenetre_w = min(16 * 33, SCREEN_W, 16 * (2 * W + 1))
fenetre_h = min(16 * 33, SCREEN_H, 16 * (2 * H + 1))

# liste de coordonnees des monstres
monstre_liste = []
pioche_liste = []  # TODO: ajouter des pioches pour casser des murs


# Pour la génération du labyrinthe
muter_laby = False  # TODO: ajouter la possibilité de modifier le labyrinthe pour le rendre imparfait

victoire = False
game_over = False
random_positioning = True  # Choisir si le coffre se place au hasard (mais loin) ou en bas à droite du laby
deplacements_possibles = {"l": (-1, 0), "r": (1, 0), "u": (0, -1), "d": (0, 1)}
distance_min = 40  # Distance min de la sortie à l'entrée


# Couleurs
NOIR = 0
B_MARINE = 1
VIOLET = 2
B_CYAN = 3
MARRON = 4
B_ROI = 5
B_CLAIR = 6
BLANC = 7
MAUVE = 8
ORANGE = 9
JAUNE = 10
TURQUOISE = 11
B_CIEL = 12
GRIS = 13
ROSE = 14
BEIGE = 15

apostrophe = "'"

DEBUG = True

##############################
#          Labyrinthe        #
##############################


class Case:
    def __init__(self, x, y):
        self.__voisines__ = {"u": None, "d": None, "l": None, "r": None}
        self.__linked__ = {"u": False, "d": False, "l": False, "r": False}
        self.visite = False
        self.dist_to_source = -1
        self.contenu = []
        self.__x = x
        self.__y = y

    @property
    def x(self):
        return self.__x

    @property
    def y(self):
        return self.__y

    @property
    def left(self):
        return self.__voisines__["l"]

    @property
    def right(self):
        return self.__voisines__["r"]

    @property
    def up(self):
        return self.__voisines__["u"]

    @property
    def down(self):
        return self.__voisines__["d"]

    @left.setter
    def left(self, value):
        self.__voisines__["l"] = value

    @right.setter
    def right(self, value):
        self.__voisines__["r"] = value

    @up.setter
    def up(self, value):
        self.__voisines__["u"] = value

    @down.setter
    def down(self, value):
        self.__voisines__["d"] = value

    @property
    def move_left(self):
        return self.__linked__["l"]

    @property
    def move_right(self):
        return self.__linked__["r"]

    @property
    def move_up(self):
        return self.__linked__["u"]

    @property
    def move_down(self):
        return self.__linked__["d"]

    @move_left.setter
    def move_left(self, v):
        self.__linked__["l"] = v

    @move_right.setter
    def move_right(self, v):
        self.__linked__["r"] = v

    @move_up.setter
    def move_up(self, v):
        self.__linked__["u"] = v

    @move_down.setter
    def move_down(self, v):
        self.__linked__["d"] = v

    @property
    def voisines(self):
        return list(filter(lambda x: x is not None, self.__voisines__.values()))

    @property
    def voisines_visitees(self):
        return list(
            filter(lambda x: x is not None and x.visite, self.__voisines__.values())
        )

    @property
    def voisines_non_visitees(self):
        return list(
            filter(lambda x: x is not None and not x.visite, self.__voisines__.values())
        )

    def link(self, other, r=True):
        if other in self.__voisines__.values():
            i = self.__voisines__.items()
            k, v = list(map(lambda x: x[0], i)), list(map(lambda x: x[1], i))
            self.__linked__[k[v.index(other)]] = True
            if r:
                other.link(self, False)
        else:
            print("ERROR", self, other)
            raise ValueError("La case n'est pas une case voisine")

    @property
    def accessibles(self):
        return [
            self.__voisines__[d] for d in self.__voisines__.keys() if self.__linked__[d]
        ]

    @property
    def accessibles_visites(self):
        return [
            self.__voisines__[d]
            for d in self.__voisines__.keys()
            if self.__linked__[d] and self.__voisines__[d].visite
        ]

    @property
    def accessibles_non_visites(self):
        return [
            self.__voisines__[d]
            for d in self.__voisines__.keys()
            if self.__linked__[d] and not self.__voisines__[d].visite
        ]

    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        s = ""
        if self.contenu == []:
            s += "None"
        else:
            s += "/".join(self.contenu)
        s += f"({self.x},{self.y})"
        return s


##############################
# fonctions d'initialisation #
##############################


def in_laby(x: int, y: int, w: int, h: int) -> bool:
    """Cherche si la case (x,y) est dans le labyrinthe"""
    return 0 <= x < w and 0 <= y < h


def debug(*args, **kwargs):
    if DEBUG:
        print(*args, **kwargs)


def dbg_links(l):
    for j in range(H):
        for i in range(W):
            debug(
                f"{'.' if l[j][i].move_left else ' '}{[' ','.',apostrophe,':'][int(l[j][i].move_up)*2+int(l[j][i].move_down)]}{'.' if l[j][i].move_right else ' '}",
                end=" ",
            )
        debug()
    debug()


def laby_init(w: int, h: int) -> list[list[int]]:
    """Cette fonction genere un labyrinthe parfait.
    Entree : Les dimensions w et h en cases du labyrinthe
    Sortie: Le labyrinthe généré
    """

    # Fonctions aux utiles
    def dbg_visite():
        for j in range(h):
            for i in range(w):
                if laby[j][i].visite:
                    debug("X", end="")
                else:
                    debug(".", end="")
            debug()
        debug()

    def dbg_dist_to_source():
        for j in range(h):
            for i in range(w):
                debug(str(laby[j][i].dist_to_source) + "  ", end="")
            debug()
        debug()

    def gen_point_ok(pos: tuple[int]) -> bool:
        c = laby[pos[1]][pos[0]]
        return not c.visite and len(c.voisines_visitees) > 0

    def suiv(pos):  # -> tuple[int] | None:
        if pos[0] == w - 1:
            if pos[1] == h - 1:
                return None
            else:
                return (0, pos[1] + 1)
        else:
            return (pos[0] + 1, pos[1])

    laby = [[Case(i, j) for i in range(w)] for j in range(h)]
    for i in range(w):
        for j in range(h):
            deplacements_faisables = list(
                filter(
                    lambda x: in_laby(i + x[1][0], j + x[1][1], w, h),
                    deplacements_possibles.items(),
                )
            )
            for d, (di, dj) in deplacements_faisables:
                laby[j][i].__voisines__[d] = laby[j + dj][i + di]

    last_pos = (0, 0)
    courante = laby[0][0]
    courante.dist_to_source = 0
    stop = False
    while not stop:
        suivantes = courante.voisines_non_visitees
        courante.visite = True
        if len(suivantes) == 0:
            # On cherche un nouveau point de génération
            found = False
            while not (found or stop):
                if gen_point_ok(last_pos):
                    courante = laby[last_pos[1]][last_pos[0]]
                    suivante = choice(courante.voisines_visitees)
                    courante.link(suivante)
                    courante.dist_to_source = suivante.dist_to_source + 1
                    found = True
                else:
                    last_pos = suiv(last_pos)
                    if last_pos is None:
                        stop = True
        else:
            suivante = choice(suivantes)
            courante.link(suivante)
            suivante.dist_to_source = courante.dist_to_source + 1
            courante = suivante

    if random_positioning:
        max_dist = 0
        case_de_sortie = laby[0][0]
        for j in range(h):
            for i in range(w):
                if laby[j][i].dist_to_source >= max_dist:
                    max_dist = laby[j][i].dist_to_source
                    case_de_sortie = laby[j][i]
        case_de_sortie.contenu = ["sortie"]
    else:
        laby[-1][-1].contenu = ["sortie"]
    # dbg_links(laby)
    dbg_dist_to_source()
    return laby


############################
# fonctions intermediaires #
############################


def speleo_mvt(x, y):
    if pyxel.btnp(pyxel.KEY_RIGHT, hold_time, repeat_time):
        if in_laby(x + 1, y, W, H) and laby[y][x].move_right:
            x += 1
    elif pyxel.btnp(pyxel.KEY_LEFT, hold_time, repeat_time):
        if in_laby(x - 1, y, W, H) and laby[y][x].move_left:
            x -= 1
    elif pyxel.btnp(pyxel.KEY_DOWN, hold_time, repeat_time):
        if in_laby(x, y + 1, W, H) and laby[y][x].move_down:
            y += 1
    elif pyxel.btnp(pyxel.KEY_UP, hold_time, repeat_time):
        if in_laby(x, y - 1, W, H) and laby[y][x].move_up:
            y -= 1
    return x, y


def fenetre_mvt(x, y):
    if pyxel.btnp(pyxel.KEY_D, hold_time, repeat_time):
        if in_laby(x + fenetre_w // 16, y, 2 * W + 1, 2 * H + 1):
            x += 1
    if pyxel.btnp(pyxel.KEY_Q, hold_time, repeat_time):
        if in_laby(x - 1, y, 2 * W + 1, 2 * H + 1):
            x -= 1
    if pyxel.btnp(pyxel.KEY_S, hold_time, repeat_time):
        if in_laby(x, y + fenetre_h // 16, 2 * W + 1, 2 * H + 1):
            y += 1
    if pyxel.btnp(pyxel.KEY_Z, hold_time, repeat_time):
        if in_laby(x, y - 1, 2 * W + 1, 2 * H + 1):
            y -= 1
    return x, y


#########################
#  fonctions de dessin  #
#########################


def dessin_perso():
    pyxel.blt(
        (2 * speleo_x + 1) * 16 - fenetre_x * 16,
        (2 * speleo_y + 1) * 16 - fenetre_y * 16,
        0,
        (pyxel.frame_count // periode_flash_perso % 4) * 16,
        48,
        16,
        16,
    )


def dessin_pioche(x, y):
    pyxel.blt((x - fenetre_x) * 16, (y - fenetre_y) * 16, 0, 0, 64, 16, 16)


def dessin_mur(x, y):
    pyxel.blt((x - fenetre_x) * 16, (y - fenetre_y) * 16, 0, 0, 0, 16, 16)


def dessin_mur_friable(x, y):
    pyxel.blt((x - fenetre_x) * 16, (y - fenetre_y) * 16, 0, 16, 0, 16, 16)


def dessin_couloir(x, y):
    pyxel.blt((x - fenetre_x) * 16, (y - fenetre_y) * 16, 0, 0, 16, 16, 16)


def dessin_porte(x, y):
    pyxel.blt(
        (x - fenetre_x) * 16,
        (y - fenetre_y) * 16,
        0,
        (9 - (pyxel.frame_count // 2 % 10)) * 16,
        32,
        16,
        16,
    )


def dessin_victoire():
    pyxel.rect(fenetre_w // 4, fenetre_h // 4, fenetre_w // 2, fenetre_h // 2, 10)


fonctions_dessin = {
    "sortie": dessin_porte,
    "porte": dessin_porte,
}

#########################
# fonctions principales #
#########################


def update():
    """mise a jour des variables 30 fois par seconde (toutes les frames)"""

    # pour avoir le droit de modifier les variables
    global speleo_x, speleo_y, fenetre_x, fenetre_y

    # mise a jour de la position du speleologue avec les fleches du clavier
    speleo_x, speleo_y = speleo_mvt(speleo_x, speleo_y)

    # mise a jour de la position de la fenetre avec les touches ZSQD
    fenetre_x, fenetre_y = fenetre_mvt(fenetre_x, fenetre_y)


def draw():
    """dessin 30 fois par seconde (toutes les frames)"""
    if victoire:
        dessin_victoire()
    elif game_over:
        dessin_game_over()
    else:
        # on remet l'ecran tout noir
        pyxel.cls(0)

        # dessin du labyrinthe
        for j in range(H):
            for i in range(W):
                # dessin du croisement de mur superieur gauche
                dessin_mur(2 * i, 2 * j)

                # dessin du couloir potentiel de gauche
                if laby[j][i].move_left:
                    dessin_couloir(2 * i, 2 * j + 1)
                else:
                    dessin_mur(2 * i, 2 * j + 1)

                # dessin du couloir potentiel du haut
                if laby[j][i].move_up:
                    dessin_couloir(2 * i + 1, 2 * j)
                else:
                    dessin_mur(2 * i + 1, 2 * j)

                # dessin du croisement de couloir sur lequel on est
                dessin_couloir(2 * i + 1, 2 * j + 1)

                # dessin du contenu potentiel du croisement de couloir
                for elt in laby[j][i].contenu:
                    fonctions_dessin[elt](2 * i + 1, 2 * j + 1)

        # dessin des murs en bas et à droite
        for i in range(2 * W + 1):
            dessin_mur(i, 2 * H)
        for j in range(2 * H):
            dessin_mur(2 * W, j)

        # dessin du speleologue
        dessin_perso()


# initialisation de la fenetre
pyxel.init(fenetre_w, fenetre_h, "LABYRINTHE", 30, None, fenetre_ratio)

# chargement des ressources
pyxel.load("res.pyxres")

# initialisation du labyrinthe
laby = laby_init(W, H)

# fonction qui fait tourner le jeu
pyxel.run(update, draw)
