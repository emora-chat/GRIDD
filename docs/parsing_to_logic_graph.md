
TODO - update all rules that determine tense to consider if auxiliary is present and remove auxiliary rule (and for auxiliary interrogative?)

## Adverbial Questions

Captures questions that start with `When`, `Where`, `Why`, and `How` in the adverb role.

Represented as `question(main_predicate, question(object()))`.

The mapping between question word and semantic concept is:

`when`=`time` | `where`=`locate` | `why`=`cause` | `how`=`qualifier`

<details>
  <summary>Conversions</summary>
  
	adv(X/pos(), Y/question_word())
	aux(X, Z/pos())
	nsbj(X, A/pos())
	precede(Y, Z)
	precede(Z, A)
	-> q_nadv ->
	p/Y(X, o/object())
	question(o)
	focus(p)
	center(Y)
	cover(Z)
	;
	
	adv(X/pos(), Y/question_word())
	aux(X, Z/pos())
	csbj(X, A/pos())
	precede(Y, Z)
	precede(Z, A)
	-> q_cadv ->
	p/Y(X, o/object())
	question(o)
	focus(p)
	center(Y)
	cover(Z)
	;
  
</details>

#### Examples

How did this happen

How did you do on the test

Why are you sad

When did you start reading

## Copular Questions

Captures questions that start with `How`, `What`, and `Who` as the root of a copular construction or as the determiner of the root. 

Represented as `copula(nsbj, question(question_word))`.

<details>
  <summary>Conversions</summary>
  
	cop(X/pos(), Y/present_tense())
	nsbj(X, Z/pos())
	det(X, D/question_word())
	-> qdet_ncopula_present ->
	is_type(Y)
	is_type(X)
	p/Y(Z, inst/X())
	question(inst)
	time(p, now)
	focus(p)
	center(X)
	cover(D)
	;
	
	cop(X/pos(), Y/present_tense())
	nsbj(X, Z/pos())
	det(X, D/question_word())
	-> qdet_ccopula_present ->
	is_type(Y)
	is_type(X)
	p/Y(Z, inst/X())
	question(inst)
	time(p, now)
	focus(p)
	center(X)
	cover(D)
	;
	
	cop(X/pos(), Y/past_tense())
	nsbj(X, Z/pos())
	det(X, D/question_word())
	-> qdet_ncopula_past ->
	is_type(Y)
	is_type(X)
	p/Y(Z, inst/X())
	question(inst)
	time(p, past)
	focus(p)
	center(X)
	cover(D)
	;
	
	cop(X/pos(), Y/past_tense())
	nsbj(X, Z/pos())
	det(X, D/question_word())
	-> qdet_ccopula_past ->
	is_type(Y)
	is_type(X)
	p/Y(Z, inst/X())
	question(inst)
	time(p, past)
	focus(p)
	center(X)
	cover(D)
	;
  
	cop(X/question_word(), Y/present_tense())
	nsbj(X, Z/pos())
	-> qw_ncopula_present ->
	is_type(Y)
	p/Y(Z, X)
	question(X)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/question_word(), Y/present_tense())
	csbj(X, Z/pos())
	-> qw_ccopula_present ->
	is_type(Y)
	p/Y(Z, X)
	question(X)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/question_word(), Y/past_tense())
	nsbj(X, Z/pos())
	-> qw_ncopula_past ->
	is_type(Y)
	p/Y(Z, X)
	question(X)
	time(p, past)
	focus(p)
	center(X)
	;
	
	cop(X/question_word(), Y/past_tense())
	csbj(X, Z/pos())
	-> qw_ccopula_past ->
	is_type(Y)
	p/Y(Z, X)
	question(X)
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

Represented by wrapping the subject/object/dative with the `question` predicate. 

<details>
  <summary>Conversions</summary>
  
	obj(X/pos(), Y/question_word())
	-> obj_question ->
	q/question(object())
	center(Y)
	focus(q)
	;
	
	nsbj(X/pos(), Y/question_word())
	-> nsbj_question ->
	q/question(object())
	center(Y)
	focus(q)
	;
	
	dat(X/pos(), Y/question_word())
	aux(X, Z/pos())
	nsbj(X, A/pos())
	precede(Y, Z)
	precede(Z, A)
	-> q_ndat ->
	p/indirect_obj(X, o/object())
	question(o)
	center(Y)
	cover(Z)
	focus(p)
	;
		
	dat(X/pos(), Y/question_word())
	aux(X, Z/pos())
	csbj(X, A/pos())
	precede(Y, Z)
	precede(Z, A)
	-> q_cdat ->
	p/indirect_obj(X, o/object())
	question(o)
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
  
	det(X/pos(), Y/question_word())
	obj(Z/pos(), X)
	aux(Z, A/pos())
	-> q_aux_det ->
	is_type(X)
	inst/X()
	question(inst)
	focus(inst)
	center(X)
	cover(Y)
	;
	
	det(X/pos(), Y/question_word())
	obj(Z/pos(), X)
	aux(Z, A/present_tense())
	-> q_aux_det_pres ->
	p/time(Z, now)
	focus(p)
	center(A)
	;
	
	det(X/pos(), Y/question_word())
	obj(Z/pos(), X)
	aux(Z, A/past_tense())
	-> q_aux_det_past ->
	p/time(Z, past)
	focus(p)
	center(A)
	;
	
	det(X/pos(), Y/question_word())
	-> q_det ->
	is_type(X)
	inst/X()
	question(inst)
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

Subject can be a noun or clause.

<details>
  <summary>Conversions</summary>

	cop(X/pos(), Y/present_tense())
	nsbj(X, Z/pos())
	precede(Y, Z)
	-> q_nsbj_copula_present ->
	is_type(Y)
	p/Y(Z,X)
	q/question(p)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/present_tense())
	csbj(X, Z/pos())
	precede(Y, Z)
	-> q_csbj_copula_present ->
	is_type(Y)
	p/Y(Z,X)
	q/question(p)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/past_tense())
	nsbj(X, Z/pos())
	precede(Y, Z)
	-> q_nsbj_copula_past ->
	is_type(Y)
	p/Y(Z,X)
	q/question(p)
	time(p, past)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/past_tense())
	csbj(X, Z/pos())
	precede(Y, Z)
	-> q_csbj_copula_past ->
	is_type(Y)
	p/Y(Z,X)
	q/question(p)
	time(p, past)
	focus(p)
	center(X)
	;
 
</details>

#### Examples

Is John a student?

Was the book good?

## Copula

Copula constructions become two-argument predicates of the format `copula(subject, root)`.

Subject can be a noun or clause.

The specific copular verb is captured by an identifier rule s.t. it will be merged into the 
predicate.

<details>
  <summary>Conversions</summary>

	cop(X/pos(), Y/present_tense())
	nsbj(X, Z/pos())
	-> nsbj_copula_present ->
	is_type(Y)
	p/Y(Z,X)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/present_tense())
	csbj(X, Z/pos())
	-> csbj_copula_present ->
	is_type(Y)
	p/Y(Z,X)
	time(p, now)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/past_tense())
	nsbj(X, Z/pos())
	-> nsbj_copula_past ->
	is_type(Y)
	p/Y(Z,X)
	time(p,past)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/past_tense())
	csbj(X, Z/pos())
	-> csbj_copula_past ->
	is_type(Y)
	p/Y(Z,X)
	time(p,past)
	focus(p)
	center(X)
	;
	
	cop(X/pos(), Y/pos())
	-> id_copular_verb ->
	focus(Y)
	center(Y)
	;
 
</details>
 
#### Examples

John is a student.

Sally became a doctor last year.

## Subject-Verb-Object

Two-argument predicates of the format `root(subject, object)`.

Subject can be a noun or clause.

 <details>
  <summary>Conversions</summary>
  
	nsbj(X/past_tense(), Y/pos())
	obj(X, Z/pos())
	-> nsbj_dobj_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	;
	
	csbj(X/past_tense(), Y/pos())
	obj(X, Z/pos())
	-> csbj_dobj_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	;
	
	nsbj(X/present_tense(), Y/pos())
	obj(X, Z/pos())
	-> nsbj_dobj_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	csbj(X/present_tense(), Y/pos())
	obj(X, Z/pos())
	-> csbj_dobj_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;

 </details>


## Light Verb with Subject and Object

Two-argument predicates of the format `root(subject, object)`. The light verb is dropped. The determiner of the root is dropped, if there is one.

Subject can be a noun or clause.

 <details>
  <summary>Conversions</summary>

	nsbj(X/noun(), Y/pos())
	det(X, A/dt())
	obj(X, Z/pos())
	lv(X, U/past_tense())
	-> nsbj_obj_det_light_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;
	
	csbj(X/noun(), Y/pos())
	det(X, A/dt())
	obj(X, Z/pos())
	lv(X, U/past_tense())
	-> csbj_obj_det_light_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;
	
	nsbj(X/noun(), Y/pos())
	det(X, A/dt())
	obj(X, Z/pos())
	lv(X, U/present_tense())
	-> nsbj_obj_det_light_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;
	
	csbj(X/noun(), Y/pos())
	det(X, A/dt())
	obj(X, Z/pos())
	lv(X, U/present_tense())
	-> csbj_obj_det_light_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;

	nsbj(X/noun(), Y/pos())
	obj(X, Z/pos())
	lv(X, U/past_tense())
	-> nsbj_obj_light_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	;
	
	csbj(X/noun(), Y/pos())
	obj(X, Z/pos())
	lv(X, U/past_tense())
	-> csbj_obj_light_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p, past)
	focus(p)
	center(X)
	;
	
	nsbj(X/noun(), Y/pos())
	obj(X, Z/pos())
	lv(X, U/present_tense())
	-> nsbj_obj_light_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	csbj(X/noun(), Y/pos())
	obj(X, Z/pos())
	lv(X, U/present_tense())
	-> csbj_obj_light_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;

 </details>



#### Examples

John made a call to Mary.

## Light Verb with Subject only

One-argument predicates of the format `root(subject)`. The light verb is dropped. The determiner of the root is dropped, if there is one.

Subject can be a noun or clause.

 <details>
  <summary>Conversions</summary>

	nsbj(X/noun(), Y/pos())
	det(X, A/dt())
	lv(X, U/past_tense())
	-> nsbj_det_light_verb_past ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;
	
	csbj(X/noun(), Y/pos())
	det(X, A/dt())
	lv(X, U/past_tense())
	-> csbj_det_light_verb_past ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	cover(A)
	;
	
	nsbj(X/noun(), Y/pos())
	det(X, A/dt())
	lv(X, U/present_tense())
	-> nsbj_det_light_verb_present ->
	is_type(X)
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;
	
	csbj(X/noun(), Y/pos())
	det(X, A/dt())
	lv(X, U/present_tense())
	-> csbj_det_light_verb_present ->
	is_type(X)
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	cover(A)
	;

	nsbj(X/noun(), Y/pos())
	lv(X, U/past_tense())
	-> nsbj_light_verb_past ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	;
	
	csbj(X/noun(), Y/pos())
	lv(X, U/past_tense())
	-> csbj_light_verb_past ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	;
	
	nsbj(X/noun(), Y/pos())
	lv(X, U/present_tense())
	-> nsbj_light_verb_present ->
	is_type(X)
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	;
	
	csbj(X/noun(), Y/pos())
	lv(X, U/present_tense())
	-> csbj_light_verb_present ->
	is_type(X)
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	;

 </details>

#### Examples

John made a call.

## Complement

 <details>
  <summary>Conversions</summary>

	nsbj(X/past_tense(), Y/pos())
	comp(X, Z/pos())
	-> nsbj_outer_comp_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p,past)
	focus(p)
	center(X)
	;
	
	csbj(X/past_tense(), Y/pos())
	comp(X, Z/pos())
	-> csbj_outer_comp_verb_past ->
	is_type(X)
	p/X(Y,Z)
	time(p,past)
	focus(p)
	center(X)
	;
	
	nsbj(X/present_tense(), Y/pos())
	comp(X, Z/pos())
	-> nsbj_outer_comp_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	csbj(X/present_tense(), Y/pos())
	comp(X, Z/pos())
	-> csbj_outer_comp_verb_present ->
	is_type(X)
	p/X(Y,Z)
	time(p, now)
	focus(p)
	center(X)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	nsbj(Z, B/pos())
	obj(Z, A/pos())
	-> nsbj_nsbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(B,A)
	focus(p)
	center(Z)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	csbj(Z, B/pos())
	obj(Z, A/pos())
	-> nsbj_csbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(B,A)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	nsbj(Z, B/pos())
	obj(Z, A/pos())
	-> csbj_nsbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(B,A)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	csbj(Z, B/pos())
	obj(Z, A/pos())
	-> csbj_csbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(B,A)
	focus(p)
	center(Z)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	nsbj(Z, A/pos())
	-> nsbj_nsbj_inner_comp_verb ->
	is_type(Z)
	p/Z(A)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	nsbj(Z, A/pos())
	-> csbj_nsbj_inner_comp_verb ->
	is_type(Z)
	p/Z(A)
	focus(p)
	center(Z)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	csbj(Z, A/pos())
	-> nsbj_csbj_inner_comp_verb ->
	is_type(Z)
	p/Z(A)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	csbj(Z, A/pos())
	-> csbj_csbj_inner_comp_verb ->
	is_type(Z)
	p/Z(A)
	focus(p)
	center(Z)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	obj(Z, A/pos())
	-> nsbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(Y,A)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	obj(Z, A/pos())
	-> csbj_inner_comp_with_obj_verb ->
	is_type(Z)
	p/Z(Y,A)
	focus(p)
	center(Z)
	;
	
	nsbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	-> nsbj_inner_comp_verb ->
	is_type(Z)
	p/Z(Y)
	focus(p)
	center(Z)
	;
	
	csbj(X/verb(), Y/pos())
	comp(X, Z/pos())
	-> csbj_inner_comp_verb ->
	is_type(Z)
	p/Z(Y)
	focus(p)
	center(Z)
	;

 </details>

## Verbs without Objects

Captures expressions where the verb only has a subject.

 <details>
  <summary>Conversions</summary>

	nsbj(X/past_tense(), Y/pos())
	-> nsbj_no_obj_past_verb ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	;
	
	csbj(X/past_tense(), Y/pos())
	-> csbj_no_obj_past_verb ->
	is_type(X)
	p/X(Y)
	time(p, past)
	focus(p)
	center(X)
	;
	
	nsbj(X/present_tense(), Y/pos())
	-> nsbj_no_obj_present_verb ->
	is_type(X)
	p/X(Y)
	time(p, now)
	focus(p)
	center(X)
	;
	
	csbj(X/present_tense(), Y/pos())
	-> csbj_no_obj_present_verb ->
	is_type(X)
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
	
	aux(X/pos(), Y/past_tense())
	ref(Y, E/expression())
	expr(E, do)
	nsbj(X, Z/pos())
	precede(Y,Z)
	-> q_aux_do_past ->
	q/question(X)
	aux_time(X, past)
	center(Y)
	focus(q)
	;
	
	aux(X/pos(), Y/present_tense())
	ref(Y, E/expression())
	expr(E, do)
	nsbj(X, Z/pos())
	precede(Y,Z)
	-> q_aux_do_present ->
	q/question(X)
	aux_time(X, now)
	center(Y)
	focus(q)
	;
	
	aux(X/pos(), Y/past_tense())
	ref(Y, E/expression())
	expr(E, be)
	nsbj(X, Z/pos())
	precede(Y,Z)
	-> q_aux_be_past ->
	q/question(X)
	aux_time(X, past)
	center(Y)
	focus(q)
	;
	
	aux(X/pos(), Y/present_tense())
	ref(Y, E/expression())
	expr(E, be)
	nsbj(X, Z/pos())
	precede(Y,Z)
	-> q_aux_be_present ->
	q/question(X)
	aux_time(X, now)
	center(Y)
	focus(q)
	;
	
	aux(X/pos(), Y/pos())
	ref(Y, E/expression())
	expr(E, have)
	nsbj(X, Z/pos())
	precede(Y,Z)
	-> q_aux_have ->
	q/question(X)
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

TODO - properly update tense of main verb using auxiliaries, right now we have both a `time` predicate and an `aux_time` predicate

 <details>
  <summary>Conversions</summary>

	aux(X/pos(), Y/past_tense())
	ref(Y, E/expression())
	expr(E, do)
	-> aux_do_past ->
	t/aux_time(X, past)
	center(Y)
	focus(t)
	;
	
	aux(X/pos(), Y/present_tense())
	ref(Y, E/expression())
	expr(E, do)
	-> aux_do_present ->
	t/aux_time(X, now)
	center(Y)
	focus(t)
	;
	
	aux(X/pos(), Y/past_tense())
	ref(Y, E/expression())
	expr(E, be)
	-> aux_be_past ->
	t/aux_time(X, past)
	center(Y)
	focus(t)
	;
	
	aux(X/pos(), Y/present_tense())
	ref(Y, E/expression())
	expr(E, be)
	-> aux_be_present ->
	t/aux_time(X, now)
	center(Y)
	focus(t)
	;

</details>

## Interrogative Modal Verb

Interrogative sentences can be formed by the modal verb preceding the subject. 

The overall meaning of the verb is also modified by the modal. 

 <details>
  <summary>Conversions</summary>
  
	modal(X/pos(), Y/md())
	nsbj(X, Z/pos())
	precede(Y, Z)
	-> q_modal ->
	m/mode(X, Y)
	q/question(m)
	center(Y)
	focus(m)
	;
	
</details>

## Modals

Modify the meaning of the parent verbs by inducing a contemplation of possibilities/necessities.

TODO - does this ever affect tense? 

 <details>
  <summary>Conversions</summary>
  
	modal(X/pos(), Y/md())
	-> modal ->
	m/mode(Y,X)
	center(Y)
	focus(m)
	;
	
</details>

## Raising Verbs

Modify the meaning of their parent verbs.

 <details>
  <summary>Conversions</summary>
  
	raise(X/pos(), Y/past_tense())
	-> raise_verb_past ->
	p/mode(X, Y)
	time(X, past)
	focus(p)
	center(Y)
	;
	
	raise(X/pos(), Y/present_tense())
	-> raise_verb_present ->
	p/mode(X, Y)
	time(X, now)
	focus(p)
	center(Y)
	;
	
</details>

## Prepositional Phrases

Captures prepositional phrases by converting the preposition into a predicate of the form `preposition(parent_predicate, object_of_preposition)`

 <details>
  <summary>Conversions</summary>

	ppmod(X/pos(), Y/pos())
	case(Y, Z/pos())
	-> preposition_phrase ->
	is_type(Z)
	p/Z(X,Y)
	focus(p)
	center(Z)
	;

</details>

#### Examples

I walked in the door.

The cat hid under the bed.

## Passive Constructions

Captures sentences with passive voice.

 <details>
  <summary>Conversions</summary>

	nsbj(X/pos(), Y/pos())
	obj(X, Z/pos())
	precede(Z, X)
	-> nobj_passive_voice ->
	is_type(X)
	p/X(Y, Z)
	focus(p)
	center(X)
	;
	
	csbj(X/pos(), Y/pos())
	obj(X, Z/pos())
	precede(Z, X)
	-> cobj_passive_voice ->
	is_type(X)
	p/X(Y, Z)
	focus(p)
	center(X)
	;

	obj(X/pos(), Y/pos())
	precede(Y, X)
	-> obj_passive_voice ->
	is_type(X)
	p/X(Y)
	focus(p)
	center(X)
	;

</details>

#### Examples

The dog was found.

The dog was found by the policeman.

I was chosen.

## Relative Clause

TODO - make better

 <details>
  <summary>Conversions</summary>

	relcl(X/pos(), Y/pos())
	-> relative_clause ->
	p/qualifier(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Determiner

Captures definite and indefinite specifications of concepts.

`det` dependency relation specifies instances of a concept, where
definite instances exist in a `referential` predicate and ndefinite instances exist in an `instantiative` predicate.

Determiners which are not a part of a `det` dependency relation are `object` instances, following the same predicate structure as above. 

 <details>
  <summary>Conversions</summary>

	det(X/pos(), Y/dt())
	ltype(Y, ref_det)
	-> ref_concept_determiner ->
	is_type(X)
	focus(inst/X())
	referential(inst)
	center(X)
	cover(Y)
	;
	
	det(X/pos(), Y/dt())
	ltype(Y, inst_det)
	-> inst_concept_determiner ->
	is_type(X)
	focus(inst/X())
	instantiative(inst)
	center(X)
	cover(Y)
	;
	
	det(X/pos(), Y/dt())
	-> other_concept_determiner ->
	is_type(X)
	focus(X())
	center(X)
	cover(Y)
	;
	
	X/dt()
	ltype(X, ref_det)
	-> ref_determiner ->
	focus(o/object())
	referential(o)
	center(X)
	;
	
	X/dt()
	ltype(X, inst_det)
	-> inst_determiner ->
	focus(o/object())
	instantiative(o)
	center(X)
	;

</details>


## Indirect Object

Captures verb constructions with indirect objects.

 <details>
  <summary>Conversions</summary>

	dat(X/pos(), Y/pos())
	-> indirect_obj ->
	p/indirect_obj(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

I gave the letter to you.

I bought a present for my mom.

## General Attribute

Captures `attr` dependency relation as `property` logic relation.

 <details>
  <summary>Conversions</summary>
  
	attr(X/pos(), Y/pos())
	-> general_attribute ->
	p/property(X,Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

The red car

## ACL

 <details>
  <summary>Conversions</summary>
  
	acl(X/pos(), Y/pos())
	-> acl ->
	p/property(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Possessive

Captures possessive phrases by constructing a `possess` predicate between the possessor and the possessed.

 <details>
  <summary>Conversions</summary>
	  
	poss(X/pos(), Y/pos())
	-> obj_of_possessive ->
	is_type(X)
	focus(X())
	center(X)
	;
	
	poss(X/pos(), Y/pos())
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

 <details>
  <summary>Conversions</summary>
  
	advnp(X/pos(), Y/pos())
	-> advnp ->
	p/qualifier(X, Y)
	focus(p)
	center(Y)
	;
	
	advcl(X/pos(), Y/pos())
	adv(Y, Z/pos())
	-> advcl_adv ->
	is_type(Z)
	p/Z(X,Y)
	focus(p)
	center(Z)
	;
	
	advcl(X/pos(), Y/pos())
	-> advcl ->
	p/qualifier(X, Y)
	focus(p)
	center(Y)
	;
	
	adv(X/pos(), Y/pos())
	-> adv ->
	p/qualifier(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Verb Particle

Captures verb particles by attaching a `particle` predicate to the verb.

 <details>
  <summary>Conversions</summary>
  
	prt(X/pos(), Y/pos())
	-> verb_particle ->
	p/particle(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

He made up an excuse.

## Conjunct

 <details>
  <summary>Conversions</summary>
  
	conj(X/pos(), Y/pos())
	-> conjunct ->
	p/conjunct(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Numeric

Captures expressions of quantities by constructing a `numeric` predicate between the source of the quantity and the quantity itself.

 <details>
  <summary>Conversions</summary>
  
	num(X/pos(), Y/pos())
	-> numeric ->
	p/numeric(X, Y)
	focus(p)
	center(Y)
	;

</details>

#### Examples

I bought four tickets.

## Negation

 <details>
  <summary>Conversions</summary>
  
	neg(X/pos(), Y/pos())
	-> negation ->
	p/negate(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Appositive

 <details>
  <summary>Conversions</summary>
  
	appo(X/pos(), Y/pos())
	-> appositive ->
	p/appositive(X, Y)
	focus(p)
	center(Y)
	;

</details>

## Vocative

Captures when the speaker addresses a specific person.

Represented as the predicate `relay_info` where the subject is information being presented and the object is the person receiving the information.

<details>
  <summary>Conversions</summary>

	voc(X/pos(), Y/pos())
	-> vocalization ->
	p/relay_info(X, Y)
	focus(p)
	center(Y)
	;

</details>

## General Parenthetical

<details>
  <summary>Conversions</summary>

	prn(X/pos(), Y/pos())
	-> parenthetical ->
	p/parenthical(X, Y)
	focus(p)
	center(Y)
	;

</details>

## General Dependency

<details>
  <summary>Conversions</summary>

	dep(X/pos(), Y/pos())
	-> unknown_relation ->
	p/attachment(X, Y)
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

	disc(X/pos(), Y/pos())
	ref(Y, E/expression())
	expr(E, affirm)
	-> affirm_disc ->
	p/affirm(user, X)
	focus(p)
	center(Y)
	;
	
	ref(Y/interj(), E/expression())
	expr(E, affirm)
	-> affirm_interj ->
	p/affirm(user, object())
	focus(p)
	center(Y)
	;
	
	disc(X/pos(), Y/pos())
	ref(Y, E/expression())
	expr(E, reject)
	-> reject_disc ->
	p/reject(user, X)
	focus(p)
	center(Y)
	;
	
	ref(Y/interj(), E/expression())
	expr(E, reject)
	-> reject_interj ->
	p/reject(user, object())
	focus(p)
	center(Y)
	;
	
	disc(X/pos(), Y/pos())
	ref(Y, E/expression())
	expr(E, acknowledge)
	-> acknowledge_disc ->
	p/acknowledge(user, X)
	focus(p)
	center(Y)
	;
	
	ref(Y/interj(), E/expression())
	expr(E, acknowledge)
	-> acknowledge_interj ->
	p/acknowledge(user, object())
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

If pronoun is referential (e.g. `it`), then it has a `referential` predicate. 

<details>
  <summary>Conversions</summary>

	X/pron()
	ltype(X, ref_det)
	-> ref_pron ->
	focus(o/object())
	referential(o)
	center(X)
	;

	X/pron()
	-> pron ->
	focus(X)
	center(X)
	;
	
</details>

## Named Entity

Recognize all nouns that exist as concepts in the KG. 

<details>
  <summary>Conversions</summary>

	X/noun()
	-> concept ->
	focus(X)
	center(X)
	;
	
</details>

## Single Words

If a word is mentioned that does not match a previous rule, instantiate it as a lone concept.

<details>
  <summary>Conversions</summary>

	X/pos()
	-> single_word ->
	focus(X())
	center(X)
	;
	
</details>

## Compound Concept

Compound concepts are condensed into a single entity when the dependency relations are preprocessed  into a `concept graph`, before any conversion rules are applied.
 