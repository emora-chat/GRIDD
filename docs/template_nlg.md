# NLG Templates

1. [NLG Template Specification](#spec)
2. [Template Response Priorities](#priority)
3. [Template Response Types](#type)

<a name="spec"></a>
## NLG Template Specification

NLG templates allow you to specify how to transform a collection of predicates 
into a natural language response.

Applicable NLG templates are identified following the inference procedure.

The collection of predicates is treated as a precondition and any subgraph of working memory
that matches the precondition produces the appropriate response according to the template.

### Format

The template is composed of an ordered sequence of token and variable elements, 
which are enclosed within dollar sign symbols:
    
    `$ token variable token variable $`

A token element represents a constant string that will be produced in the response.

A variable element will be replaced by the value that the variable takes in match of the precondition.

All tokens and variables must be delimited by spaces, including any tokens representing punctuation
marks.

The tokens and variables can be annotated with various grammatical markers 
to modify their produced natural language form. 

### Markers

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


### Examples

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

### More examples

More examples can be found in `GRIDD/resources/kg_files/nlg_templates/`.

<a name="priority"></a>
## Template Response Priorities

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

<a name="type"></a>
## Template Response Types

All NLG response templates have a response type associated with them.
This response type delegates how different responses can be combined together
to form compound responses.

There are 3 response types:

* `_react` - acknowledges what the user has just said

* `_present` - offers a new piece of information that drives the conversation forward

* `_rpresent` - both acknowledges AND offers a new piece of information to continue the conversation

The salience and priority systems are used to select the response(s) from their candidates sets.

* If the best option is an `_rpresent` response, then no `_react` response is selected.

* If the best option is a `_present` response, then the best `_react` response is selected and prepended to the `_present` response.

You can specify a specific type using the `_t` predicate in the postcondition of the template.

You do not need to specify a type for every template. The default type is `_present` 
and is assigned to responses which do not have a manually specified one.

### Default Responses

There are default `_react` responses in place in order to ensure Emora acknowledges the user in a reasonable manner, even if 
no specific `_react` is found.

These defaults are only taken if no other `_react` is found:

* If the user provides an answer to Emora's question -> `Gotcha` or similar.

* If the user provides a statement -> `Yeah` or similar

There is also a default `_rpresent` for the case where the user asks a question that Emora does not have an answer to:
* `I don't know` or similar.

### Determining the Response Type

* `_react`
    * Responds directly to a user statement
    * Usually should be used in tandem with turn tracking in order to make sure the reaction is only a possibility right after the user utterance it is reacting to
    * Does not contain any highly contentful information; rather, these are things like `That is cool!` and `Sounds like you had a good time.`
    
* `_present`
    * Provides a new idea from Emora that is related to something the user brought up
    * These responses do not need to exactly follow a certain previous utterance from the user; instead, they are just as reasonable later on in the conversation
    * These will be paired with a `_react` response type.
    * If a response is just asking a follow up question or sharing an experience, it generally falls into this type.
    
* `_rpresent`
    * This is for responses that should NOT take be paired with an external `_react` response.
    * Instead, these responses have a targeted response to the user's utterance baked into them.
    * For instance, answers to user requests should be tagged as the `_rpresent` type.
    * If you are developing content and the default reaction is being prepended when you don't want it to be,
    you have two choices: (1) create a specific `_react` for your case or (2) tag your case as a `_rpresent` type.

### Examples

* NOTE: You can test out the following examples by saying `I worked on a project` in response to `What did you do today` when you run the system

#### Example 1
The following interaction illustrates the usage of a default `_react` with a targeted `_present`.

In this case, there is no `_react` template that is applicable to `U1`, so the default for statements `Yeah` is taken.

There is an applicable `_present` template, which presents the `dream job` question.
As mentioned earlier, the default type of a template is `_present`, so it does not need to be manually specified, which
is shown below.

```
U1: I worked on a project today.

---------
rules
---------

time(w/work(user), past)
->
t:<on(w, t/task())>
request(emora, t)

j2:<
    possess(user, j/job())
    best(j)
    be(j, j2/job())
>
request(emora, j2)
;

---------
templates
---------

possess(user, j/job())
best(j)
be(j, j2/job())
request(emora, j2)
->
$ Speaking of working, what is your dream job ? $
;

E1: Yeah . Speaking of working, what is your dream job ?
```

#### Example 2
In this next example, we have both an applicable `_react` and `_present`.

Separating the `_react` and `_present` in this case allows for greater flexibility in the responses.

No matter what dream job is mentioned, our `_react` is a reasonable acknowledgement.

But it is likely that we want to create more targeted responses to different dream jobs, rather than just asking 
the generic question that we do here, which is applicable regardless of the mentioned dream job. 

```
U2: a nurse

---------
rules
---------

possess(user, j/job())
best(j)
be(j, j2/job())
_specific(j2)
->
X:<
    like(user, X/predicate(object()))
    as(X, j2)
>
request(emora, X)
;

---------
templates
---------

possess(user, j/job())
best(j)
be(j, j2/job())
_specific(j2)
uturn(j2, 0)
->
_t(_react)
$ That sounds neat ! $
;

like(user, X/predicate(object()))
as(X, j2/job())
request(emora, X)
_specific(j2)
->
_pr(_low)
$ What do you find interesting about becoming a j2 ? $
;

E2: That sounds neat ! What do you find interesting about becoming a nurse ?
```

#### Example 3
In some cases, we want to specify both a `_react` and a `_present` together,
rather than allowing for an external `_react` (or the default) being chosen.

The next example illustrates such a case.

To do this, the reaction and presentation are combined into a single NLG
template and we use the `_rpresent` type, as shown in the next interaction.

As you can see, it is unnecessary for a reaction to be prepended to the NLG
template in this example, since the first sentence `I admire that` is already
functioning as a reaction.

When your reaction and presentation are related/come from the same precondition 
and you want them to always occur together,
it is generally the best option to make them a `_rpresent` response.

```
U3: I like to help people

---------
rules
---------

l/like(user, help(user, person()))
->
eadmire(emora, l)
like(emora, help(emora, p2/person()))
type(p2, group)
;

---------
templates
---------

l/like(user, help(user, person()))
eadmire(emora, l)
like(emora, help(emora, p2/person()))
type(p2, group)
uturn(l, 0)
->
_t(_rpresent)
$ I admire that . I also like to help people as much as I can . $
;

E3: I admire that . I also like to help people as much as I can.
```

#### Example 4
Setting up Emora's response to a user question is perhaps one of the most
straightforward cases, as shown next.

When the user asks a question of Emora, Emora's answer should always be 
a `_rpresent` type, since our response to the user is acting as the acknowledgement
and new piece of information being shared.

We should always respond to a user's question on the following turn, so
it makes sense to set the priority to `_high` and to restrict the template
to only be applicable when the user asked the question on the current turn
`uturn(r, 0)`.

```
U4: Do you have a job ?

---------
templates
---------

time(h/have(emora, job()), now)
req_unsat(r/request_truth(user, h))
uturn(r, 0)
-> answer_job_q ->
_t(_rpresent)
_pr(_high)
$ Yeah , I have a job . $
;

E4: Yeah , I have a job .
```
