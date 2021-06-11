# Turn Tracking

Each concept spoken by Emora or the user records the speaker and the turn in which it was 
spoken as a predicate in Working Memory.

It is often useful to utilize this turn information in preconditions of
inference rules and templates, especially for generating reactions or answers to the 
user's utterance.

To restrict a rule based on Emora's turns, use the `eturn` predicate in 
the precondition.

```
eturn(<concept>, <integer>)
```

The `integer` object specifies the desired turn index, relative to the current turn.
* `0` - current turn
* `1` - previous turn
* `2` - two turns ago
* and so on...

The format is the same for the user:

```
uturn(<concept>, <integer>)
```

Since Emora is always responding to the user, the last thing that the user said
actually occurs on the current turn. 

So, if you want to restrict to what the user has said most recently, you would do:

`uturn(<concept>, 0)`

If you want to restrict to what the user said on the previous turn,

`uturn(<concept>, 1)`

To restrict to what Emora has said most recently, do:

`eturn(<concept>, 1)`

As an example,

```
U1: hi
E1: I am an alexa prize socialbot. What is your name?
U2: sarah
E2: <current_turn>
```

At this point in the conversation `E2`,
* `uturn(..., 0)` -> `U2`
* `uturn(..., 1)` -> `U1`
* `eturn(..., 1)` -> `E1`

If we have the following rule,

```
uturn(n/name(), 0)
->
$ You told me your name ! Wahoo ! $
```

it checks if the user just mentioned a name in their current utterance.

This rule would be triggered in this example, since we are on turn `2` and
`U2` is that the user just said `sarah`.