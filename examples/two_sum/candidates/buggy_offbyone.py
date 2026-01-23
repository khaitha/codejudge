def two_sum(nums, target):
    """Looks right, but the loop stops one element early (off-by-one), so any
    answer that needs the final index is silently missed."""
    seen = {}
    for index in range(len(nums) - 1):  # BUG: should be range(len(nums))
        value = nums[index]
        complement = target - value
        if complement in seen:
            return [seen[complement], index]
        seen[value] = index
    return []
