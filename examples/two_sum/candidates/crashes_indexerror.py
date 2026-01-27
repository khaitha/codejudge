def two_sum(nums, target):
    # Broken: wrong logic AND walks off the end of the list -> IndexError.
    for i in range(len(nums) + 1):
        if nums[i] == target:
            return [i]
    return []
