# Inference Rules

1. [Confidence Specification](#conf)
2. [Argument Ontology Specification](#inst)

<a name="conf"></a>
## Confidence Specification

Confidence is the mechanism by which predicates are assigned to the domain 
of all things true, false, or uncertain.

Every predicate has a confidence tag. 

If no explicit confidence tag is given, the predicate is assigned to the `true` class:

`like(emora, avengers)`

To specify a predicate is false, use the `not` monopredicate:

`not(like(emora, avengers))`

To specify a predicate as uncertain, use the `maybe` monopredicate:

`maybe(like(emora, avengers))`

#### Requests

Requests are automatically assigned to the `uncertain` class and no explicit confidence needs to be specified:

`request_truth(emora, like(user, avengers))`

#### Existence

Sometimes, it is useful to define a rule that matches if some predicate exists and it does not matter what
confidence class it belongs to.

To do this, use the `_exists` monopredicate:

`_exists(like(user, avengers))`

For instance, if we wanted to check that emora has asked a certain question 
regardless of whether it was answered or not, we do:

```
request_truth(emora, l/like(user, avengers))
_exists(l)
->
...
```

<a name="inst"></a>
## Argument Ontology Specification

It can be useful to discriminate what type of instance fills a particular argument in a predicate when 
making a dialogue decision.

For instance, you may want to trigger a rule if we receive a specific subtype of food that the user likes, but not
if we receive the entity class itself:

```
like(user, f/food())
_specific(f)
->
favorite(s/food())
possess(user, s)
request_truth(emora, be(s, f))
```

This rule produces the request `Is <f> your favorite food?` given that the user likes `f` and
would match `like(user, apple)` but not `like(user, food)`.

Similarly, you may want to trigger a rule in the opposite case, when the entity class matches an argument
rather than a specific subtype:

```
like(user, s/sport())
category(s)
->
favorite(st/sport())
possess(user, st)
be(st, si/sport())
request(emora, si)
```

This rule produces the request `What is your favorite sport?` given that the user likes sports in general
and would match `like(user, sport)` but not `like(user, basketball)`.