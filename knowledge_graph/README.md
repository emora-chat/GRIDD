# Knowledge Graph Interface

[Knowledge Graph Specification and Guidelines](https://docs.google.com/document/d/1mfdZIY09JwZ-DN4eBmIpxQ9phItEbrJqD5d1QtFKBN8/edit?usp=sharing)

[Ontology Documentation](https://drive.google.com/drive/folders/1Cdn8DQZMtoV3i4r5s-9hzVRA9bYteVEq?usp=sharing)

This package contains the supporting data structures for building and 
maintaining the Knowledge Graph. 

Currently, the knowledge that is contained within a Knowledge Graph 
is specified through the construction of KG text files.

## KG Text Files
    
An example of a KG text file can be found in `example.kg`.

### Instantiation

The Base Knowledge Graph contains all primitive entity and predicate
types that subsequent Knowledge Graph additions build on top of.

It is specified in the `base.kg` text file.

When testing your additions, you must instantiate your Knowledge Graph
first with `base.kg`.

```
kg = KnowledgeGraph('base.kg')
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
unique id when it is added to the KG. Except for the case
of `named instances`, this id is not able to be manually 
specified and is not available to the designer.

#### Named instances

Adding new named entities to the KG is an important task, 
such as specifying people, locations, items, and more. 

In the text file, named entities are specified as instances of 
their ontological type where their name is treated as their 
id like `id=type()` as in:
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
you do not have a guaranteed unique name to use for the id. 
Instead, an unnamed instance is specified like `type()` as in:

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