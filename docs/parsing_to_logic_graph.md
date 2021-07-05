
## Adverbial Questions

Captures questions that start with `When`, `Where`, `Why`, and `How` in the adverb role.

Represented as `question_concept(main_predicate, request(user, object()))`.

The mapping between question word and semantic concept is:

`when`=`time` | `where`=`locate` | `why`=`cause` | `how`=`qualifier`

<details>
  <summary>Conversions</summary>
  
	adv(X/pstg(), Y/question_word())
	aux(X, Z/pstg())
	sbj(X, A/pstg())
	precede(Y, Z)
	precede(Z, A)
	-> q_aux_adv ->
	p/Y(X, o/object())
	request(user, o)
	focus(p)
	center(Y)
	cover(Z)
	;
	
	adv(X/pstg(), Y/question_word())
	cop(X, Z/pstg())
	sbj(X, A/pstg())
	precede(Y, Z)
	precede(Z, A)
	-> q_cop_adv ->
	p/Y(X, o/object())
	request(user, o)
	focus(p)
	center(Y)
	;
  
</details>

#### Examples

How did this happen

How did you do on the test

Why are you sad

When did you start reading

## Copular Questions

Captures questions that start with `How`, `What`, and `Who` as the root of a copular construction or as the determiner of the root. 

Represented as `copula(sbj, request(user, question_concept))`.

<details>
  <summary>Conversions</summary>
  
	cop(X/pstg(), Y/present_tense())
	sbj(X, Z/pstg())
	det(X, D/question_word())
	precede(Y, Z)
	-> qdet_copula_present ->
	p/Y(Z, inst/X())
	request(user, inst)
	time(p, now)
	focus(p)
	center(X)
	cover(D)
	;
	
	cop(X/pstg(), Y/past_tense())
	sbj(X, Z/pstg())
	det(X, D/question_word())
	precede(Y, Z)
	-> qdet_copula_past ->
	p/Y(Z, inst/X())
	request(user, inst)
	time(p, past)
	focus(p)
	center(X)
	cover(D)
	;
  
	cop(X/question_word(), Y/present_tense())
	sbj(X, Z/pstg())
	precede(Y, Z)
	-> qw_copula_present ->
	p/Y(Z, o/object())
	request(user, o)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/question_word(), Y/past_tense())
	sbj(X, Z/pstg())
	precede(Y, Z)
	-> qw_copula_past ->
	p/Y(Z, o/object())
	request(user, o)
	time(p, past)
	focus(p)
	center(X)
	;
  
</details>

#### Examples

How are you

What is your name

Who is your favorite actor

What color was it

## Subject/Object/Dative Questions

Captures questions that contain `Who` and `What` as subjects, objects, or datives. 

Represented by wrapping the subject/object/dative with the `request` predicate. 

<details>
  <summary>Conversions</summary>
  
	obj(X/pstg(), Y/question_word())
	-> obj_question ->
	request(user, o/object())
	center(Y)
	focus(o)
	;
	
	sbj(X/pstg(), Y/question_word())
	-> sbj_question ->
	request(user, o/object())
	center(Y)
	focus(o)
	;
	
	dat(X/pstg(), Y/question_word())
	aux(X, Z/pstg())
	sbj(X, A/pstg())
	precede(Y, Z)
	precede(Z, A)
	-> dat_question ->
	p/beneficiary(X, o/object())
	request(user, o)
	center(Y)
	cover(Z)
	focus(p)
	;
  
</details>

#### Examples

What are you doing

Who played Thanos

Who did you give it to

Who did John make a call to

Who did Mary take care of

## Interrogative Determiner

Captures questions that ask for a specific instance of a concept by using question words as determiners.

Overrules the auxiliary question rule, which would cause an incorrect interpretation of such questions, but need to maintain the tense determined by auxiliary.

<details>
  <summary>Conversions</summary>
  
	det(X/pstg(), Y/question_word())
	obj(Z/pstg(), X)
	aux(Z, A/pstg())
	-> q_aux_det ->
	inst/X()
	request(user, inst)
	focus(inst)
	center(X)
	cover(Y)
	;
	
	det(X/pstg(), Y/question_word())
	obj(Z/pstg(), X)
	aux(Z, A/present_tense())
	-> q_aux_det_pres ->
	p/p_time(Z, now)
	focus(p)
	center(A)
	;
	
	det(X/pstg(), Y/question_word())
	obj(Z/pstg(), X)
	aux(Z, A/past_tense())
	-> q_aux_det_past ->
	p/p_time(Z, past)
	focus(p)
	center(A)
	;
	
	det(X/pstg(), Y/question_word())
	-> q_det ->
	inst/X()
	request(user, inst)
	focus(inst)
	center(X)
	cover(Y)
	;
  
</details>

#### Examples

What candy did you buy

What show has dinosaurs

## Interrogative Copula

Copula constructions are in interrogative form when the copula precedes the subject. 

<details>
  <summary>Conversions</summary>

	cop(X/pstg(), Y/present_tense())
	sbj(X, Z/pstg())
	precede(Y, Z)
	-> q_sbj_copula_present ->
	p/Y(Z,X)
	q/request_truth(user, p)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pstg(), Y/past_tense())
	sbj(X, Z/pstg())
	precede(Y, Z)
	-> q_sbj_copula_past ->
	p/Y(Z,X)
	q/request_truth(user, p)
	time(p, past)
	focus(p)
	center(X)
	;
 
</details>

#### Examples

Is John a student?

Was the book good?

## Copula

Copula constructions have different logical forms depending on the copular verb. 

(A) The `be` copular verb takes one of four logical forms:

* Cause-less property specifiers take the form `property(subject)` as in `I am happy`. 
Properties are often specified as adjectives.

* Property specifiers can also be specified with their causes as in `I am proud of her`. 
In this case, the final logical form is `p/property(subject) cause(obj, p)`

* Equivalence specifiers take the form `copula(subject, root)` as in `I am a student`.
 
* Prepositional specifiers take the form `root(subject, object)` as in `I am in Georgia`.

(B) All other copular verbs are maintained and result in the logical form `copula(subject, root)`, 
just like the third case of the `be` copular verb. It may have a `cause` attachment, if one is given.
For these cases, the specific copular verb is captured by an identifier rule such that it will be 
merged into the predicate.

<details>
  <summary>Conversions</summary>

    cop(X/adj(), Y/present_tense())
    sbj(X, Z/pstg())
    ref(Y, E/expression())
	expr(E, be)
    -> be_adj_copula_present ->
    p/X(Z)
    time(p, now)
    focus(p)
    center(X)
    cover(Y)
    ;

    cop(X/adj(), Y/past_tense())
    sbj(X, Z/pstg())
    ref(Y, E/expression())
	expr(E, be)
    -> be_adj_copula_past ->
    p/X(Z)
    time(p, past)
    focus(p)
    center(X)
    cover(Y)
    ;
    
    cop(X/adj(), Y/verb())
	sbj(X, Z/pstg())
	obj(X, A/pstg())
	case(A, B/pstg())
	ref(Y, E/expression())
	expr(E, be)
	-> cause_of_be_adj_copula ->
	p/cause(A, X)
	focus(p)
	center(B)
	;
	
    cop(X/prepo(), Y/present_tense())
	sbj(X, Z/pstg())
	obj(X, A/pstg())
	ref(Y, E/expression())
	expr(E, be)
	-> be_prepo_copula_present ->
	p/X(Z, A)
	time(p, now)
	focus(p)
	center(X)
	cover(Y)
	;
	
	cop(X/prepo(), Y/past_tense())
	sbj(X, Z/pstg())
	obj(X, A/pstg())
	ref(Y, E/expression())
	expr(E, be)
	-> be_prepo_copula_past ->
	p/X(Z, A)
	time(p, past)
	focus(p)
	center(X)
	cover(Y)
	;
	
    cop(X/pstg(), Y/present_tense())
	det(X, D/dt())
	sbj(X, Z/pstg())
	-> det_copula_present ->
	p/Y(Z,X)
	time(p, now)
	focus(p)
	center(Y)
	cover(D)
	;
	
	cop(X/pstg(), Y/past_tense())
	det(X, D/dt())
	sbj(X, Z/pstg())
	-> det_copula_past ->
	p/Y(Z,X)
	time(p,past)
	focus(p)
	center(Y)
	cover(D)
	;
	
	cop(X/pstg(), Y/verb())
	det(X, D/dt())
	sbj(X, Z/pstg())
	-> det_copula_obj ->
	inst/X()
	focus(inst)
	center(X)
	;

	cop(X/pstg(), Y/present_tense())
	sbj(X, Z/pstg())
	-> copula_present ->
	p/Y(Z,X)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pstg(), Y/past_tense())
	sbj(X, Z/pstg())
	-> copula_past ->
	p/Y(Z,X)
	time(p,past)
	focus(p)
	center(X)
	;
	
	cop(X/pstg(), Y/pstg())
	-> id_copula ->
	focus(Y)
	center(Y)
	;
 
</details>
 
#### Examples

John is a student.

Sally became a doctor last year.

## Interrogative Auxiliary with Passive Constructions

Captures truth questions asked about sentences with passive voice.

 <details>
  <summary>Conversions</summary>

	sbj(X/pstg(), Y/pstg())
	obj(X, Z/pstg())
	aux(X, A/past_tense())
	precede(Z, X)
	precede(A, Z)
	-> q_sbj_obj_passive_voice_past ->
	p/X(Y, Z)
	time(p, past)
	request_truth(user, p)
	focus(p)
	center(X)
	cover(A)
	;

	obj(X/pstg(), Z/pstg())
	aux(X, A/past_tense())
	precede(Z, X)
	precede(A, Z)
	-> q_obj_passive_voice_past ->
	p/X(object(), Z)
	time(p, past)
	request_truth(user, p)
	focus(p)
	center(X)
	cover(A)
	;

	sbj(X/pstg(), Y/pstg())
	obj(X, Z/pstg())
	aux(X, A/present_tense())
	precede(Z, X)
	precede(A, Z)
	-> q_sbj_obj_passive_voice_present ->
	p/X(Y, Z)
	time(p, now)
	request_truth(user, p)
	focus(p)
	center(X)
	cover(A)
	;

	obj(X/pstg(), Z/pstg())
	aux(X, A/present_tense())
	precede(Z, X)
	precede(A, Z)
	-> q_obj_passive_voice_present ->
	p/X(object(), Z)
	time(p, now)
	request_truth(user, p)
	focus(p)
	center(X)
	cover(A)
	;

</details>

#### Examples

Was the dog found

Was the dog was found by the policeman

Was I chosen

## Passive Constructions

Captures sentences with passive voice.

 <details>
  <summary>Conversions</summary>

	sbj(X/pstg(), Y/pstg())
	obj(X, Z/pstg())
	aux(X, A/past_tense())
	precede(Z, X)
	precede(Z, A)
	-> sbj_obj_passive_voice_past ->
	p/X(Y, Z)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;
	
	sbj(X/pstg(), Y/pstg())
	obj(X, Z/pstg())
	aux(X, A/present_tense())
	precede(Z, X)
	precede(Z, A)
	-> sbj_obj_passive_voice_present ->
	p/X(Y, Z)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;

	obj(X/pstg(), Y/pstg())
	aux(X, A/past_tense())
	precede(Y, X)
	precede(Y, A)
	-> obj_passive_voice_past ->
	p/X(object(), Y)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;

	obj(X/pstg(), Y/pstg())
	aux(X, A/present_tense())
	precede(Y, X)
	precede(Y, A)
	-> obj_passive_voice_present ->
	p/X(object(), Y)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;

</details>

#### Examples

The dog was found.

The dog was found by the policeman.

I was chosen.

## Subject-Verb-Object

Two-argument predicates of the format `root(subject, object)`.

 <details>
  <summary>Conversions</summary>
  
	sbj(X/past_tense(), Y/pstg())
	obj(X, Z/pstg())
	-> sbj_dobj_past ->
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	;
	
	sbj(X/present_tense(), Y/pstg())
	obj(X, Z/pstg())
	-> sbj_dobj_present ->
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	sbj(X/pstg(), Y/pstg())
	obj(X, Z/pstg())
	-> sbj_dobj_nonverb_head ->
	p/X(Y,Z)
	focus(p)
	center(X)
	;

 </details>


## Light Verb with Subject and Object

Two-argument predicates of the format `root(subject, object)`. The light verb is dropped. The determiner of the root is dropped, if there is one.

 <details>
  <summary>Conversions</summary>

	sbj(X/noun(), Y/pstg())
	det(X, A/dt())
	obj(X, Z/pstg())
	lv(X, U/past_tense())
	-> sbj_obj_det_light_verb_past ->
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	cover(U)
	;
	
	sbj(X/noun(), Y/pstg())
	det(X, A/dt())
	obj(X, Z/pstg())
	lv(X, U/present_tense())
	-> sbj_obj_det_light_verb_present ->
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	cover(U)
	;

	sbj(X/noun(), Y/pstg())
	obj(X, Z/pstg())
	lv(X, U/past_tense())
	-> sbj_obj_light_verb_past ->
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	cover(U)
	;
	
	sbj(X/noun(), Y/pstg())
	obj(X, Z/pstg())
	lv(X, U/present_tense())
	-> sbj_obj_light_verb_present ->
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	cover(U)
	;
	


 </details>



#### Examples

John made a call to Mary.

## Light Verb with Subject only

One-argument predicates of the format `root(subject)`. The light verb is dropped. The determiner of the root is dropped, if there is one.

 <details>
  <summary>Conversions</summary>

	sbj(X/noun(), Y/pstg())
	det(X, A/dt())
	lv(X, U/past_tense())
	-> sbj_det_light_verb_past ->
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	cover(U)
	;
	
	sbj(X/noun(), Y/pstg())
	det(X, A/dt())
	lv(X, U/present_tense())
	-> sbj_det_light_verb_present ->
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	cover(U)
	;

	sbj(X/noun(), Y/pstg())
	lv(X, U/past_tense())
	-> sbj_light_verb_past ->
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	cover(U)
	;
	
	sbj(X/noun(), Y/pstg())
	lv(X, U/present_tense())
	-> sbj_light_verb_present ->
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	cover(U)
	;

 </details>

#### Examples

John made a call.

## Complement

 <details>
  <summary>Conversions</summary>

	sbj(X/past_tense(), Y/pstg())
	comp(X, Z/pstg())
	-> sbj_outer_comp_past ->
	p/X(Y,Z)
	time(p,past)
	focus(p)
	center(X)
	;
	
	sbj(X/present_tense(), Y/pstg())
	comp(X, Z/pstg())
	-> sbj_outer_comp_present ->
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	comp(X/past_tense(), Z/pstg())
	-> missing_outer_sbj_comp_past ->
	p/X(object(),Z)
	time(p,past)
	focus(p)
	center(X)
	;
		
	comp(X/present_tense(), Z/pstg())
	-> missing_outer_sbj_comp_present ->
	p/X(object(),Z)
	time(p,past)
	focus(p)
	center(X)
	;
	
	sbj(X/verb(), Y/pstg())
	comp(X, Z/pstg())
	sbj(Z, B/pstg())
	obj(Z, A/pstg())
	-> sbj_sbj_inner_comp_with_obj ->
	p/Z(B,A)
	focus(p)
	center(Z)
	;
	
	sbj(X/verb(), Y/pstg())
	comp(X, Z/pstg())
	sbj(Z, A/pstg())
	-> sbj_sbj_inner_comp ->
	p/Z(A)
	focus(p)
	center(Z)
	;
	
	sbj(X/verb(), Y/pstg())
	comp(X, Z/pstg())
	obj(Z, A/pstg())
	-> sbj_inner_comp_with_obj ->
	p/Z(Y,A)
	focus(p)
	center(Z)
	;
	
	sbj(X/verb(), Y/pstg())
	comp(X, Z/pstg())
	-> sbj_inner_comp ->
	p/Z(Y)
	focus(p)
	center(Z)
	;

 </details>

#### Examples

I thought John bought a house.

I thought that John did buy a house.

I like buying a house.

## Verbs without Objects

Captures expressions where the verb only has a subject.

 <details>
  <summary>Conversions</summary>

	sbj(X/past_tense(), Y/pstg())
	-> sbj_no_obj_past ->
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	;
	
	sbj(X/present_tense(), Y/pstg())
	-> sbj_no_obj_present ->
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	;

</details>

#### Examples

I run.

The program ended.

## Interrogative Auxiliary Verb

Interrogative sentences can be formed by the aux verb preceding the subject. 

The overall tense of the question is also affected by the aux verb.

 <details>
  <summary>Conversions</summary>
	
	aux(X/pstg(), Y/past_tense())
	type(Y, tenseful_aux)
	sbj(X, Z/pstg())
	precede(Y,Z)
	-> q_aux_past ->
	q/request_truth(user, X)
	p_time(X, past)
	center(Y)
	focus(q)
	;
	
	aux(X/pstg(), Y/present_tense())
	type(Y, tenseful_aux)
	sbj(X, Z/pstg())
	precede(Y,Z)
	-> q_aux_present ->
	q/request_truth(user, X)
	p_time(X, now)
	center(Y)
	focus(q)
	;
	
	aux(X/pstg(), Y/pstg())
	ref(Y, E/expression())
	expr(E, have)
	sbj(X, Z/pstg())
	precede(Y,Z)
	-> q_aux_have ->
	q/request_truth(user, X)
	center(Y)
	focus(q)
	;
	
</details>

#### Examples

Did you buy a house

Do you buy houses

Were you buying a house

Are you buying a house

Have you bought a house

## Auxiliary Verbs

Auxiliary verbs modify the tense of their parent verb.

TODO - missing 'go' auxiliary

 <details>
  <summary>Conversions</summary>

	aux(X/pstg(), Y/past_tense())
	type(Y, tenseful_aux)
	-> aux_past ->
	t/p_time(X, past)
	center(Y)
	focus(t)
	;
	
	aux(X/pstg(), Y/present_tense())
	type(Y, tenseful_aux)
	-> aux_present ->
	t/p_time(X, now)
	center(Y)
	focus(t)
	;

</details>

## Interrogative Modal Verb

Interrogative sentences can be formed by the modal verb preceding the subject. 

The overall meaning of the verb is also modified by the modal. 

 <details>
  <summary>Conversions</summary>
  
	modal(X/pstg(), Y/md())
	sbj(X, Z/pstg())
	precede(Y, Z)
	-> q_modal ->
	m/Y(X)
	q/request_truth(user, m)
	center(Y)
	focus(m)
	;
	
</details>

## Modals

Modify the meaning of the parent verbs by inducing a contemplation of possibilities/necessities. 

 <details>
  <summary>Conversions</summary>
  
	modal(X/pstg(), Y/pstg())
	-> modal_rule ->
	m/Y(X)
	center(Y)
	focus(m)
	;
	
</details>

## Raising Verbs

Modify the meaning of their parent verbs.

 <details>
  <summary>Conversions</summary>
  
	raise(X/pstg(), Y/past_tense())
	-> raise_verb_past ->
	p/Y(X)
	p_time(X, past)
	focus(p)
	center(Y)
	;
	
	raise(X/pstg(), Y/present_tense())
	-> raise_verb_present ->
	p/Y(X)
	p_time(X, now)
	focus(p)
	center(Y)
	;
	
</details>

## Prepositional Phrases

Captures prepositional phrases by converting the preposition into a predicate of the form `preposition(parent_predicate, object_of_preposition)`

 <details>
  <summary>Conversions</summary>

	ppmod(X/pstg(), Y/pstg())
	case(Y, Z/pstg())
	-> preposition_phrase ->
	p/Z(X,Y)
	focus(p)
	center(Z)
	;

</details>

#### Examples

I walked in the door.

The cat hid under the bed.

## Relative Clause

TODO - make better

 <details>
  <summary>Conversions</summary>

	relcl(X/pstg(), Y/pstg())
	-> relative_clause ->
	p/property(X, Y)
	focus(p)
	link(Y)
	;

</details>

## Determiner

Captures definite and indefinite specifications of concepts.

`det` dependency relation specifies instances of a concept, where
definite instances are used to construct reference links and indefinite instances aren't.

Determiners which are not a part of a `det` dependency relation are `object` instances, following the same predicate structure as above. 

 <details>
  <summary>Conversions</summary>

	det(X/pstg(), Y/dt())
	ltype(Y, ref_det)
	-> ref_concept_determiner ->
	focus(inst/X())
	center(X)
	cover(Y)
	;
	
	det(X/pstg(), Y/dt())
	ltype(Y, inst_det)
	-> inst_concept_determiner ->
	focus(inst/X())
	center(X)
	cover(Y)
	;
	
	det(X/pstg(), Y/dt())
	-> other_concept_determiner ->
	focus(X())
	center(X)
	cover(Y)
	;
	
	X/dt()
	-> determiner ->
	focus(o/object())
	center(X)
	;

</details>


## Indirect Object

Captures verb constructions with indirect objects.

 <details>
  <summary>Conversions</summary>

	dat(X/pstg(), Y/pstg())
	-> indirect_obj ->
	p/beneficiary(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

I gave the letter to you.

I bought a present for my mom.

## General Attribute

Captures `attr` dependency relation as current `property` logic which takes the form `property(subject)`.

 <details>
  <summary>Conversions</summary>
  
	attr(X/pstg(), Y/pstg())
	-> general_attribute ->
	p/Y(X)
	time(p, now)
	focus(p)
	center(Y)
	;

</details>

#### Examples

The red car

## ACL

 <details>
  <summary>Conversions</summary>

	acl(X/pstg(), Y/pstg())
	acl_indicator(Y, Z/pstg())
	-> acl_with_mention ->
	p/Z(X, Y)
	focus(p)
	center(Z)
	;
  
	acl(X/pstg(), Y/pstg())
	-> acl_rule ->
	p/property(X, Y)
	focus(p)
	link(Y)
	;

</details>

## Possessive

Captures possessive phrases by constructing a `possess` predicate between the possessor and the possessed.

 <details>
  <summary>Conversions</summary>
	  
	poss(X/pstg(), Y/pstg())
	-> obj_of_possessive ->
	focus(X())
	center(X)
	;
	
	poss(X/pstg(), Y/pstg())
	-> agent_of_possessive ->
	p/possess(Y, X)
	focus(p)
	center(Y)
	;

</details>

#### Examples

My car

John's sister

## Adverbials

Adverbial attachments usually specify some linking between predicates, without being explicitly tied
to a token in the expression. For instance, in `I bought a house yesterday morning`, the `adv` connects 
`I bought a house` with `yesterday morning` but there is not a token we want to extract as the linking predicate
itself. Instead, the two predicates are just linked together through the appropriate canonical predicate;
in this case, the most appropriate choice would be the `time` predicate.

Sometimes, there is an indicator word used that we do want to take as the linking predicate, 
like `when` in `I bought milk when I was hungry`.

Sometimes, the adverb itself is used as a predicate involving the subject it is modifying, 
as in `I ran quickly`.

Wh-adverbs (`where`, `when`, etc.) occur with `advcl` and so do not need a lone rule unlike other adverbs.

 <details>
  <summary>Conversions</summary>
  
	advnp(X/pstg(), Y/pstg())
	-> advnp_rule ->
	p/qualifier(X, Y)
	focus(p)
	link(Y)
	;
	
	advcl(X/pstg(), Y/pstg())
	advcl_indicator(Y, Z/pstg())
	-> mention_advcl ->
	p/Z(X,Y)
	focus(p)
	center(Z)
	;
	
	adv(X/pstg(), Y/adv_pos())
	-> non_wh_adv_rule ->
	p/Y(X)
	focus(p)
	link(Y)
	;

</details>

## Verb Particle

Captures verb particles by attaching a `particle` predicate to the verb.

 <details>
  <summary>Conversions</summary>
  
	prt(X/pstg(), Y/pstg())
	-> verb_particle ->
	p/particle(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

He made up an excuse.

I worked out.

I picked up my kids.

I turned on the oven.

## Conjunct

 <details>
  <summary>Conversions</summary>
  
	conj(X/pstg(), Y/pstg())
	-> conjunct_rule ->
	p/conjunct(X, Y)
	focus(p)
	link(Y)
	;
	
	cc(X/pstg(), Y/pstg())
	-> coord_conj ->
	p/conjunct_type(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Numeric

Captures expressions of quantities by constructing a `numeric` predicate between the source of the quantity and the quantity itself.

 <details>
  <summary>Conversions</summary>
  
	num(X/pstg(), Y/pstg())
	-> numeric ->
	p/quantity(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

I bought four tickets.

## Negation

 <details>
  <summary>Conversions</summary>
  
	neg(X/pstg(), Y/pstg())
	-> negation ->
	p/Y(X)
	focus(p)
	center(Y)
	;

</details>

## Appositive

 <details>
  <summary>Conversions</summary>
  
	appo(X/pstg(), Y/pstg())
	-> appositive_rule ->
	p/appositive(X, Y)
	focus(p)
	link(Y)
	;

</details>

## Vocative

Captures when the speaker addresses a specific person.

Represented as the predicate `relay_info` where the subject is information being presented and the object is the person receiving the information.

<details>
  <summary>Conversions</summary>

	voc(X/pstg(), Y/pstg())
	-> vocalization ->
	p/relay_info(X, Y)
	focus(p)
	center(Y)
	;

</details>

## General Parenthetical

<details>
  <summary>Conversions</summary>

	prn(X/pstg(), Y/pstg())
	-> parenthetical_rule ->
	p/parenthical(X, Y)
	focus(p)
	center(Y)
	;

</details>

## General Dependency

<details>
  <summary>Conversions</summary>

	dep(X/pstg(), Y/pstg())
	-> unknown_relation ->
	p/attachment(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Compound Concept

Compound attachments are treated as attributes.

<details>
  <summary>Conversions</summary>

    com(X/pstg(), Y/pstg())
    -> compound_concept ->
    p/Y(X)
	focus(p)
	center(Y)
    ;
	
</details>

## Dialogue Acknowledgements

Recognize when the speaker affirms, rejects, or acknowledges.

Represented as a predicate where the speaker is the subject and the thing being talked about is the object. 

If a target of the indication is not explicitly provided, then it is a variable.

<details>
  <summary>Conversions</summary>

	ref(Y/pstg(), E/expression())
    expr(E, affirm)
    -> affirm_interj ->
    p/affirm(user, predicate())
    focus(p)
    center(Y)
    ;
    
    ref(Y/pstg(), E/expression())
    expr(E, reject)
    -> reject_interj ->
    p/reject(user, predicate())
    focus(p)
    center(Y)
    ;
    
    ref(Y/pstg(), E/expression())
    expr(E, acknowledge)
    -> acknowledge_interj ->
    p/acknowledge(user, predicate())
    focus(p)
    center(Y)
    ;

</details>

## Dialogue Pleasantries

Recognize single-word greetings (`greet`) and goodbyes (`dismiss`).

Represented as predicates where the speaker is the subject and the dialogue partner is the object.

<details>
  <summary>Conversions</summary>

	ref(Y/interj(), E/expression())
	expr(E, greet)
	-> greet_interj ->
	p/greet(user, emora)
	focus(p)
	center(Y)
	;
	
	ref(Y/interj(), E/expression())
	expr(E, dismiss)
	-> dismiss_interj ->
	p/dismiss(user, emora)
	focus(p)
	center(Y)
	;

</details>

## Pronoun

Recognize all pronouns that exist as concepts in the KG.

If pronoun is referential (e.g. `it`), then it uses the reference linking (?)

TODO - not currently set up as references

<details>
  <summary>Conversions</summary>
  
    X/pron()  
    ref(X, E/expression())
	expr(E, he)
	-> he_pron ->
	focus(o/living_thing())
	center(X)
	;
	
	X/pron()  
    ref(X, E/expression())
	expr(E, she)
	-> she_pron ->
	focus(o/living_thing())
	center(X)
	;

	X/pron()
	ltype(X, ref_det)
	-> ref_pron ->
	focus(o/object())
	center(X)
	;

</details>
	

## Single Words

If a word is mentioned that does not match a previous rule, generate the concept if it 
is a noun or pronoun; otherwise, instantiate it as a lone concept.

<details>
  <summary>Conversions</summary>

    X/singular()
    ltype(X, object)
    kbinstance(X)
    -> instance_singular_noun ->
    focus(X)
    center(X)
    ;
    
    X/singular()
    ltype(X, object)
    -> notinstance_singular_noun ->
    focus(X())
    center(X)
    ;
    
    X/pron()
    ltype(X, object)
    -> pronoun ->
    focus(X)
    center(X)
    ;
    
    X/allow_single()
    ltype(X, object)
    -> single_word ->
    focus(X())
    center(X)
    ;
	
</details>
