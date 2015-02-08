qwerk
=====

qwerk is a tool for organizing, documenting, and tracking accountability for software requirements.The name means nothing, it's just easy to type.

qwerk works together with version control software to track software requirements from submission through implementation and verification. It is not a task-tracking tool or really a project planning tool, although it does produce requirements dependency diagrams. Instead, it is designed to reduce the administrative burden of managing requirements in regulated fields.

qwerk does this by allowing programmers to document and manage requirements using programmer-friendly tools, directly within the project hierarchy. Project contributors and leads can easily sign off on implementation and review of individual requirements, with an audit trail provided by cryptographic signatures and your existing version control. qwerk is designed to have minimal features, minimal configuration, and minimal impact on existing good practices workflows.

Features
--------

* manages requirements as trivial YAML files, on-disk, in project.
* provides cryptographic audit trail for requirements life cycle (when used with version control).
* synthesizes unified requirements document (in Markdown for now).
* synthesizes requirement dependency graph in dot format for use in GraphViz.

Manual
======

qwerk represents requirements as individual YAML files stored in the target project's version control repository. Each file defines a single requirement, with a name determined by removing the `.y` suffix from the requirement file: for example, `client_executable.y` defines a requirement called `client_executable`.

Each requirement file contains a YAML list (called `deps`) of each requirement on which this one depends, and a requirement description (called `text`) that describes the requirement in as much detail as process dictates. Requirement dependencies are listed only by name, not by filename.

Requirements are organized into categories. Each category is represented by a single directory under the main requirements directory in the project. So, if the main requirements directory is `qwerk/requirements` then all requirements in the Core category are stored in `qwerk/requirements/Core`.

One special requirements directory is called `backlog`. Within this directory, you should create additional category directories representing requirements that have been accepted for implementation but have not yet been completed and reviewed. If requirements accountability is being used, requirements should start in the backlog and be moved to an appropriate category directory only by the `qwerk sign reviewed` command.

Two additional directories are created in the requirements directory if the requirements tracking features are used:

* `.users` - holds YAML files, one for each qwerk user in this project. The user files contain user's names and public RSA keys.

* `.sig` - holds signature files. Each signature file represents a person signing off on a particular life cycle stage for a particular requirement. Each signature file is named after a particular requirement name, suffixed with `_$lifecycle` where $lifcycle is a requirement life cycle tag name.

qwerk signature files are also YAML files, containing the name of the file in `.users` with the signing key, and the RSA-signed SHA-1 hash of the corresponding requirements file.

For qwerk requirement accountability to work, you **must** check both the `.users` and `.sig` directories and all of their contents into version control. While the directories are prefixed with `.` for convenience on UNIX-like systems, these directories are **mandatory** for the proper functioning of the accountability and tracking system. However, they're not necessary if qwerk is being used only for report and document generation.


Requirement Life Cycle
----------------------

When using qwerk requirement tracking and accountability, the life cycle of a requirement generally goes as follows:

0. A requirement is formulated and written up in qwerk .y format.
0. The requirement is saved with a unique, meaningful name in an appropriate category directory under `backlog`.
0. A team contributor implements the requirement.
0. The contributor runs the `qwerk sign completed` command on the finished requirement.
0. The contributor checks the resulting signature file into the project's version control system.
0. A project lead reviews the contributor's work.
0. The lead runs the `qwerk sign reviewed` command, and the requirement file is automatically moved from the `backlog` hierarchy to the corresponding main category directory.
0. The lead checks the resulting signature file and requirement file rename into the project's version control system.

Qwerkfile
---------

At the root of your project, you should create (and check in) a file called `Qwerkfile`. This is a YAML file defining project-level information. When invoked, qwerk recursively searches parent directories looking for a Qwerkfile. If it finds one, its contents are used to find the project requirements information. An error is printed and qwerk exits if there is no Qwerkfile found in any parent directory during operations that require a project.

The easiest way to make a Qwerkfile is with the `qwerk init` command.

The Qwerkfile must define the following keys:

* project_name - a short name for the project; must be valid in a filename.
* req_dir - the root directory containing the requirements category directories, backlog directory, and accountability directory (if used).
* output_dir - the directory in which synthesized documents should be written.


Commands
--------

Additional help can be gotten with the `--help` argument to qwerk, as well as `qwerk $command --help` for help on specific commands (note that the command is the word directly after `qwerk`).

* `qwerk id new` - create a new QwerkID file in your home directory. This file will identify you and permit you to sign requirements. Do *not* share this file, but do copy it between different work machines you use. Do *not* forget your password! It may be best to make it long (like a sentence), and write it down somewhere safe.

* `qwerk init $project_name $requirements_directory $output_directory` - creates a new Qwerkfile and basic requirements directory structure based on the arguments given on the commandline.

* `qwerk id join` - when run from within a qwerk project directory, adds your name and public key to the project as a signer.

* `qwerk doc` - generate project requirements documents and graphs. Takes an optional `-t` argument with the type of document to create. By default, creates all available documents.

* `qwerk sign {completed|reviewed} $requirement_name` - used to sign requirements. The `completed` subcommand indicates that a requirement has been implemented and is ready for review. The `reviewed` subcommand indicates that a requirement's implementation has been reviewed; additionally, using this subcommand will automatically move requirements from the backlog to the appropriate main category directory.

* `qwerk checksig $requirements` - check all signatures for the given requirements, making sure that they are valid. If no requirements are given, the signatures are checked on all requirements in the project. It is not an error for a requirement to lack signatures. This command checks the validity of signatures that *do* exist.
