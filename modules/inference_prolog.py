from modules.module import Module
from knowledge_base.knowledge_graph import KnowledgeGraph

class PrologInference(Module):

    def __init__(self, name, infer_files):
        super().__init__(name)
        self.inferences = KnowledgeGraph('infer_', loading_kb=False)
        for fn in infer_files:
            with open(fn, 'r') as f:
                self.inferences.add_knowledge(f.read())
        self.inference_rules = self.inferences._concept_graph.generate_inference_graphs(self.inferences._concept_graph.prefix)

    def run(self, input, working_memory):
        """

        :param input: None object from merge pipeline
        :param working_memory: dialogue graph updated by merge pipeline
        :return: graph of new inferred additions
        """
        additions = {}
        for rule in self.inference_rules:
            matches = working_memory.graph.infer(rule.precondition)
            additions[rule] = self._get_variable_assignments(matches)
        self.display_additions(additions)
        return additions

    def display_additions(self, additions):
        print("\nINFERENCES::")
        for rule, solutions in additions.items():
            for sol in solutions:
                for (subject, object, typ), inst in rule.postcondition.bipredicate_instances():
                    print('\t%s(%s,%s) [%s]' % (self._sol_lkup(sol, typ), self._sol_lkup(sol, subject),
                                              self._sol_lkup(sol, object), self._sol_lkup(sol, inst)))
                for (subject, typ), inst in rule.postcondition.monopredicate_instances():
                    print('\t%s(%s) [%s]' % (self._sol_lkup(sol, typ), self._sol_lkup(sol, subject),
                                           self._sol_lkup(sol, inst)))
                print()

    def _sol_lkup(self, solution, key):
        return solution.get(key, key)

    # todo - copied from text_to_logic_model; need better inference engine setup so that this duplication doesnt happen
    def _get_variable_assignments(self, var_matches):
        var_map, matches = var_matches
        solutions = []
        for match in matches:
            variable_assignments = {}
            for key, value in var_map.items():
                variable_assignments[key] = match[value]
            solutions.append(variable_assignments)
        return solutions
