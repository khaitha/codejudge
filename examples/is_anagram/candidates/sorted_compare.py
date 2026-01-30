def is_anagram(s, t):
    # Correct and concise; O(n log n) from sorting rather than O(n).
    return sorted(s) == sorted(t)
