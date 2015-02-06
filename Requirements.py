import yaml
import collections
import os
import os.path
import pprint
import copy
import glob

Requirement = collections.namedtuple('Requirement', ['name', 'text', 'deps', 'parsed_deps', 'dirname'])

ReqState = collections.namedtuple('ReqState', ['req_dir', 'req_path'])

def find_file_on_path(filename, state):
    pass

def parse_requirement(filename, state):
    '''
    Parse a YAML requirement file.
    '''
    yml = None
    with open(filename, 'r') as f:
        yml = yaml.load(f.read())
    req_name = os.path.basename(filename)[:-2] # without .y
    text = ''
    deps = []
    if 'text' in yml:
        text = yml['text'].strip()
    if 'deps' in yml:
        deps = yml['deps']
    dirname = os.path.dirname(filename)
    req = Requirement(req_name, text, deps, [], dirname)
    state.req_dir[req_name] = req
    return req
    
def recursive_load(req, state):
    '''
    Load the dependencies listed in the given requirement.
    '''
    for d in req.deps:
        if d in state.req_dir:
            req.parsed_deps.append(state.req_dir[d])
        else:
            req.parsed_deps.append(parse_recursive(d + ".y", state))
    
def parse_recursive(filename, state):
    '''
    Recursively parse with the given file as root.
    '''
    root = parse_requirement(filename, state)
    recursive_load(root, state)
    return root

def parse_directory(dirname, state):
    '''
    Parse a directory full of requirements.
    '''
    for f in glob.glob(os.path.join(dirname, "*")):
        parse_recursive(f, state)
    
def dotify_recursive(root, state, outlines):
    '''
    Recursively dotify elements.
    '''
    for d in root.parsed_deps:
        outlines.append("{0} -> {1};".format(d.name, root.name))
        if d.name in state.req_dir:
            dotify_recursive(d, state, outlines)
    if root.name in state.req_dir:
        del state.req_dir[root.name]

def dotify(state):
    '''
    Dotify a complete collection of requirements.
    '''
    state_copy = copy.deepcopy(state)
    outlines = []
    outlines.append("digraph Dependency {")
    while state_copy.req_dir:
        k, v = state_copy.req_dir.popitem()
        dotify_recursive(v, state_copy, outlines)
    outlines.append("}")
    return outlines

def build_requirements_document(req_dir):
    '''
    Build a document out of the list of requirements.
    '''
    pass
    
    
    
    
    
    
    
    
    
    
    