#!/bin/bash
# job.sh - Script executado em cada job HTCondor

# Ativa o ambiente Conda com ROOT + Garfield++
source /sampa/daniel-magpali/miniconda3/etc/profile.d/conda.sh
conda activate myenv

# Define variáveis de ambiente
ENV_BASE=/sampa/daniel-magpali/miniconda3/envs/myenv

export GARFIELD_HOME=$ENV_BASE/bin/garfieldpp
export ROOTSYS=$ENV_BASE
export PATH=$GARFIELD_HOME/bin:$ENV_BASE/bin:$PATH
export LD_LIBRARY_PATH=$ROOTSYS/lib:$GARFIELD_HOME/lib:$LD_LIBRARY_PATH
export GARFIELD_DIR=$GARFIELD_HOME/install/lib64/cmake/Garfield
export CMAKE_PREFIX_PATH=$GARFIELD_DIR:$CMAKE_PREFIX_PATH
export MAGBOLTZ_DIR=$GARFIELD_HOME/install/lib64/cmake/Magboltz
export CMAKE_PREFIX_PATH=$MAGBOLTZ_DIR:$CMAKE_PREFIX_PATH
export DEGRADE_DIR=$GARFIELD_HOME/install/lib64/cmake/Degrade
export CMAKE_PREFIX_PATH=$DEGRADE_DIR:$CMAKE_PREFIX_PATH

# Verifica se o Python está instalado
if ! command -v python &> /dev/null
then
  echo "Python não encontrado. Instale o Python e tente novamente."
  exit 1
fi

# Executa o script Python
python exec_simu_auto.py

# Verifica o código de saída do script Python
if [ $? -ne 0 ]; then
  echo "Erro ao executar o script Python."
  exit 1
fi

echo "Script Python executado com sucesso."