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


def test_boolop_and_comprehension_count_as_branches():
    code = "def f(xs):\n    return [x for x in xs if x and x > 0]\n"
    q = analyze_quality(code)
    # one comprehension `if` + one `and` -> base 1 + 2
    assert q.max_function_complexity == 3


def test_syntax_error_scores_zero():
    q = analyze_quality("def f(:\n    pass")
    assert not q.syntax_ok
    assert q.score == 0.0


def test_empty_or_comments_only_scores_zero():
    assert analyze_quality("").score == 0.0
    assert analyze_quality("   \n\n  ").score == 0.0
    assert analyze_quality("# just a comment\n# another\n").score == 0.0


def test_lower_complexity_scores_higher():
    simple = analyze_quality('def f(x):\n    """doc"""\n    return x\n')
    tangled = analyze_quality(
        "def f(x):\n"
        + "".join(f"    if x == {i}:\n        return {i}\n" for i in range(12))
        + "    return -1\n"
    )
    assert simple.score > tangled.score
