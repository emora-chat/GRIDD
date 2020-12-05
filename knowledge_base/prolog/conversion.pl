type(person,entity).
type(enemy,predicate).
type(expression,object).
type(comedy,genre).
type(var,predicate).
type(entity,object).
type(time,predicate).
type(pre,predicate).
type(genre,entity).
type(love,like).
type(expr,predicate).
type(is_type,predicate).
type(starwars,movie).
type(john,person).
type(like,predicate).
type(now,entity).
type(happy,predicate).
type(predicate,object).
type(like,positive).
type(post,predicate).
type(type,predicate).
type(sad,predicate).
type(reason,predicate).
type(positive,predicate).
type(bot,entity).
type(is_genre,predicate).
type(past,entity).
type(mary,person).
type(action,genre).
type(movie,entity).
type(avengers,movie).
type(future,entity).
predinst(reason(108,115),116).
predinst(love(mary,avengers),108).
predinst(reason(104,112),120).
predinst(is_genre(starwars,action),112).
predinst(is_genre(avengers,comedy),115).
predinst(like(john,starwars),104).

%---- Query -------

% type(A,genre), type(B,movie), type(I,person),
% ((predinst(C,E),functor(C,D,_),type(D,is_genre));(predinst(C,E),functor(C,is_genre,_))), arg(1,C,B), arg(2,C,A),
% ((predinst(F,H),functor(F,G,_),type(G,like));(predinst(F,H),functor(F,like,_))), arg(1,F,I), arg(2,F,B),
% ((predinst(J,L),functor(J,K,_),type(K,reason));(predinst(J,L),functor(J,reason,_))), arg(1,J,H), arg(2,J,E).

% (predinst(F,H),functor(F,G,_),type(G,like));(predinst(F,H),functor(F,like,_)).