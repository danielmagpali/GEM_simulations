import yaml
import os
import subprocess
import shutil
from jinja2 import Environment, FileSystemLoader

#Converte um dicionário de parâmetros (como o carregado do gem.yaml para o formato gem.conf usado no Garfield++.
def salvar_conf_para_garfield(parametros, caminho):
    with open(caminho, "w") as f:
        for chave, valor in parametros.items():
            f.write(f"{chave}={valor}\n")

#cria um novo arquivo yaml para cada simulação de novo parâmetro alterado
#converte um dicionario python em um arquivo yaml
def salvar_yaml(parametros, caminho):
    with open(caminho, 'w') as f:
        yaml.dump(parametros, f) #dump converte o dicionario python para yaml 

#cria cada job.sub de cada simu no seu respectivo diretorio para ser executado dentro dele
def criar_job_sub(pasta_simulacao):
    caminho_absoluto = os.path.abspath(pasta_simulacao)
    conteudo = f"""
initialdir = {caminho_absoluto}
universe    = vanilla
getenv      = True
executable  = job.sh

transfer_input_files = geometria.py, libgeo.py, exec_simu_auto.py, IonMobility_Ar+_Ar.txt, dielectrics.dat, gem.yaml, gem.conf, CMakeLists.txt, gem3D.C

log         = job.log
output      = job.out
error       = job.err

notification = Never

should_transfer_files = YES
when_to_transfer_output = ON_EXIT
transfer_output_files = build

queue
"""
    with open(os.path.join(pasta_simulacao, "job.sub"), "w") as f:
        f.write(conteudo)

##------------------------------------------------------------------------------##

#roda um comando no terminal e verifica se foi bem-sucedido
def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, check=True, cwd=cwd)
        print(f"Comando executado com sucesso: {command}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar o comando: {e}")
        raise

#executa o arquivo do gmsh que gera a malha 
def gerar_malha_gmsh(script_gmsh):
    command = f"python3 {script_gmsh}"
    run_command(command)

#Executa o comando ElmerGrid no terminal e gera os arquivos necessários
def rodar_elmergrid(arquivo_msh):
    command = f"ElmerGrid 14 2 {arquivo_msh} -autoclean"
    run_command(command)

#Executa o comando ElmerSolver no terminal gerando o .result
def rodar_elmersolver(arquivo_sif):
    command = f"ElmerSolver {arquivo_sif}"
    run_command(command)

#Cria uma pasta build e executa tudo lá dentro
def mover_para_build(pasta_origem, pasta_destino):
    # Verifica se o diretório destino 'build' existe. Se não existir, cria.
    if not os.path.exists(pasta_destino):  
        os.makedirs(pasta_destino) 

    # Para cada item na pasta de origem (gemcell), move ou copia para o destino
    for item in os.listdir(pasta_origem): 
        origem_item = os.path.join(pasta_origem, item)  # Cria o caminho completo para o item
        destino_item = os.path.join(pasta_destino, item)  # Cria o caminho completo para o destino
        
        if os.path.isdir(origem_item):  # Verifica se o item é um diretório
            shutil.copytree(origem_item, destino_item)  # Se for diretório, copia recursivamente
        else:
            shutil.copy2(origem_item, destino_item)  # Se for arquivo, copia preservando metadados

    # Adicional: copiar arquivos fixos também
    shutil.copy2("IonMobility_Ar+_Ar.txt", pasta_destino)
    shutil.copy2("dielectrics.dat", pasta_destino)

    print(f"Pasta {pasta_origem} movida para {pasta_destino}, e arquivos fixos copiados.")

#Executa os comandos no terminal necessários para executar o Garfield
def compilar_garfield(diretorio_build):
    print("Rodando comandos para compilar Garfield++")
    run_command("cmake ..", cwd=diretorio_build)
    run_command("make", cwd=diretorio_build)
    run_command("./gem3D", cwd=diretorio_build)

#carrega e le o arquivo yaml e o converte em um dicionario
def carregar_yaml(caminho_yaml):
    with open(caminho_yaml, "r") as f:
        return yaml.safe_load(f)

# Renderiza o base.sif a partir do template e salva no destino   
def renderizar_template_sif(parametros, template_path, destino):

    env = Environment(loader=FileSystemLoader(searchpath=os.path.dirname(template_path)))
    template = env.get_template(os.path.basename(template_path))

    texto_renderizado = template.render(parametros)

    with open(destino, 'w') as f:
        f.write(texto_renderizado)