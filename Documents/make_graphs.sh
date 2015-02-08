#!/bin/bash

dot -Tsvg qwerk_Requirements_Dependency.dot -o qwerk_Dependency.svg
dot -Tpng qwerk_Requirements_Dependency.dot -o qwerk_Dependency.png

