"""Desenho minimo de graficos (linhas e barras) sobre o escritor de PNG do
spectro.py. Sem matplotlib. Rotulos so ASCII (a fonte embutida nao tem acento).
Compartilhado pelos scripts das subpastas de G10-FIGURAS-CANAL."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from spectro import write_png, draw_text  # noqa: E402

CORES = [(26, 74, 158), (200, 40, 40), (30, 140, 60), (230, 140, 20),
         (120, 60, 160), (90, 90, 90)]
TEXTO = (35, 35, 35)
GRADE = (222, 222, 222)
EIXO = (60, 60, 60)


class Fig:
    def __init__(self, w=1000, h=560, xlim=(0, 1), ylim=(0, 1), xlabel='', ylabel='',
                 titulo='', xticks=None, yticks=None, esq=84, dir_=24, topo=84, base=70):
        self.w, self.h = w, h
        self.img = np.full((h, w, 3), 255, np.uint8)
        self.x0, self.x1, self.y0, self.y1 = esq, w - dir_, topo, h - base
        self.xlim, self.ylim = xlim, ylim
        self.leg = 0
        self.leg_baixo = False
        if xticks is None:
            xticks = np.linspace(xlim[0], xlim[1], 6)
        if yticks is None:
            yticks = np.linspace(ylim[0], ylim[1], 6)
        for v in xticks:
            x = self.px(v)
            self.img[self.y0:self.y1, x:x + 1] = GRADE
            draw_text(self.img, x - 12, self.y1 + 10, self.fmt(v), TEXTO, 1)
        for v in yticks:
            y = self.py(v)
            self.img[y:y + 1, self.x0:self.x1] = GRADE
            draw_text(self.img, self.x0 - 50, y - 3, self.fmt(v), TEXTO, 1)
        draw_text(self.img, (self.x0 + self.x1) // 2 - 6 * len(xlabel), self.y1 + 34, xlabel, TEXTO, 2)
        draw_text(self.img, self.x0 - 50, self.y0 - 28, ylabel, TEXTO, 2)
        draw_text(self.img, self.x0 - 50, 10, titulo, TEXTO, 2)
        self.frame()

    @staticmethod
    def fmt(v):
        return ('%d' % round(v)) if abs(v - round(v)) < 1e-6 else ('%.1f' % v)

    def px(self, x):
        return int(self.x0 + (x - self.xlim[0]) / (self.xlim[1] - self.xlim[0]) * (self.x1 - self.x0))

    def py(self, y):
        return int(self.y1 - (y - self.ylim[0]) / (self.ylim[1] - self.ylim[0]) * (self.y1 - self.y0))

    def frame(self):
        im = self.img
        im[self.y0:self.y1, self.x0:self.x0 + 1] = EIXO
        im[self.y0:self.y1, self.x1 - 1:self.x1] = EIXO
        im[self.y1:self.y1 + 1, self.x0:self.x1] = EIXO
        im[self.y0:self.y0 + 1, self.x0:self.x1] = EIXO

    def clipy(self, y):
        return min(max(y, self.y0), self.y1 - 1)

    def line(self, xs, ys, cor, larg=1, pontos=False):
        xs, ys = list(xs), list(ys)
        for i in range(len(xs) - 1):
            a, b, c, d = self.px(xs[i]), self.clipy(self.py(ys[i])), self.px(xs[i + 1]), self.clipy(self.py(ys[i + 1]))
            n = max(abs(c - a), abs(d - b), 1)
            for k in range(n + 1):
                x, y = a + (c - a) * k // n, b + (d - b) * k // n
                self.img[max(self.y0, y - larg):min(self.y1, y + larg + 1), min(max(x, self.x0), self.x1 - 1)] = cor
        if pontos:
            for x, y in zip(xs, ys):
                X, Y = self.px(x), self.clipy(self.py(y))
                self.img[max(self.y0, Y - 3):Y + 4, max(self.x0, X - 3):X + 4] = cor

    def vline(self, x, cor, larg=0):
        X = self.px(x)
        self.img[self.y0:self.y1, X:X + 1 + larg] = cor

    def legenda(self, texto, cor, x=None, y=None):
        lx = self.x0 + 14 if x is None else x
        ly = (self.y0 + 12 + 16 * self.leg) if y is None else y
        if self.leg_baixo and y is None:
            ly = self.y1 - 20 - 16 * self.leg
        self.img[ly + 2:ly + 8, lx:lx + 18] = cor
        draw_text(self.img, lx + 26, ly, texto, TEXTO, 1)
        self.leg += 1

    def salva(self, path):
        write_png(path, self.img)
