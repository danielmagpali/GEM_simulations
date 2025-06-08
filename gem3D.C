#include <iostream>
#include <fstream>
#include <string>
#include <unordered_map>
#include <TFile.h>
#include <TDirectory.h>
#include <TF1.h>
#include <TApplication.h>
#include <TCanvas.h>
#include <TH1F.h>
#include <TH2F.h>
#include <TH3F.h>
#include <TTree.h> 

#include "Garfield/MediumMagboltz.hh"
#include "Garfield/SolidTube.hh"
#include "Garfield/GeometrySimple.hh"
#include "Garfield/ComponentConstant.hh"
#include "Garfield/Sensor.hh"
#include "Garfield/TrackHeed.hh"
#include "Garfield/Random.hh"
#include "Garfield/AvalancheMicroscopic.hh"
#include "Garfield/ComponentElmer.hh"
#include "Garfield/ViewDrift.hh"
#include "Garfield/ViewFEMesh.hh"
#include "Garfield/ViewField.hh"
#include "Garfield/GarfieldConstants.hh"
#include "Garfield/AvalancheMC.hh"

void RndCircle(double& x, double& y) {
  const double r = std::sqrt(Garfield::RndmUniform());
  const double theta = 2. * M_PI * Garfield::RndmUniform();
  x = r * std::cos(theta);
  y = r * std::sin(theta);
};

std::unordered_map<std::string, std::string> read_config(const std::string &file_name) {
  std::ifstream gem_file(file_name);
  std::string line, key, value;

  if (!gem_file.is_open()) {
    std::cerr << "File '" << file_name << "' not found\n";
    throw std::runtime_error("Config file not found");
  }

  std::unordered_map<std::string, std::string> conf;

  while (std::getline(gem_file, line)) {
    auto pos = line.find('=');
    if (pos != std::string::npos) {
      key = line.substr(0, pos);
      value = line.substr(pos + 1);
      conf[key] = value;
    }
  }

  return conf;
}

int main() {
 
// Leitura do arquivo .conf
auto conf = read_config("gem.conf");

std::string hole_type = conf["hole_type"];
std::string diameter = conf["diameter"];
std::string decoration = conf["top_decoration"];
std::string decoration_size = conf["decoration_size"];
std::string Edrift = conf["Edrift"];
std::string Eind = conf["Eind"];
std::string deltaV = conf["deltaV"];
std::string nEvents = conf["nEvents"];
std::string bottom_decoration = conf["bottom_decoration"];
std::string bottom_decoration_size = conf["bottom_decoration_size"];
int nEvent = std::stoi(nEvents);

// Criar o meio gasoso
Garfield::MediumMagboltz gas;
gas.SetTemperature(293.15);
gas.SetPressure(760.);
gas.SetComposition("ar", 70., "co2", 30.);
gas.EnableDrift(); //permitir que cargas passem pelo gás
gas.LoadIonMobility("IonMobility_Ar+_Ar.txt"); //carregar o arquivo de mobilidade dos íons

// Colocando o Efeito Penning
const double rPenning = 0.57;
const double lambdaPenning = 0.;
gas.EnablePenningTransfer(rPenning, lambdaPenning, "ar");

//Importar as geometrias e campos do elmer
Garfield::ComponentElmer * elm = new Garfield::ComponentElmer("mesh.header", 
"mesh.elements", "mesh.nodes","dielectrics.dat", 
"outputelmer.result","cm"); 

//Implementando periodicidade x e y (espelhada) na geometria
elm->EnablePeriodicityX();
elm->EnableMirrorPeriodicityY();
elm->PrintMaterials();

//Designando o gás ao meio do elmer
elm->SetMedium(0, &gas);

double lat = 0.07;
double up  = 0.1;
double low = 0.1;

//adicionando um sensor = objeto que lida com o campo elétrico
Garfield::Sensor sensor;
sensor.AddComponent(elm);
sensor.SetArea(-lat,-lat,-low,lat,lat,up);

//track: comando que transporta fótons
Garfield::TrackHeed track; //computa as ioniozacoes dos fotons 
track.SetSensor(&sensor);

//Criando uma avalanche de elétrons
Garfield::AvalancheMicroscopic aval;
aval.SetSensor(&sensor);
aval.SetCollisionSteps(100);
aval.EnableSignalCalculation();

//Criando a avalanche de ions
Garfield::AvalancheMC driftions;
driftions.SetSensor(&sensor);
driftions.SetDistanceSteps(5e-4);
driftions.EnableSignalCalculation();

// ------------- Armazenar dados ------------------------- //

//Criando uma TTree

TTree *tree = new TTree("avalanche_tree", "Coordenadas Eletron e Ion");

Double_t eletron_pos[4];  // coordendas e tempo finais para o eletron
Double_t ion_pos[4];      // coordenadas e tempo finais para o íon
Double_t ionization_pos[4]; //coordenadas e tempo da ionização

tree->Branch("eletron", eletron_pos, "x_electron/D:y_electron/D:z_electron/D:t_electron/D");
tree->Branch("ion", ion_pos, "x_ion/D:y_ion/D:z_ion/D:t_ion/D");
tree->Branch("ionization", ionization_pos, "x_ioniz/D:y_ioniz/D:z_ioniz/D:t_ioniz/D");

// --------------------- Realizando a simulação dos elétrons ---------------- //

int run = nEvent;
int ne_sec = 0;
double t,dx,dy = 0;
double z = 0.03;
double dz = 0;
double energy = 0.1;
double r0 = 0.0035;

for (int i =0; i < run; i++) {

    double x, y;
    RndCircle(x,y);
    x *= r0;
    y *= r0;

    aval.AvalancheElectron(x,y,z,t,energy,dx,dy,dz);
    ne_sec = aval.GetNumberOfElectronEndpoints();

    for (int j = 0; j < ne_sec; j++)
    {
    double x1,y1,z1,t1,e1;
    double x2,y2,z2,t2,e2;
    int status_e;
    int status_i;
    //pegando as coorddenadas finais e inicias dos e da avalanche
    aval.GetElectronEndpoint(j,x1,y1,z1,t1,e1,x2,y2,z2,t2,e2,status_e);
    // Passando as coordenadas diretamente para os arrays da TTree
    ionization_pos[0] = x1;ionization_pos[1] = y1;ionization_pos[2] = z1;ionization_pos[3] = t1;
    eletron_pos[0] = x2; eletron_pos[1] = y2; eletron_pos[2] = z2; eletron_pos[3] = t2;	

    //usamos as coordenadas iniciais do getelectronendpoint como coordenadas iniciais dos ions
    driftions.DriftIon(x1,y1,z1,t1); //falando para propagar os ions gerados
    driftions.GetIonEndpoint(0,x1,y1,z1,t1,x2,y2,z2,t2,status_i);
    
    ion_pos[0] = x2;ion_pos[1] = y2;ion_pos[2] = z2;ion_pos[3] = t2;
    tree->Fill();
    };
    
};

std::string filename = hole_type + diameter  + "_up" + decoration + decoration_size + "_low" +  bottom_decoration + bottom_decoration_size + "_Ed=" + 
Edrift + "_Ei=" + Eind + "_V=" + deltaV + ".root";

TFile *file = new TFile(filename.c_str(), "RECREATE");
tree->Write();
file->Close();

std::cout << "finalizado com sucesso" << '\n';

return 0;

}
