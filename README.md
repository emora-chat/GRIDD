# GRIDD Framework

The Graph Reasoning for Inference Driven Dialogue (GRIDD) Framework provides an API 
for building dialogue management pipelines that use a Dialogue Semantic Graph (DSG) for 
utterance understanding and decision-making.

![](docs/img/gridd_diagram.svg)

The general dialogue management pipeline available within the Framework 
is shown in Figure 1 (above).  

## Content Development Test App

For local content development work, follow the instructions in this section.

And review the following documents for guidelines:

[Knowledge Format Documentation](https://docs.google.com/document/d/1mfdZIY09JwZ-DN4eBmIpxQ9phItEbrJqD5d1QtFKBN8/edit?usp=sharing)

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
1. Create the following directory structure under the project directory:
   ```
   emora/
       gridd_files/
           kb_test/
               kb/
                   kb.kg
               rules/
                   rules.kg
   ```
   * Add your knowledge base content (ontology, world knowledge, etc.) to `kb.kg`.
   * Add your implication rules to `rules.kg`.
   * Note: You can separate your content development into separate `.kg` files in `kb/` and `rules/`, if desired. There is no necessary naming convention.
1. Go to the project directory (e.g., `emora`) and run the test app:
   ```
   python GRIDD/scripts/knowledge_base_test_app.py
   ```
1. You will be prompted to choose either the logic or language interface, and you have the option within the language interface to see intermediate debugging results (the working memory at various steps in the dialogue pipeline). The default options if you don't provide anything at the prompts is the language interface with no debugging outputs.

## Full System

To run the whole system end-to-end, follow the instructions in this section.

### Setup

(0) Required `Python >= 3.7`

(1) Install required dependencies:

* (a) Execute `pip install -r GRIDD/requirements.txt`

(2) Clone the [structpy repository](https://github.com/jdfinch/structpy). 
Put the inner `structpy` directory into the **parent** directory of your cloned GRIDD directory 
(i.e. it should be on the same directory level as GRIDD, **not** contained within GRIDD).

(3) Download required files:

* [SentenceCasing data](https://github.com/nreimers/truecaser/releases/download/v1.0/english_distributions.obj.zip)
into the `GRIDD/resources` directory.

(4) Install the ELIT package and execute `elit serve` in a terminal. 
`elit serve` will run in the background.

### Execution

Set your runtime working directory to the directory that contains `GRIDD`.

Run the `GRIDD/chatbot.py` script.
