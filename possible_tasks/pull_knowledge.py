import unittest
import time
import random

from GRIDD.data_structures.concept_graph import ConceptGraph

def recurse_essential(kb, c, tot_pulled, pulled, temp_pull, already_pulled, already_checked):
	# Check for essential predicates related to our related node
	elem_preds = set(kb.predicates(c)) | set(kb.predicates(object=c))
	for pred in elem_preds:
		# We only want to take stuff from essential predicates
		if pred[1] in ["subj_essential", "obj_essential"]:
			# Now same deal as normal add
			good_e = [x for x in [pred[0], pred[2], pred[3]] if x]
			for e in good_e:
				if e not in already_pulled:
					tot_pulled += 1
					already_pulled[e] = 1
					temp_pull.append(e)   
					pulled.append(e)
					tot_pulled = recurse_essential(kb, e, tot_pulled, pulled, temp_pull, already_pulled, already_checked)
	
	# update # of pulled nodes to include what we have added here
	# note that we could exceed our limit while adding here
	return tot_pulled

def return_salience(wm, c):
	try:
		return wm.features[c]["SALIENCE"]
	except:
		return 0

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
	tot_pulled = 0	   # Tracks total number of pulled nodes
	curr_pull = set()	# holds all nodes of a certain edge distance from our original nodes

	# Add all subject, object, and predicate instance nodes from WM
	for c in curr_concepts:
		curr_pull.add(c[0])
		curr_pull.add(c[3])
		# Make sure object exists as it is possible to have a monopredicate
		if c[2]:
			curr_pull.add(c[2])

	pulled = []

	# Each iteration of this layer is effectively moving one edge away from the original node
	for outward_dist in range(reach):
		# If we got no new nodes last iteration, stop now
		if curr_pull == []:
			return pulled

		# Sort by salience
		curr_pull = sorted(curr_pull, key= lambda x: return_salience(wm, x), reverse=True)

		# Mark new nodes as pulled (will be redundant in some cases)
		for c in curr_pull:
			already_pulled[c] = 1
		temp_pull = [] # Keeps track of nodes added this layer

		for s in curr_pull:
			# Don't waste time re-checking the same nodes
			if s in already_checked:
				continue
			already_checked[s] = 1

			branch_pulled = 0 # Track how many nodes are pulled for this node
			
			# Get related predicates for our related node
			related_predicates = set(kb.predicates(s)) | set(kb.predicates(object=s))
			for g in related_predicates:
				# Don't pull any type predicate instances
				if g[1] == "type":
					continue
			
				# Consider adding from subj, obj, and instance pred of quadruple
				good_elem = [x for x in [g[0], g[2], g[3]] if x]
			
				# Make sure we aren't about to add more to our limit
				# than acceptable.
				# This is only an estimate for the overall limit
				# As the number of essential predicates can't be estimated
				# and actually counting them would be computationally expensive.
				if (limit and (len(good_elem) + tot_pulled) > limit):
					continue
			
				add = False
				for i, elem in enumerate(good_elem):
					if elem not in already_pulled:
						tot_pulled += 1
						already_pulled[elem] = 1
						temp_pull.append(elem)
						pulled.append(elem)
						tmp = tot_pulled
						# Recursively add essential attachments for this node we're pulling (if any)
						tot_pulled = recurse_essential(kb, s, tot_pulled, pulled, temp_pull, already_pulled, already_checked)
						add = True

				# Check if we're now over limit
				if (limit and tot_pulled >= limit):
					return pulled

				if add:
					branch_pulled += 1

				if (branch_limit and branch_pulled == branch_limit):
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
		wm.features['d'] = {"SALIENCE": 0.8}
		wm.features['happy'] = {"SALIENCE": 1.0}
		wm.features['0'] = {"SALIENCE": 0.5}

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
		#assert len(set(pulled)) == 1

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
		fff=happy(g)
		;
		
		''')

		wm = ConceptGraph('''
		happy(d)
		happy(e)
		''')

		wm.features['d'] = {"SALIENCE": 0.8}
		wm.features['e'] = {"SALIENCE": 1.0}
		wm.features['happy'] = {"SALIENCE": 1.0}
		wm.features['1'] = {"SALIENCE": 1.0}
		wm.features['0'] = {"SALIENCE": 0.5}

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
		# of d's and one of e's connections, the pull operation should terminate
		# without pulling any additional neighbors of d or e
		
		# Can't predict presence of essential attachments
		#assert len(set(pulled)) == 2

		first = time.time()
		pulled = pull(kb, wm, branch_limit=200, reach=20)

	def test_larger_2(self):
		a = '''
		dog = (entity)
		cat = (entity)
		chase = (predicate)
		happy = (predicate)
		;
		'''
		for x in range(400):
			a += "a{} = dog()\n".format(x)
		a += ";\n"
		for x in range(400):
			a += "ca{}a{} = chase(a{},a{})\n".format(x, x+1, x, x+1)
		a += ";\n"
		
		meta = {'d': {"SALIENCE": 1.0},}
		for i in range(399):
			meta['a'+str(i)] = {"SALIENCE": random.random()}
		kb = ConceptGraph(a, metadata=meta)

		wm = ConceptGraph('''
		happy(a0)
		happy(a1)
		''')
		#pulled = pull(kb, wm, limit = 3)

		first = time.time()
		pulled = pull(kb, wm, limit = 100, branch_limit=5, reach=100)
		print("Elapsed Time: {}".format(time.time() - first))
		print(pulled)
		print(len(pulled))


if __name__ == '__main__':
	unittest.main()
