import yaml
import collections
import os
import os.path
import pprint
import copy
import glob

class Requirement(object):
    def __init__(self, name, text, category, deps):
        self.name = name
        self.text = text
        self.category = category
        self.deps = deps
        
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

class ProjectState(object):
    '''
    Represents the state of a project, including all discovered requirements
    and the search path for finding undiscovered requirements.
    '''
    def __init__(self):
        self.requirements = {}
        self.categories = {}
        self.path = []
    
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
        req = Requirement(name, text, category, deps)
        self.requirements[name] = req
        if category in self.categories:
            self.categories[category].append(req)
        else:
            self.categories[category] = [req]
        
    def load_directory(self, dirname):
        '''
        Load all .y files in the directory.
        '''
        for f in glob.glob(os.path.join(dirname, "*.y")):
            self.load_requirement(f)
    
    def load_all_from_root(self, root_dirname):
        '''
        Load all of the subdirectories under the given directory.
        '''
        for entry in os.listdir(root_dirname):
            if os.path.isdir(entry):
                self.load_directory(entry)
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
    
    def dotify_project(self):
        '''
        Produce a dot file for the dependency graph of the project.
        '''
        outlines = []
        outlines.append("digraph Dependency {")
        
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