import yaml
import collections
import os
import os.path
import pprint
import copy
import glob
import textwrap
import tracking

_req_text_wrapper = textwrap.TextWrapper(width = 80, replace_whitespace = True, initial_indent = '    ', subsequent_indent = '    ', break_long_words = False)

def new_requirement(state, category, req_name, dependencies, text=None):
    '''
    Create a new requirement in the backlog.
    '''
    if req_name in state.requirements.keys():
        print("Cannot create requirement with name {0}, name already defined by: {1}".format(req_name, state.requirements[req_name].file))
        print("Exiting.")
        exit()
    for d in dependencies:
        if d not in state.requirements.keys():
            print("Undefined dependency: {0}\nExiting.".format(d))
            exit()
    if not category[0].isupper():
        print("Category name should begin with an uppercase letter. Exiting.")
        exit()
    cat_dir = os.path.join(state.root, "backlog", category)
    if not os.path.exists(cat_dir):
        os.makedirs(cat_dir)
    newfile_name =  os.path.join(cat_dir, "{0}.y".format(req_name))
    with open(newfile_name, 'w') as f:
        if dependencies:
            f.write("deps:")
            f.write("\n    - ")
            f.write("\n    - ".join(dependencies))
            f.write("\n")
        f.write("text: |\n")
        if not text:
            f.write("    FILL ME IN\n")
        else:
            f.write(_req_text_wrapper.fill(text))
            f.write("\n")

class Requirement(object):
    def __init__(self, name, text, category, deps, filename, backlog):
        self.name = name
        self.text = text
        self._category = category
        self.backlog = backlog
        self.deps = deps
        self.file = filename
        
        self.incoming = []
        self.transient = 0
    
    def get_category(self):
        return self._category
    
    category = property(get_category)
        
    def number_of_incoming(self):
        '''
        Get the number of incoming links.
        '''
        return len(self.incoming)
    
    def __str__(self):
        return "Req|{0}/{1}".format(self.category, self.name)
        
    def __repr__(self):
        return self.__str__()
        
    def is_backlog(self):
        '''
        Is this a backlog requirement?
        '''
        return self.backlog
    
    def base_category(self):
        '''
        Get base category without _backlog suffix.
        '''
        return self._category
        
    def increment_transient(self, state):
        '''
        Increment our own transient count, and recursively
        increment our dependencies.
        '''
        self.transient += 1
        for d in self.deps:
            state.requirements[d].increment_transient(state)


def node_color(state, req):
    '''
    Color of the node in a graphical view.
    '''
    if tracking.is_completed(req, state) and tracking.is_reviewed(req, state):
        return '8DFFD2';
    elif tracking.is_completed(req, state):
        return 'FCFF8D';
    elif req.backlog:
        return 'FF8D8D'
    return 'FFFFFF'
            
class ProjectState(object):
    '''
    Represents the state of a project, including all discovered requirements
    and the search path for finding undiscovered requirements.
    '''
    def __init__(self, name, backlog=False):
        self.name = name
        self.requirements = {}
        self.categories = {}
        self.path = {}
        self.backlog = backlog
        self.root = ""
    
    def add_to_path(self, dirname):
        '''
        Add a new directory fully of requirements to the path. This
        will automatically scan in all requirements (*.y files) found.
        '''
        path.append(dirname)
        load_directory(dirname)
    
    def load_requirement(self, filename):
        '''
        Load a single requirement file.
        '''
        yml = None
        with open(filename, 'r') as f:
            yml = yaml.load(f.read())
        if not yml:
            return #throw exception
        
        name = os.path.basename(filename)[:-2]
        category = os.path.split(os.path.dirname(filename))[1]
        
        text = ''
        deps = []
        if 'text' in yml:
            text = yml['text'].strip().replace("-\n", "").replace("\n", " ")
        if 'deps' in yml:
            deps = yml['deps']
        req = Requirement(name, text, category, deps, filename, self.backlog)
        if name in self.requirements.keys():
            print("Error: Duplicate requirement names.")
            print(req.filename)
            print(self.requirements[name].filename)
            print("Exiting.")
            exit()
        self.requirements[name] = req
        if req.category in self.categories:
            self.categories[req.category].append(req.name)
        else:
            self.categories[req.category] = [req.name]
        
    def load_directory(self, dirname):
        '''
        Load all .y files in the directory.
        '''
        for f in glob.glob(os.path.join(dirname, "*.y")):
            self.load_requirement(f)
    
    def load_all_from_root(self, root_dirname, graphify=True):
        '''
        Load all of the subdirectories under the given directory.
        '''
        self.root = root_dirname
        for entry in os.listdir(root_dirname):
            f = os.path.join(root_dirname, entry)
            if os.path.isdir(f):
                dname = os.path.split(f)[1]
                if dname.startswith('.'):
                    continue
                elif dname == 'backlog':
                    backlog_state = ProjectState(self.name, True)
                    backlog_state.load_all_from_root(f, False)
                    self.merge_from(backlog_state)
                else:
                    self.load_directory(f)
        if graphify:
            self.graphify()

    def graph_out_req(self, key):
        '''
        Graphify a single requirement.
        '''
        req = self.requirements[key]
        for d in req.deps:
            if d not in self.requirements.keys():
                print("Requirement {0} depends on `{1}`, which is not defined in this project.".format(key, d))
                exit()
            self.requirements[d].incoming.append(key)
        req.increment_transient(self)
                
    def graphify(self):
        '''
        Used after loading to build the dependency graph.
        '''
        req_keys = self.requirements.keys()
        while req_keys:
            self.graph_out_req(req_keys.pop(0))
            
    
    def req_sort_key(self, req_key):
        '''
        Used to sort requirements according to transient number.
        '''
        return self.requirements[req_key].transient
    
    def category_transient_key(self, category):
        '''
        Get the sum of the transient values for all reqs in the category.
        '''
        return sum(map(lambda r: self.requirements[r].transient, self.categories[category]))

    
    def sort_requirement_keys(self, req_keys, high_to_low=True):
        '''
        Sort a list of requirement keys by their transient number.
        '''
        return sorted(req_keys, key=lambda k: self.req_sort_key(k), reverse=high_to_low)
    
    def sort_categories(self, cat_keys, high_to_low=True):
        '''
        Sort categories according to sum transient number
        '''
        return sorted(cat_keys, key=lambda c: self.category_transient_key(c), reverse=high_to_low)
    
    def dotify(self, req_name, outlines, remaining_keys):
        '''
        Write out the dot graph description for the node
        and its dependencies.
        '''
        if req_name not in remaining_keys:
            print "\n".join(outlines)
            print remaining_keys
            print req_name
            exit()
        remaining_keys.remove(req_name)
        
        req = self.requirements[req_name]
        
        for d in req.incoming:
            outlines.append("{0} -> {1};".format(req.name, d))
            if d in remaining_keys:
                self.dotify(d, outlines, remaining_keys)
    
    
    def dotify_category(self, category, outlines):
        outlines.append("subgraph \"cluster_{0}\" {{".format(category))
        outlines.append("label = \"{0}\";".format(category))
        outlines.append("color=blue;")
    
        #quoted = map(lambda x: '"{0}"'.format(x), self.categories[category])
        #
        #outlines.append(" ".join(quoted) + ";")
        
        for r in self.sort_requirement_keys(self.categories[category]):
            req = self.requirements[r]
            outlines.append("node [style=filled, fillcolor=\"#{1}\"] {0};".format(req.name, node_color(self, req)))
        
        outlines.append("}\n\n")
        
    
    def dotify_project(self):
        '''
        Produce a dot file for the dependency graph of the project.
        '''
        outlines = []
        outlines.append("digraph \"{0} Requirements Dependency\" {{".format(self.name))
        #outlines.append("graph [compound=true];")
        outlines.append("node [shape=record, style=filled];\n\n")
        
        for cat in self.categories.keys():
            self.dotify_category(cat, outlines)
    
        remaining_keys = self.sort_requirement_keys(self.requirements.keys())
        
        while remaining_keys:
            self.dotify(remaining_keys[0], outlines, remaining_keys)
        
        outlines.append("}\n\n")
        return outlines
        
    def dump_reqs(self):
        '''
        Dump the currently loaded requirements.
        '''
        pprint.pprint(sorted(self.requirements.values(), reverse=True, key=lambda r: r.number_of_incoming()))
        
    def merge_from(self, other):
        '''
        Merge all requirements entries from the other into this one.
        '''
        for p in other.path.keys():
            if p not in self.path.keys():
                self.path[p] = other.path[p] 
        
        for r in other.requirements.keys():
            if r in self.requirements.keys():
                print("Duplicate requirement: " + r)
                exit()
            self.requirements[r] = other.requirements[r]
            
        for c in other.categories.keys():
            if c not in self.categories.keys():
                self.categories[c] = []
            for cr in other.categories[c]:
                if cr not in self.categories[c]:
                    self.categories[c].append(cr)
        pass
    