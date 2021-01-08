

%----- ONT -------

type(like, like).
type(positive, positive).
type(love, love).
type(movie, movie).
type(genre, genre).
type(reason, reason).
type(property, property).

type(like, positive).
type(love, like).
type(love, positive).



%----- WKB --------

type(starwars, movie).
type(avengers, movie).
type(action, genre).
type(comedy, genre).

predinst(like(john, starwars), ljs).

predinst(genre(starwars, action), gsa).

predinst(reason(ljs, gsa), rlg).

predinst(love(mary, avengers), lma).

predinst(genre(avengers, comedy), gac).

predinst(reason(lma, gac), rlh).


%---- Query -------

% predinst(A, B), functor(A, C, _), arg(1, A, D), arg(2, A, E), type(C, like), type(E, movie), 
% predinst(F, G), functor(F, H, _), arg(1, F, E), arg(2, F, J), type(J, genre),
% predinst(K, L), functor(K, M, _), arg(1, K, B), arg(2, K, G), type(M, reason).



