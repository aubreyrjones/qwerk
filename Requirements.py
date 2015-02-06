import yaml
import collections
import os
import os.path
import pprint
import copy


Requirement = collections.namedtuple('Requirement', ['name', 'text', 'deps', 'parsed_deps'])

def parse_requirement(filename, req_dir):
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
    req = Requirement(req_name, text, deps, [])
    req_dir[req_name] = req
    return req
    
def recursive_load(req, req_dir):
    '''
    Load the dependencies listed in the given requirement.
    '''
    for d in req.deps:
        if d in req_dir:
            req.parsed_deps.append(req_dir[d])
        else:
            req.parsed_deps.append(parse_recursive(d + ".y", req_dir))
    
def parse_recursive(filename, req_dir):
    '''
    Recursively parse with the given file as root.
    '''
    root = parse_requirement(filename, req_dir)
    recursive_load(root, req_dir)
    return root

def dotify_recursive(root, req_dir, outlines):
    '''
    Recursively dotify elements.
    '''
    for d in root.parsed_deps:
        outlines.append("{0} -> {1};".format(d.name, root.name))
        if d.name in req_dir:
            dotify_recursive(d, req_dir, outlines)
    if root.name in req_dir:
        del req_dir[root.name]

def dotify(req_dir):
    '''
    Dotify a complete collection of requirements.
    '''
    dir_copy = copy.deepcopy(req_dir)
    outlines = []
    outlines.append("digraph Dependency {")
    while dir_copy:
        k, v = dir_copy.popitem()
        dotify_recursive(v, dir_copy, outlines)
    outlines.append("}")
    return outlines

def build_requirements_document(req_dir):
    '''
    Build a document out of the list of requirements.
    '''
    pass
    
    
    
    
    
    
    
    
    
    
    