
from structpy import specification
from GRIDD.data_structures.span import Span
from GRIDD.data_structures.knowledge_base import KnowledgeBase
from GRIDD.data_structures.id_map import IdMap
import os

@specification
class ElitDPSpec:

    @specification.init
    def ELITDP(ElitDPToLogic, knowledge_base, template_file_names, device='cpu'):
        """
        `knowledge_base` is a KnowledgeBase object that the expression working memory has access to
        `template_file_names` are a variable number of filenames specifying parse-to-logic templates to load
        `device` specifies whether to run the inference engine on cpu or gpu for the conversions
        """
        kb_dir = os.path.join('GRIDD', 'resources', 'kg_files', 'kb')
        template_file = os.path.join('GRIDD', 'resources', 'kg_files', 'elit_dp_templates.kg')
        elit_dp_to_logic = ElitDPToLogic(KnowledgeBase(kb_dir), template_file, device=device)
        return elit_dp_to_logic

    def __call__(elit_dp_to_logic, args):
        """
        `args` is a variable number of arguments that get passed to TextToLogic.translate() which
        runs all of the logic to compile the mentions and merges from the argument data.

        For this implementation, there are 3 args:
            `tok` is a list of spans corresponding to the tokens
            `pos` is a part of speech tag list of the tokens
            `dp` is a list of dependency relations between tokens

        All mention graphs share the same namespace.
        """
        tok = [Span.from_string('<span>i(0,1,0,0,1)'), Span.from_string('<span>run(1,2,0,0,1)')]
        pos = ['NN', 'VB']
        dp = [(1, 'nsbj'), (-1, 'root')]
        mentions, merges = elit_dp_to_logic(tok, pos, dp)
        assert len(mentions) == 2
        assert mentions['<span>i(0,1,0,0,1)'].id_map() == mentions['<span>run(1,2,0,0,1)'].id_map()

        concepts_i = mentions['<span>i(0,1,0,0,1)'].concepts()
        concepts_run = mentions['<span>run(1,2,0,0,1)'].concepts()
        for concept in concepts_i:
            if concept.startswith(mentions['<span>i(0,1,0,0,1)'].id_map().namespace):
                assert concept not in concepts_run