from codejudge.scorer import analyze_quality


def test_simple_function_is_low_complexity_and_high_score():
    code = 'def f(x):\n    """Add one."""\n    return x + 1\n'
    q = analyze_quality(code)
    assert q.syntax_ok
    assert q.has_docstring
    assert q.max_function_complexity == 1
    assert q.score > 0.8


def test_branches_increase_complexity():
    code = (
        "def f(x):\n"
        "    if x > 0:\n"
        "        for i in range(x):\n"
        "            if i % 2:\n"
        "                pass\n"
        "    return x\n"
    )
    q = analyze_quality(code)
    # if + for + if  ->  base 1 + 3 branches
    assert q.max_function_complexity == 4
    assert not q.has_docstring


