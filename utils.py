# Returns idx of the value if value in self.nodes
# Or the index of the next element if values not in self.nodes
def binary_search(lst, value, selector=lambda x: x):
    l = 0
    r = len(lst) - 1
    while l < r:
        mid_point = int((l + r)/2)
        mid_el = lst[mid_point]
        if value == selector(mid_el):
            return mid_point
        elif value > selector(mid_el):
            l = mid_point + 1
        else:
            r = mid_point - 1
    res_el = lst[r]
    return r if selector(res_el) > value else r + 1
