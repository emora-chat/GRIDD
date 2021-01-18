
# Knowledge Base Test App

**The knowledge base test app is an iteractive console app for testing knowledge base
predicates and implication rules.**

1. **Run** `GRIDD/data_structures/knowledge_base_test_app.py` (working directory=`GRIDD` folder)

2. **Edit** files `GRIDD/kb.kg` and `GRIDD/rules.kg`:

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

## Installation
Python version: 

`Python3.7`

(1) Follow installation instructions at [pyswip](https://github.com/yuce/pyswip/blob/master/INSTALL.md) 
to install the latest stable version of SWI-Prolog.

* Note 1: For MacOS installation, for Step 3 (exporting executables), the given example paths 
may not be correct for your computer. To determine your `PATH` update, find where the `SWI-Prolog` executable file is located.
To determine your `DYLD_FALLBACK_LIBRARY_PATH` update, find where the `libswipl.dylib` file is located.
For our development machine, we used the following export commands:
```
export PATH=$PATH:/Applications/SWI-Prolog.app/Contents/MacOS
export DYLD_FALLBACK_LIBRARY_PATH=/Applications/SWI-Prolog.app/Contents/Frameworks
```

<!--- * Note 2: For MacOS installation, add the two export commands to the end of the file: `~/.bash_profile`.
When you open a new terminal, the changes you made to your `bash_profile` will take effect.--->

* Note 2: For MacOS, update the `PATH` variable of your `environment variables` execution configuration to contain the location identified in Note 1.
And add the `DYLD_FALLBACK_LIBRARY_PATH` variable from Note 1 to your `environment variables` script execution configuration as well. If you are 
using Pycharm, you can do this through the `Edit Configurations...` option of your script execution.

(2) Install required dependencies:

`pip install -r GRIDD/requirements.txt`
    
