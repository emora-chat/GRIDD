
# Knowledge Base Test App

**The knowledge base test app is an iteractive console app for testing knowledge base
predicates and implication rules.**

1. **Run** `GRIDD/scripts/knowledge_base_test_app.py` (working directory = folder _containing_ `GRIDD` folder)

2. **Edit** files `gridd_files/kb/kb.kg` and `gridd_files/rules/rules.kg` (generated when running script for the first time):

    - `kb.kg` and other files in the `kb` folder define predicates in the knowledge base
    - `rules.kg` and other files in the `rules` folder define rules to apply to input predicates
    
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

## Installation

(0) Required `Python >= 3.7`

(1) Install required dependencies:

* (a) Follow installation instructions at [pyswip](https://github.com/yuce/pyswip/blob/master/INSTALL.md) 
to install the latest stable version of SWI-Prolog.

    * Note: For MacOS, you must update your `PATH` and `DYLD_FALLBACK_LIBRARY_PATH` 
    environment variables to contain the SWI-Prolog file locations when executing `chatbot.py`. 
    The pyswip installation instructions provide example updated variables, however they 
    may not be correct for your computer. 
    To determine your `PATH` update, find where the `SWI-Prolog` executable file is located.
    To determine your `DYLD_FALLBACK_LIBRARY_PATH` update, find where the `libswipl.dylib` file is located.
    For our development machine, the appropriate locations were the following:

        PATH += `/Applications/SWI-Prolog.app/Contents/MacOS`

        DYLD_FALLBACK_LIBRARY_PATH = `/Applications/SWI-Prolog.app/Contents/Frameworks`
        
        If executing the script in the terminal, do the appropriate export commands for updating 
        PATH and DYLD_FALLBACK_LIBRARY_PATH.
        
        If executing the script in an IDE (e.g. Pycharm), modify the environment variables of 
        your execution configuration to appropriately update PATH and DYLD_FALLBACK_LIBRARY_PATH.

* (b) Execute `pip install -r GRIDD/requirements.txt`


(2) Clone the [structpy repository](https://github.com/jdfinch/structpy). 
Put the inner `structpy` directory into the **parent** directory of your cloned GRIDD directory 
(i.e. it should be on the same directory level as GRIDD, **not** contained within GRIDD).

    
### Running Scripts

All scripts/apps in GRIDD assume the working directory is the top-level GRIDD folder.
