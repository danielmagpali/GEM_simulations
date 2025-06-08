import subprocess
import os
import shutil
import yaml
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from utils import salvar_conf_para_garfield,carregar_yaml,renderizar_template_sif
from utils import gerar_malha_gmsh,rodar_elmergrid,rodar_elmersolver,mover_para_build,compilar_garfield

def main():
    # Arquivos fixos
    script_gmsh = "geometria.py"
    arquivo_msh = "gemcell.msh"
    arquivo_sif = "base.sif"
    build_dir = "./build"

    # 1. Carregar parâmetros do YAML
    parametros = carregar_yaml("gem.yaml")

    # 2. Criar o base.sif da simu baseado no template mas com os parametros do gem.yaml
    renderizar_template_sif(parametros, "base.sif.template", "base.sif")

    # 3. Gerar o arquivo gem.conf (para Garfield++)
    salvar_conf_para_garfield(parametros, "gem.conf")

    # 4. Gerar malha GMSH
    gerar_malha_gmsh(script_gmsh)

    # 5. Rodar ElmerGrid
    rodar_elmergrid(arquivo_msh)

    # 6. Rodar ElmerSolver
    rodar_elmersolver(arquivo_sif)

    # 7. Mover arquivos de input no garfield para o build/
    mover_para_build("gemcell", build_dir)
    shutil.copy2("gem.conf", build_dir)
    shutil.copy2("base.sif", build_dir)

    # 8. Compilar e rodar Garfield++
    compilar_garfield(build_dir)

if __name__ == "__main__":
    main()