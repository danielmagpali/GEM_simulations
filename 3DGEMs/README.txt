Como funciona a submissão de simulações múltiplas no HTCondor?

----------------------------- RESUMO ----------------------------------- 

1 - Aqui conseguimos submeter múltiplas simulações de uma vez mas variando
apenas 1 parâmetro por vez

2 - O arquivo cria_multiplas_simus é responsável por criar varios diretorios,
cada um com seus job.sub, job.sh e todos os arquivos necessarios separadinhos,
com o nome do diretorio indicando o parametro sendo variado

3 - O arquivo exec_simu_auto é responsável por, dentro de cada uma dessas pastas,
executar todos os comandos necessários para rodar a simulação, desde o GMSH, Elmer,
até o Garfield - ele é executado para cada simulação

4 - Os arquivos geometria.py, libgeo.py, gemconfig.yaml e base.sif.template definem
a geometria e seu campo elétrico

5 - O utils.py guarda as funções usadas no cria_multiplas_simus e no exec_simu_auto

6 - O submit_multiple_simu.sh é o arquivo de execução a ser executado no terminal 
do HTCondor para submeter as simulações todas de uma vez

7 - o job.sh executa o exec_simu_auto.py dentro de cada pasta (e passa tbm as
variaveis de ambiente)

8 - O base.sif.template é o arquivo base de input para o Elmer, se for para alterar
Edrift, deltaV, Eind é possível através do gemconfig.yaml não precisa mexer nesse

9 - O CMakeLists.txt é o arquivo responsável por executar o cmake 

10 - o gem3D.C é o código da simulação do garfield++ 

11 - o IonMobility_Ar+_Ar.txt é o arquivo com a mobilidade dos íons de argônio e
e o dielectrics.dat contém as constantes dielétricas dos materiais da simu
---------------------------- LEMBRETES --------------------------------------

1 - Você deve setar os parâmetros desejados apenas no gemconfig.yaml, esse é o
único arquivo a ser modificado, deixa os outros em paz

2 - Se atente aos caminhos passados no job.sh para que o cluster encontre o Garfield
e suas dependências, serão diferentes em cada caso
(ex de comando para encontrar a dependencia no cluster caso vc n saiba onde está:
find /sampa/daniel-magpali/miniconda3/envs/myenv/ -name "GarfieldConfig.cmake")

3 - NÃO MUDE O NOME DE NADA 
---------------------------- COMO SUBMETER ----------------------------------

1 - Primeiramente rodar o script cria_multiplas_simus.py e passar a ele um argumento
do tipo --prefix "argumento", que deve corresponder ao nome do parâmetro que está
sendo variado (isso é para que ele crie uma subpasta para esse parâmetro)

Ex: se estou variando o diâmetro vou realizar no terminal o comando:

            python3 cria_multiplas_simus.py --prefix diameter

Isso vai criar um diretorio separado para cada simu de cada valor do parametro

2 - Em seguida rodar o submit_multiple_simu.sh passando o caminho da pasta = 
pasta_base + prefixo

Ex:         ./submit_multiple_simu.sh simulacoes/diameter

OBS: antes de rodar esse comando tem que dar a permissão com:  chmod +x submit_multiple_simu.sh

Pronto rodou as simus agr 
