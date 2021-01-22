# Knowledge Graph Interface

[Knowledge Graph Specification and Guidelines](https://docs.google.com/document/d/1mfdZIY09JwZ-DN4eBmIpxQ9phItEbrJqD5d1QtFKBN8/edit?usp=sharing)

[Ontology Documentation](https://drive.google.com/drive/folders/1Cdn8DQZMtoV3i4r5s-9hzVRA9bYteVEq?usp=sharing)

This package contains the supporting data structures for building and 
maintaining the Knowledge Graph. 

Currently, the knowledge that is contained within a Knowledge Graph 
is specified through the construction of KG text files.

[KG Text File Quick Reference](#quick-reference)

## KG Text Files
    
An example of a KG text file can be found in `example.kg`.

### Instantiation

The Base Knowledge Graph contains all primitive entity and predicate
types that subsequent Knowledge Graph additions build on top of, 
specified in the `base.kg` text file.

A new `KnowledgeGraph` object is automatically instantiated with 
`base.kg`. You instantiate a new `KnowledgeGraph` by:

```
kg = KnowledgeGraph()
```
and add new knowledge to it by:

```
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


### Anonymous Implication Rules

Some knowledge you want to specify in the knowledge base is inferential instead of assertive.
In other words, specifying knowledge such as predicates or entities asserts what is true, but
some knowledge is concerned with deriving new truths from existing knowledge instead of asserting
facts directly. 

Implication rules take the form `precondition -> postcondition` and are used to generate new
knowledge from existing knowledge in a parameterized way. The rules can then be applied to a set
of knowledge to check for satisfactions: ways in which the rule applies to the knowledge set
to imply new facts. These rules are similar to prolog rules using the `:-` syntax.

Implication rules are written as `blocks`, in the form

```
precondition
=>
postcondition;
```

where both the `precondition` and `postcondition` can be an arbitrary collection of statements,
including bipredicates, monopredicates, and entity declarations. The only ways the `precondition`
and `postcondition` differ from normal statements are:

1. All instances initialized in the precondition are considered `variables` and do not "count" as
actual entities.

2. The poscondition can reference `variables` defined in the precondition without declaring them
in the postcondition body.

A rule can be applied to a set of facts if there is some assignment of each `variable` in the
precondition to a concept in the fact set such that every predicate in the `precondition` holds
true within the fact set. For each full assignment of `variables` to concept `values` (known as
a solution), the implication rule asserts that the `postcondition` body holds true.


## Quick Reference

#### Entity Type with N>=1 Supertype

```
entity_type<supertype1, ..., supertypeN>
```

Note: This is for building the entity ontology.

#### Predicate Type with Expected Arguments

```
predicate_type=supertype(subject_type(), object_type())
```

Note: This is for building the predicate ontology. It 
influences the inference procedure, such that all 
instances of `predicate_type` will have to have the 
expected arguments, or else an `Error` will be raised.

For example, if we want to specify that the predicate `buy`
is an `event` and has a `person` subject and a `purchasable` object:

```
buy=event(person(), purchasable())
```


#### Predicate Type with Expected Arguments and Properties

```
predicate_type=supertype(subject_type(), object_type())
property(predicate_type, property_object_type())
```

Note: This is for building the predicate ontology.
Similar to the previous, all instances will have to have 
the expected arguments and also expected properties, or 
else an `Error` will be raised.

#### Bipredicate

```
predicate_type(subject,object)
```

#### Monopredicate

```
predicate_type(subject)
```

#### Entity Instance

```
entity_type()
```
