def two_sum(nums, target):
    # Correct but O(n^2): check every pair. Fine for tiny inputs, slow at scale.
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []
