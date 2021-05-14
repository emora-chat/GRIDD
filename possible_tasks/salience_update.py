import sys, os
sys.path.append(os.getcwd())
import unittest
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.data_structures.inference_engine import InferenceEngine
from GRIDD.data_structures.concept_compiler import ConceptCompiler
from GRIDD.utilities.utilities import uniquify, operators, interleave
from itertools import chain, combinations
from GRIDD.data_structures.update_graph import UpdateGraph
from GRIDD.globals import *
from GRIDD.data_structures.assertions import assertions
from GRIDD.data_structures.confidence import *
from GRIDD.data_structures.id_map import IdMap
from GRIDD.data_structures.concept_graph import ConceptGraph
from GRIDD.globals import *
import numpy as np
import time
MY_DECAY = 0.1
def update_salienceold(wm):
    """
    wm: a ConceptGraph representing current working memory.
    """

    edges = []
    for e in wm.to_graph().edges():
        if e[0] not in SAL_FREE and e[1] not in SAL_FREE:
            if not wm.has(predicate_id=e[0]) or wm.type(e[0]) not in SAL_FREE:
                edges.append(e)
    redges = [(t, s, l) for s, t, l in edges]
    and_links = [edge for edge in wm.metagraph.edges() if isinstance(edge[2], tuple) and AND_LINK == edge[2][0]]
    for evidence, and_node, _ in and_links:
        or_links = [edge for edge in wm.metagraph.out_edges(and_node) if
                    isinstance(edge[2], tuple) and OR_LINK == edge[2][0]]
        for _, implication, _ in or_links:
            redges.append((evidence, implication, None))

    def moderated_salience(salience, connectivity):
        return salience / connectivity

    def update_instance_salience(val, args):
        in_ms = []
        out_ms = [val[0]]
        for (sal, con), lnk in args:
            if lnk == SALIENCE_IN_LINK:
                in_ms.append(moderated_salience(sal, con) - ASSOCIATION_DECAY)
            else:
                out_ms.append(sal)
        avg = sum(in_ms) / len(in_ms) if len(in_ms) > 0 else 0
        return (max(out_ms + [avg]), val[1])

    updater = UpdateGraph(
        [*[(s, t, SALIENCE_OUT_LINK) for s, t, _ in edges],
         *[(s, t, SALIENCE_IN_LINK) for s, t, _ in redges]],
        nodes={
            c: (wm.features.get(c, {}).get(SALIENCE, 0),
                wm.features.get(c, {}).get(CONNECTIVITY, 1))
            for c in wm.concepts()},
        updaters={c: update_instance_salience for c in wm.concepts()},
        default=(0, 1),
        set_fn=(lambda n, v: wm.features.setdefault(n, {}).__setitem__(SALIENCE, v[0]))
    )
    updater.update(1, push=True)
    sal = {}
    for i in wm.to_graph().nodes():
        try:
            sal[i] = wm.features[i][SALIENCE]
        except:
            sal[i] = 0
    return sal
    #raise NotImplementedError



#def to_graph(self):
 #       graph = Graph()
  #      for s, t, o, i in self.predicates():
   #         graph.add(i, s, 's')
    #        graph.add(i, t, 't')
     #       if o is not None:
      #          graph.add(i, o, 'o')
       # for c in self.concepts():
        #    graph.add(c)
        #return graph



def update_salience(wm):
    names = {}
   # g = wm.to_graph()
    wmc = wm.concepts()
    npsal = np.zeros(shape=(1,len(wmc)))
    npedges = np.zeros(shape=(len(wmc), len(wmc)))
    #for i, name in enumerate(g.nodes()):
    for i, name in enumerate(wmc):
        names[name] = i
        try:
            npsal[0][i]=wm.features[name][SALIENCE]
        except:
            pass


   # for e in g.edges():
       # if e[0] not in SAL_FREE and e[1] not in SAL_FREE and (not wm.has(predicate_id=e[0]) or wm.type(e[0]) not in SAL_FREE):
       #     npedges[names[e[1]]][names[e[0]]] = MY_DECAY
    for s, t, o, i in wm.predicates():
        if i not in SAL_FREE:
            if s not in SAL_FREE:
                npedges[names[s]][names[i]] = MY_DECAY
                npedges[names[i]][names[s]] = MY_DECAY
            if t not in SAL_FREE:
                npedges[names[t]][names[i]] = MY_DECAY
                npedges[names[i]][names[t]] = MY_DECAY
            if o is not None and o not in SAL_FREE:
                npedges[names[o]][names[i]] = MY_DECAY
                npedges[names[i]][names[o]] = MY_DECAY

    for edge in wm.metagraph.edges():
        if isinstance(edge[2], tuple) and AND_LINK == edge[2][0]:
            for evidence, and_node, _ in edge:
                or_links = [edge for edge in wm.metagraph.out_edges(and_node) if
                            isinstance(edge[2], tuple) and OR_LINK == edge[2][0]]
                for _, implication, _ in or_links:
                    npedges[names[evidence]][names[implication]] = MY_DECAY

  #  print(npsal)
    a = np.matmul(npsal, npedges)

    sal = {}
    #for i in g.nodes():
    for i in wm.concepts():
        try:
            sal[i] = wm.features[i][SALIENCE] + a[0][names[i]]
            wm.features[i][SALIENCE] += a[0][names[i]]
        except:
            sal[i] = a[0][names[i]]
            wm.features[i][SALIENCE] = a[0][names[i]]
    return sal



class TestSalienceUpdate(unittest.TestCase):

    def test_update_salience(self):
        wm = ConceptGraph('''
        
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
        a0 = dog() 
        a1 = dog() 
        a2 = dog() 
        a3 = dog() 
        a4 = dog() 
        a5 = dog() 
        a6 = dog() 
        a7 = dog() 
        a8 = dog() 
        a9 = dog() 
        a10 = dog() 
        a11 = dog() 
        a12 = dog() 
        a13 = dog() 
        a14 = dog() 
        a15 = dog() 
        a16 = dog() 
        a17 = dog() 
        a18 = dog() 
        a19 = dog() 
        a20 = dog() 
        a21 = dog() 
        a22 = dog() 
        a23 = dog() 
        a24 = dog() 
        a25 = dog() 
        a26 = dog() 
        a27 = dog() 
        a28 = dog() 
        a29 = dog() 
        a30 = dog() 
        a31 = dog() 
        a32 = dog() 
        a33 = dog() 
        a34 = dog() 
        a35 = dog() 
        a36 = dog() 
        a37 = dog() 
        a38 = dog() 
        a39 = dog() 
        a40 = dog() 
        a41 = dog() 
        a42 = dog() 
        a43 = dog() 
        a44 = dog() 
        a45 = dog() 
        a46 = dog() 
        a47 = dog() 
        a48 = dog() 
        a49 = dog() 
        a50 = dog() 
        a51 = dog() 
        a52 = dog() 
        a53 = dog() 
        a54 = dog() 
        a55 = dog() 
        a56 = dog() 
        a57 = dog() 
        a58 = dog() 
        a59 = dog() 
        a60 = dog() 
        a61 = dog() 
        a62 = dog() 
        a63 = dog() 
        a64 = dog() 
        a65 = dog() 
        a66 = dog() 
        a67 = dog() 
        a68 = dog() 
        a69 = dog() 
        a70 = dog() 
        a71 = dog() 
        a72 = dog() 
        a73 = dog() 
        a74 = dog() 
        a75 = dog() 
        a76 = dog() 
        a77 = dog() 
        a78 = dog() 
        a79 = dog() 
        a80 = dog() 
        a81 = dog() 
        a82 = dog() 
        a83 = dog() 
        a84 = dog() 
        a85 = dog() 
        a86 = dog() 
        a87 = dog() 
        a88 = dog() 
        a89 = dog() 
        a90 = dog() 
        a91 = dog() 
        a92 = dog() 
        a93 = dog() 
        a94 = dog() 
        a95 = dog() 
        a96 = dog() 
        a97 = dog() 
        a98 = dog() 
        a99 = dog() 
        a100 = dog() 
        a101 = dog() 
        a102 = dog() 
        a103 = dog() 
        a104 = dog() 
        a105 = dog() 
        a106 = dog() 
        a107 = dog() 
        a108 = dog() 
        a109 = dog() 
        a110 = dog() 
        a111 = dog() 
        a112 = dog() 
        a113 = dog() 
        a114 = dog() 
        a115 = dog() 
        a116 = dog() 
        a117 = dog() 
        a118 = dog() 
        a119 = dog() 
        a120 = dog() 
        a121 = dog() 
        a122 = dog() 
        a123 = dog() 
        a124 = dog() 
        a125 = dog() 
        a126 = dog() 
        a127 = dog() 
        a128 = dog() 
        a129 = dog() 
        a130 = dog() 
        a131 = dog() 
        a132 = dog() 
        a133 = dog() 
        a134 = dog() 
        a135 = dog() 
        a136 = dog() 
        a137 = dog() 
        a138 = dog() 
        a139 = dog() 
        a140 = dog() 
        a141 = dog() 
        a142 = dog() 
        a143 = dog() 
        a144 = dog() 
        a145 = dog() 
        a146 = dog() 
        a147 = dog() 
        a148 = dog() 
        a149 = dog() 
        a150 = dog() 
        a151 = dog() 
        a152 = dog() 
        a153 = dog() 
        a154 = dog() 
        a155 = dog() 
        a156 = dog() 
        a157 = dog() 
        a158 = dog() 
        a159 = dog() 
        a160 = dog() 
        a161 = dog() 
        a162 = dog() 
        a163 = dog() 
        a164 = dog() 
        a165 = dog() 
        a166 = dog() 
        a167 = dog() 
        a168 = dog() 
        a169 = dog() 
        a170 = dog() 
        a171 = dog() 
        a172 = dog() 
        a173 = dog() 
        a174 = dog() 
        a175 = dog() 
        a176 = dog() 
        a177 = dog() 
        a178 = dog() 
        a179 = dog() 
        a180 = dog() 
        a181 = dog() 
        a182 = dog() 
        a183 = dog() 
        a184 = dog() 
        a185 = dog() 
        a186 = dog() 
        a187 = dog() 
        a188 = dog() 
        a189 = dog() 
        a190 = dog() 
        a191 = dog() 
        a192 = dog() 
        a193 = dog() 
        a194 = dog() 
        a195 = dog() 
        a196 = dog() 
        a197 = dog() 
        a198 = dog() 
        a199 = dog() 
        a200 = dog() 
        a201 = dog() 
        a202 = dog() 
        a203 = dog() 
        a204 = dog() 
        a205 = dog() 
        a206 = dog() 
        a207 = dog() 
        a208 = dog() 
        a209 = dog() 
        a210 = dog() 
        a211 = dog() 
        a212 = dog() 
        a213 = dog() 
        a214 = dog() 
        a215 = dog() 
        a216 = dog() 
        a217 = dog() 
        a218 = dog() 
        a219 = dog() 
        a220 = dog() 
        a221 = dog() 
        a222 = dog() 
        a223 = dog() 
        a224 = dog() 
        a225 = dog() 
        a226 = dog() 
        a227 = dog() 
        a228 = dog() 
        a229 = dog() 
        a230 = dog() 
        a231 = dog() 
        a232 = dog() 
        a233 = dog() 
        a234 = dog() 
        a235 = dog() 
        a236 = dog() 
        a237 = dog() 
        a238 = dog() 
        a239 = dog() 
        a240 = dog() 
        a241 = dog() 
        a242 = dog() 
        a243 = dog() 
        a244 = dog() 
        a245 = dog() 
        a246 = dog() 
        a247 = dog() 
        a248 = dog() 
        a249 = dog() 
        a250 = dog() 
        a251 = dog() 
        a252 = dog() 
        a253 = dog() 
        a254 = dog() 
        a255 = dog() 
        a256 = dog() 
        a257 = dog() 
        a258 = dog() 
        a259 = dog() 
        a260 = dog() 
        a261 = dog() 
        a262 = dog() 
        a263 = dog() 
        a264 = dog() 
        a265 = dog() 
        a266 = dog() 
        a267 = dog() 
        a268 = dog() 
        a269 = dog() 
        a270 = dog() 
        a271 = dog() 
        a272 = dog() 
        a273 = dog() 
        a274 = dog() 
        a275 = dog() 
        a276 = dog() 
        a277 = dog() 
        a278 = dog() 
        a279 = dog() 
        a280 = dog() 
        a281 = dog() 
        a282 = dog() 
        a283 = dog() 
        a284 = dog() 
        a285 = dog() 
        a286 = dog() 
        a287 = dog() 
        a288 = dog() 
        a289 = dog() 
        a290 = dog() 
        a291 = dog() 
        a292 = dog() 
        a293 = dog() 
        a294 = dog() 
        a295 = dog() 
        a296 = dog() 
        a297 = dog() 
        a298 = dog() 
        a299 = dog() 
        a300 = dog() 
        a301 = dog() 
        a302 = dog() 
        a303 = dog() 
        a304 = dog() 
        a305 = dog() 
        a306 = dog() 
        a307 = dog() 
        a308 = dog() 
        a309 = dog() 
        a310 = dog() 
        a311 = dog() 
        a312 = dog() 
        a313 = dog() 
        a314 = dog() 
        a315 = dog() 
        a316 = dog() 
        a317 = dog() 
        a318 = dog() 
        a319 = dog() 
        a320 = dog() 
        a321 = dog() 
        a322 = dog() 
        a323 = dog() 
        a324 = dog() 
        a325 = dog() 
        a326 = dog() 
        a327 = dog() 
        a328 = dog() 
        a329 = dog() 
        a330 = dog() 
        a331 = dog() 
        a332 = dog() 
        a333 = dog() 
        a334 = dog() 
        a335 = dog() 
        a336 = dog() 
        a337 = dog() 
        a338 = dog() 
        a339 = dog() 
        a340 = dog() 
        a341 = dog() 
        a342 = dog() 
        a343 = dog() 
        a344 = dog() 
        a345 = dog() 
        a346 = dog() 
        a347 = dog() 
        a348 = dog() 
        a349 = dog() 
        a350 = dog() 
        a351 = dog() 
        a352 = dog() 
        a353 = dog() 
        a354 = dog() 
        a355 = dog() 
        a356 = dog() 
        a357 = dog() 
        a358 = dog() 
        a359 = dog() 
        a360 = dog() 
        a361 = dog() 
        a362 = dog() 
        a363 = dog() 
        a364 = dog() 
        a365 = dog() 
        a366 = dog() 
        a367 = dog() 
        a368 = dog() 
        a369 = dog() 
        a370 = dog() 
        a371 = dog() 
        a372 = dog() 
        a373 = dog() 
        a374 = dog() 
        a375 = dog() 
        a376 = dog() 
        a377 = dog() 
        a378 = dog() 
        a379 = dog() 
        a380 = dog() 
        a381 = dog() 
        a382 = dog() 
        a383 = dog() 
        a384 = dog() 
        a385 = dog() 
        a386 = dog() 
        a387 = dog() 
        a388 = dog() 
        a389 = dog() 
        a390 = dog() 
        a391 = dog() 
        a392 = dog() 
        a393 = dog() 
        a394 = dog() 
        a395 = dog() 
        a396 = dog() 
        a397 = dog() 
        a398 = dog() 
        a399 = dog() 
        
        ;
        
        cab=chase(a, b)
        cbc=chase(b, c)
        ccd=chase(c, d)
        cde=chase(d, e)
        cef=chase(e, f)
        cfg=chase(f, g)
        cgh=chase(g, h)
        cgi=chase(g, i)
        ca0a1 = chase(a0,a1) 
        ca1a2 = chase(a1,a2) 
        ca2a3 = chase(a2,a3) 
        ca3a4 = chase(a3,a4) 
        ca4a5 = chase(a4,a5) 
        ca5a6 = chase(a5,a6) 
        ca6a7 = chase(a6,a7) 
        ca7a8 = chase(a7,a8) 
        ca8a9 = chase(a8,a9) 
        ca9a10 = chase(a9,a10) 
        ca10a11 = chase(a10,a11) 
        ca11a12 = chase(a11,a12) 
        ca12a13 = chase(a12,a13) 
        ca13a14 = chase(a13,a14) 
        ca14a15 = chase(a14,a15) 
        ca15a16 = chase(a15,a16) 
        ca16a17 = chase(a16,a17) 
        ca17a18 = chase(a17,a18) 
        ca18a19 = chase(a18,a19) 
        ca19a20 = chase(a19,a20) 
        ca20a21 = chase(a20,a21) 
        ca21a22 = chase(a21,a22) 
        ca22a23 = chase(a22,a23) 
        ca23a24 = chase(a23,a24) 
        ca24a25 = chase(a24,a25) 
        ca25a26 = chase(a25,a26) 
        ca26a27 = chase(a26,a27) 
        ca27a28 = chase(a27,a28) 
        ca28a29 = chase(a28,a29) 
        ca29a30 = chase(a29,a30) 
        ca30a31 = chase(a30,a31) 
        ca31a32 = chase(a31,a32) 
        ca32a33 = chase(a32,a33) 
        ca33a34 = chase(a33,a34) 
        ca34a35 = chase(a34,a35) 
        ca35a36 = chase(a35,a36) 
        ca36a37 = chase(a36,a37) 
        ca37a38 = chase(a37,a38) 
        ca38a39 = chase(a38,a39) 
        ca39a40 = chase(a39,a40) 
        ca40a41 = chase(a40,a41) 
        ca41a42 = chase(a41,a42) 
        ca42a43 = chase(a42,a43) 
        ca43a44 = chase(a43,a44) 
        ca44a45 = chase(a44,a45) 
        ca45a46 = chase(a45,a46) 
        ca46a47 = chase(a46,a47) 
        ca47a48 = chase(a47,a48) 
        ca48a49 = chase(a48,a49) 
        ca49a50 = chase(a49,a50) 
        ca50a51 = chase(a50,a51) 
        ca51a52 = chase(a51,a52) 
        ca52a53 = chase(a52,a53) 
        ca53a54 = chase(a53,a54) 
        ca54a55 = chase(a54,a55) 
        ca55a56 = chase(a55,a56) 
        ca56a57 = chase(a56,a57) 
        ca57a58 = chase(a57,a58) 
        ca58a59 = chase(a58,a59) 
        ca59a60 = chase(a59,a60) 
        ca60a61 = chase(a60,a61) 
        ca61a62 = chase(a61,a62) 
        ca62a63 = chase(a62,a63) 
        ca63a64 = chase(a63,a64) 
        ca64a65 = chase(a64,a65) 
        ca65a66 = chase(a65,a66) 
        ca66a67 = chase(a66,a67) 
        ca67a68 = chase(a67,a68) 
        ca68a69 = chase(a68,a69) 
        ca69a70 = chase(a69,a70) 
        ca70a71 = chase(a70,a71) 
        ca71a72 = chase(a71,a72) 
        ca72a73 = chase(a72,a73) 
        ca73a74 = chase(a73,a74) 
        ca74a75 = chase(a74,a75) 
        ca75a76 = chase(a75,a76) 
        ca76a77 = chase(a76,a77) 
        ca77a78 = chase(a77,a78) 
        ca78a79 = chase(a78,a79) 
        ca79a80 = chase(a79,a80) 
        ca80a81 = chase(a80,a81) 
        ca81a82 = chase(a81,a82) 
        ca82a83 = chase(a82,a83) 
        ca83a84 = chase(a83,a84) 
        ca84a85 = chase(a84,a85) 
        ca85a86 = chase(a85,a86) 
        ca86a87 = chase(a86,a87) 
        ca87a88 = chase(a87,a88) 
        ca88a89 = chase(a88,a89) 
        ca89a90 = chase(a89,a90) 
        ca90a91 = chase(a90,a91) 
        ca91a92 = chase(a91,a92) 
        ca92a93 = chase(a92,a93) 
        ca93a94 = chase(a93,a94) 
        ca94a95 = chase(a94,a95) 
        ca95a96 = chase(a95,a96) 
        ca96a97 = chase(a96,a97) 
        ca97a98 = chase(a97,a98) 
        ca98a99 = chase(a98,a99) 
        ca99a100 = chase(a99,a100) 
        ca100a101 = chase(a100,a101) 
        ca101a102 = chase(a101,a102) 
        ca102a103 = chase(a102,a103) 
        ca103a104 = chase(a103,a104) 
        ca104a105 = chase(a104,a105) 
        ca105a106 = chase(a105,a106) 
        ca106a107 = chase(a106,a107) 
        ca107a108 = chase(a107,a108) 
        ca108a109 = chase(a108,a109) 
        ca109a110 = chase(a109,a110) 
        ca110a111 = chase(a110,a111) 
        ca111a112 = chase(a111,a112) 
        ca112a113 = chase(a112,a113) 
        ca113a114 = chase(a113,a114) 
        ca114a115 = chase(a114,a115) 
        ca115a116 = chase(a115,a116) 
        ca116a117 = chase(a116,a117) 
        ca117a118 = chase(a117,a118) 
        ca118a119 = chase(a118,a119) 
        ca119a120 = chase(a119,a120) 
        ca120a121 = chase(a120,a121) 
        ca121a122 = chase(a121,a122) 
        ca122a123 = chase(a122,a123) 
        ca123a124 = chase(a123,a124) 
        ca124a125 = chase(a124,a125) 
        ca125a126 = chase(a125,a126) 
        ca126a127 = chase(a126,a127) 
        ca127a128 = chase(a127,a128) 
        ca128a129 = chase(a128,a129) 
        ca129a130 = chase(a129,a130) 
        ca130a131 = chase(a130,a131) 
        ca131a132 = chase(a131,a132) 
        ca132a133 = chase(a132,a133) 
        ca133a134 = chase(a133,a134) 
        ca134a135 = chase(a134,a135) 
        ca135a136 = chase(a135,a136) 
        ca136a137 = chase(a136,a137) 
        ca137a138 = chase(a137,a138) 
        ca138a139 = chase(a138,a139) 
        ca139a140 = chase(a139,a140) 
        ca140a141 = chase(a140,a141) 
        ca141a142 = chase(a141,a142) 
        ca142a143 = chase(a142,a143) 
        ca143a144 = chase(a143,a144) 
        ca144a145 = chase(a144,a145) 
        ca145a146 = chase(a145,a146) 
        ca146a147 = chase(a146,a147) 
        ca147a148 = chase(a147,a148) 
        ca148a149 = chase(a148,a149) 
        ca149a150 = chase(a149,a150) 
        ca150a151 = chase(a150,a151) 
        ca151a152 = chase(a151,a152) 
        ca152a153 = chase(a152,a153) 
        ca153a154 = chase(a153,a154) 
        ca154a155 = chase(a154,a155) 
        ca155a156 = chase(a155,a156) 
        ca156a157 = chase(a156,a157) 
        ca157a158 = chase(a157,a158) 
        ca158a159 = chase(a158,a159) 
        ca159a160 = chase(a159,a160) 
        ca160a161 = chase(a160,a161) 
        ca161a162 = chase(a161,a162) 
        ca162a163 = chase(a162,a163) 
        ca163a164 = chase(a163,a164) 
        ca164a165 = chase(a164,a165) 
        ca165a166 = chase(a165,a166) 
        ca166a167 = chase(a166,a167) 
        ca167a168 = chase(a167,a168) 
        ca168a169 = chase(a168,a169) 
        ca169a170 = chase(a169,a170) 
        ca170a171 = chase(a170,a171) 
        ca171a172 = chase(a171,a172) 
        ca172a173 = chase(a172,a173) 
        ca173a174 = chase(a173,a174) 
        ca174a175 = chase(a174,a175) 
        ca175a176 = chase(a175,a176) 
        ca176a177 = chase(a176,a177) 
        ca177a178 = chase(a177,a178) 
        ca178a179 = chase(a178,a179) 
        ca179a180 = chase(a179,a180) 
        ca180a181 = chase(a180,a181) 
        ca181a182 = chase(a181,a182) 
        ca182a183 = chase(a182,a183) 
        ca183a184 = chase(a183,a184) 
        ca184a185 = chase(a184,a185) 
        ca185a186 = chase(a185,a186) 
        ca186a187 = chase(a186,a187) 
        ca187a188 = chase(a187,a188) 
        ca188a189 = chase(a188,a189) 
        ca189a190 = chase(a189,a190) 
        ca190a191 = chase(a190,a191) 
        ca191a192 = chase(a191,a192) 
        ca192a193 = chase(a192,a193) 
        ca193a194 = chase(a193,a194) 
        ca194a195 = chase(a194,a195) 
        ca195a196 = chase(a195,a196) 
        ca196a197 = chase(a196,a197) 
        ca197a198 = chase(a197,a198) 
        ca198a199 = chase(a198,a199) 
        ca199a200 = chase(a199,a200) 
        ca200a201 = chase(a200,a201) 
        ca201a202 = chase(a201,a202) 
        ca202a203 = chase(a202,a203) 
        ca203a204 = chase(a203,a204) 
        ca204a205 = chase(a204,a205) 
        ca205a206 = chase(a205,a206) 
        ca206a207 = chase(a206,a207) 
        ca207a208 = chase(a207,a208) 
        ca208a209 = chase(a208,a209) 
        ca209a210 = chase(a209,a210) 
        ca210a211 = chase(a210,a211) 
        ca211a212 = chase(a211,a212) 
        ca212a213 = chase(a212,a213) 
        ca213a214 = chase(a213,a214) 
        ca214a215 = chase(a214,a215) 
        ca215a216 = chase(a215,a216) 
        ca216a217 = chase(a216,a217) 
        ca217a218 = chase(a217,a218) 
        ca218a219 = chase(a218,a219) 
        ca219a220 = chase(a219,a220) 
        ca220a221 = chase(a220,a221) 
        ca221a222 = chase(a221,a222) 
        ca222a223 = chase(a222,a223) 
        ca223a224 = chase(a223,a224) 
        ca224a225 = chase(a224,a225) 
        ca225a226 = chase(a225,a226) 
        ca226a227 = chase(a226,a227) 
        ca227a228 = chase(a227,a228) 
        ca228a229 = chase(a228,a229) 
        ca229a230 = chase(a229,a230) 
        ca230a231 = chase(a230,a231) 
        ca231a232 = chase(a231,a232) 
        ca232a233 = chase(a232,a233) 
        ca233a234 = chase(a233,a234) 
        ca234a235 = chase(a234,a235) 
        ca235a236 = chase(a235,a236) 
        ca236a237 = chase(a236,a237) 
        ca237a238 = chase(a237,a238) 
        ca238a239 = chase(a238,a239) 
        ca239a240 = chase(a239,a240) 
        ca240a241 = chase(a240,a241) 
        ca241a242 = chase(a241,a242) 
        ca242a243 = chase(a242,a243) 
        ca243a244 = chase(a243,a244) 
        ca244a245 = chase(a244,a245) 
        ca245a246 = chase(a245,a246) 
        ca246a247 = chase(a246,a247) 
        ca247a248 = chase(a247,a248) 
        ca248a249 = chase(a248,a249) 
        ca249a250 = chase(a249,a250) 
        ca250a251 = chase(a250,a251) 
        ca251a252 = chase(a251,a252) 
        ca252a253 = chase(a252,a253) 
        ca253a254 = chase(a253,a254) 
        ca254a255 = chase(a254,a255) 
        ca255a256 = chase(a255,a256) 
        ca256a257 = chase(a256,a257) 
        ca257a258 = chase(a257,a258) 
        ca258a259 = chase(a258,a259) 
        ca259a260 = chase(a259,a260) 
        ca260a261 = chase(a260,a261) 
        ca261a262 = chase(a261,a262) 
        ca262a263 = chase(a262,a263) 
        ca263a264 = chase(a263,a264) 
        ca264a265 = chase(a264,a265) 
        ca265a266 = chase(a265,a266) 
        ca266a267 = chase(a266,a267) 
        ca267a268 = chase(a267,a268) 
        ca268a269 = chase(a268,a269) 
        ca269a270 = chase(a269,a270) 
        ca270a271 = chase(a270,a271) 
        ca271a272 = chase(a271,a272) 
        ca272a273 = chase(a272,a273) 
        ca273a274 = chase(a273,a274) 
        ca274a275 = chase(a274,a275) 
        ca275a276 = chase(a275,a276) 
        ca276a277 = chase(a276,a277) 
        ca277a278 = chase(a277,a278) 
        ca278a279 = chase(a278,a279) 
        ca279a280 = chase(a279,a280) 
        ca280a281 = chase(a280,a281) 
        ca281a282 = chase(a281,a282) 
        ca282a283 = chase(a282,a283) 
        ca283a284 = chase(a283,a284) 
        ca284a285 = chase(a284,a285) 
        ca285a286 = chase(a285,a286) 
        ca286a287 = chase(a286,a287) 
        ca287a288 = chase(a287,a288) 
        ca288a289 = chase(a288,a289) 
        ca289a290 = chase(a289,a290) 
        ca290a291 = chase(a290,a291) 
        ca291a292 = chase(a291,a292) 
        ca292a293 = chase(a292,a293) 
        ca293a294 = chase(a293,a294) 
        ca294a295 = chase(a294,a295) 
        ca295a296 = chase(a295,a296) 
        ca296a297 = chase(a296,a297) 
        ca297a298 = chase(a297,a298) 
        ca298a299 = chase(a298,a299) 
        ca299a300 = chase(a299,a300) 
        ca300a301 = chase(a300,a301) 
        ca301a302 = chase(a301,a302) 
        ca302a303 = chase(a302,a303) 
        ca303a304 = chase(a303,a304) 
        ca304a305 = chase(a304,a305) 
        ca305a306 = chase(a305,a306) 
        ca306a307 = chase(a306,a307) 
        ca307a308 = chase(a307,a308) 
        ca308a309 = chase(a308,a309) 
        ca309a310 = chase(a309,a310) 
        ca310a311 = chase(a310,a311) 
        ca311a312 = chase(a311,a312) 
        ca312a313 = chase(a312,a313) 
        ca313a314 = chase(a313,a314) 
        ca314a315 = chase(a314,a315) 
        ca315a316 = chase(a315,a316) 
        ca316a317 = chase(a316,a317) 
        ca317a318 = chase(a317,a318) 
        ca318a319 = chase(a318,a319) 
        ca319a320 = chase(a319,a320) 
        ca320a321 = chase(a320,a321) 
        ca321a322 = chase(a321,a322) 
        ca322a323 = chase(a322,a323) 
        ca323a324 = chase(a323,a324) 
        ca324a325 = chase(a324,a325) 
        ca325a326 = chase(a325,a326) 
        ca326a327 = chase(a326,a327) 
        ca327a328 = chase(a327,a328) 
        ca328a329 = chase(a328,a329) 
        ca329a330 = chase(a329,a330) 
        ca330a331 = chase(a330,a331) 
        ca331a332 = chase(a331,a332) 
        ca332a333 = chase(a332,a333) 
        ca333a334 = chase(a333,a334) 
        ca334a335 = chase(a334,a335) 
        ca335a336 = chase(a335,a336) 
        ca336a337 = chase(a336,a337) 
        ca337a338 = chase(a337,a338) 
        ca338a339 = chase(a338,a339) 
        ca339a340 = chase(a339,a340) 
        ca340a341 = chase(a340,a341) 
        ca341a342 = chase(a341,a342) 
        ca342a343 = chase(a342,a343) 
        ca343a344 = chase(a343,a344) 
        ca344a345 = chase(a344,a345) 
        ca345a346 = chase(a345,a346) 
        ca346a347 = chase(a346,a347) 
        ca347a348 = chase(a347,a348) 
        ca348a349 = chase(a348,a349) 
        ca349a350 = chase(a349,a350) 
        ca350a351 = chase(a350,a351) 
        ca351a352 = chase(a351,a352) 
        ca352a353 = chase(a352,a353) 
        ca353a354 = chase(a353,a354) 
        ca354a355 = chase(a354,a355) 
        ca355a356 = chase(a355,a356) 
        ca356a357 = chase(a356,a357) 
        ca357a358 = chase(a357,a358) 
        ca358a359 = chase(a358,a359) 
        ca359a360 = chase(a359,a360) 
        ca360a361 = chase(a360,a361) 
        ca361a362 = chase(a361,a362) 
        ca362a363 = chase(a362,a363) 
        ca363a364 = chase(a363,a364) 
        ca364a365 = chase(a364,a365) 
        ca365a366 = chase(a365,a366) 
        ca366a367 = chase(a366,a367) 
        ca367a368 = chase(a367,a368) 
        ca368a369 = chase(a368,a369) 
        ca369a370 = chase(a369,a370) 
        ca370a371 = chase(a370,a371) 
        ca371a372 = chase(a371,a372) 
        ca372a373 = chase(a372,a373) 
        ca373a374 = chase(a373,a374) 
        ca374a375 = chase(a374,a375) 
        ca375a376 = chase(a375,a376) 
        ca376a377 = chase(a376,a377) 
        ca377a378 = chase(a377,a378) 
        ca378a379 = chase(a378,a379) 
        ca379a380 = chase(a379,a380) 
        ca380a381 = chase(a380,a381) 
        ca381a382 = chase(a381,a382) 
        ca382a383 = chase(a382,a383) 
        ca383a384 = chase(a383,a384) 
        ca384a385 = chase(a384,a385) 
        ca385a386 = chase(a385,a386) 
        ca386a387 = chase(a386,a387) 
        ca387a388 = chase(a387,a388) 
        ca388a389 = chase(a388,a389) 
        ca389a390 = chase(a389,a390) 
        ca390a391 = chase(a390,a391) 
        ca391a392 = chase(a391,a392) 
        ca392a393 = chase(a392,a393) 
        ca393a394 = chase(a393,a394) 
        ca394a395 = chase(a394,a395) 
        ca395a396 = chase(a395,a396) 
        ca396a397 = chase(a396,a397) 
        ca397a398 = chase(a397,a398) 
        ca398a399 = chase(a398,a399) 
        ;
        
        ''', metadata={
            'd': {SALIENCE: 1.0},
            'a0': {SALIENCE: 0.023899116621920347} ,
        
        'a1': {SALIENCE: 0.7691733973909711} ,
        
        'a2': {SALIENCE: 0.27889583184307276} ,
        
        'a3': {SALIENCE: 0.626419224683245} ,
        
        'a4': {SALIENCE: 0.6179537673495425} ,
        
        'a5': {SALIENCE: 0.4869829677425417} ,
        
        'a6': {SALIENCE: 0.8702729055591084} ,
        
        'a7': {SALIENCE: 0.9074223202629685} ,
        
        'a8': {SALIENCE: 0.8253189668215223} ,
        
        'a9': {SALIENCE: 0.24518212998180178} ,
        
        'a10': {SALIENCE: 0.2516602965688718} ,
        
        'a11': {SALIENCE: 0.13970185496533327} ,
        
        'a12': {SALIENCE: 0.725862441335661} ,
        
        'a13': {SALIENCE: 0.9600144433384424} ,
        
        'a14': {SALIENCE: 0.07847416045783495} ,
        
        'a15': {SALIENCE: 0.8439080690399352} ,
        
        'a16': {SALIENCE: 0.6305809851883728} ,
        
        'a17': {SALIENCE: 0.09813205601016362} ,
        
        'a18': {SALIENCE: 0.25760300707766715} ,
        
        'a19': {SALIENCE: 0.5988609965725218} ,
        
        'a20': {SALIENCE: 0.247350041224764} ,
        
        'a21': {SALIENCE: 0.812542724208213} ,
        
        'a22': {SALIENCE: 0.3666558643334089} ,
        
        'a23': {SALIENCE: 0.0425265834616787} ,
        
        'a24': {SALIENCE: 0.11790132721657809} ,
        
        'a25': {SALIENCE: 0.9645312092680323} ,
        
        'a26': {SALIENCE: 0.18391726569142341} ,
        
        'a27': {SALIENCE: 0.1166329523697287} ,
        
        'a28': {SALIENCE: 0.6531583092843698} ,
        
        'a29': {SALIENCE: 0.9411016724517332} ,
        
        'a30': {SALIENCE: 0.6210551142569067} ,
        
        'a31': {SALIENCE: 0.828821884707351} ,
        
        'a32': {SALIENCE: 0.3502491465369264} ,
        
        'a33': {SALIENCE: 0.8519470998544527} ,
        
        'a34': {SALIENCE: 0.3165351394489162} ,
        
        'a35': {SALIENCE: 0.12020580069519116} ,
        
        'a36': {SALIENCE: 0.7128815987889874} ,
        
        'a37': {SALIENCE: 0.08285067544696889} ,
        
        'a38': {SALIENCE: 0.45321451496168563} ,
        
        'a39': {SALIENCE: 0.91577443122166} ,
        
        'a40': {SALIENCE: 0.10991171173194114} ,
        
        'a41': {SALIENCE: 0.9287909989677642} ,
        
        'a42': {SALIENCE: 0.9196753113019273} ,
        
        'a43': {SALIENCE: 0.22542110576705898} ,
        
        'a44': {SALIENCE: 0.022656703103119513} ,
        
        'a45': {SALIENCE: 0.7910238854329581} ,
        
        'a46': {SALIENCE: 0.43007584670945354} ,
        
        'a47': {SALIENCE: 0.6718936007687625} ,
        
        'a48': {SALIENCE: 0.6934419984314221} ,
        
        'a49': {SALIENCE: 0.23159468990788623} ,
        
        'a50': {SALIENCE: 0.10422215028820603} ,
        
        'a51': {SALIENCE: 0.5258901016612744} ,
        
        'a52': {SALIENCE: 0.5429994656130084} ,
        
        'a53': {SALIENCE: 0.28019404973113116} ,
        
        'a54': {SALIENCE: 0.21735524381610183} ,
        
        'a55': {SALIENCE: 0.2955198400482515} ,
        
        'a56': {SALIENCE: 0.024105845094003153} ,
        
        'a57': {SALIENCE: 0.38029490443425884} ,
        
        'a58': {SALIENCE: 0.9114875029803786} ,
        
        'a59': {SALIENCE: 0.9683519993911659} ,
        
        'a60': {SALIENCE: 0.27176179024164626} ,
        
        'a61': {SALIENCE: 0.5037406017266555} ,
        
        'a62': {SALIENCE: 0.4956006457257699} ,
        
        'a63': {SALIENCE: 0.40458542664450026} ,
        
        'a64': {SALIENCE: 0.7801822415327151} ,
        
        'a65': {SALIENCE: 0.5926283989457775} ,
        
        'a66': {SALIENCE: 0.15742047595538744} ,
        
        'a67': {SALIENCE: 0.17238626510270283} ,
        
        'a68': {SALIENCE: 0.19356489088240636} ,
        
        'a69': {SALIENCE: 0.30060096198728303} ,
        
        'a70': {SALIENCE: 0.09196659301537857} ,
        
        'a71': {SALIENCE: 0.8281512465949638} ,
        
        'a72': {SALIENCE: 0.942040016693936} ,
        
        'a73': {SALIENCE: 0.8396301170607702} ,
        
        'a74': {SALIENCE: 0.2856881389839234} ,
        
        'a75': {SALIENCE: 0.9420880320116404} ,
        
        'a76': {SALIENCE: 0.533874588999786} ,
        
        'a77': {SALIENCE: 0.9189502578103731} ,
        
        'a78': {SALIENCE: 0.5343032965601336} ,
        
        'a79': {SALIENCE: 0.20285432941144665} ,
        
        'a80': {SALIENCE: 0.2996730445571617} ,
        
        'a81': {SALIENCE: 0.4848419445660469} ,
        
        'a82': {SALIENCE: 0.3742940245650421} ,
        
        'a83': {SALIENCE: 0.16789774593229934} ,
        
        'a84': {SALIENCE: 0.43098529865648116} ,
        
        'a85': {SALIENCE: 0.2678553157935447} ,
        
        'a86': {SALIENCE: 0.7105196690374539} ,
        
        'a87': {SALIENCE: 0.30437564476900303} ,
        
        'a88': {SALIENCE: 0.7235341743299419} ,
        
        'a89': {SALIENCE: 0.9223710961999433} ,
        
        'a90': {SALIENCE: 0.8178646893107065} ,
        
        'a91': {SALIENCE: 0.21809906834501114} ,
        
        'a92': {SALIENCE: 0.8379022138166569} ,
        
        'a93': {SALIENCE: 0.46387720807405386} ,
        
        'a94': {SALIENCE: 0.6182901525038814} ,
        
        'a95': {SALIENCE: 0.8026026238034288} ,
        
        'a96': {SALIENCE: 0.7939641277416787} ,
        
        'a97': {SALIENCE: 0.2431015548900055} ,
        
        'a98': {SALIENCE: 0.32417326045464967} ,
        
        'a99': {SALIENCE: 0.5942213745672907} ,
        
        'a100': {SALIENCE: 0.9902251550209438} ,
        
        'a101': {SALIENCE: 0.8062868935005185} ,
        
        'a102': {SALIENCE: 0.4023977719164358} ,
        
        'a103': {SALIENCE: 0.43424018978466883} ,
        
        'a104': {SALIENCE: 0.4154391947586207} ,
        
        'a105': {SALIENCE: 0.4013743902425284} ,
        
        'a106': {SALIENCE: 0.5486294389141465} ,
        
        'a107': {SALIENCE: 0.21764575735457925} ,
        
        'a108': {SALIENCE: 0.7485748199341732} ,
        
        'a109': {SALIENCE: 0.9299924370664523} ,
        
        'a110': {SALIENCE: 0.20619840795767885} ,
        
        'a111': {SALIENCE: 0.1361333175849404} ,
        
        'a112': {SALIENCE: 0.4020369603414712} ,
        
        'a113': {SALIENCE: 0.7031801536230186} ,
        
        'a114': {SALIENCE: 0.5792840331687722} ,
        
        'a115': {SALIENCE: 0.6569272966650261} ,
        
        'a116': {SALIENCE: 0.38324390868693314} ,
        
        'a117': {SALIENCE: 0.7764633882694655} ,
        
        'a118': {SALIENCE: 0.027115284107960713} ,
        
        'a119': {SALIENCE: 0.2055424531311314} ,
        
        'a120': {SALIENCE: 0.749385445446739} ,
        
        'a121': {SALIENCE: 0.3516092525701886} ,
        
        'a122': {SALIENCE: 0.25151146112350364} ,
        
        'a123': {SALIENCE: 0.3734419819885695} ,
        
        'a124': {SALIENCE: 0.4987605157895396} ,
        
        'a125': {SALIENCE: 0.485688464757699} ,
        
        'a126': {SALIENCE: 0.7129172098148505} ,
        
        'a127': {SALIENCE: 0.876666191105639} ,
        
        'a128': {SALIENCE: 0.9199038115161805} ,
        
        'a129': {SALIENCE: 0.08152612381614976} ,
        
        'a130': {SALIENCE: 0.6640087596469675} ,
        
        'a131': {SALIENCE: 0.722164271162843} ,
        
        'a132': {SALIENCE: 0.13179957787280172} ,
        
        'a133': {SALIENCE: 0.006339104492545933} ,
        
        'a134': {SALIENCE: 0.8017457003939485} ,
        
        'a135': {SALIENCE: 0.503945586180475} ,
        
        'a136': {SALIENCE: 0.8971166661738349} ,
        
        'a137': {SALIENCE: 0.6009395655185603} ,
        
        'a138': {SALIENCE: 0.03697786651289836} ,
        
        'a139': {SALIENCE: 0.6604168378249943} ,
        
        'a140': {SALIENCE: 0.5768887623076554} ,
        
        'a141': {SALIENCE: 0.9643844883441652} ,
        
        'a142': {SALIENCE: 0.26365024366281575} ,
        
        'a143': {SALIENCE: 0.9142432991402841} ,
        
        'a144': {SALIENCE: 0.8571926441039858} ,
        
        'a145': {SALIENCE: 0.141951209477443} ,
        
        'a146': {SALIENCE: 0.79089451908534} ,
        
        'a147': {SALIENCE: 0.3069709333682926} ,
        
        'a148': {SALIENCE: 0.13222054860581278} ,
        
        'a149': {SALIENCE: 0.29955995817227266} ,
        
        'a150': {SALIENCE: 0.34037430852340567} ,
        
        'a151': {SALIENCE: 0.5938274899376944} ,
        
        'a152': {SALIENCE: 0.9950938723582832} ,
        
        'a153': {SALIENCE: 0.7399362102375092} ,
        
        'a154': {SALIENCE: 0.31212895703998234} ,
        
        'a155': {SALIENCE: 0.5247796772720733} ,
        
        'a156': {SALIENCE: 0.7798564205852266} ,
        
        'a157': {SALIENCE: 0.2036208721573779} ,
        
        'a158': {SALIENCE: 0.7730466311204933} ,
        
        'a159': {SALIENCE: 0.6938646011123412} ,
        
        'a160': {SALIENCE: 0.02055234023108865} ,
        
        'a161': {SALIENCE: 0.026464043377296242} ,
        
        'a162': {SALIENCE: 0.35510534194943677} ,
        
        'a163': {SALIENCE: 0.8419786015564049} ,
        
        'a164': {SALIENCE: 0.7256447086544107} ,
        
        'a165': {SALIENCE: 0.10955581621194155} ,
        
        'a166': {SALIENCE: 0.9167590635283455} ,
        
        'a167': {SALIENCE: 0.05157603453190851} ,
        
        'a168': {SALIENCE: 0.28255016275845457} ,
        
        'a169': {SALIENCE: 0.12051279625455424} ,
        
        'a170': {SALIENCE: 0.26284512144973315} ,
        
        'a171': {SALIENCE: 0.04089893748840645} ,
        
        'a172': {SALIENCE: 0.8534788565584281} ,
        
        'a173': {SALIENCE: 0.7310874842150755} ,
        
        'a174': {SALIENCE: 0.7133797653637451} ,
        
        'a175': {SALIENCE: 0.38240183840993147} ,
        
        'a176': {SALIENCE: 0.9692595640973687} ,
        
        'a177': {SALIENCE: 0.004554833463495833} ,
        
        'a178': {SALIENCE: 0.2389006661649834} ,
        
        'a179': {SALIENCE: 0.6528353698857621} ,
        
        'a180': {SALIENCE: 0.6611378585138101} ,
        
        'a181': {SALIENCE: 0.5928657778172512} ,
        
        'a182': {SALIENCE: 0.40162981969700484} ,
        
        'a183': {SALIENCE: 0.2729485784231308} ,
        
        'a184': {SALIENCE: 0.05389968304170556} ,
        
        'a185': {SALIENCE: 0.9778569855178388} ,
        
        'a186': {SALIENCE: 0.3717282561088483} ,
        
        'a187': {SALIENCE: 0.733383539688043} ,
        
        'a188': {SALIENCE: 0.9493089020673806} ,
        
        'a189': {SALIENCE: 0.9522790333082397} ,
        
        'a190': {SALIENCE: 0.7777429301829532} ,
        
        'a191': {SALIENCE: 0.18813712252732828} ,
        
        'a192': {SALIENCE: 0.49638032212860894} ,
        
        'a193': {SALIENCE: 0.993252942832144} ,
        
        'a194': {SALIENCE: 0.8356957418064092} ,
        
        'a195': {SALIENCE: 0.44209501538862683} ,
        
        'a196': {SALIENCE: 0.9063552248654322} ,
        
        'a197': {SALIENCE: 0.1587268158482853} ,
        
        'a198': {SALIENCE: 0.4076693139917148} ,
        
        'a199': {SALIENCE: 0.1667768716111362} ,
        
        'a200': {SALIENCE: 0.2984906279957923} ,
        
        'a201': {SALIENCE: 0.1476833540056457} ,
        
        'a202': {SALIENCE: 0.9296660852495305} ,
        
        'a203': {SALIENCE: 0.16238802593803092} ,
        
        'a204': {SALIENCE: 0.8052243028195811} ,
        
        'a205': {SALIENCE: 0.4962896188361413} ,
        
        'a206': {SALIENCE: 0.29610336695087014} ,
        
        'a207': {SALIENCE: 0.28831238878628074} ,
        
        'a208': {SALIENCE: 0.31502451733594283} ,
        
        'a209': {SALIENCE: 0.1533412391249328} ,
        
        'a210': {SALIENCE: 0.31994970121954647} ,
        
        'a211': {SALIENCE: 0.36757011307692145} ,
        
        'a212': {SALIENCE: 0.4439441974978803} ,
        
        'a213': {SALIENCE: 0.5774697359808512} ,
        
        'a214': {SALIENCE: 0.6698934684705146} ,
        
        'a215': {SALIENCE: 0.45144618447504414} ,
        
        'a216': {SALIENCE: 0.6549509071413091} ,
        
        'a217': {SALIENCE: 0.03169555674465008} ,
        
        'a218': {SALIENCE: 0.5900731445752193} ,
        
        'a219': {SALIENCE: 0.9983856975254257} ,
        
        'a220': {SALIENCE: 0.6368115128003085} ,
        
        'a221': {SALIENCE: 0.2973990576333527} ,
        
        'a222': {SALIENCE: 0.7651832160479834} ,
        
        'a223': {SALIENCE: 0.090860283244797} ,
        
        'a224': {SALIENCE: 0.9859393701482669} ,
        
        'a225': {SALIENCE: 0.04059372713597731} ,
        
        'a226': {SALIENCE: 0.7686395049964941} ,
        
        'a227': {SALIENCE: 0.35389392549100274} ,
        
        'a228': {SALIENCE: 0.7835989437760168} ,
        
        'a229': {SALIENCE: 0.49120351181178856} ,
        
        'a230': {SALIENCE: 0.8782910572501417} ,
        
        'a231': {SALIENCE: 0.13545275438637483} ,
        
        'a232': {SALIENCE: 0.5908561693357167} ,
        
        'a233': {SALIENCE: 0.5330012954937315} ,
        
        'a234': {SALIENCE: 0.8278426540069228} ,
        
        'a235': {SALIENCE: 0.22742932341083755} ,
        
        'a236': {SALIENCE: 0.33824323195598593} ,
        
        'a237': {SALIENCE: 0.7972305500375291} ,
        
        'a238': {SALIENCE: 0.8411850743003968} ,
        
        'a239': {SALIENCE: 0.6327580568563473} ,
        
        'a240': {SALIENCE: 0.6695423574956754} ,
        
        'a241': {SALIENCE: 0.5615475161995195} ,
        
        'a242': {SALIENCE: 0.435481284146225} ,
        
        'a243': {SALIENCE: 0.5085802789401784} ,
        
        'a244': {SALIENCE: 0.28530790258659633} ,
        
        'a245': {SALIENCE: 0.06305341296662337} ,
        
        'a246': {SALIENCE: 0.24009630978898633} ,
        
        'a247': {SALIENCE: 0.6192796811346575} ,
        
        'a248': {SALIENCE: 0.0027663550945010718} ,
        
        'a249': {SALIENCE: 0.5291144696611011} ,
        
        'a250': {SALIENCE: 0.7653660010491801} ,
        
        'a251': {SALIENCE: 0.38516708488240836} ,
        
        'a252': {SALIENCE: 0.09934656987105206} ,
        
        'a253': {SALIENCE: 0.6144711418700032} ,
        
        'a254': {SALIENCE: 0.38049012320000664} ,
        
        'a255': {SALIENCE: 0.29598239325273623} ,
        
        'a256': {SALIENCE: 0.4313915201155035} ,
        
        'a257': {SALIENCE: 0.025789292836050803} ,
        
        'a258': {SALIENCE: 0.8411037805571062} ,
        
        'a259': {SALIENCE: 0.06665303916775656} ,
        
        'a260': {SALIENCE: 0.7101560112735157} ,
        
        'a261': {SALIENCE: 0.9646984300728267} ,
        
        'a262': {SALIENCE: 0.28816668692620573} ,
        
        'a263': {SALIENCE: 0.11608348217872977} ,
        
        'a264': {SALIENCE: 0.8382309140438385} ,
        
        'a265': {SALIENCE: 0.4823102901634424} ,
        
        'a266': {SALIENCE: 0.9358879215302628} ,
        
        'a267': {SALIENCE: 0.2711072738194512} ,
        
        'a268': {SALIENCE: 0.7153848937756262} ,
        
        'a269': {SALIENCE: 0.6729123583766606} ,
        
        'a270': {SALIENCE: 0.8547785122709125} ,
        
        'a271': {SALIENCE: 0.48355265070060094} ,
        
        'a272': {SALIENCE: 0.23607205267728626} ,
        
        'a273': {SALIENCE: 0.47502179498896946} ,
        
        'a274': {SALIENCE: 0.7665960054894864} ,
        
        'a275': {SALIENCE: 0.2710343371971624} ,
        
        'a276': {SALIENCE: 0.6869877744139583} ,
        
        'a277': {SALIENCE: 0.7627797719047156} ,
        
        'a278': {SALIENCE: 0.5000286626246923} ,
        
        'a279': {SALIENCE: 0.6792911118876717} ,
        
        'a280': {SALIENCE: 0.46187826802668885} ,
        
        'a281': {SALIENCE: 0.4782094102921226} ,
        
        'a282': {SALIENCE: 0.26839319856379706} ,
        
        'a283': {SALIENCE: 0.94199089396276} ,
        
        'a284': {SALIENCE: 0.4923751837484922} ,
        
        'a285': {SALIENCE: 0.36128231900246377} ,
        
        'a286': {SALIENCE: 0.33075189274322103} ,
        
        'a287': {SALIENCE: 0.6686723509505146} ,
        
        'a288': {SALIENCE: 0.27324531064768} ,
        
        'a289': {SALIENCE: 0.02878955376441583} ,
        
        'a290': {SALIENCE: 0.19379471684163552} ,
        
        'a291': {SALIENCE: 0.45840335625976536} ,
        
        'a292': {SALIENCE: 0.0332171274300066} ,
        
        'a293': {SALIENCE: 0.8139125408314154} ,
        
        'a294': {SALIENCE: 0.18062901816061327} ,
        
        'a295': {SALIENCE: 0.39259581797439724} ,
        
        'a296': {SALIENCE: 0.7950873463370141} ,
        
        'a297': {SALIENCE: 0.13273332905899493} ,
        
        'a298': {SALIENCE: 0.26777417245442714} ,
        
        'a299': {SALIENCE: 0.7455155392390896} ,
        
        'a300': {SALIENCE: 0.13452241768666662} ,
        
        'a301': {SALIENCE: 0.4400565680395313} ,
        
        'a302': {SALIENCE: 0.43372065925404835} ,
        
        'a303': {SALIENCE: 0.6502710115644037} ,
        
        'a304': {SALIENCE: 0.32271882254123896} ,
        
        'a305': {SALIENCE: 0.1719982656905482} ,
        
        'a306': {SALIENCE: 0.023682623141305537} ,
        
        'a307': {SALIENCE: 0.05666129323751301} ,
        
        'a308': {SALIENCE: 0.05790817471121312} ,
        
        'a309': {SALIENCE: 0.8256883848082425} ,
        
        'a310': {SALIENCE: 0.0818051067158887} ,
        
        'a311': {SALIENCE: 0.9893626969076641} ,
        
        'a312': {SALIENCE: 0.980995680806577} ,
        
        'a313': {SALIENCE: 0.1316794307256136} ,
        
        'a314': {SALIENCE: 0.8783033264493519} ,
        
        'a315': {SALIENCE: 0.3632445750601415} ,
        
        'a316': {SALIENCE: 0.33344039227684374} ,
        
        'a317': {SALIENCE: 0.8041282922592498} ,
        
        'a318': {SALIENCE: 0.10984503705159565} ,
        
        'a319': {SALIENCE: 0.8293859656371609} ,
        
        'a320': {SALIENCE: 0.11642076378348076} ,
        
        'a321': {SALIENCE: 0.201149304124714} ,
        
        'a322': {SALIENCE: 0.942269252588011} ,
        
        'a323': {SALIENCE: 0.707582712063398} ,
        
        'a324': {SALIENCE: 0.5229814715989899} ,
        
        'a325': {SALIENCE: 0.5252405217098893} ,
        
        'a326': {SALIENCE: 0.2971122479344396} ,
        
        'a327': {SALIENCE: 0.8137623339410499} ,
        
        'a328': {SALIENCE: 0.26371116808542694} ,
        
        'a329': {SALIENCE: 0.4020782234610585} ,
        
        'a330': {SALIENCE: 0.4930844476656857} ,
        
        'a331': {SALIENCE: 0.07542916142469824} ,
        
        'a332': {SALIENCE: 0.8991090556258534} ,
        
        'a333': {SALIENCE: 0.37854842587101367} ,
        
        'a334': {SALIENCE: 0.14200360520911792} ,
        
        'a335': {SALIENCE: 0.46345872362815244} ,
        
        'a336': {SALIENCE: 0.9872062544150372} ,
        
        'a337': {SALIENCE: 0.15583795179439408} ,
        
        'a338': {SALIENCE: 0.231430461350435} ,
        
        'a339': {SALIENCE: 0.4943838846737284} ,
        
        'a340': {SALIENCE: 0.2553243094879183} ,
        
        'a341': {SALIENCE: 0.9950655806221382} ,
        
        'a342': {SALIENCE: 0.14395056522281646} ,
        
        'a343': {SALIENCE: 0.8434331366591963} ,
        
        'a344': {SALIENCE: 0.5257585621551883} ,
        
        'a345': {SALIENCE: 0.8746731683739165} ,
        
        'a346': {SALIENCE: 0.4879562340762156} ,
        
        'a347': {SALIENCE: 0.49133676780452884} ,
        
        'a348': {SALIENCE: 0.25617536985032074} ,
        
        'a349': {SALIENCE: 0.7183843488612579} ,
        
        'a350': {SALIENCE: 0.27414265136031535} ,
        
        'a351': {SALIENCE: 0.21537573167674606} ,
        
        'a352': {SALIENCE: 0.3627110666792419} ,
        
        'a353': {SALIENCE: 0.7752346239075797} ,
        
        'a354': {SALIENCE: 0.37944335314115873} ,
        
        'a355': {SALIENCE: 0.9848953948010569} ,
        
        'a356': {SALIENCE: 0.6522407799143158} ,
        
        'a357': {SALIENCE: 0.17344403845137168} ,
        
        'a358': {SALIENCE: 0.16350224892567178} ,
        
        'a359': {SALIENCE: 0.8517482075732539} ,
        
        'a360': {SALIENCE: 0.6260682519974766} ,
        
        'a361': {SALIENCE: 0.42440971559378526} ,
        
        'a362': {SALIENCE: 0.19594333095591598} ,
        
        'a363': {SALIENCE: 0.945406637897845} ,
        
        'a364': {SALIENCE: 0.686774754417035} ,
        
        'a365': {SALIENCE: 0.5888755488928561} ,
        
        'a366': {SALIENCE: 0.9871427832104646} ,
        
        'a367': {SALIENCE: 0.558218956796884} ,
        
        'a368': {SALIENCE: 0.7038540832882736} ,
        
        'a369': {SALIENCE: 0.6972975185417274} ,
        
        'a370': {SALIENCE: 0.7123643835371611} ,
        
        'a371': {SALIENCE: 0.24008194259089188} ,
        
        'a372': {SALIENCE: 0.4260208726721816} ,
        
        'a373': {SALIENCE: 0.30049745373153136} ,
        
        'a374': {SALIENCE: 0.950690457733595} ,
        
        'a375': {SALIENCE: 0.4172581967024245} ,
        
        'a376': {SALIENCE: 0.8823042134658584} ,
        
        'a377': {SALIENCE: 0.5914379305414266} ,
        
        'a378': {SALIENCE: 0.8405526837216588} ,
        
        'a379': {SALIENCE: 0.33632988382288986} ,
        
        'a380': {SALIENCE: 0.004013215755486077} ,
        
        'a381': {SALIENCE: 0.8531669298846265} ,
        
        'a382': {SALIENCE: 0.08257348411842602} ,
        
        'a383': {SALIENCE: 0.3785772586359142} ,
        
        'a384': {SALIENCE: 0.7461535325129273} ,
        
        'a385': {SALIENCE: 0.3144940328705822} ,
        
        'a386': {SALIENCE: 0.3319945149747212} ,
        
        'a387': {SALIENCE: 0.01628201920346295} ,
        
        'a388': {SALIENCE: 0.24593132196824818} ,
        
        'a389': {SALIENCE: 0.7794306702365773} ,
        
        'a390': {SALIENCE: 0.1225452151894082} ,
        
        'a391': {SALIENCE: 0.3406972083500205} ,
        
        'a392': {SALIENCE: 0.983204906464494} ,
        
        'a393': {SALIENCE: 0.7110067975150617} ,
        
        'a394': {SALIENCE: 0.7136760479360563} ,
        
        'a395': {SALIENCE: 0.7454511707733014} ,
        
        'a396': {SALIENCE: 0.6526599840354983} ,
        
        'a397': {SALIENCE: 0.9799271565973386} ,
        
        'a398': {SALIENCE: 0.6087323894186925} ,
        
        
        })

        # Here's how to access concept salience
        assert wm.features['d'][SALIENCE] == 1.0
        import time
        t1 = time.time()
        saliencesold = update_salienceold(wm)
        t2 = time.time()
        print("\nOld method: {}".format(t2 - t1))
        wm = ConceptGraph('''

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
                 a0 = dog() 
                 a1 = dog() 
                 a2 = dog() 
                 a3 = dog() 
                 a4 = dog() 
                 a5 = dog() 
                 a6 = dog() 
                 a7 = dog() 
                 a8 = dog() 
                 a9 = dog() 
                 a10 = dog() 
                 a11 = dog() 
                 a12 = dog() 
                 a13 = dog() 
                 a14 = dog() 
                 a15 = dog() 
                 a16 = dog() 
                 a17 = dog() 
                 a18 = dog() 
                 a19 = dog() 
                 a20 = dog() 
                 a21 = dog() 
                 a22 = dog() 
                 a23 = dog() 
                 a24 = dog() 
                 a25 = dog() 
                 a26 = dog() 
                 a27 = dog() 
                 a28 = dog() 
                 a29 = dog() 
                 a30 = dog() 
                 a31 = dog() 
                 a32 = dog() 
                 a33 = dog() 
                 a34 = dog() 
                 a35 = dog() 
                 a36 = dog() 
                 a37 = dog() 
                 a38 = dog() 
                 a39 = dog() 
                 a40 = dog() 
                 a41 = dog() 
                 a42 = dog() 
                 a43 = dog() 
                 a44 = dog() 
                 a45 = dog() 
                 a46 = dog() 
                 a47 = dog() 
                 a48 = dog() 
                 a49 = dog() 
                 a50 = dog() 
                 a51 = dog() 
                 a52 = dog() 
                 a53 = dog() 
                 a54 = dog() 
                 a55 = dog() 
                 a56 = dog() 
                 a57 = dog() 
                 a58 = dog() 
                 a59 = dog() 
                 a60 = dog() 
                 a61 = dog() 
                 a62 = dog() 
                 a63 = dog() 
                 a64 = dog() 
                 a65 = dog() 
                 a66 = dog() 
                 a67 = dog() 
                 a68 = dog() 
                 a69 = dog() 
                 a70 = dog() 
                 a71 = dog() 
                 a72 = dog() 
                 a73 = dog() 
                 a74 = dog() 
                 a75 = dog() 
                 a76 = dog() 
                 a77 = dog() 
                 a78 = dog() 
                 a79 = dog() 
                 a80 = dog() 
                 a81 = dog() 
                 a82 = dog() 
                 a83 = dog() 
                 a84 = dog() 
                 a85 = dog() 
                 a86 = dog() 
                 a87 = dog() 
                 a88 = dog() 
                 a89 = dog() 
                 a90 = dog() 
                 a91 = dog() 
                 a92 = dog() 
                 a93 = dog() 
                 a94 = dog() 
                 a95 = dog() 
                 a96 = dog() 
                 a97 = dog() 
                 a98 = dog() 
                 a99 = dog() 
                 a100 = dog() 
                 a101 = dog() 
                 a102 = dog() 
                 a103 = dog() 
                 a104 = dog() 
                 a105 = dog() 
                 a106 = dog() 
                 a107 = dog() 
                 a108 = dog() 
                 a109 = dog() 
                 a110 = dog() 
                 a111 = dog() 
                 a112 = dog() 
                 a113 = dog() 
                 a114 = dog() 
                 a115 = dog() 
                 a116 = dog() 
                 a117 = dog() 
                 a118 = dog() 
                 a119 = dog() 
                 a120 = dog() 
                 a121 = dog() 
                 a122 = dog() 
                 a123 = dog() 
                 a124 = dog() 
                 a125 = dog() 
                 a126 = dog() 
                 a127 = dog() 
                 a128 = dog() 
                 a129 = dog() 
                 a130 = dog() 
                 a131 = dog() 
                 a132 = dog() 
                 a133 = dog() 
                 a134 = dog() 
                 a135 = dog() 
                 a136 = dog() 
                 a137 = dog() 
                 a138 = dog() 
                 a139 = dog() 
                 a140 = dog() 
                 a141 = dog() 
                 a142 = dog() 
                 a143 = dog() 
                 a144 = dog() 
                 a145 = dog() 
                 a146 = dog() 
                 a147 = dog() 
                 a148 = dog() 
                 a149 = dog() 
                 a150 = dog() 
                 a151 = dog() 
                 a152 = dog() 
                 a153 = dog() 
                 a154 = dog() 
                 a155 = dog() 
                 a156 = dog() 
                 a157 = dog() 
                 a158 = dog() 
                 a159 = dog() 
                 a160 = dog() 
                 a161 = dog() 
                 a162 = dog() 
                 a163 = dog() 
                 a164 = dog() 
                 a165 = dog() 
                 a166 = dog() 
                 a167 = dog() 
                 a168 = dog() 
                 a169 = dog() 
                 a170 = dog() 
                 a171 = dog() 
                 a172 = dog() 
                 a173 = dog() 
                 a174 = dog() 
                 a175 = dog() 
                 a176 = dog() 
                 a177 = dog() 
                 a178 = dog() 
                 a179 = dog() 
                 a180 = dog() 
                 a181 = dog() 
                 a182 = dog() 
                 a183 = dog() 
                 a184 = dog() 
                 a185 = dog() 
                 a186 = dog() 
                 a187 = dog() 
                 a188 = dog() 
                 a189 = dog() 
                 a190 = dog() 
                 a191 = dog() 
                 a192 = dog() 
                 a193 = dog() 
                 a194 = dog() 
                 a195 = dog() 
                 a196 = dog() 
                 a197 = dog() 
                 a198 = dog() 
                 a199 = dog() 
                 a200 = dog() 
                 a201 = dog() 
                 a202 = dog() 
                 a203 = dog() 
                 a204 = dog() 
                 a205 = dog() 
                 a206 = dog() 
                 a207 = dog() 
                 a208 = dog() 
                 a209 = dog() 
                 a210 = dog() 
                 a211 = dog() 
                 a212 = dog() 
                 a213 = dog() 
                 a214 = dog() 
                 a215 = dog() 
                 a216 = dog() 
                 a217 = dog() 
                 a218 = dog() 
                 a219 = dog() 
                 a220 = dog() 
                 a221 = dog() 
                 a222 = dog() 
                 a223 = dog() 
                 a224 = dog() 
                 a225 = dog() 
                 a226 = dog() 
                 a227 = dog() 
                 a228 = dog() 
                 a229 = dog() 
                 a230 = dog() 
                 a231 = dog() 
                 a232 = dog() 
                 a233 = dog() 
                 a234 = dog() 
                 a235 = dog() 
                 a236 = dog() 
                 a237 = dog() 
                 a238 = dog() 
                 a239 = dog() 
                 a240 = dog() 
                 a241 = dog() 
                 a242 = dog() 
                 a243 = dog() 
                 a244 = dog() 
                 a245 = dog() 
                 a246 = dog() 
                 a247 = dog() 
                 a248 = dog() 
                 a249 = dog() 
                 a250 = dog() 
                 a251 = dog() 
                 a252 = dog() 
                 a253 = dog() 
                 a254 = dog() 
                 a255 = dog() 
                 a256 = dog() 
                 a257 = dog() 
                 a258 = dog() 
                 a259 = dog() 
                 a260 = dog() 
                 a261 = dog() 
                 a262 = dog() 
                 a263 = dog() 
                 a264 = dog() 
                 a265 = dog() 
                 a266 = dog() 
                 a267 = dog() 
                 a268 = dog() 
                 a269 = dog() 
                 a270 = dog() 
                 a271 = dog() 
                 a272 = dog() 
                 a273 = dog() 
                 a274 = dog() 
                 a275 = dog() 
                 a276 = dog() 
                 a277 = dog() 
                 a278 = dog() 
                 a279 = dog() 
                 a280 = dog() 
                 a281 = dog() 
                 a282 = dog() 
                 a283 = dog() 
                 a284 = dog() 
                 a285 = dog() 
                 a286 = dog() 
                 a287 = dog() 
                 a288 = dog() 
                 a289 = dog() 
                 a290 = dog() 
                 a291 = dog() 
                 a292 = dog() 
                 a293 = dog() 
                 a294 = dog() 
                 a295 = dog() 
                 a296 = dog() 
                 a297 = dog() 
                 a298 = dog() 
                 a299 = dog() 
                 a300 = dog() 
                 a301 = dog() 
                 a302 = dog() 
                 a303 = dog() 
                 a304 = dog() 
                 a305 = dog() 
                 a306 = dog() 
                 a307 = dog() 
                 a308 = dog() 
                 a309 = dog() 
                 a310 = dog() 
                 a311 = dog() 
                 a312 = dog() 
                 a313 = dog() 
                 a314 = dog() 
                 a315 = dog() 
                 a316 = dog() 
                 a317 = dog() 
                 a318 = dog() 
                 a319 = dog() 
                 a320 = dog() 
                 a321 = dog() 
                 a322 = dog() 
                 a323 = dog() 
                 a324 = dog() 
                 a325 = dog() 
                 a326 = dog() 
                 a327 = dog() 
                 a328 = dog() 
                 a329 = dog() 
                 a330 = dog() 
                 a331 = dog() 
                 a332 = dog() 
                 a333 = dog() 
                 a334 = dog() 
                 a335 = dog() 
                 a336 = dog() 
                 a337 = dog() 
                 a338 = dog() 
                 a339 = dog() 
                 a340 = dog() 
                 a341 = dog() 
                 a342 = dog() 
                 a343 = dog() 
                 a344 = dog() 
                 a345 = dog() 
                 a346 = dog() 
                 a347 = dog() 
                 a348 = dog() 
                 a349 = dog() 
                 a350 = dog() 
                 a351 = dog() 
                 a352 = dog() 
                 a353 = dog() 
                 a354 = dog() 
                 a355 = dog() 
                 a356 = dog() 
                 a357 = dog() 
                 a358 = dog() 
                 a359 = dog() 
                 a360 = dog() 
                 a361 = dog() 
                 a362 = dog() 
                 a363 = dog() 
                 a364 = dog() 
                 a365 = dog() 
                 a366 = dog() 
                 a367 = dog() 
                 a368 = dog() 
                 a369 = dog() 
                 a370 = dog() 
                 a371 = dog() 
                 a372 = dog() 
                 a373 = dog() 
                 a374 = dog() 
                 a375 = dog() 
                 a376 = dog() 
                 a377 = dog() 
                 a378 = dog() 
                 a379 = dog() 
                 a380 = dog() 
                 a381 = dog() 
                 a382 = dog() 
                 a383 = dog() 
                 a384 = dog() 
                 a385 = dog() 
                 a386 = dog() 
                 a387 = dog() 
                 a388 = dog() 
                 a389 = dog() 
                 a390 = dog() 
                 a391 = dog() 
                 a392 = dog() 
                 a393 = dog() 
                 a394 = dog() 
                 a395 = dog() 
                 a396 = dog() 
                 a397 = dog() 
                 a398 = dog() 
                 a399 = dog() 

                 ;

                 cab=chase(a, b)
                 cbc=chase(b, c)
                 ccd=chase(c, d)
                 cde=chase(d, e)
                 cef=chase(e, f)
                 cfg=chase(f, g)
                 cgh=chase(g, h)
                 cgi=chase(g, i)
                 ca0a1 = chase(a0,a1) 
                 ca1a2 = chase(a1,a2) 
                 ca2a3 = chase(a2,a3) 
                 ca3a4 = chase(a3,a4) 
                 ca4a5 = chase(a4,a5) 
                 ca5a6 = chase(a5,a6) 
                 ca6a7 = chase(a6,a7) 
                 ca7a8 = chase(a7,a8) 
                 ca8a9 = chase(a8,a9) 
                 ca9a10 = chase(a9,a10) 
                 ca10a11 = chase(a10,a11) 
                 ca11a12 = chase(a11,a12) 
                 ca12a13 = chase(a12,a13) 
                 ca13a14 = chase(a13,a14) 
                 ca14a15 = chase(a14,a15) 
                 ca15a16 = chase(a15,a16) 
                 ca16a17 = chase(a16,a17) 
                 ca17a18 = chase(a17,a18) 
                 ca18a19 = chase(a18,a19) 
                 ca19a20 = chase(a19,a20) 
                 ca20a21 = chase(a20,a21) 
                 ca21a22 = chase(a21,a22) 
                 ca22a23 = chase(a22,a23) 
                 ca23a24 = chase(a23,a24) 
                 ca24a25 = chase(a24,a25) 
                 ca25a26 = chase(a25,a26) 
                 ca26a27 = chase(a26,a27) 
                 ca27a28 = chase(a27,a28) 
                 ca28a29 = chase(a28,a29) 
                 ca29a30 = chase(a29,a30) 
                 ca30a31 = chase(a30,a31) 
                 ca31a32 = chase(a31,a32) 
                 ca32a33 = chase(a32,a33) 
                 ca33a34 = chase(a33,a34) 
                 ca34a35 = chase(a34,a35) 
                 ca35a36 = chase(a35,a36) 
                 ca36a37 = chase(a36,a37) 
                 ca37a38 = chase(a37,a38) 
                 ca38a39 = chase(a38,a39) 
                 ca39a40 = chase(a39,a40) 
                 ca40a41 = chase(a40,a41) 
                 ca41a42 = chase(a41,a42) 
                 ca42a43 = chase(a42,a43) 
                 ca43a44 = chase(a43,a44) 
                 ca44a45 = chase(a44,a45) 
                 ca45a46 = chase(a45,a46) 
                 ca46a47 = chase(a46,a47) 
                 ca47a48 = chase(a47,a48) 
                 ca48a49 = chase(a48,a49) 
                 ca49a50 = chase(a49,a50) 
                 ca50a51 = chase(a50,a51) 
                 ca51a52 = chase(a51,a52) 
                 ca52a53 = chase(a52,a53) 
                 ca53a54 = chase(a53,a54) 
                 ca54a55 = chase(a54,a55) 
                 ca55a56 = chase(a55,a56) 
                 ca56a57 = chase(a56,a57) 
                 ca57a58 = chase(a57,a58) 
                 ca58a59 = chase(a58,a59) 
                 ca59a60 = chase(a59,a60) 
                 ca60a61 = chase(a60,a61) 
                 ca61a62 = chase(a61,a62) 
                 ca62a63 = chase(a62,a63) 
                 ca63a64 = chase(a63,a64) 
                 ca64a65 = chase(a64,a65) 
                 ca65a66 = chase(a65,a66) 
                 ca66a67 = chase(a66,a67) 
                 ca67a68 = chase(a67,a68) 
                 ca68a69 = chase(a68,a69) 
                 ca69a70 = chase(a69,a70) 
                 ca70a71 = chase(a70,a71) 
                 ca71a72 = chase(a71,a72) 
                 ca72a73 = chase(a72,a73) 
                 ca73a74 = chase(a73,a74) 
                 ca74a75 = chase(a74,a75) 
                 ca75a76 = chase(a75,a76) 
                 ca76a77 = chase(a76,a77) 
                 ca77a78 = chase(a77,a78) 
                 ca78a79 = chase(a78,a79) 
                 ca79a80 = chase(a79,a80) 
                 ca80a81 = chase(a80,a81) 
                 ca81a82 = chase(a81,a82) 
                 ca82a83 = chase(a82,a83) 
                 ca83a84 = chase(a83,a84) 
                 ca84a85 = chase(a84,a85) 
                 ca85a86 = chase(a85,a86) 
                 ca86a87 = chase(a86,a87) 
                 ca87a88 = chase(a87,a88) 
                 ca88a89 = chase(a88,a89) 
                 ca89a90 = chase(a89,a90) 
                 ca90a91 = chase(a90,a91) 
                 ca91a92 = chase(a91,a92) 
                 ca92a93 = chase(a92,a93) 
                 ca93a94 = chase(a93,a94) 
                 ca94a95 = chase(a94,a95) 
                 ca95a96 = chase(a95,a96) 
                 ca96a97 = chase(a96,a97) 
                 ca97a98 = chase(a97,a98) 
                 ca98a99 = chase(a98,a99) 
                 ca99a100 = chase(a99,a100) 
                 ca100a101 = chase(a100,a101) 
                 ca101a102 = chase(a101,a102) 
                 ca102a103 = chase(a102,a103) 
                 ca103a104 = chase(a103,a104) 
                 ca104a105 = chase(a104,a105) 
                 ca105a106 = chase(a105,a106) 
                 ca106a107 = chase(a106,a107) 
                 ca107a108 = chase(a107,a108) 
                 ca108a109 = chase(a108,a109) 
                 ca109a110 = chase(a109,a110) 
                 ca110a111 = chase(a110,a111) 
                 ca111a112 = chase(a111,a112) 
                 ca112a113 = chase(a112,a113) 
                 ca113a114 = chase(a113,a114) 
                 ca114a115 = chase(a114,a115) 
                 ca115a116 = chase(a115,a116) 
                 ca116a117 = chase(a116,a117) 
                 ca117a118 = chase(a117,a118) 
                 ca118a119 = chase(a118,a119) 
                 ca119a120 = chase(a119,a120) 
                 ca120a121 = chase(a120,a121) 
                 ca121a122 = chase(a121,a122) 
                 ca122a123 = chase(a122,a123) 
                 ca123a124 = chase(a123,a124) 
                 ca124a125 = chase(a124,a125) 
                 ca125a126 = chase(a125,a126) 
                 ca126a127 = chase(a126,a127) 
                 ca127a128 = chase(a127,a128) 
                 ca128a129 = chase(a128,a129) 
                 ca129a130 = chase(a129,a130) 
                 ca130a131 = chase(a130,a131) 
                 ca131a132 = chase(a131,a132) 
                 ca132a133 = chase(a132,a133) 
                 ca133a134 = chase(a133,a134) 
                 ca134a135 = chase(a134,a135) 
                 ca135a136 = chase(a135,a136) 
                 ca136a137 = chase(a136,a137) 
                 ca137a138 = chase(a137,a138) 
                 ca138a139 = chase(a138,a139) 
                 ca139a140 = chase(a139,a140) 
                 ca140a141 = chase(a140,a141) 
                 ca141a142 = chase(a141,a142) 
                 ca142a143 = chase(a142,a143) 
                 ca143a144 = chase(a143,a144) 
                 ca144a145 = chase(a144,a145) 
                 ca145a146 = chase(a145,a146) 
                 ca146a147 = chase(a146,a147) 
                 ca147a148 = chase(a147,a148) 
                 ca148a149 = chase(a148,a149) 
                 ca149a150 = chase(a149,a150) 
                 ca150a151 = chase(a150,a151) 
                 ca151a152 = chase(a151,a152) 
                 ca152a153 = chase(a152,a153) 
                 ca153a154 = chase(a153,a154) 
                 ca154a155 = chase(a154,a155) 
                 ca155a156 = chase(a155,a156) 
                 ca156a157 = chase(a156,a157) 
                 ca157a158 = chase(a157,a158) 
                 ca158a159 = chase(a158,a159) 
                 ca159a160 = chase(a159,a160) 
                 ca160a161 = chase(a160,a161) 
                 ca161a162 = chase(a161,a162) 
                 ca162a163 = chase(a162,a163) 
                 ca163a164 = chase(a163,a164) 
                 ca164a165 = chase(a164,a165) 
                 ca165a166 = chase(a165,a166) 
                 ca166a167 = chase(a166,a167) 
                 ca167a168 = chase(a167,a168) 
                 ca168a169 = chase(a168,a169) 
                 ca169a170 = chase(a169,a170) 
                 ca170a171 = chase(a170,a171) 
                 ca171a172 = chase(a171,a172) 
                 ca172a173 = chase(a172,a173) 
                 ca173a174 = chase(a173,a174) 
                 ca174a175 = chase(a174,a175) 
                 ca175a176 = chase(a175,a176) 
                 ca176a177 = chase(a176,a177) 
                 ca177a178 = chase(a177,a178) 
                 ca178a179 = chase(a178,a179) 
                 ca179a180 = chase(a179,a180) 
                 ca180a181 = chase(a180,a181) 
                 ca181a182 = chase(a181,a182) 
                 ca182a183 = chase(a182,a183) 
                 ca183a184 = chase(a183,a184) 
                 ca184a185 = chase(a184,a185) 
                 ca185a186 = chase(a185,a186) 
                 ca186a187 = chase(a186,a187) 
                 ca187a188 = chase(a187,a188) 
                 ca188a189 = chase(a188,a189) 
                 ca189a190 = chase(a189,a190) 
                 ca190a191 = chase(a190,a191) 
                 ca191a192 = chase(a191,a192) 
                 ca192a193 = chase(a192,a193) 
                 ca193a194 = chase(a193,a194) 
                 ca194a195 = chase(a194,a195) 
                 ca195a196 = chase(a195,a196) 
                 ca196a197 = chase(a196,a197) 
                 ca197a198 = chase(a197,a198) 
                 ca198a199 = chase(a198,a199) 
                 ca199a200 = chase(a199,a200) 
                 ca200a201 = chase(a200,a201) 
                 ca201a202 = chase(a201,a202) 
                 ca202a203 = chase(a202,a203) 
                 ca203a204 = chase(a203,a204) 
                 ca204a205 = chase(a204,a205) 
                 ca205a206 = chase(a205,a206) 
                 ca206a207 = chase(a206,a207) 
                 ca207a208 = chase(a207,a208) 
                 ca208a209 = chase(a208,a209) 
                 ca209a210 = chase(a209,a210) 
                 ca210a211 = chase(a210,a211) 
                 ca211a212 = chase(a211,a212) 
                 ca212a213 = chase(a212,a213) 
                 ca213a214 = chase(a213,a214) 
                 ca214a215 = chase(a214,a215) 
                 ca215a216 = chase(a215,a216) 
                 ca216a217 = chase(a216,a217) 
                 ca217a218 = chase(a217,a218) 
                 ca218a219 = chase(a218,a219) 
                 ca219a220 = chase(a219,a220) 
                 ca220a221 = chase(a220,a221) 
                 ca221a222 = chase(a221,a222) 
                 ca222a223 = chase(a222,a223) 
                 ca223a224 = chase(a223,a224) 
                 ca224a225 = chase(a224,a225) 
                 ca225a226 = chase(a225,a226) 
                 ca226a227 = chase(a226,a227) 
                 ca227a228 = chase(a227,a228) 
                 ca228a229 = chase(a228,a229) 
                 ca229a230 = chase(a229,a230) 
                 ca230a231 = chase(a230,a231) 
                 ca231a232 = chase(a231,a232) 
                 ca232a233 = chase(a232,a233) 
                 ca233a234 = chase(a233,a234) 
                 ca234a235 = chase(a234,a235) 
                 ca235a236 = chase(a235,a236) 
                 ca236a237 = chase(a236,a237) 
                 ca237a238 = chase(a237,a238) 
                 ca238a239 = chase(a238,a239) 
                 ca239a240 = chase(a239,a240) 
                 ca240a241 = chase(a240,a241) 
                 ca241a242 = chase(a241,a242) 
                 ca242a243 = chase(a242,a243) 
                 ca243a244 = chase(a243,a244) 
                 ca244a245 = chase(a244,a245) 
                 ca245a246 = chase(a245,a246) 
                 ca246a247 = chase(a246,a247) 
                 ca247a248 = chase(a247,a248) 
                 ca248a249 = chase(a248,a249) 
                 ca249a250 = chase(a249,a250) 
                 ca250a251 = chase(a250,a251) 
                 ca251a252 = chase(a251,a252) 
                 ca252a253 = chase(a252,a253) 
                 ca253a254 = chase(a253,a254) 
                 ca254a255 = chase(a254,a255) 
                 ca255a256 = chase(a255,a256) 
                 ca256a257 = chase(a256,a257) 
                 ca257a258 = chase(a257,a258) 
                 ca258a259 = chase(a258,a259) 
                 ca259a260 = chase(a259,a260) 
                 ca260a261 = chase(a260,a261) 
                 ca261a262 = chase(a261,a262) 
                 ca262a263 = chase(a262,a263) 
                 ca263a264 = chase(a263,a264) 
                 ca264a265 = chase(a264,a265) 
                 ca265a266 = chase(a265,a266) 
                 ca266a267 = chase(a266,a267) 
                 ca267a268 = chase(a267,a268) 
                 ca268a269 = chase(a268,a269) 
                 ca269a270 = chase(a269,a270) 
                 ca270a271 = chase(a270,a271) 
                 ca271a272 = chase(a271,a272) 
                 ca272a273 = chase(a272,a273) 
                 ca273a274 = chase(a273,a274) 
                 ca274a275 = chase(a274,a275) 
                 ca275a276 = chase(a275,a276) 
                 ca276a277 = chase(a276,a277) 
                 ca277a278 = chase(a277,a278) 
                 ca278a279 = chase(a278,a279) 
                 ca279a280 = chase(a279,a280) 
                 ca280a281 = chase(a280,a281) 
                 ca281a282 = chase(a281,a282) 
                 ca282a283 = chase(a282,a283) 
                 ca283a284 = chase(a283,a284) 
                 ca284a285 = chase(a284,a285) 
                 ca285a286 = chase(a285,a286) 
                 ca286a287 = chase(a286,a287) 
                 ca287a288 = chase(a287,a288) 
                 ca288a289 = chase(a288,a289) 
                 ca289a290 = chase(a289,a290) 
                 ca290a291 = chase(a290,a291) 
                 ca291a292 = chase(a291,a292) 
                 ca292a293 = chase(a292,a293) 
                 ca293a294 = chase(a293,a294) 
                 ca294a295 = chase(a294,a295) 
                 ca295a296 = chase(a295,a296) 
                 ca296a297 = chase(a296,a297) 
                 ca297a298 = chase(a297,a298) 
                 ca298a299 = chase(a298,a299) 
                 ca299a300 = chase(a299,a300) 
                 ca300a301 = chase(a300,a301) 
                 ca301a302 = chase(a301,a302) 
                 ca302a303 = chase(a302,a303) 
                 ca303a304 = chase(a303,a304) 
                 ca304a305 = chase(a304,a305) 
                 ca305a306 = chase(a305,a306) 
                 ca306a307 = chase(a306,a307) 
                 ca307a308 = chase(a307,a308) 
                 ca308a309 = chase(a308,a309) 
                 ca309a310 = chase(a309,a310) 
                 ca310a311 = chase(a310,a311) 
                 ca311a312 = chase(a311,a312) 
                 ca312a313 = chase(a312,a313) 
                 ca313a314 = chase(a313,a314) 
                 ca314a315 = chase(a314,a315) 
                 ca315a316 = chase(a315,a316) 
                 ca316a317 = chase(a316,a317) 
                 ca317a318 = chase(a317,a318) 
                 ca318a319 = chase(a318,a319) 
                 ca319a320 = chase(a319,a320) 
                 ca320a321 = chase(a320,a321) 
                 ca321a322 = chase(a321,a322) 
                 ca322a323 = chase(a322,a323) 
                 ca323a324 = chase(a323,a324) 
                 ca324a325 = chase(a324,a325) 
                 ca325a326 = chase(a325,a326) 
                 ca326a327 = chase(a326,a327) 
                 ca327a328 = chase(a327,a328) 
                 ca328a329 = chase(a328,a329) 
                 ca329a330 = chase(a329,a330) 
                 ca330a331 = chase(a330,a331) 
                 ca331a332 = chase(a331,a332) 
                 ca332a333 = chase(a332,a333) 
                 ca333a334 = chase(a333,a334) 
                 ca334a335 = chase(a334,a335) 
                 ca335a336 = chase(a335,a336) 
                 ca336a337 = chase(a336,a337) 
                 ca337a338 = chase(a337,a338) 
                 ca338a339 = chase(a338,a339) 
                 ca339a340 = chase(a339,a340) 
                 ca340a341 = chase(a340,a341) 
                 ca341a342 = chase(a341,a342) 
                 ca342a343 = chase(a342,a343) 
                 ca343a344 = chase(a343,a344) 
                 ca344a345 = chase(a344,a345) 
                 ca345a346 = chase(a345,a346) 
                 ca346a347 = chase(a346,a347) 
                 ca347a348 = chase(a347,a348) 
                 ca348a349 = chase(a348,a349) 
                 ca349a350 = chase(a349,a350) 
                 ca350a351 = chase(a350,a351) 
                 ca351a352 = chase(a351,a352) 
                 ca352a353 = chase(a352,a353) 
                 ca353a354 = chase(a353,a354) 
                 ca354a355 = chase(a354,a355) 
                 ca355a356 = chase(a355,a356) 
                 ca356a357 = chase(a356,a357) 
                 ca357a358 = chase(a357,a358) 
                 ca358a359 = chase(a358,a359) 
                 ca359a360 = chase(a359,a360) 
                 ca360a361 = chase(a360,a361) 
                 ca361a362 = chase(a361,a362) 
                 ca362a363 = chase(a362,a363) 
                 ca363a364 = chase(a363,a364) 
                 ca364a365 = chase(a364,a365) 
                 ca365a366 = chase(a365,a366) 
                 ca366a367 = chase(a366,a367) 
                 ca367a368 = chase(a367,a368) 
                 ca368a369 = chase(a368,a369) 
                 ca369a370 = chase(a369,a370) 
                 ca370a371 = chase(a370,a371) 
                 ca371a372 = chase(a371,a372) 
                 ca372a373 = chase(a372,a373) 
                 ca373a374 = chase(a373,a374) 
                 ca374a375 = chase(a374,a375) 
                 ca375a376 = chase(a375,a376) 
                 ca376a377 = chase(a376,a377) 
                 ca377a378 = chase(a377,a378) 
                 ca378a379 = chase(a378,a379) 
                 ca379a380 = chase(a379,a380) 
                 ca380a381 = chase(a380,a381) 
                 ca381a382 = chase(a381,a382) 
                 ca382a383 = chase(a382,a383) 
                 ca383a384 = chase(a383,a384) 
                 ca384a385 = chase(a384,a385) 
                 ca385a386 = chase(a385,a386) 
                 ca386a387 = chase(a386,a387) 
                 ca387a388 = chase(a387,a388) 
                 ca388a389 = chase(a388,a389) 
                 ca389a390 = chase(a389,a390) 
                 ca390a391 = chase(a390,a391) 
                 ca391a392 = chase(a391,a392) 
                 ca392a393 = chase(a392,a393) 
                 ca393a394 = chase(a393,a394) 
                 ca394a395 = chase(a394,a395) 
                 ca395a396 = chase(a395,a396) 
                 ca396a397 = chase(a396,a397) 
                 ca397a398 = chase(a397,a398) 
                 ca398a399 = chase(a398,a399) 
                 ;

                 ''', metadata={
            'd': {SALIENCE: 1.0},
            'a0': {SALIENCE: 0.023899116621920347},

            'a1': {SALIENCE: 0.7691733973909711},

            'a2': {SALIENCE: 0.27889583184307276},

            'a3': {SALIENCE: 0.626419224683245},

            'a4': {SALIENCE: 0.6179537673495425},

            'a5': {SALIENCE: 0.4869829677425417},

            'a6': {SALIENCE: 0.8702729055591084},

            'a7': {SALIENCE: 0.9074223202629685},

            'a8': {SALIENCE: 0.8253189668215223},

            'a9': {SALIENCE: 0.24518212998180178},

            'a10': {SALIENCE: 0.2516602965688718},

            'a11': {SALIENCE: 0.13970185496533327},

            'a12': {SALIENCE: 0.725862441335661},

            'a13': {SALIENCE: 0.9600144433384424},

            'a14': {SALIENCE: 0.07847416045783495},

            'a15': {SALIENCE: 0.8439080690399352},

            'a16': {SALIENCE: 0.6305809851883728},

            'a17': {SALIENCE: 0.09813205601016362},

            'a18': {SALIENCE: 0.25760300707766715},

            'a19': {SALIENCE: 0.5988609965725218},

            'a20': {SALIENCE: 0.247350041224764},

            'a21': {SALIENCE: 0.812542724208213},

            'a22': {SALIENCE: 0.3666558643334089},

            'a23': {SALIENCE: 0.0425265834616787},

            'a24': {SALIENCE: 0.11790132721657809},

            'a25': {SALIENCE: 0.9645312092680323},

            'a26': {SALIENCE: 0.18391726569142341},

            'a27': {SALIENCE: 0.1166329523697287},

            'a28': {SALIENCE: 0.6531583092843698},

            'a29': {SALIENCE: 0.9411016724517332},

            'a30': {SALIENCE: 0.6210551142569067},

            'a31': {SALIENCE: 0.828821884707351},

            'a32': {SALIENCE: 0.3502491465369264},

            'a33': {SALIENCE: 0.8519470998544527},

            'a34': {SALIENCE: 0.3165351394489162},

            'a35': {SALIENCE: 0.12020580069519116},

            'a36': {SALIENCE: 0.7128815987889874},

            'a37': {SALIENCE: 0.08285067544696889},

            'a38': {SALIENCE: 0.45321451496168563},

            'a39': {SALIENCE: 0.91577443122166},

            'a40': {SALIENCE: 0.10991171173194114},

            'a41': {SALIENCE: 0.9287909989677642},

            'a42': {SALIENCE: 0.9196753113019273},

            'a43': {SALIENCE: 0.22542110576705898},

            'a44': {SALIENCE: 0.022656703103119513},

            'a45': {SALIENCE: 0.7910238854329581},

            'a46': {SALIENCE: 0.43007584670945354},

            'a47': {SALIENCE: 0.6718936007687625},

            'a48': {SALIENCE: 0.6934419984314221},

            'a49': {SALIENCE: 0.23159468990788623},

            'a50': {SALIENCE: 0.10422215028820603},

            'a51': {SALIENCE: 0.5258901016612744},

            'a52': {SALIENCE: 0.5429994656130084},

            'a53': {SALIENCE: 0.28019404973113116},

            'a54': {SALIENCE: 0.21735524381610183},

            'a55': {SALIENCE: 0.2955198400482515},

            'a56': {SALIENCE: 0.024105845094003153},

            'a57': {SALIENCE: 0.38029490443425884},

            'a58': {SALIENCE: 0.9114875029803786},

            'a59': {SALIENCE: 0.9683519993911659},

            'a60': {SALIENCE: 0.27176179024164626},

            'a61': {SALIENCE: 0.5037406017266555},

            'a62': {SALIENCE: 0.4956006457257699},

            'a63': {SALIENCE: 0.40458542664450026},

            'a64': {SALIENCE: 0.7801822415327151},

            'a65': {SALIENCE: 0.5926283989457775},

            'a66': {SALIENCE: 0.15742047595538744},

            'a67': {SALIENCE: 0.17238626510270283},

            'a68': {SALIENCE: 0.19356489088240636},

            'a69': {SALIENCE: 0.30060096198728303},

            'a70': {SALIENCE: 0.09196659301537857},

            'a71': {SALIENCE: 0.8281512465949638},

            'a72': {SALIENCE: 0.942040016693936},

            'a73': {SALIENCE: 0.8396301170607702},

            'a74': {SALIENCE: 0.2856881389839234},

            'a75': {SALIENCE: 0.9420880320116404},

            'a76': {SALIENCE: 0.533874588999786},

            'a77': {SALIENCE: 0.9189502578103731},

            'a78': {SALIENCE: 0.5343032965601336},

            'a79': {SALIENCE: 0.20285432941144665},

            'a80': {SALIENCE: 0.2996730445571617},

            'a81': {SALIENCE: 0.4848419445660469},

            'a82': {SALIENCE: 0.3742940245650421},

            'a83': {SALIENCE: 0.16789774593229934},

            'a84': {SALIENCE: 0.43098529865648116},

            'a85': {SALIENCE: 0.2678553157935447},

            'a86': {SALIENCE: 0.7105196690374539},

            'a87': {SALIENCE: 0.30437564476900303},

            'a88': {SALIENCE: 0.7235341743299419},

            'a89': {SALIENCE: 0.9223710961999433},

            'a90': {SALIENCE: 0.8178646893107065},

            'a91': {SALIENCE: 0.21809906834501114},

            'a92': {SALIENCE: 0.8379022138166569},

            'a93': {SALIENCE: 0.46387720807405386},

            'a94': {SALIENCE: 0.6182901525038814},

            'a95': {SALIENCE: 0.8026026238034288},

            'a96': {SALIENCE: 0.7939641277416787},

            'a97': {SALIENCE: 0.2431015548900055},

            'a98': {SALIENCE: 0.32417326045464967},

            'a99': {SALIENCE: 0.5942213745672907},

            'a100': {SALIENCE: 0.9902251550209438},

            'a101': {SALIENCE: 0.8062868935005185},

            'a102': {SALIENCE: 0.4023977719164358},

            'a103': {SALIENCE: 0.43424018978466883},

            'a104': {SALIENCE: 0.4154391947586207},

            'a105': {SALIENCE: 0.4013743902425284},

            'a106': {SALIENCE: 0.5486294389141465},

            'a107': {SALIENCE: 0.21764575735457925},

            'a108': {SALIENCE: 0.7485748199341732},

            'a109': {SALIENCE: 0.9299924370664523},

            'a110': {SALIENCE: 0.20619840795767885},

            'a111': {SALIENCE: 0.1361333175849404},

            'a112': {SALIENCE: 0.4020369603414712},

            'a113': {SALIENCE: 0.7031801536230186},

            'a114': {SALIENCE: 0.5792840331687722},

            'a115': {SALIENCE: 0.6569272966650261},

            'a116': {SALIENCE: 0.38324390868693314},

            'a117': {SALIENCE: 0.7764633882694655},

            'a118': {SALIENCE: 0.027115284107960713},

            'a119': {SALIENCE: 0.2055424531311314},

            'a120': {SALIENCE: 0.749385445446739},

            'a121': {SALIENCE: 0.3516092525701886},

            'a122': {SALIENCE: 0.25151146112350364},

            'a123': {SALIENCE: 0.3734419819885695},

            'a124': {SALIENCE: 0.4987605157895396},

            'a125': {SALIENCE: 0.485688464757699},

            'a126': {SALIENCE: 0.7129172098148505},

            'a127': {SALIENCE: 0.876666191105639},

            'a128': {SALIENCE: 0.9199038115161805},

            'a129': {SALIENCE: 0.08152612381614976},

            'a130': {SALIENCE: 0.6640087596469675},

            'a131': {SALIENCE: 0.722164271162843},

            'a132': {SALIENCE: 0.13179957787280172},

            'a133': {SALIENCE: 0.006339104492545933},

            'a134': {SALIENCE: 0.8017457003939485},

            'a135': {SALIENCE: 0.503945586180475},

            'a136': {SALIENCE: 0.8971166661738349},

            'a137': {SALIENCE: 0.6009395655185603},

            'a138': {SALIENCE: 0.03697786651289836},

            'a139': {SALIENCE: 0.6604168378249943},

            'a140': {SALIENCE: 0.5768887623076554},

            'a141': {SALIENCE: 0.9643844883441652},

            'a142': {SALIENCE: 0.26365024366281575},

            'a143': {SALIENCE: 0.9142432991402841},

            'a144': {SALIENCE: 0.8571926441039858},

            'a145': {SALIENCE: 0.141951209477443},

            'a146': {SALIENCE: 0.79089451908534},

            'a147': {SALIENCE: 0.3069709333682926},

            'a148': {SALIENCE: 0.13222054860581278},

            'a149': {SALIENCE: 0.29955995817227266},

            'a150': {SALIENCE: 0.34037430852340567},

            'a151': {SALIENCE: 0.5938274899376944},

            'a152': {SALIENCE: 0.9950938723582832},

            'a153': {SALIENCE: 0.7399362102375092},

            'a154': {SALIENCE: 0.31212895703998234},

            'a155': {SALIENCE: 0.5247796772720733},

            'a156': {SALIENCE: 0.7798564205852266},

            'a157': {SALIENCE: 0.2036208721573779},

            'a158': {SALIENCE: 0.7730466311204933},

            'a159': {SALIENCE: 0.6938646011123412},

            'a160': {SALIENCE: 0.02055234023108865},

            'a161': {SALIENCE: 0.026464043377296242},

            'a162': {SALIENCE: 0.35510534194943677},

            'a163': {SALIENCE: 0.8419786015564049},

            'a164': {SALIENCE: 0.7256447086544107},

            'a165': {SALIENCE: 0.10955581621194155},

            'a166': {SALIENCE: 0.9167590635283455},

            'a167': {SALIENCE: 0.05157603453190851},

            'a168': {SALIENCE: 0.28255016275845457},

            'a169': {SALIENCE: 0.12051279625455424},

            'a170': {SALIENCE: 0.26284512144973315},

            'a171': {SALIENCE: 0.04089893748840645},

            'a172': {SALIENCE: 0.8534788565584281},

            'a173': {SALIENCE: 0.7310874842150755},

            'a174': {SALIENCE: 0.7133797653637451},

            'a175': {SALIENCE: 0.38240183840993147},

            'a176': {SALIENCE: 0.9692595640973687},

            'a177': {SALIENCE: 0.004554833463495833},

            'a178': {SALIENCE: 0.2389006661649834},

            'a179': {SALIENCE: 0.6528353698857621},

            'a180': {SALIENCE: 0.6611378585138101},

            'a181': {SALIENCE: 0.5928657778172512},

            'a182': {SALIENCE: 0.40162981969700484},

            'a183': {SALIENCE: 0.2729485784231308},

            'a184': {SALIENCE: 0.05389968304170556},

            'a185': {SALIENCE: 0.9778569855178388},

            'a186': {SALIENCE: 0.3717282561088483},

            'a187': {SALIENCE: 0.733383539688043},

            'a188': {SALIENCE: 0.9493089020673806},

            'a189': {SALIENCE: 0.9522790333082397},

            'a190': {SALIENCE: 0.7777429301829532},

            'a191': {SALIENCE: 0.18813712252732828},

            'a192': {SALIENCE: 0.49638032212860894},

            'a193': {SALIENCE: 0.993252942832144},

            'a194': {SALIENCE: 0.8356957418064092},

            'a195': {SALIENCE: 0.44209501538862683},

            'a196': {SALIENCE: 0.9063552248654322},

            'a197': {SALIENCE: 0.1587268158482853},

            'a198': {SALIENCE: 0.4076693139917148},

            'a199': {SALIENCE: 0.1667768716111362},

            'a200': {SALIENCE: 0.2984906279957923},

            'a201': {SALIENCE: 0.1476833540056457},

            'a202': {SALIENCE: 0.9296660852495305},

            'a203': {SALIENCE: 0.16238802593803092},

            'a204': {SALIENCE: 0.8052243028195811},

            'a205': {SALIENCE: 0.4962896188361413},

            'a206': {SALIENCE: 0.29610336695087014},

            'a207': {SALIENCE: 0.28831238878628074},

            'a208': {SALIENCE: 0.31502451733594283},

            'a209': {SALIENCE: 0.1533412391249328},

            'a210': {SALIENCE: 0.31994970121954647},

            'a211': {SALIENCE: 0.36757011307692145},

            'a212': {SALIENCE: 0.4439441974978803},

            'a213': {SALIENCE: 0.5774697359808512},

            'a214': {SALIENCE: 0.6698934684705146},

            'a215': {SALIENCE: 0.45144618447504414},

            'a216': {SALIENCE: 0.6549509071413091},

            'a217': {SALIENCE: 0.03169555674465008},

            'a218': {SALIENCE: 0.5900731445752193},

            'a219': {SALIENCE: 0.9983856975254257},

            'a220': {SALIENCE: 0.6368115128003085},

            'a221': {SALIENCE: 0.2973990576333527},

            'a222': {SALIENCE: 0.7651832160479834},

            'a223': {SALIENCE: 0.090860283244797},

            'a224': {SALIENCE: 0.9859393701482669},

            'a225': {SALIENCE: 0.04059372713597731},

            'a226': {SALIENCE: 0.7686395049964941},

            'a227': {SALIENCE: 0.35389392549100274},

            'a228': {SALIENCE: 0.7835989437760168},

            'a229': {SALIENCE: 0.49120351181178856},

            'a230': {SALIENCE: 0.8782910572501417},

            'a231': {SALIENCE: 0.13545275438637483},

            'a232': {SALIENCE: 0.5908561693357167},

            'a233': {SALIENCE: 0.5330012954937315},

            'a234': {SALIENCE: 0.8278426540069228},

            'a235': {SALIENCE: 0.22742932341083755},

            'a236': {SALIENCE: 0.33824323195598593},

            'a237': {SALIENCE: 0.7972305500375291},

            'a238': {SALIENCE: 0.8411850743003968},

            'a239': {SALIENCE: 0.6327580568563473},

            'a240': {SALIENCE: 0.6695423574956754},

            'a241': {SALIENCE: 0.5615475161995195},

            'a242': {SALIENCE: 0.435481284146225},

            'a243': {SALIENCE: 0.5085802789401784},

            'a244': {SALIENCE: 0.28530790258659633},

            'a245': {SALIENCE: 0.06305341296662337},

            'a246': {SALIENCE: 0.24009630978898633},

            'a247': {SALIENCE: 0.6192796811346575},

            'a248': {SALIENCE: 0.0027663550945010718},

            'a249': {SALIENCE: 0.5291144696611011},

            'a250': {SALIENCE: 0.7653660010491801},

            'a251': {SALIENCE: 0.38516708488240836},

            'a252': {SALIENCE: 0.09934656987105206},

            'a253': {SALIENCE: 0.6144711418700032},

            'a254': {SALIENCE: 0.38049012320000664},

            'a255': {SALIENCE: 0.29598239325273623},

            'a256': {SALIENCE: 0.4313915201155035},

            'a257': {SALIENCE: 0.025789292836050803},

            'a258': {SALIENCE: 0.8411037805571062},

            'a259': {SALIENCE: 0.06665303916775656},

            'a260': {SALIENCE: 0.7101560112735157},

            'a261': {SALIENCE: 0.9646984300728267},

            'a262': {SALIENCE: 0.28816668692620573},

            'a263': {SALIENCE: 0.11608348217872977},

            'a264': {SALIENCE: 0.8382309140438385},

            'a265': {SALIENCE: 0.4823102901634424},

            'a266': {SALIENCE: 0.9358879215302628},

            'a267': {SALIENCE: 0.2711072738194512},

            'a268': {SALIENCE: 0.7153848937756262},

            'a269': {SALIENCE: 0.6729123583766606},

            'a270': {SALIENCE: 0.8547785122709125},

            'a271': {SALIENCE: 0.48355265070060094},

            'a272': {SALIENCE: 0.23607205267728626},

            'a273': {SALIENCE: 0.47502179498896946},

            'a274': {SALIENCE: 0.7665960054894864},

            'a275': {SALIENCE: 0.2710343371971624},

            'a276': {SALIENCE: 0.6869877744139583},

            'a277': {SALIENCE: 0.7627797719047156},

            'a278': {SALIENCE: 0.5000286626246923},

            'a279': {SALIENCE: 0.6792911118876717},

            'a280': {SALIENCE: 0.46187826802668885},

            'a281': {SALIENCE: 0.4782094102921226},

            'a282': {SALIENCE: 0.26839319856379706},

            'a283': {SALIENCE: 0.94199089396276},

            'a284': {SALIENCE: 0.4923751837484922},

            'a285': {SALIENCE: 0.36128231900246377},

            'a286': {SALIENCE: 0.33075189274322103},

            'a287': {SALIENCE: 0.6686723509505146},

            'a288': {SALIENCE: 0.27324531064768},

            'a289': {SALIENCE: 0.02878955376441583},

            'a290': {SALIENCE: 0.19379471684163552},

            'a291': {SALIENCE: 0.45840335625976536},

            'a292': {SALIENCE: 0.0332171274300066},

            'a293': {SALIENCE: 0.8139125408314154},

            'a294': {SALIENCE: 0.18062901816061327},

            'a295': {SALIENCE: 0.39259581797439724},

            'a296': {SALIENCE: 0.7950873463370141},

            'a297': {SALIENCE: 0.13273332905899493},

            'a298': {SALIENCE: 0.26777417245442714},

            'a299': {SALIENCE: 0.7455155392390896},

            'a300': {SALIENCE: 0.13452241768666662},

            'a301': {SALIENCE: 0.4400565680395313},

            'a302': {SALIENCE: 0.43372065925404835},

            'a303': {SALIENCE: 0.6502710115644037},

            'a304': {SALIENCE: 0.32271882254123896},

            'a305': {SALIENCE: 0.1719982656905482},

            'a306': {SALIENCE: 0.023682623141305537},

            'a307': {SALIENCE: 0.05666129323751301},

            'a308': {SALIENCE: 0.05790817471121312},

            'a309': {SALIENCE: 0.8256883848082425},

            'a310': {SALIENCE: 0.0818051067158887},

            'a311': {SALIENCE: 0.9893626969076641},

            'a312': {SALIENCE: 0.980995680806577},

            'a313': {SALIENCE: 0.1316794307256136},

            'a314': {SALIENCE: 0.8783033264493519},

            'a315': {SALIENCE: 0.3632445750601415},

            'a316': {SALIENCE: 0.33344039227684374},

            'a317': {SALIENCE: 0.8041282922592498},

            'a318': {SALIENCE: 0.10984503705159565},

            'a319': {SALIENCE: 0.8293859656371609},

            'a320': {SALIENCE: 0.11642076378348076},

            'a321': {SALIENCE: 0.201149304124714},

            'a322': {SALIENCE: 0.942269252588011},

            'a323': {SALIENCE: 0.707582712063398},

            'a324': {SALIENCE: 0.5229814715989899},

            'a325': {SALIENCE: 0.5252405217098893},

            'a326': {SALIENCE: 0.2971122479344396},

            'a327': {SALIENCE: 0.8137623339410499},

            'a328': {SALIENCE: 0.26371116808542694},

            'a329': {SALIENCE: 0.4020782234610585},

            'a330': {SALIENCE: 0.4930844476656857},

            'a331': {SALIENCE: 0.07542916142469824},

            'a332': {SALIENCE: 0.8991090556258534},

            'a333': {SALIENCE: 0.37854842587101367},

            'a334': {SALIENCE: 0.14200360520911792},

            'a335': {SALIENCE: 0.46345872362815244},

            'a336': {SALIENCE: 0.9872062544150372},

            'a337': {SALIENCE: 0.15583795179439408},

            'a338': {SALIENCE: 0.231430461350435},

            'a339': {SALIENCE: 0.4943838846737284},

            'a340': {SALIENCE: 0.2553243094879183},

            'a341': {SALIENCE: 0.9950655806221382},

            'a342': {SALIENCE: 0.14395056522281646},

            'a343': {SALIENCE: 0.8434331366591963},

            'a344': {SALIENCE: 0.5257585621551883},

            'a345': {SALIENCE: 0.8746731683739165},

            'a346': {SALIENCE: 0.4879562340762156},

            'a347': {SALIENCE: 0.49133676780452884},

            'a348': {SALIENCE: 0.25617536985032074},

            'a349': {SALIENCE: 0.7183843488612579},

            'a350': {SALIENCE: 0.27414265136031535},

            'a351': {SALIENCE: 0.21537573167674606},

            'a352': {SALIENCE: 0.3627110666792419},

            'a353': {SALIENCE: 0.7752346239075797},

            'a354': {SALIENCE: 0.37944335314115873},

            'a355': {SALIENCE: 0.9848953948010569},

            'a356': {SALIENCE: 0.6522407799143158},

            'a357': {SALIENCE: 0.17344403845137168},

            'a358': {SALIENCE: 0.16350224892567178},

            'a359': {SALIENCE: 0.8517482075732539},

            'a360': {SALIENCE: 0.6260682519974766},

            'a361': {SALIENCE: 0.42440971559378526},

            'a362': {SALIENCE: 0.19594333095591598},

            'a363': {SALIENCE: 0.945406637897845},

            'a364': {SALIENCE: 0.686774754417035},

            'a365': {SALIENCE: 0.5888755488928561},

            'a366': {SALIENCE: 0.9871427832104646},

            'a367': {SALIENCE: 0.558218956796884},

            'a368': {SALIENCE: 0.7038540832882736},

            'a369': {SALIENCE: 0.6972975185417274},

            'a370': {SALIENCE: 0.7123643835371611},

            'a371': {SALIENCE: 0.24008194259089188},

            'a372': {SALIENCE: 0.4260208726721816},

            'a373': {SALIENCE: 0.30049745373153136},

            'a374': {SALIENCE: 0.950690457733595},

            'a375': {SALIENCE: 0.4172581967024245},

            'a376': {SALIENCE: 0.8823042134658584},

            'a377': {SALIENCE: 0.5914379305414266},

            'a378': {SALIENCE: 0.8405526837216588},

            'a379': {SALIENCE: 0.33632988382288986},

            'a380': {SALIENCE: 0.004013215755486077},

            'a381': {SALIENCE: 0.8531669298846265},

            'a382': {SALIENCE: 0.08257348411842602},

            'a383': {SALIENCE: 0.3785772586359142},

            'a384': {SALIENCE: 0.7461535325129273},

            'a385': {SALIENCE: 0.3144940328705822},

            'a386': {SALIENCE: 0.3319945149747212},

            'a387': {SALIENCE: 0.01628201920346295},

            'a388': {SALIENCE: 0.24593132196824818},

            'a389': {SALIENCE: 0.7794306702365773},

            'a390': {SALIENCE: 0.1225452151894082},

            'a391': {SALIENCE: 0.3406972083500205},

            'a392': {SALIENCE: 0.983204906464494},

            'a393': {SALIENCE: 0.7110067975150617},

            'a394': {SALIENCE: 0.7136760479360563},

            'a395': {SALIENCE: 0.7454511707733014},

            'a396': {SALIENCE: 0.6526599840354983},

            'a397': {SALIENCE: 0.9799271565973386},

            'a398': {SALIENCE: 0.6087323894186925},

        })

        # Here's how to access concept salience
        assert wm.features['d'][SALIENCE] == 1.0
        t21 = time.time()
        saliencesnew = update_salience(wm)
        t22 = time.time()
        print("My method: {}".format(t22 - t21))
        #  for concept, salience in saliences.items():
        #   print(concept, ':', salience)
        #for concept, salience in saliences.items():
        #    print(concept, ':', salience)
        '''
        Considerations:
        
        * Salience is supposed to model how an intelligent agent's attention
          shifts between concepts based on their semantic relatedness. There
          may be a few formulas for this; we basically just want the salience
          to "pool" onto concepts that are related to most of the existing 
          mentioned concepts. Feel free to change the salience update formula
          if you feel like the salience should be updated differently to get
          the right behavior.
        
        * Efficiency matters here. We want to update the salience of about
          200-400 concepts in under 0.1s if possible.        
          Best practices for efficient code:
            1) make sure time complexity of your algorithm makes sense
            2) don't bother with ANY micro-optimizations (optimizations
               that fall within the same big-O) until you run a profiler
               (cProfile is really good).
            3) Python is slow, especially when using lots of function calls
               within loops. If you do get to micro-optmizing, and are confident
               your alogrithm doesn't repeat any work, try refactoring to use 
               more built-in functions (e.g. python set operations) or libraries
               implemented in C such as numpy.
        '''

    def test_update_salience2(self):
        wm = ConceptGraph('''

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

        ''', metadata={
            'd': {SALIENCE: 1.0}
        })

        # Here's how to access concept salience
        assert wm.features['d'][SALIENCE] == 1.0

        saliences = update_salience(wm)
        saliences = update_salience(wm)
        for concept, salience in saliences.items():
            print(concept, ':', salience)
        print()
        '''
        Considerations:

        * Salience is supposed to model how an intelligent agent's attention
          shifts between concepts based on their semantic relatedness. There
          may be a few formulas for this; we basically just want the salience
          to "pool" onto concepts that are related to most of the existing 
          mentioned concepts. Feel free to change the salience update formula
          if you feel like the salience should be updated differently to get
          the right behavior.

        * Efficiency matters here. We want to update the salience of about
          200-400 concepts in under 0.1s if possible.        
          Best practices for efficient code:
            1) make sure time complexity of your algorithm makes sense
            2) don't bother with ANY micro-optimizations (optimizations
               that fall within the same big-O) until you run a profiler
               (cProfile is really good).
            3) Python is slow, especially when using lots of function calls
               within loops. If you do get to micro-optmizing, and are confident
               your alogrithm doesn't repeat any work, try refactoring to use 
               more built-in functions (e.g. python set operations) or libraries
               implemented in C such as numpy.
        '''



if __name__ == '__main__':
    unittest.main()


