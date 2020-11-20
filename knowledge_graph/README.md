# Knowledge Graph Interface

[Knowledge Graph Specification and Guidelines](https://docs.google.com/document/d/1mfdZIY09JwZ-DN4eBmIpxQ9phItEbrJqD5d1QtFKBN8/edit?usp=sharing)

[Ontology Documentation](https://drive.google.com/drive/folders/1Cdn8DQZMtoV3i4r5s-9hzVRA9bYteVEq?usp=sharing)

This package contains the supporting data structures for building and 
maintaining the Knowledge Graph. 

There are two interfaces for adding new knowledge into the Knowledge
Graph: text files and API.

## KG Text Files

Adding knowledge through the creation of text files is recommended 
when any of the following is true:

* Knowledge is not crawled programmatically
* You want:
    * High designer control
    * To perform quick knowledge graph modifications 
    (e.g. edge cases, bug fixes, quick tests)
    
An example of a KG text file can be found in `example.kg`.

### Instantiation

All entity and predicate types that will be used in your KG 
text file must be added to the KG before you load your text
file. When instantiating your KG, you can pass them in as a 
list to the `nodes` parameter and then `add_knowledge()` as in
the following:

```
ontology=['type','person','bot','movie','actor','store',
      'reason','like','happy','time','now','past','future','watch','go','expr']
kg = KnowledgeGraph(nodes=ontology)
additions = kg.add_knowledge('example.kg')
```

### Format

A KG text file specifies `blocks` of knowledge statements 
that will be added to the KG. 
Each `block` is independent from one another, which means
that the statements specified in previous `blocks` cannot be 
accessed by subsequent `blocks` within the text file. 
All statements that rely on one another should be specified within
the same `block`.
`Blocks` are separated by the character `;`.

`example.kg` is composed of 2 `blocks`.

#### Knowledge Ids
Each knowledge statement is given an automatically generated
unique id when it is added to the KG. 
This unique id is integral to the functioning of the underlying 
data structure, but it is not easily available through the 
text file interface, which leads to the local naming paradigm
 described in future sections.

#### Named instances

Adding new named entities to the KG is an important task, 
such as specifying people, locations, items, and more. 

In the text file, named entities are specified as instances of 
their ontological type where their name is treated as an 
id like`id=type()` as in:
```
emora=bot()
avengers=movie()
chris_evans=actor()
```

These named entities can then be referenced in later statements 
simply by their names (e.g. `emora`).

*NOTE: Alias/synonym specification coming soon...

#### Unnamed instances

In many cases, you will want to add specific instances of a type
to the KG where the instance is not a named entity. 
For this, you should not use the `named entity` specification since
you do not have a name to use for the id. Instead, an unnamed 
instance is specified like `type()` as in:

```
sandwich()
blanket()
house()
```

It is necessary to give a local name to these unnamed instances if 
you will be referencing them in later statements in the KG block.
This local name is not utilized in the underlying KG data structure;
it only exists when parsing the KG text file for linking purposes.

An instance local name is specified by the prefix `name/` before 
the instance specification as in:
```
s1/sandwich()
b1/blanket()
```

#### Bipredicates

Once entities have been specified, you are now able to capture 
the relationships between them. 

A relationship between 2 entities is called a `bipredicate`, 
or a predicate with 2 arguments. `Bipredicates` are specified 
by indicating the relationship type between a subject and an 
object in the following format `type(subject,object)`. 
Some examples are:

```
like(emora,avengers)
like(emora,chris_evans)
watch(emora,avengers)
```

Often, it is useful to provide modifying information to these 
`bipredicates`, like what time they occurred, 
or these `bipredicates` may act like `entities` themselves by
having some relationship with another `entity` (or `bipredicate`).

As a result, it is possible to nest `bipredicates` within other
`bipredicates` in either the subject or object position as in:

```
reason(like(emora,avengers),like(emora,chris_evans))
time(watch(emora,avengers),now)
```

However, if a `bipredicate` is involved in more than relationship,
the examples specified previously will not work because there is
no way to reference the nested `bipredicate`. 

Instead, you will follow the same local naming principle as for 
unnamed instances.
For `bipredicates`, local names are specified as the prefix `name/` to the `bipredicate`
specification as in:
```
ela/like(emora,avengers)
reason(ela,like(emora,chris_evans))
time(ela,now)
```

#### Monopredicates

You may also want to capture knowledge that does not follow the 
`bipredicate` format of a relationship between a subject and 
an object. There are many cases where there is only 1 argument
instead. 

A predicate with only 1 argument is called a `monopredicate`. 
`Monopredicates` are specified as `type(subject)` as in:

```
happy(emora)
run(emora)
```

`Monopredicates` have the same nesting and naming principles 
as defined for `bipredicates`.

#### Predicate Type 

Coming soon...

#### Entity Type

Coming soon...

## API

Coming soon...