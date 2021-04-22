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
10. [Modality](#m)
11. [Habitual](#h)
12. [Negation](#n)
13. [Question](#q)
14. [Plurals](#pl)
15. [Groups](#gr)
16. [Generics](#g)
17. [Comparatives](#s)

NOTE: In the following documentation, pronoun concepts (`me`, `you`, etc.) are used as placeholders within predicate structures. In practice, concept ids of valid concepts should be used instead, since pronouns have no actual meaning as concept ids. For example, in a human-computer interaction, a `user` concept would be appropriate to represent the user. 

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
&h<h/house()>
```

This representation is used to construct a logical reference to an existing concept. The inference process of reference resolution is used to resolve a reference to its referent, at which point the reference and referent concepts merge. 

Upon instantiation of the reference, the reference is unresolved. It may be the case that its referent is resolvable or unresolvable due to ambiguity or non-existence. 

*"The great bridge in London"*

```
&b<in(b/bridge(), London) great(b)>
```

References may have many constraints. All constraints must be true for referents to be valid and must be specified within the angled brackets.

*"The great bridge in London is falling"*

```
f/fall(&b<in(b/bridge(), London) great(b)>)
time(f, now)
```

References are valid subjects and objects of other predicates. Note that constraints on what the reference resolves to are denoted within the angled brackets, whereas propositions about the intended referent are denoted in the standard manner. In this example, `fall` is an event predicate that is claimed to be happening to the `bridge` referent.

*"The fall"*

```
&f<f/fall()>
```

Event predicates can be references too.

<a name="poss"></a>
### Possessives 

*"Mary's dog"*

```
&d<own(Mary, d/dog())>
```

This possessive expression denotes ownership between Mary and the dog. Since all possessive expressions are referential, we construct a logical reference to allow later reference resolution.

*"My aunt"*

```
&p<aunt(p/person(), me)>
```

Possessive expressions often do not denote ownership. In this case, the possessive expression indicates a relationship between two people.

*"Georgia's weather"*

```
&w<in(w/weather(), Georgia)>
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
quick(r)
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

<a name="m"></a>
### Modality 

*"Sally should buy a house."*

```
b/buy(Sally, house())
should(b)
```

Expressions of modality impose some manner of existence on the predicate that they are describing. In the given example, it is not indicating that Sally has bought or even will buy a house in the future; rather, it is meant to suggest the benefit or obligation that exists between Sally and her decision to purchase a house. 


<a name="h"></a>
### Habituals 

*"He runs."*

```
r/run(he)
time(r, present_habitual)
```

Habitual expressions indicate the frequently recurring occurrence of an event. Such expressions are grounded in the habitual-specific time `present_habitual`.

*"He used to swim."*

```
r/run(he)
time(r, past_habitual)
```

Habitual expressions do not necessarily indicate currently recurring events; instead, they can express events that were habitual in the past. For these cases, the `past_habitual` time is used.


*"He swims every day."*

```
r/swim(he)
time(r, every_day)
```

Habitual expressions can be more concretely defined, which is reflected in the `time` expression.


<a name="n"></a>
### Negation 

*"Sally didn't buy a house."*

```
b/buy(Sally, house())
not(b)
time(b, past)
```

Predicates can be negated directly. `not` is the frequent indication of negation, especially for predicates that exist in one specific timepoint (past, future, etc.). 
 
 *"Sally is never happy."*

```
b/happy(Sally)
not(b)
time(b, always)
```

Predicates can also be negated through specific adverbs which indicate the lack of existence, such as `never`. These adverbs operate over more than a specific timepoint, unlike `not`. As a result, such negation interacts with time specifications to produce the desired representation. In the above example, the `not` predicate negates the `happy(Sally)` event such that it means Sally is not happy. The time specification of `always` then transforms the meaning to Sally is always not happy (i.e. Sally is never happy).

*"Sally is not always happy."*

```
b/happy(Sally)
t/time(b, always)
not(t)
```

Different configurations of `not` and time specifications result in varied meanings. In this case, the `time` specification is negated, instead of the `happy` event. This results in the desired meaning of Sally not always being happy, which is distinct from the previous example.
 

<a name="q"></a>
### Questions 

*"Did you watch Avengers"*

```
&w<w/watch(you, Avengers) time(w, past)>
request_truth(me, w)
```

Questions are represented as references with a request predicate denoting the question as an explicit dialogue action. `request_truth` request predicates are used to signal a request made by the subject for the truth value of the predicate in the object position.

*"What musical instrument do you play"*

```
&m<play(you, m/musical_instrument())>
request(me, m)
```

Questions can also refer to a specific argument of a predicate structure. In this case, the request is not for the truth value of a constructed predicate, but rather for the concept that fills the argument in the given predicate structure. In this example, there is a request to resolve a `musical_instrument` argument with a `play` predicate as a constraint.

*"Where did you go last weekend"*

```
&l<go(you, l/location()) time(g, &w<last(w/weekend())>)>
request(me, l)
```

Where questions typically involves requesting a location resolution.

*"Why did you call me"*

```
&p<c/call(you, me) cause(p/predicate(), c)>
request(me, p)
```

Why questions request causes of predicates, represented using a `cause` predicate.

*"When do you want to leave"*

```
&t<w/want(you, leave(you)) time(w, t/timepoint())>
request(me, t)
```

When questions request resolution of the object of a `time` predicate.

*"How did you do on the test"*

```
&o<d/do(you) on(d, &t<t/test()>) quality(d, o/object()) time(d, past)>
request(me, o)
```

How questions request resolution of the object of a `quality` predicate.

<a name="pl"></a>
### Plurals

*"brown dogs"*

```
@brown_dog<brown(brown_dog/dog())>
```

This language expresses a group of concepts. The group is defined by a set of constraints. In this case, members satisfy group membership by being both `brown` and type `dog`.

```
brown_dog = (class);
brown(x/dog()) -> type(x, brown_dog);
```

This is the equivalent, fully expanded form of the above.


*"Brown dogs are cute."*

```
< 
  @brown_dog<brown(brown_dog/dog())>
  cute(brown_dog)
>
```

In this example, `brown_dog` represents the set of all dogs that are brown as specified by the group syntax. There is also a proposition that all dogs in this group are cute, represented by the `cute` monopredicate with `brown_dog` as its argument. 

Note that all propositions operating on groups must be declared within angled braces `<...>` along with the group definitions themselves. This is necessary to constrain what information is attributed to members of the group.

```
brown_dog = (class);
brown(x/dog()) -> type(x, brown_dog);
x/brown_dog() -> cute(x);
```

The above syntax is equivalent to the original syntax for representing *"Brown dogs are cute"*. It is the expanded form of the original group representation and demonstrates how a group representation can be obtained using implication rules. 

*"Big dogs chase scared cats."*

```
<
	@d<d/dog() big(d)>
	@c<c/cat() scared(c)>
	chase(d, c)
>
```

Sometimes a proposition involves multiple groups. All groups need to be declared in order to define such a proposition. 

*"Big dogs are fast and dangerous."*

```
<
	@d<d/dog() big(d)>
	fast(d)
	dangerous(d)
>
```

Multiple propositions can be specified at once for a single group or set of groups.

*"Do you like big dogs"*

```
&l <
  @big_dog<big_dog/dog() big(big_dog)>
  l/like(you, big_dog)
>
request_truth(me, l)
```

Questions can involve generic concepts, such as groups. The entire representation of the group and the claims made on the group is defined within the question reference. This allows the reference to resolve to the appropriate generic knowledge, if it exists.


<a name="gr"></a>
### Groups 

*"I like Sally and John"*

```
sally_and_john = (group)
type(sally, sally_and_john)
type(john, sally_and_john)

<l/like(me, sally_and_john)>
```

When multiple concepts are an argument to a single predicate, they form a group and the group is used as the argument. Groups are logically equivalent to types. In this example, there is one `like`-ing relationship between `me` and the group `sally` and `john`. 

Note that this is distinct from having separate `like`-ing relationships to `sally` and `john` each. However, both `sally` and `john` are considered objects of the single `like`-ing event. Representing `sally` and `john` as a group allows the group to be referenced again and any modifications to the predicates the group is involved in will appropriately affect `john` and `sally` synchronously.

*"People are destroying Earth."*

```
<
  d/destroy(person, Earth)
  time(d, now)
>
```

In this example, the `destroy` event is not generic. Only a single `destroy` event is being expressed, which everyone in the class `person` is participating in. Thus, the logical form for this example is similar to the previous case. Type `person` represents the group of all people who are collectively participating in the single `destroy` event.

<a name="g"></a>
### Generics 

*"I like hiking in Atlanta."*

```
<
  @atl_hike<atl_hike/hike(me) location(atl_hike, Atlanta)>
  like(me, atl_hike)
>
```

Generic verb usage is represented similarly to generalizations of entities made using plurals. In this example, *"hiking in Atlanta"* is represented as a type of event where the type definition includes a location constraint (`Atlanta`) and a subject constraint (`me`). The `like` predicate thus acts as a relationship between `me` and all events that satisfy the `atl_hike` type definition.

Similar to the expanded forms of plural expressions, the above example would be expanded as:

```
h/hike(me) location(h, Atlanta) -> type(h, atl_hike);
type(h, atl_hike) -> like(me, h);
```

<a name="s"></a>
### Comparatives 

*"My favorite color is red."*

```
<
  f/favorite(me, red) 
  out_of(f, color)
>
```

One common form of comparison is a superlative. 
Superlatives represent a single item that compares uniformly to a group that it is a part of.
The property of being superlative is represented using a property or relationship predicate on the outstanding item, such as `favorite(me, red)` representing the special quality of `red` in the example. The `out_of` predicate denotes the relationship between the outstanding quality and the group. As with all group representation, groups are represented using type concepts.

*"John is the fastest runner on the team."*

```
<
  f/fastest(John) 
  out_of(f, runner_on_team)
  @runner_on_team<on(runner_on_team/runner(), &t<t/team()>>
>
```

In this example, the superlative is declared with respect to a more complex group. By constructing a type definition to represent the group `runner_on_team`, the appropriate `out_of` relationship can be defined between the `fastest` property and the group.

*"John is faster than Tom."*

```
f/faster(John)
than(f, Tom)
```

Comparisons can also be made between two entities, rather than involving a group. In this case,
there is no group definition that the comparison is relative to. Instead, the direct comparative
is made from one entity to the other through the `than` predicate.