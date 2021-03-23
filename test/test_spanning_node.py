from GRIDD.data_structures.spanning_node import SpanningNode

def test_equal():
    a = SpanningNode('a')
    b = SpanningNode('b')
    c = SpanningNode('c')
    d = SpanningNode('d')
    e = SpanningNode('e')
    f = SpanningNode('f')
    g = SpanningNode('g')
    a.children['1'] = [b]
    b.children['2'] = [d,e,c]
    c.children['3'] = [f]
    e.children['4'] = [f]
    g.children['5'] = [f]

    aa = SpanningNode('a')
    bb = SpanningNode('b')
    cc = SpanningNode('c')
    dd = SpanningNode('d')
    ee = SpanningNode('e')
    ff = SpanningNode('f')
    gg = SpanningNode('g')
    aa.children['1'] = [bb]
    bb.children['2'] = [dd,ee,cc]
    cc.children['3'] = [ff]
    ee.children['4'] = [ff]
    gg.children['5'] = [ff]

    assert f.equal(ff)
    assert e.equal(ee)
    assert d.equal(dd)
    assert c.equal(cc)
    assert b.equal(bb)
    assert a.equal(aa)

    assert ff.equal(f)
    assert ee.equal(e)
    assert dd.equal(d)
    assert cc.equal(c)
    assert bb.equal(b)
    assert aa.equal(a)

    aaa = SpanningNode('a')
    bbb = SpanningNode('b')
    ccc = SpanningNode('c')
    ddd = SpanningNode('d')
    eee = SpanningNode('e')
    fff = SpanningNode('f')
    ggg = SpanningNode('g')
    aaa.children['1'] = [bbb]
    bbb.children['2'] = [ddd,eee,ccc]
    ccc.children['3'] = [fff,ddd]
    eee.children['4'] = [fff]
    ggg.children['5'] = [fff,fff]

    assert fff.equal(f)
    assert eee.equal(e)
    assert ddd.equal(d)
    assert not ccc.equal(c)
    assert not bbb.equal(b)
    assert not aaa.equal(a)
    assert not ggg.equal(g)
