def two_sum(nums, target):
    """Return the indices of the two values summing to ``target`` in O(n).

    Walk once, remembering each value's index; for every element check whether
    its complement has already been seen.
    """
    seen = {}
    for index, value in enumerate(nums):
        complement = target - value
        if complement in seen:
            return [seen[complement], index]
        seen[value] = index
    return []
