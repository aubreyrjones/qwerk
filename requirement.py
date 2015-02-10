import yaml
import collections
import os
import os.path
import pprint
import copy
import glob

def new_requirement(state, category, req_name, dependencies):
    '''
    Create a new requirement in the backlog.
    '''
    if req_name in state.requirements.keys():
        print("Cannot create requirement with name {0}, name already defined by: {1}".format(req_name, state.requirements[req_name].file))
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
        f.write("    FILL ME IN\n")

class Requirement(object):
    def __init__(self, name, text, category, deps, filename):
        self.name = name
        self.text = text
        self.category = category
        self.deps = deps
        self.file = filename
        
        self.incoming = []
    
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
        return self.category.endswith("_backlog")
    
    def base_category(self):
        '''
        Get base category without _backlog suffix.
        '''
        if self.is_backlog():
            return self.category[:self.category.find("_backlog")]
        return self.category

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
        
        if self.backlog:
            category = category + '_backlog'
        
        if category not in self.path.keys():
            self.path[category] = os.path.dirname(filename)
        
        text = ''
        deps = []
        if 'text' in yml:
            text = yml['text'].strip().replace("-\n", "").replace("\n", " ")
        if 'deps' in yml:
            deps = yml['deps']
        req = Requirement(name, text, category, deps, filename)
        if name in self.requirements.keys():
            print("Error: Duplicate requirement names.")
            print(req.filename)
            print(self.requirements[name].filename)
            print("Exiting.")
            exit()
        self.requirements[name] = req
        if category in self.categories:
            self.categories[category].append(req.name)
        else:
            self.categories[category] = [req.name]
        
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
            self.requirements[d].incoming.append(key)
                
    def graphify(self):
        '''
        Used after loading to build the dependency graph.
        '''
        req_keys = self.requirements.keys()
        while req_keys:
            self.graph_out_req(req_keys.pop(0))
            
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
    
    def req_sort_key(self, req_key):
        '''
        Used to sort requirements according to number of incoming deps.
        '''
        return self.requirements[req_key].number_of_incoming()
    
    def dotify_category(self, category, outlines):
        outlines.append("subgraph cluster_{0} {{".format(category))
        outlines.append("label = \"{0}\";".format(category))
        outlines.append("color=blue;")
        #outlines.append("node [style=filled];")
    
        quoted = map(lambda x: '"{0}"'.format(x), self.categories[category])
        
        outlines.append(" ".join(quoted) + ";")    
        
        outlines.append("}\n\n")
        
    
    def dotify_project(self):
        '''
        Produce a dot file for the dependency graph of the project.
        '''
        outlines = []
        outlines.append("digraph \"{0} Requirements Dependency\" {{".format(self.name))
        #outlines.append("graph [compound=true];")
        outlines.append("node [shape=record];\n\n")
        
        for cat in self.categories.keys():
            self.dotify_category(cat, outlines)
    
        remaining_keys = sorted(self.requirements.keys(), key=lambda k: self.req_sort_key(k), reverse=True)
        
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
    