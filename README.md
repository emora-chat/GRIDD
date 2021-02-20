# GRIDD Framework

The Graph Reasoning for Inference Driven Dialogue (GRIDD) Framework provides an API 
for building dialogue management pipelines that use a Dialogue Semantic Graph (DSG) for 
utterance understanding and decision-making.

![](docs/img/gridd_diagram.svg)

The general dialogue management pipeline available within the Framework 
is shown in Figure 1 (above).  

## Setup

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



