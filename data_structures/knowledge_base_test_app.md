
# Knowledge Base Test App

**The knowledge base test app is an iteractive console app for testing knowledge base
predicates and implication rules.**

1. **Run** `knowledge_base_test_app.py` (working directory=`GRIDD` folder)

2. **Edit** files `kb.kg` and `rules.kg`:

    - `kb.kg` defines predicates in the knowledge base
    - `rules.kg` defines rules to apply to input predicates
    
3. **Interact** by inputting logic strings into the console prompt.

Upon inputting a logic string to the prompt, the app will parse the string into predicates
and add them to the _Working Memory_ (a concept graph representing "in-focus" predicates).
Additional predicates from the _Knowledge Base_ (defined by `kb.kg`) are then added to
the _Working Memory_ based on whether they are related to any concepts already present in
_Working Memory_. Finally, all _Implication Rules_ (defined in `rules.kg`) are applied to
_Working Memory_. Each inference solution of each rule results in an application of the
corresponding rule's postcondition: the results printed in the console represent the results
of each solution (separated by a blank line).

## Example

`kb.kg`:
```
animal<entity>
dog<animal>
chase<predicate>
bark<predicate>
scared<predicate>

student<person>
study<predicate>
attend<predicate>
school<entity>
question<object>

fido=dog()
;
```

`rules.kg`:
```
x/dog()
-> all_dogs_bark ->
bark(x)
;

chase(x/dog(), y/entity())
=>
scared(y)
;

x/student()
=>
study(x, q/question())
attend(x, school())
;
```

`interaction`:
```
>>> beth=student()

type(a_44, school) [a_45]
type(a_41, question) [a_42]
study(beth, a_41) [a_43]
attend(beth, a_44) [a_46]



>>> beth=student() chase(fido, beth)

bark(fido) [a_1]

scared(beth) [a_12]

attend(beth, a_44) [a_46]
type(a_44, school) [a_45]
type(a_41, question) [a_42]
study(beth, a_41) [a_43]
```