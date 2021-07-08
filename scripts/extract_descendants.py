import pickle as p
from rich.tree import Tree
from rich import print
from rich.table import Table
from nltk.corpus import wordnet as wn
import nltk
import string
nltk.download('wordnet')
from GRIDD.globals import *

class Node:
	def __init__(self, word_key, parent):
		self.parents = [parent]
		self.word_key = word_key
		self.expressions = []
		self.children = []
		self.should_write_node = False
		self.should_write_expr = True
		self.node_write_count = 0

ontology = p.load(open("GRIDD/pickles/full_nodes_to_words.p","rb"))
output_dir=f"GRIDD/resources/{KB_FOLDERNAME}/kb"





def get_correct_form(word_key):
	word_key_parts = word_key.split(".")
	word_key = word_key_parts[0] + ".a." + word_key_parts[2]
	return word_key

def save_to_ont(result):
	defined = set()
	f = open(f"{output_dir}/{result[0].split('.')[0]}inheritants.kg","w")
	for i in result[2]:
		str1 = i.translate(str.maketrans('', '', string.punctuation.replace('_', '')))
		if str1 in defined:
			continue
		defined.add(str1)
		f.write(f"{str1}=({result[0].split('.')[0]})\n")
		if '_' in str1:
			f.write(f"expr(\"{ str1.replace('_', ' ') }\", {str1})\n")
	f.write(";\n")
	f.close()


while(True):
	results = []
	print("Enter the word to convert")
	to_check = input()

	present = False
	count = 1
	table = Table(title = "Found Nodes")
	table.add_column("Node", style = "indian_red1")
	table.add_column("Definition", style = "tan")
	table.add_column("Children", style = "green")
	for key in ontology:
		key_name = key.split(".")[0]
		if to_check	in ontology[key].expressions or to_check == key_name:
			present = True
			try:
				syn =  wn.synset(key)
				children = list(set([w for s in syn.closure(lambda s:s.hyponyms()) for w in s.lemma_names()]))
			except:
				children = []
			try:
				definition = wn.synset(key).definition()
			except:
				try:
					word_key = get_correct_form(key)
					definition = wn.synset(word_key).definition()
				except:
					definition = "No WordNet Definition - Added By Hand"
			table.add_row(key, definition, ', '.join(children))
			results.append((key, definition, children))
			count += 1
	if not present:
		print("Not in Ontology")
	else:
		print(table)
		print("Which version would you like to convert? Enter its index:")
		to_convert = int(input())
		result = results[to_convert]
		save_to_ont(result)
	print()
