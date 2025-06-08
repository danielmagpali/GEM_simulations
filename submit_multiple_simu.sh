#!/bin/bash

BASE_DIR=${1:-simulacoes}

for pasta in "$BASE_DIR"/*; do
    if [ -f "$pasta/job.sub" ]; then
        echo "Submetendo: $pasta/job.sub"
        condor_submit "$pasta/job.sub"
    fi
done

#tem que passar o caminho da pasta na hora de executar ele - não esquecer!!