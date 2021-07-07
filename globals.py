
KB_FOLDERNAME = 'kg_files_stripped'      # Folder name for knowledge base .kg files

KB = 'kb'                       # Namespace of Knowledge Base Concept Graph
WM = 'wm'                       # Namespace of Working Memory Concept Graph

UTTER_TRUNC = 20                # Truncate user utterance to this length for time and memory processing
PRUNE_THRESHOLD = 50            # Number of main predicate nodes to keep in WM after pruning
CONF_ITER = 5
SAL_ITER = 5

SENSORY_SALIENCE = 1.0          # salience value for predicates that are considered via sensations
ASSOCIATION_DECAY = 0.3         # decrease in salience for concepts pulled into attention by neighbors
EVIDENCE_DECAY = 0.1            # decrease in salience for concepts added to attention by inference
TIME_DECAY = 0.1                # decrease in salience for working memory concepts per timestep

NONASSERT = 'nonassert'         # predicate type indicating arguments that are unasserted
SUBJ_ESSENTIAL = 'subj_essential'         # predicate type indicating required attachments for predicate instance definition where instance is the subject
OBJ_ESSENTIAL = 'obj_essential'         # predicate type indicating required attachments for predicate instance definition where instance is the object

ASSERT = 'assert'               # monopredicate indicating argument is asserted
USER_AWARE = 'user_aware'       # monopredicate indicating user is aware of the concept

TYPE = 'type'                   # bipredicate indicating a type/subtype relationship
EXPR = 'expr'                   # bipredicate indicating ARG0 is an expression of ARG1
AFFIRM = 'affirm'               # bipredicate indicating speaker and affirmative/yes statement
REJECT = 'reject'               # bipredicate indicating speaker and rejective/no statement
TIME = 'time'                   # bipredicate indicating time specification
SPAN_REF = 'ref'                # bipredicate linking span nodes to the concepts they refer to
SPAN_DEF = 'def'                # bipredicate linking span nodes to the concept their language defines
SPANTURN = 5                    # relative historical turn index of spans to delete from WM

REQ_ARG = 'request'             # bipredicate of subject requesting disambiguation of the object (argument question)
REQ_TRUTH = 'request_truth'     # bipredicate of subject requesting truth value of the object (y/n question)
REQ_SAT = 'req_sat'             # monopredicate indicating request was answered
REQ_UNSAT = 'req_unsat'         # monopredicate indicating request is unresolved

OBJECT = 'object'               # base concept type
GROUP = 'group'                 # entity type indicating subtypes are groups
CLASS = 'class'                 # entity type indicating class definition

UTURN = '_uturn'                # predicate used for user turn tracking in WM
ETURN = '_eturn'                # predicate used for emora turn tracking in WM
OP_UTURN = 'uturn'              # operator predicate used in rule creation to specify user turn information
OP_ETURN = 'eturn'              # operator predicate used in rule creation to specify emora turn information
UTURN_POS = 'uturnpos'          # metadata feature used to indicate relative turn index used by OP_UTURN in rules
ETURN_POS = 'eturnpos'          # metadata feature used to indicate relative turn index used by OP_ETURN in rules

SALIENCE_IN_LINK = 'salin'      # UpdateGraph label for salience propagation
SALIENCE_OUT_LINK = 'salout'    # UpdateGraph label for salience propagation

COLDSTART = 'coldstart'         # metadata bool feature preventing salience decay until selected
SALIENCE = 'salience'           # metadata float feature representing attention w.r.t. emora
CONNECTIVITY = 'conn'           # metadata integer feature representing neighborhood cardinality
WINDOW = 10
SAL_WINDOW = 'salw'
COHERENCE = 'coherence'

COMPS = 'comps'                 # metagraph link for component predicate and entity instances of mention
VAR = 'var'                     # metagraph variable from one concept to another concept, in which the second concept is a variable
GROUP_DEF_SP = 'group_def_sp'   # metagraph link for spans that define the group constraints
GROUP_PROP_SP = 'group_prop_sp' # metagraph link for spans that define the group properties
GROUP_DEF = 'group_def'         # metagraph link for concepts that define the group constraints
GROUP_PROP = 'group_prop'       # metagraph link for concepts that define the group properties
REF_SP = 'refsp'                # metagraph link for spans that define reference constraints
REF = 'ref'                     # metagraph link for concepts that define reference constraints
RREF = 'rref'                   # metagraph ref link for resolved references
RVAR = 'rvar'                   # metagraph var link for vars involved in resolved references
DP_SUB = 'dp_sub'               # metagraph link between syntactic root and subtree dependencies
ASS_LINK = 'ass'                # metagraph link for propagating confidence from an assertion to syntactic children
PRE = 'pre'                     # metagraph precondition link
POST = 'post'                   # metagraph postcondition link
AND_LINK = 'and'                # metagraph link for confidence propagation w.r.t emora
NAND_LINK = 'nand'              # metagraph link for confidence propagation w.r.t emora
OR_LINK = 'or'                  # metagraph link for confidence propagation w.r.t emora
NOR_LINK = 'nor'                # metagraph link for confidence propagation w.r.t emora
UAND_LINK = 'and'                # metagraph link for confidence propagation w.r.t user
UNAND_LINK = 'nand'              # metagraph link for confidence propagation w.r.t user
UOR_LINK = 'or'                  # metagraph link for confidence propagation w.r.t user
UNOR_LINK = 'nor'                # metagraph link for confidence propagation w.r.t user

META = {COMPS, VAR,
        GROUP_DEF_SP, GROUP_PROP_SP, GROUP_DEF, GROUP_PROP,
        REF_SP, REF,
        DP_SUB, ASS_LINK,
        PRE, POST,
        AND_LINK, NAND_LINK, OR_LINK, NOR_LINK}

SAL_FREE = {ASSERT, NONASSERT, AFFIRM,
            REJECT, TIME, SPAN_DEF,
            SPAN_REF, USER_AWARE, REQ_SAT, REQ_UNSAT,
            '_tanchor'}    # Predicate types that do not propogate salience to subtypes and whose salience does not decrease

PRIM = {SPAN_DEF, SPAN_REF,
        ASSERT, NONASSERT,
        USER_AWARE, EXPR, REQ_SAT, REQ_UNSAT}             # Predicate types that are primitive


UNKNOWN_TYPES = {'unknown_verb', 'unknown_noun', 'unknown_pron', 'unknown_adj', 'unknown_adv', 'unknown_other'}


PRIORITY_WEIGHT = 0.33
SAL_WEIGHT = 0.33
COH_WEIGHT = 0.33
DEFAULT_PRIORITY = 0.5
PRIORITY_PRED = '_pr'

DEFAULT_TEMPLATE_TYPE = '_rp'
TEMPLATE_TYPE = '_t'

NLU_NAMESPACE = 'r_'
