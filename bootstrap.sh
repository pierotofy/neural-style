#!/bin/bash

# Install neural style and dependencies on a paperspace ML-box
git clone https://github.com/pierotofy/neural-style
cd neural-style
luarocks install loadcaffe
./models/download_models.sh
