
# NLG Template Specification

NLG templates allow you to specify how to transform a collection of predicates 
into a natural language response.

Applicable NLG templates are identified following the inference procedure.

The collection of predicates is treated as a precondition and any subgraph of working memory
that matches the precondition produces the appropriate response according to the template.

## Format

The template is composed of an ordered sequence of token and variable elements, 
which are enclosed within dollar sign symbols:
    
    `$ token variable token variable $`

A token element represents a constant string that will be produced in the response.

A variable element will be replaced by the value that the variable takes in match of the precondition.

All tokens and variables must be delimited by spaces, including any tokens representing punctuation
marks.

The tokens and variables can be annotated with various grammatical markers 
to modify their produced natural language form. 

## Markers

Markers are specified on elements in the string format of a json dictionary:

`element{"marker": marker_value}`

There are 4 grammatical markers:

* `s` is the subject dependency marker. 
This is used on verbs and enables subject-verb agreement. 
The value of the `s` marker should be the string subject that the verb depends on.

* `t` is the tense marker. 
It is used on verbs in order to set the appropriate tense.
It has three string values (`past`, `now`, `future`).

* `p` is the possessive marker.
It is used on nouns in order to transform the string into its possessive form.
It has two binary values (true, false) and defaults to `false` if not specified.

* `d` is the determiner marker.
It is used on nouns to automatically add the appropriate determiner based on the logical form 
of the noun.
It has two binary values (true, false) and defaults to `false` if not specified.

Sometimes, the value of the marker will be a variable from the precondition. When this happens,
the variable must be preceded by a `#`. This is illustrated in various examples below.


## Examples

```
time(hike(emora), past)
-> emora_hiked ->
$ I hiked . $
;
```

The simplest template is just an ordered sequence of tokens, with no grammatical markers.
In this case, the produced sentence is exactly that which is specified.

In most cases, this should only be used with preconditions that do not contain any variables.
In the example above, no predicates contain variable arguments; instead, the subjects and 
objects are fully specified, such that only one concept can match them (e.g. `emora`, `past`, etc.)

```
time(hike(X/person()), past)
expr(Z/expression(), X)
-> person_hiked ->
$ X hiked . $
;
```

If there is a variable in the precondition, it is likely that this variable should be expressed in the 
template in order to capture the full meaning of the predicate(s). 

In the example above, the template will be produced for all cases of some person hiking in the past. 
By constructing the template to use the `X` variable as the subject of the `hiked` verb, the appropriate
person will fill that subject slot 
(e.g. `I hiked` if `X` is `emora`, `You hiked` if `X` is `user`, `Mary hiked` if `X` is `mary`, etc.)

As a general practice, it is good to consider whether you want to constrain all variables to be those that 
have expressions by including the `expr` predicate when constructing the template preconditions. 

If you use an `expr` constraint, the template will only be produced if we have an expression for the value of the variable,
which prevents us from producing a template for which we do not know how to refer to the value of the variable.

If you do not use an `expr` constraint and an expressionless value is matched to the variable, a general indicator
will be used. For instance, `a person hiked` could be said if we did not have an expression for the value of `X`.

```
time(hike(X/person()), Y/datetime())
expr(Z/expression(), Y)
-> person_hiked ->
$ X hike{"t":"#Y", "s":"#X"} . $
;
```

An even more general template also allows the tense of the `hike` verb to be dependent on the `time` of the 
matched `hike` predicate. In this way, the produced sentence is not restricted to just being a `hiked` 
expression, unlike the previous examples. This is accomplished through the `t` marker.

In addition, the subject dependency marker `s` should also be used to ensure that the `hike` form matches the
plurality of the subject `X`.

When the marker values are variables, they must be preceded by a `#` as in this example.

If `Y` is `past`, it will be `hiked`. If `Y` is `now`, it will be `hike` or `hikes`, depending on the value of `X`.
If `Y` is `future`, it will be `will hike`.

```
time(h/hike(X/person()), Y/datetime())
expr(Z/expression(), Y)
with(h, A/friend())
possess(X, A)
-> person_hiked_with_friend ->
$ X hike{"t":"#Y", "s":"#X"} with X{"p": true} friend . $
```

You may not always want to realize the value of a variable in the template, instead using a constant token to 
express it. In this example, we do not care about the exact value of `A` (i.e. who the friend is); rather, we
just want to say `friend` with some possessive indicator between `friend` and `X`.

In order to get the possessive indicator, we use the `p` tag set to `true` on the noun that we want to be possessive, 
in this case `X`.

```
time(cute(X/cat()), now)
-> cute_cat_with_determiner ->
$ X{"d": true} be{"t": "now", "s": "#X"} cute . $
;
```

In this example, we do not constrain the template with an `expr` predicate on the `cat` instance because
we want it to be able to produce things like `a cat` or `the cats`. In order to accomplish this, we need
to use the `d` marker.

We can also tell the templates to automatically add a determiner to a noun phrase by setting the `d` marker to `true`.
When this happens, the template realizer automatically determines the plurality and specifity of the noun based on the 
logical form of the matched subgraph to the precondition. 

There are four possible cases:

* Singular and Specific - `the cat is cute .`

* Singular and Non-specific - `a cat is cute .`

* Plural and Specific - `the cats are cute .`

* Plural and Non-specific - `some cats are cute .`

```
time(cute(X/cat()), now)
-> cute_cat_without_determiner ->
$ X be{"t": "now", "s": "#X"} cute . $
;
```

Without `d` set to `true`, determiners are not added automatically. 

This results in two possible cases:

* Singular - `cat is cute .`

* Plural - `cats are cute .`

You may notice that the singular case is not grammatically correct. This is a limitation of the current template system.

To counteract this, you probably only want to not include determiners if you guarantee in the precondition that the subject is plural.

## More examples

More examples can be found in `GRIDD/resources/kg_files/nlg_templates/`.

# Template Response Priority Specification

All NLG response template have a priority category. 
This response category is used in tandem with the salience
scoring system to determine the ranked order of candidate responses.

You can specify a specific priority using the `_pr` predicate in the postcondition of the template.

You do not need to specify a priority for every template. A normal priority is given to those templates which do not have a manually specified one.

The most common priority level should be normal, which allows for Emora to rely on the salience system to do its job of determining relevant responses to the current conversation. 

Low and high priorities should be used sparingly, in cases where we want to make sure Emora behaves a certain way.

There are three priority categories:

* **low** - for responses that should only be taken if there is no better option (e.g. general interactions)

* **normal** - the default priority level. Supercedes low priority responses but high priority responses are preferred over these responses.

* **high** - for responses that must be spoken in a given situation. This should be used sparingly, only for interactions that we need to address immediately (e.g. user mentions death, etc.)

To specify a low priority response:

```
/* general activity */

time(e/event(user), past)
l/like(user, e)
request_truth(emora, l)
->
_pr(_low)
$ Did you have a good time doing that ? $
;
```

To specify a high priority response:
    
```
/* funeral interaction */

time(g/go(user), past)
to(g, funeral())
esympathy(emora, g)
feel(user, e/emotion())
request(emora, e)
->
_pr(_high)
$ I am so sorry to hear that . How are you doing ? $
;
```

To specify a normal priority response:

```
like(emora, d/doggypaddle(emora))
->
$ Swimming is awesome ! I can only do the doggypaddle, but it would be cool to get better at it and learn other swimming strokes . $
;
```