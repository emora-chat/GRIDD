DEBUG = False

SENSORY_SALIENCE = 1.0          # salience value for predicates that are considered via sensations
ASSOCIATION_DECAY = 0.3         # decrease in salience for concepts pulled into attention by neighbors
EVIDENCE_DECAY = 0.1            # decrease in salience for concepts added to attention by inference
TIME_DECAY = 0.1                # decrease in salience for working memory concepts per timestep
NONASSERT = 'nonassert'         # predicate type indicating arguments that are unasserted
ASSERT = 'assert'               # monopredicate indicating argument is asserted
TYPE = 'type'                   # bipredicate type indicating a type/subtype relationship
EXPR = 'expr'                   # bipredicate type indicating ARG0 is an expression of ARG1
COLDSTART = 'coldstart'         # metadata bool feature preventing salience decay until selected
SALIENCE = 'salience'           # metadata float feature representing attention w.r.t. emora
CONFIDENCE = 'confidence'       # metadata float feature representing truth value w.r.t emora
USER_AWARE = 'user_aware'       # monopredicate indicating user is aware of the concept
ESSENTIAL = 'essential'         # predicate type indicating required attachments for predicate instance definition
GROUP = 'group'                 # entity type indicating subtypes are groups
GROUP_DEF_SP = 'group_def_sp'   # metagraph link for spans that define the group constraints
GROUP_PROP_SP = 'group_prop_sp'  # metagraph link for spans that define the group properties
GROUP_DEF = 'group_def'         # metagraph link for concepts that define the group constraints
GROUP_PROP = 'group_prop'       # metagraph link for concepts that define the group properties
CLASS = 'class'                 # entity type indicating class definition
CONNECTIVITY = 'conn'           # metadata integer feature representing neighborhood cardinality
ASS_LINK = 'ass'                # metagraph link for propagating confidence from an assertion to syntactic children
AND_LINK = 'and'                # metagraph link for confidence propagation
NAND_LINK = 'nand'              # metagraph link for confidence propagation
OR_LINK = 'or'                  # metagraph link for confidence propagation
NOR_LINK = 'nor'                # metagraph link for confidence propagation
SALIENCE_IN_LINK = 'salin'      # UpdateGraph label for salience propagation
SALIENCE_OUT_LINK = 'salout'    # UpdateGraph label for salience propagation
BASE = 'base'                   # metadata variable to indicate base confidence (conf shouldn't drop)
IS_TYPE = 'is_type'             # metadata type/instance specifier
PRE = 'pre'                     # metagraph precondition link
POST = 'post'                   # metagraph postcondition link
REF = 'ref'                     # metagraph reference link
VAR = 'var'                     # var reference variable link
AFFIRM = 'affirm'               # predicate indicating affirmative/yes statement
REJECT = 'reject'               # predicate indicating rejective/no statement
TIME = 'time'                   # predicate indicating time specification
SPAN_REF = 'ref'                # predicate linking span nodes to the concepts they refer to
SPAN_DEF = 'def'                # predicate linking span nodes to the concept their language defines
OBJECT = 'object'               # base concept type

SAL_FREE = {ASSERT, NONASSERT, AFFIRM,
            REJECT, TIME, SPAN_DEF,
            SPAN_REF, USER_AWARE}    # Predicate types that do not propogate salience to subtypes and whose salience does not decrease

PRIM = {SPAN_DEF, SPAN_REF,
        ASSERT, NONASSERT,
        USER_AWARE, 'expr'}             # Predicate types that are primitive
