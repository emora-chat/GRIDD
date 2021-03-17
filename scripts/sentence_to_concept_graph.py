from GRIDD.chatbot_server import ChatbotServer
import os

"""
Processes files of sentences in the NLU pipeline of Emora dialogue agent.

A ConceptGraph is generated for each sentence, where each sentence must be on a new line for proper NLU understanding.

To create one ConceptGraph that represents all sentences, 
    full_cg = ConceptGraph(namespace='full_')
    for cg in sentence_cgs:
        full_cg.concatenate(cg)
"""

if __name__ == '__main__':

    # specify directory of kb files
    # all concepts in sentence files should be defined in kb files, otherwise unknown_<postag> will be used
    # and ConceptGraph will be suboptimal
    kb_dir = os.path.join('GRIDD', 'resources', 'kg_files', 'kb')
    kb = [kb_dir]
    nlu_pipeline = ChatbotServer()
    nlu_pipeline.initialize_nlu(kb_files=kb, device='cpu', local=True)

    # specify path of directory containing sentence files
    dir = os.path.join('DSG2Text', 'resources', 'data')

    # specify name of sentence files
    files = ['lion_king_clean.txt']
    for file in files:
        with open(os.path.join(dir, file), 'r') as f:
            for line in f:
                line = line.strip()
                cg = nlu_pipeline.run_nlu(line)

                # To save ConceptGraph to file:
                # cg.save(json_filepath)
                # The above saves each ConceptGraph to individual files
                # If you don't specify filepath, it returns the json dict of the ConceptGraph

                # To load ConceptGraph obtained from nlu_pipeline from file:
                # loaded_cg = ConceptGraph(namespace='WM').load(json_filepath_or_json_string)


