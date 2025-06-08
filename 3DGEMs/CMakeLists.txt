# Use the code in this section for standalone projects
cmake_minimum_required(VERSION 3.9 FATAL_ERROR) ##requerimentos do Cmake
project(Gem3D) #nome do projeto
if(NOT TARGET Garfield::Garfield) #so compile se achar o garfield
  find_package(Garfield REQUIRED)
endif()

#---Build executable------------------------------------------------------------
add_executable(gem3D gem3D.C) ##criar o executável
target_link_libraries(gem3D Garfield::Garfield ROOT::Tree) ##linkar com o Garfield, adicional o ROOT:Tree para funcionar o TTree
