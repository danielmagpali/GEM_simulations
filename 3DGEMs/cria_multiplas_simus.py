import os
import shutil
import yaml
import argparse
from utils import salvar_conf_para_garfield, salvar_yaml, criar_job_sub

# Lista de arquivos fixos para cada simulação
ARQUIVOS_COMUNS = [
    "geometria.py", "libgeo.py", "exec_simu_auto.py", "utils.py", "CMakeLists.txt", "gem3D.C",
    "base.sif.template", "IonMobility_Ar+_Ar.txt", "dielectrics.dat", "job.sh"
]

# Pasta base onde os diretórios de simulação serão criados
PASTA_BASE = "simulacoes"

# Nome do arquivo YAML base com os parâmetros
ARQUIVO_TEMPLATE_YAML = "gemconfig.yaml"

# Parâmetro a ser variado
with open("gemconfig.yaml", "r") as f:
    config_geral = yaml.safe_load(f)

PARAMETRO_VARIADO = config_geral["parametro_variado"]
VALORES_VARIADOS = config_geral["valores_variados"]

if PARAMETRO_VARIADO not in config_geral:
    raise ValueError(f"O parâmetro '{PARAMETRO_VARIADO}' não está definido nos parâmetros base do YAML.")

#função principal
def criar_simulacoes(prefixo="teste"):
    #cria o diretório onde todas as simulações ficarão armazenadas
    #adiciono o prefixo da grandeza que irá ser variada - necessário declarar na execução
    pasta_base = os.path.join(PASTA_BASE, prefixo)
    os.makedirs(pasta_base, exist_ok=True)

    #abre o arquivo yaml e carrega em um dicionário
    with open(ARQUIVO_TEMPLATE_YAML, "r") as f:
        parametros_base = yaml.safe_load(f)

    #loop sobre os valores do parametro variado a serem simulados
    for valor in VALORES_VARIADOS:
        parametros = parametros_base.copy() #copia o dicionário base 
        parametros[PARAMETRO_VARIADO] = valor #substitui pelo valor atual do loop
        nome_dir = f"{PARAMETRO_VARIADO}_{valor:.4f}".replace('.', 'p') #gera o nome do diretorio correspondente
        pasta_sim = os.path.join(pasta_base, nome_dir) #faz o caminho completo da simulacao
        os.makedirs(pasta_sim, exist_ok=True) #cria esse diretorio 

        #Salva os parâmetros no formato .yaml, para registro 
        salvar_yaml(parametros, os.path.join(pasta_sim, "gem.yaml"))
        #gera a versão gem.conf que é entrada pro Garfield e a salva na pasta
        salvar_conf_para_garfield(parametros, os.path.join(pasta_sim, "gem.conf"))

        # Faz uma cópia dos arquivos comuns na pasta de simulação
        for arquivo in ARQUIVOS_COMUNS:
            shutil.copy(arquivo, pasta_sim)

        # Criar job.sub específico para a simulação
        criar_job_sub(pasta_sim)

    print(f"{len(VALORES_VARIADOS)} simulações geradas em '{PASTA_BASE}/'.")

if __name__ == "__main__":
    #cria novo interpretador de argumento
    parser = argparse.ArgumentParser()
    #define que o script pode receber um argumento string chamado --prefix
    parser.add_argument("--prefix", type=str, default="teste",
                        help="Nome do subdiretório dentro de simulacoes/")
    #le o argumento e armazena num objeto args
    args = parser.parse_args()

    criar_simulacoes(prefixo=args.prefix)
