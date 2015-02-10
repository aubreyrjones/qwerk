
requirement_template = '''
* __{0}__

    {1}
'''

def format_requirement(req):
    #dep_text = ''
    #if req.deps:
    #    dep_text = "\n\n    [{0}]".format(", ".join(req.deps))
    return requirement_template.format(req.name, req.text)

def format_project(state):
    outlines = []
    categories = state.sort_categories(state.categories.keys())
    for c in categories:
        outlines.append(c)
        outlines.append("=" * len(c))
        reqs = sorted(state.categories[c], key=lambda r: state.req_sort_key(r), reverse=True)
        for r in reqs:
            outlines.append(format_requirement(state.requirements[r]))
    return outlines
