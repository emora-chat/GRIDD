# Semantic Representation

1. [Instantiative Instance](#ii)
2. [Intransitive Verb](#iv)
3. [Transitive Verb](#tv)
4. [Indirect Object](#io)
5. [Adjective](#adj)
6. [Referential Instance](#ri)
7. [Possessive](#poss)
8. [Prepositional Phrase](#pp)
9. [Adverbial](#adv)
10. [Generics](#g)
11. [Groups](#gr)
12. [Habitual](#h)
13. [Superlative](#s)
14. [Modality](#m)
15. [Negation](#n)
16. [Question](#q)


<a name="ii"></a>
### Instantiative Instance 

*"A house"*

```
house()
```

`house` is an entity type that is instantiated to represent a new unique house object.

*"A purchase"*

```
buy()
```

`buy` is an event type. Even though the `buy` frame expects subject and object arguments, a buying event can be instantiated without this information. Commonsense inference will expand the `buy` event to its fully specified predicate frame including a subject and object. 

Note that a `buy` event can be expressed in language as either a noun or a verb. In either case, it denotes a change of world state, which we represent logically as an event predicate.

<a name="iv"></a>
### Intransitive Verb 

*"I ran."*

```
r/run(me)
time(r, past)
```

Most intransitive verbs are eventive monopredicates. They represent some subject acting to change the world state. Note that all event predicates are grounded in some timespan or timepoint with the `time` predicate.

<a name="tv"></a>
### Transitive Verb 

*"I bought a house."*

```
b/buy(me, house())
time(b, past)
```

Eventive transitive verbs represent a subject acting on an object to change the world state at some time.

*"Avengers stars Chris Evans."*

```
star(avengers, chris_evans)
```

Some transitive verbs represent logical relationships between concepts. Relationship predicates are distinct from event predicates as they are not necessarily grounded in time and do not directly represent a change in the world state.

*"I like you."*

```
b/like(me, you)
time(b, now)
```

Transitive verbs representing relationships can still be grounded in time, without being an event predicate. In this example, the `like` predicate represents a property of the relationship between the two people, but does not represent any state change and is therefore not an event. The time grounding of such relationships is often determined by commonsense knowledge of the type of relationship.

<a name="io"></a>
### Indirect Object 

*"I bought a house for Sally."*

```
b/buy(me, house())
recipient(b, Sally)
time(b, past)
```

Indirect objects are represented using bipredicates between the event predicate instance and the indirect object itself. Logically, there is a relationship between the `buy`-ing event and Sally, represented with the `recipient` predicate.

*"I like Sally for you."*

```
l/like(me, Sally)
beneficiary(l, you)
```

As with most linguistic expressions, the same indirect object construction may refer to a variety of logical relationships, depending on the context.

Although rare, indirect objects might denote additional relationships between concepts, rather than additional event information. In this example, there is no event and no recipient of some object, unlike previously. Instead, logical relationships are being established between 3 people. 

<a name="adj"></a>
### Adjectives 

*"a red house"*

```
red(house())
```

Properties of objects are represented by a monopredicate. Properties represent state information of the predicate's subject. Such properties are not necessarily grounded in time, but may be time-grounded if the property does not always hold.

*"Atlanta is hot"*

```
hot(Atlanta)
```

Be verb constructions also often represent properties.

*"a destroyed car"*

```
destroy(object(), car())
```

Sometimes adjectives can indicate the occurrence of an event. In these cases, the representation should follow the eventive predicate form, rather than the standard property.

*"a red house used to be brown"*

```
time(red(h/house()), now)
time(brown(h), past)
```

Some expressions denote a difference of state without referring to any causal event. This example expresses a color property of the house at two points in time, but does not directly express any event creating the change.

*"an Atlanta summer"*

```
in(summer(), Atlanta)
```

Adjective constructions can also denote a logical relationship between two concepts.

*"an Atlanta outbreak"*

```
in(o/break_out(), Atlanta)
time(o, timepoint())
```

Similar to the above example, this expression represents a relationship between the entity `Atlanta` and an `outbreak` event. Note that the `outbreak` event must be logically grounded in some time, although there is no information about the outbreak time to any other timepoint.

*"a coronavirus outbreak"*

```
o/break_out(coronavirus)
time(o, timepoint())
```

In this case, the adjective construction represents a subject relationship between the `outbreak` event and its `coronavirus` argument.

<a name="ri"></a>
### Referential Instance 

*"The house"*

```
h:<h/house()>
```

This representation is used to construct a logical reference to an existing concept. The inference process of reference resolution is used to resolve a reference to its referent, at which point the reference and referent concepts merge. 

Upon instantiation of the reference, the reference is unresolved. It may be the case that its referent is resolvable or unresolvable due to ambiguity or non-existence. 

*"The great bridge in London"*

```
b:<in(b/bridge(), London) property(b, great)>
```

References may have many constraints. All constraints must be true for referents to be valid and must be specified within the angled brackets.

*"The great bridge in London is falling"*

```
f/fall(b:<in(b/bridge(), London) property(b, great)>)
time(f, now)
```

References are valid subjects and objects of other predicates. Note that constraints on what the reference resolves to are denoted within the angled brackets, whereas propositions about the intended referent are denoted in the standard manner. In this example, `fall` is an event predicate that is claimed to be happening to the `bridge` referent.

*"The fall"*

```
f:<f/fall()>
```

Event predicates can be references too.

<a name="poss"></a>
### Possessives 

*"Mary's dog"*

```
d:<own(Mary, d/dog())
```

This possessive expression denotes ownership between Mary and the dog. Since all possessive expressions are referential, we construct a logical reference to allow later reference resolution.

*"My aunt"*

```
p:<aunt(p/person(), me)>
```

Possessive expressions often do not denote ownership. In this case, the possessive expression indicates a relationship between two people.

*"Georgia's weather"*

```
w:<in(w/weather(), Georgia)>
```

There is a lot of variety in the relationships between concepts introduced by possessive language.

<a name="pp"></a>
### Prepositional Phrase 

*"I bought a house in London."*

```
b/buy(me, h/house())
location(h, London)
time(b, past)
```

Prepositional phrases almost always represent logical relationships between concepts.

*"I bought a house in London."*

```
b/buy(me, h/house())
location(b, London)
time(b, past)
```

** Fun fact: this sentence is syntactically ambiguous!

Relationship predicates can operate on predicate instances as well as entities. In this interpretation of the sentence, the `buy`-ing event happened in London, rather than the house being located in London.

*"I am in a play"*

```
p/participate(me, play())
time(p, now)
```

There are a variety of relationship predicates that can be indicated by the same prepositional marker, depending on the context. In this example, the `in` preposition is not indicative of a `location` predicate, unlike the previous examples. Rather, it expresses that the person is `participate`-ing in an event, namely a `play`.

*"We are in agreement"*

```
a/agree(us)
time(a, now)
```

Prepositional phrases can also be used to express the occurrence of an event. 

*"He was proud of her."*

```
p/proud(he)
cause(her, p)
time(p, past)
```

This expression denotes both a property of `he` and a relationship between `he` and `her`, using the prepositional phrase.

*"entrance of Kroger"*

```
part(entrance, Kroger)
```

This is yet another example of the variety of relationship predicates that a single prepositional marker - in this case `of` - can indicate, depending on the context.

<a name="adv"></a>
### Adverbials 

*"I ran quickly."*

```
r/run(me)
time(r, past)
qualifier(r, quick)
```

Adverbial statements indicate some quality of the concept they are modifying.

*"I bought a house yesterday."*

```
b/buy(me, house())
time(b, yesterday)
```

Time expression adverbs can denote some specific time relationship between a predicate and the time it is grounded in.

*"She found a toy where he left a stick."*

```
f/find(she, toy())
time(f, past)
l/leave(he, stick())
time(l, past)
location(f, l)
```

Adverbs can denote specific relationships between predicates.


<a name="gr"></a>
### Groups

*""*

<a name="g"></a>
### Generics 

*"I like dogs."*

```
g/group() 
type(g, dog)

member_of(x, g) -> like(me, x)
```



*"Puppies are cute."*

```
x/puppy() -> cute(x)
```

*"I like hiking in Atlanta."*

```
h/hike(me)
location(h, Atlanta)
->
like(me, h)
```


<a name="h"></a>
### Habituals 

*"I swim every day."*

*"He runs."*

<a name="s"></a>
### Superlatives 

*"My favorite color is red."*

<a name="m"></a>
### Modality 

*"You should buy a house."*

*"I can read."*

*"She is always happy."*

<a name="n"></a>
### Negation 

*"I didnt buy a house."*

*"She is never happy."*

<a name="q"></a>
### Questions 

*"What color is your favorite"*

*"Where did you go last weekend"*

*"Why did you call me"*

*"When do you want to leave"*

*"How did you do on the test"*

*"Did you watch Avengers"*

*"Are you sure"*
