# Démonstration de la Somme de la Série Géométrique

## Introduction
Cette démonstration explore la convergence de la somme d'une série géométrique infinie.

## Théorème
La somme d'une série géométrique infinie $S = a + ar + ar^2 + ar^3 + \dots$ converge si et seulement si la valeur absolue du rapport commun $r$ est strictement inférieure à 1 (c'est-à-dire $|r| < 1$).

La formule de la somme de cette série convergente est donnée par :
$$S = \frac{a}{1 - r}$$

Où :
* $a$ est le premier terme de la série.
* $r$ est la raison (le rapport commun).

## Démonstration par le calcul de la somme partielle
Nous considérons la somme partielle $S_n$ des $n$ premiers termes de la série :
$$S_n = a + ar + ar^2 + \dots + ar^{n-1}$$

La formule de la somme des $n$ premiers termes d'une suite géométrique est :
$$S_n = a \frac{1 - r^n}{1 - r}$$

Pour la somme infinie (la limite de $S_n$ lorsque $n \to \infty$) :
$$S = \lim_{n \to \infty} S_n = \lim_{n \to \infty} a \frac{1 - r^n}{1 - r}$$

Si $|r| < 1$, alors $\lim_{n \to \infty} r^n = 0$.
$$S = a \frac{1 - 0}{1 - r} = \frac{a}{1 - r}$$

**Condition de convergence :**
Pour que cette somme finie existe, il est nécessaire que la raison $r$ satisfasse la condition de convergence :
$$|r| < 1$$

**Conclusion :**
La série géométrique $S = a + ar + ar^2 + \dots$ converge si et seulement si la valeur absolue de la raison $r$ est strictement inférieure à 1 ($|r| < 1$). Si elle converge, la somme est donnée par $\frac{a}{1 - r}$.