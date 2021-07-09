# Interactions


### Initiate Conversation

Working Memory
```
greet(emora, user);
```

Templates
```
greet(emora, user)
->
$ Hello, ... $
```


### Initiate New Topic

Fallbacks
```
l:<time(l/have(user, pet()), now)>
r/request_truth(emora, l)
-> pet_fallback ->
$ By the way , do you have a pet ? $
;
```


### Ask Yes/No Question

Rules
```
... 
-> 
h:<time(h/have(user, pet()), now)> 
request_truth(emora, h)
;

time(h/have(user, pet()), now)
->
...
;

time(h/have(user, pet()), now)
not(h)
->
...
;
```

Templates
```
time(h/have(user, pet()), now)
request_truth(emora, h)
->
$ Do you have a pet ? $
;
```


### Ask What-Kind Question

Rules
```
... 
-> 
h:<time(h/have(user, pet()), now)> 
request_truth(emora, h)
;

time(h/have(user, p/pet()), now)
_category(p)
->
op_more_info(p, h)
request(emora, p)
;

time(have(user, p/pet()), now)
_specific(p)
->
...
;
```
Templates
```
h:<time(h/have(user, pet()), now)> 
request_truth(emora, h)
->
$ Do you have a pet ? $
;

time(have(user, p/pet()), now)
request(emora, p)
->
$ What kind of pet do you have ? $
;
```


### Ask Entity Question

Rules
```
...
->
q:<possess(user, a/animal()) favorite(a) be(a, q/animal()) _specific(q)>
request(emora, q)
;

possess(user, a/animal()) favorite(a) be(a, q/hawk())
->
...
;

possess(user, a/animal()) favorite(a) be(a, q/dog())
->
...
;

...
->
...
;

```

Templates
```
possess(user, a/animal()) favorite(a) be(a, q/animal())
request(emora, q)
->
$ What is your favorite animal? $
;
```


### Ask Predicate Question

Rules
```
...
->
a:<a/activity(user) time(a, past)>
request(emora, a)
;

time(h/hike(user), past)
->
...
;

time(w/watch(user, movie()), past)
->
...
;

...
->
...
;
```

Templates
```
time(a/activity(user), past)
request(emora, a)
->
$ What did you get up to today? $
;
```


### Answer Yes/No Question

Knowledge Base
```
nyla = dog()
time(have(emora, nyla), now)
;
```

Templates
```
time(have(emora, nyla), now)
->
$ I have a dog named Nyla! $
;
```


### Answer Typed Question
```

```



### Respond to Open-Ended Question/Presentation




### Respond with Pronoun for Unknown Entity



### Respond with Predicate With Correct Surface Form




# Content