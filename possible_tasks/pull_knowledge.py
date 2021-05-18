import unittest

from GRIDD.data_structures.concept_graph import ConceptGraph


def pull(kb, wm, limit=None, branch_limit=None, reach=1):
	"""
	kb:			 ConceptGraph representing the knowledge base.
	wm:			 ConceptGraph representing current working memory.
	limit:		  maximum total number of concepts to pull.
	branch_limit:   maximum number of concepts to pull per puller.
	reach:		  number of "hops"
	"""

	# Get all initial predicates in the working memory
	curr_concepts = wm.predicates()

	already_pulled = {}  # Tracks nodes that have been pulled
	already_checked = {} # Tracks nodes that have been pulled from
	tot_pulled = 0       # Tracks total number of pulled nodes
	curr_pull = []       # holds all nodes of a certain edge distance from our original nodes

	# Add all subject and object nodes from WM
	for c in curr_concepts:
		curr_pull.append(c[0])
		# Make sure object exists as it is possible to have a monopredicate
		if c[2]:
			curr_pull.append(c[2])

	# Since subjects and objects could be same in diff preds, remove redundancies
	curr_pull = set(curr_pull)

	pulled = []

	# Each iteration of this layer is effectively moving one edge away from the original node
	for outward_dist in range(reach):
		for c in curr_pull:
			already_pulled[c] = 1
		temp_pull = [] # Keeps track of nodes added this layer
		if curr_pull == []:
			return pulled
		for s in curr_pull:
			# Don't waste time re-checking the same nodes
			if s in already_checked:
				continue
			already_checked[s] = 1
			branch_pulled = 0
			related_predicates = set(kb.predicates(s)) | set(kb.predicates(object=s))
			done = 0
			for g in related_predicates:
				if done:
					break

				# These seem to be entity definitions from ontology - unnecessary?
				if g[3].isnumeric():
					continue
				for elem in [g[0], g[2], g[3]]:
					if elem not in already_pulled:
						already_pulled[elem] = 1
						branch_pulled += 1
						tot_pulled += 1
						temp_pull.append(elem)   
						pulled.append(elem)

					# Reached number of desired pulled nodes
					if (limit and tot_pulled >= limit):
						return(pulled)

					# Reached number of desired pulled nodes from this puller
					if (branch_limit and branch_pulled >= branch_limit):
						done = 1
						break

		# Restock puller list with new nodes
		curr_pull = temp_pull

	return(pulled)

	


class TestPullKnowledge(unittest.TestCase):

	def test_pull_simple(self):
		kb = ConceptGraph('''
		
		dog = (entity)
		cat = (entity)
		chase = (predicate)
		happy = (predicate)
		;
		
		a = dog()
		b = dog()
		c = cat()
		d = dog()
		e = cat()
		f = dog()
		g = dog()
		h = cat()
		i = cat()
		;
		
		cab=chase(a, b)
		cbc=chase(b, c)
		ccd=chase(c, d)
		cde=chase(d, e)
		cef=chase(e, f)
		cfg=chase(f, g)
		cgh=chase(g, h)
		cgi=chase(g, i)
		;
		
		''')

		wm = ConceptGraph('''
		happy(d)
		''')

		pulled = pull(kb, wm)
		# neighbors of d pulled, since d was mentioned
		assert set(pulled) == {'c', 'e', 'ccd', 'cde'}

		pulled = pull(kb, wm, reach=2)
		# neighbors of d and neighbors-of-neighbors of d pulled
		assert set(pulled) == {'c', 'e', 'ccd', 'cde','b', 'cbc', 'f', 'cef'}

		pulled = pull(kb, wm, limit=3)
		# since the absolute limit is 3, a maximum of 3 concepts
		# should be returned by the pull operation.
		assert len(set(pulled)) <= 3

		pulled = pull(kb, wm, branch_limit=1)
		# since the branch limit is 1, after pulling along one
		# of d's connections, the pull operation should terminate
		# without pulling any additional neighbors of d
		assert len(set(pulled)) == 1

		'''
		Additional considerations:
		
		* there will potentially be hundreds of nodes in working memory--
		  make sure the pull operation efficiently scales for large working
		  memory and large KB.
		
		* if a predicate instance is pulled, its arguments MUST be pulled
		
		* when pulling concept A, any related predicates of type ESSENTIAL
		  (see globals.ESSENTIAL) MUST be pulled
		  
		* Test pulling with a large branch factor-- setting a small limit
		  such as branch_limit=5 should make pulling efficient even with
		  thousands of neighbors per concept
		'''


	def test_pull_simple_2(self):
		kb = ConceptGraph('''
		
		dog = (entity)
		cat = (entity)
		chase = (predicate)
		happy = (predicate)
		;
		
		a = dog()
		b = dog()
		c = cat()
		d = dog()
		e = cat()
		f = dog()
		g = dog()
		h = cat()
		i = cat()
		;
		
		cab=chase(a, b)
		cbc=chase(b, c)
		ccd=chase(c, d)
		cde=chase(d, e)
		cef=chase(e, f)
		cfg=chase(f, g)
		cgh=chase(g, h)
		cgi=chase(g, i)
		;
		
		''')

		wm = ConceptGraph('''
		happy(d)
		happy(e)
		''')

		pulled = pull(kb, wm)
		# neighbors of d and e pulled, since both were mentioned
		assert set(pulled) == {'c', 'ccd', 'cde', 'cef', 'f'}

		pulled = pull(kb, wm, reach=2)
		# neighbors of d and neighbors-of-neighbors of d pulled
		assert set(pulled) == {'c', 'b', 'cbc', 'ccd', 'cde', 'f', 'cef', 'g', 'cfg'}

		pulled = pull(kb, wm, limit=3)
		# since the absolute limit is 3, a maximum of 3 concepts
		# should be returned by the pull operation.
		assert len(set(pulled)) <= 3

		pulled = pull(kb, wm, branch_limit=1)
		# since the branch limit is 1, after pulling along one
		# of d's connections, the pull operation should terminate
		# without pulling any additional neighbors of d
		assert len(set(pulled)) == 2

		pulled = pull(kb, wm, branch_limit=200, reach=20)


if __name__ == '__main__':
	unittest.main()
