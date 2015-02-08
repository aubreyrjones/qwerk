import rsa
import aes
import getpass
import hashlib
from base64 import b64encode, b64decode
from pbkdf2 import PBKDF2
import yaml
import os.path
import glob

_qwerkid_file = os.path.expanduser("~/QwerkID")

def read_qwerkid():
    '''
    Read the user's qwerkid.
    '''
    qwerkid = _qwerkid_file
    if not os.path.exists(qwerkid):
        print("No QwerkID file exists. Please create one with `qwerk id new` before continuing with these operations.")
        exit()
    with open(qwerkid, 'r') as qi:
        return yaml.load(qi)

def hash_file(filename):
    '''
    Take a hash of a file's contents.
    '''
    h = hashlib.new("sha1")
    with open(filename, 'r') as f:
        h.update(f.read())
    return h.hexdigest()

def aes_key(password):
    '''
    Get aes key from password.
    '''
    return PBKDF2(password, "salty").read(32)

def encode_privkey(privkey, password):
    '''
    Encode a private key to text.
    '''
    keystring = "CHECK:{0}:{1}:{2}:{3}:{4}".format(privkey.n, privkey.e, privkey.d, privkey.p, privkey.q)
    return b64encode(aes.encryptData(aes_key(password), keystring))

def decode_privkey(text, password):
    '''
    Decode private key from text.
    '''
    keystring = aes.decryptData(aes_key(password), b64decode(text))
    k = keystring.split(":")
    if not k.pop(0) == "CHECK":
        print("Incorrect password to decode private key. Exiting.")
        exit()
    ks = map(long, k)
    return rsa.PrivateKey(ks[0], ks[1], ks[2], ks[3], ks[4])
    
def encode_pubkey(pubkey):
    '''
    Encode a public key to text.
    '''
    return b64encode("{0}:{1}".format(pubkey.n, pubkey.e))

def decode_pubkey(text):
    '''
    Decode a public key from text.
    '''
    k = b64decode(text).split(":")
    ks = map(long, k)
    return rsa.PublicKey(ks[0], ks[1])

def write_identity(privkey, pubkey, first, last, password):
    '''
    Write out the private identity file for a new identity.
    '''
    to_write = {}
    to_write['first_name'] = first
    to_write['last_name'] = last
    to_write['private_key'] = encode_privkey(privkey, password)
    to_write['public_key'] = encode_pubkey(pubkey)
    
    qwerkid = os.path.expanduser("~/.qwerk.user")
    if os.path.exists(qwerkid):
        print(".qwerk.user file already exists in user home directory. Exiting.")
        exit()
    
    with open(qwerkid, 'w') as f:
        yaml.dump(to_write, f)
    
def new_identity():
    '''
    Create a new .qwerk.user file.
    '''
    first = raw_input("Enter first name: ")
    last = raw_input("Enter last name: ")
    first_pass = 'not'
    second_pass = 'the_same'
    while not first_pass == second_pass:
        first_pass = getpass.getpass("Enter key password: ")
        second_pass = getpass.getpass("Re-enter key password: ")
        if not first_pass == second_pass:
            print("Passwords do not match, please try again.")
    
    print("Generating keys. This is in python, so it may take a minute.")
    (pubkey, privkey) = rsa.newkeys(2048)
    write_identity(privkey, pubkey, first, last, first_pass)

def verify_file_signature(filename, b64_sig, pubkey):
    '''
    Verify the signature of a file.
    '''
    with open(filename, 'r') as f:
        try:
            rsa.verify(f, b64decode(b64_sig), pubkey)
            return True
        except:
            return False
    return False

def get_pubkey(reqdir, user_name):
    '''
    Get the public key for the given user.
    '''
    filename = os.path.join(reqdir, ".users", user_name)
    with open(filename, 'r') as f:
        y = yaml.load(f)
        return decode_pubkey(y['public_key'])

def join_project(reqdir):
    '''
    Copy public credentials into the current project.
    '''
    qwerkid = read_qwerkid()
    del qwerkid['private_key'] #sanitize out the private key
    uname = qwerkid['first_name'] + "_" + qwerkid['last_name']
    os.makedirs(os.path.join(reqdir, ".users"))
    pubfile = os.path.join(reqdir, ".users", uname)
    if os.path.exists(pubfile):
        print("You've already joined this project.")
        exit()
    with open(pubfile, 'w') as f:
        yaml.dump(qwerkid, f)

def sig_file_name(reqdir, req_name, sig_type):
    '''
    Get the signature filename for the given requirement name and signature type.
    Also creates the necessary .sig directory in the reqdir.
    '''
    d = os.path.join(reqdir, ".sig")
    os.makedirs(d)
    return os.path.join(d, "{0}_{1}".format(req_name, sig_type))

def check_sig(reqdir, sigfile, reqfile):
    '''
    Check a particular signature file against a particular requirement file.
    '''
    sigy = None
    with open(sigfile, 'r') as f:
        sigy = yaml.load(f)
    username = sigy['user']
    pubkey = get_pubkey(reqdir, username)
    return verify_file_signature(reqfile, sigy['signature'], pubkey)
    
def check_sigs(state, req_name):
    '''
    Check all signatures found for the given requirement name.
    '''
    signatures = glob.glob(os.path.join(state.root, ".sig", req_name + "_*"))
    allPassed = True
    for s in signatures:
        if not check_sig(state.root, s, state.requirements[req_name].file):
            print("Signature failed: " + s)
            allPassed = False
    
    return allPassed
    
    
class Authority(object):
    def __init__(self):
        yml = read_qwerkid()
        self.first_name = yml['first_name']
        self.last_name = yml['last_name']
        try:
            password = getpass.getpass("Enter qwerk key password: ")
            self.private_key = decode_privkey(yml['private_key'], password)
        except ValueError:
            print("Incorrect password to decode private key. Exiting.")
            exit()
        self.public_key = decode_pubkey(yml['public_key'])
    
    def sign_file(self, filename):
        '''
        Sign a file as this authority.
        '''
        with open(filename, 'r') as f:
            return b64encode(rsa.sign(f, self.private_key, 'SHA-1'))
    
    def sign_requirement(self, state, req_name, sign_type):
        '''
        Sign a requirement with the given sign_type, and save the signature
        in the .sigs directory.
        '''
        requirement = state.requirements[req_name]
        filesig = self.sign_file(requirement.file)
        sigfile = sig_file_name(state.root, req_name, sign_type)
        sig = {}
        sig['signature'] = filesig
        sig['user'] = "{0}_{1}".format(self.first_name, self.last_name)
        with open(sigfile, 'w') as f:
            yaml.dump(sig, f)
        
