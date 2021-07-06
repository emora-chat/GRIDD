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

### Ask Typed Question


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

### Ask Open-Ended Question
### Share Emora Experience
### React
### Answer Yes/No Question
### Answer Typed Question
### Answer Open-Ended Question
### Respond with Pronoun for Unknown Entity

# Content