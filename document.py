
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
    for c in state.categories.keys():
        outlines.append(c)
        outlines.append("=" * len(c))
        for r in state.categories[c]:
            outlines.append(format_requirement(state.requirements[r]))
    return outlines
