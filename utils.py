# Returns idx of the value if value in self.nodes
# Or the index of the next element if values not in self.nodes
def binary_search(self, lst, value, selector=lambda x: x):
    l = 0
    r = len(lst) - 1
    while l < r:
        mid_point = int((l + r)/2)
        mid_el = self.nodes[mid_point]
        if value == selector(mid_el):
            return mid_point
        elif value > selector(mid_el):
            l = mid_point + 1
        else:
            r = mid_point - 1
    res_el = self.nodes[r]
    return r if selector(res_el) > value else r + 1
