
requirement_template = '''
* __{0}__

    {1}
'''

def format_requirement(req):
    #dep_text = ''
    #if req.deps:
    #    dep_text = "\n\n    [{0}]".format(", ".join(req.deps))
    return requirement_template.format(req.name, req.text)

def category_transient_key(state, category):
    '''
    Get the sum of the transient values for all reqs in the category.
    '''
    return sum(map(lambda r: state.requirements[r].transient, state.categories[category]))

def format_project(state):
    outlines = []
    categories = sorted(state.categories.keys(), key=lambda c: category_transient_key(state, c), reverse=True)
    for c in categories:
        outlines.append(c)
        outlines.append("=" * len(c))
        reqs = sorted(state.categories[c], key=lambda r: state.req_sort_key(r), reverse=True)
        for r in reqs:
            outlines.append(format_requirement(state.requirements[r]))
    return outlines
