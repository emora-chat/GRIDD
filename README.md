# GRIDD Framework

The Graph Reasoning for Inference Driven Dialogue (GRIDD) Framework provides an API 
for building dialogue management pipelines that use a Dialogue Semantic Graph (DSG) for 
utterance understanding and decision-making.

![](docs/img/gridd_diagram.svg)

The general dialogue management pipeline available within the Framework 
is shown in Figure 1 (above).  

## Content Development

For local content development work, follow the instructions in this section.

And review the following documents for guidelines:

[Knowledge Format Documentation](https://docs.google.com/document/d/1mfdZIY09JwZ-DN4eBmIpxQ9phItEbrJqD5d1QtFKBN8/edit?usp=sharing)

[Semantic Representation](https://github.com/emora-chat/GRIDD/blob/main/docs/SemanticRepresentation.md)

[Content Development Guidelines](https://github.com/emora-chat/GRIDD/wiki/Content-Development-Guidelines)

### Getting Started

This framework requires `Python >= 3.7`

1. Create a project directory (this instruction uses `emora` as the name of the project directory):
   ```
   mkdir emora
   cd emora
   ```
1. Create a virtual environment:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
1. Install GitHub Clone (for cloning `structpy` below):
   ```
   pip install git+git://github.com/HR/github-clone#egg=ghclone
   ```
1. Clone the `GRIDD` repository under the project directory:
   ```
   git clone https://github.com/emora-chat/GRIDD.git
   ```
1. Clone the `structpy` package from the `structpy` repository:
   ```
   ghclone https://github.com/jdfinch/structpy/tree/master/structpy
   ```
1. Install the `GRIDD` requirements:
   ```
   pip install -r GRIDD/requirements.txt
   ```
1. The files that compose the knowledge base, inference rules, and template rules are found in `GRIDD/resources/kg_files/`.

   * Add your knowledge base content (ontology, world knowledge, etc.) to topic-specific files in `GRIDD/resources/kg_files/kb/`.
        
     NOTE! There are various common files already in place; before adding new content, verify that it is not already located in an existing file.
   
   * Add your implication rules to topic-specific files in `GRIDD/resources/kg_files/rules/`.
   
   * Add your implication rules to topic-specific files in `GRIDD/resources/kg_files/nlg_templates/`.


### Execution

Set your runtime working directory to the `emora` directory.

Run the `GRIDD/intcore_chatbot_server.py` script.

You will be prompted to enter the device that you want to use. 

* For GPU-enabled machines, find an unused GPU and enter it (`cuda:0`, `cuda:1`, etc). 
You can see the usage of the GPU by executing `nvidia-smi` in the terminal.

* For CPU-only machines, enter `cpu`.

Begin the conversation by typing some greeting like `hi`.

There is no end-phrase, so you must manually stop the execution when you want to be done.


