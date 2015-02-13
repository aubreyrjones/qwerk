import textwrap
import tracking

_req_text_wrapper = textwrap.TextWrapper(width = 80, replace_whitespace = True, initial_indent = '    ', subsequent_indent = '    ', break_long_words = False)

signoff_template = "    * {0} {1} [{2}]\n"

requirement_template = '''
* __{0}__

{2}
{1}
'''

def format_requirement(state, req):
    signoffs = []
    for s in sorted(tracking.get_signoffs(state, req.name), key=lambda k: k[2]):
        signoffs.append(signoff_template.format(*s))
    return requirement_template.format(req.name, "".join(signoffs), _req_text_wrapper.fill(req.text))

def format_project(state):
    outlines = []
    categories = state.sort_categories(state.categories.keys())
    for c in categories:
        outlines.append(c)
        outlines.append("=" * len(c))
        reqs = sorted(state.categories[c], key=lambda r: state.req_sort_key(r), reverse=True)
        for r in reqs:
            outlines.append(format_requirement(state, state.requirements[r]))
    return outlines
