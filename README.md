qwerk
=====

qwerk is a tool for organizing, documenting, and tracking accountability for software requirements.The name means nothing, it's just easy to type.

qwerk works together with version control software to track software requirements from submission through implementation and verification. It is not a task-tracking tool or really a project planning tool, although it does produce requirements dependency diagrams. Instead, it is designed to reduce the administrative burden of managing requirements in regulated fields.

qwerk does this by allowing programmers to document and manage requirements using programmer-friendly tools, directly within the project hierarchy. Project contributors and leads can easily sign off on implementation and review of individual requirements, with an audit trail provided by cryptographic hashes and your existing version control. qwerk is designed to have minimal features, minimal configuration, and minimal impact on existing good practices workflows.

Features
--------

* manages requirements as trivial YAML files, on-disk, in project.
* provides audit trail for requirements life cycle (when used with version control).
* synthesizes unified requirements document (in Markdown for now).
* synthesizes requirement dependency graph in dot format for use in GraphViz.

Manual
======

qwerk represents requirements as individual YAML files stored in the target project's version control repository. Each file defines a single requirement, with a name determined by removing the `.y` suffix from the requirement file: for example, `client_executable.y` defines a requirement called `client_executable`.

Each requirement file contains a YAML list (called `deps`) of each requirement on which this one depends, and a requirement description (called `text`) that describes the requirement in as much detail as process dictates. Requirement dependencies are listed only by name, not by filename.

Requirements are organized into categories. Each category is represented by a single directory under the main requirements directory in the project. So, if the main requirements directory is `qwerk/requirements` then all requirements in the Core category are stored in `qwerk/requirements/Core`.

One special requirements directory is called `backlog`. This directory is for storing requirements that have not yet been implemented in the project. If requirements accountability is being used, requirements must start in the backlog and be moved to an appropriate category directory only by the `qwerk reviewed` command.

Qwerkfile
---------

At the root of your project, you should create (and check in) a file called `Qwerkfile`. This is a YAML file defining project-level information. When invoked, qwerk recursively searches parent directories looking for a Qwerkfile. If it finds one, its contents are used to find the project requirements information. An error is printed and qwerk exits if there is no Qwerkfile found in any parent directory.

Qwerkfile must define the following keys:

* project_name - a short name for the project; must be valid in a filename.
* req_dir - the root directory containing the requirements category directories, backlog directory, and accountability directory (if used).
* output_dir - the directory in which synthesized documents should be written.
