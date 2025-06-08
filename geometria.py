import math
import gmsh
import libgeo
import yaml

occ = gmsh.model.occ


gmsh.initialize()
#para mostrar infos no terminal, 1 mostra e 0 nao
gmsh.option.setNumber("General.Terminal", 1)
#para controlar a verbosidade da saída do terminal, vai de 0 a 4 os níveis
#com 3 veremos erros e warnings e mensagens gerais
gmsh.option.setNumber("General.Verbosity", 3)

# lê arquivo de configuração
with open("gem.yaml", "r") as f:
    conf = yaml.safe_load(f)

# Valores definidos pelo usuário
radius = conf['diameter'] / 2
pitch = conf['pitch']
etch = conf['etch']
d_th = conf['dieletric_thickness']
c_th = conf['conductor_thickness']
u_dist = conf['upper_plate']
b_dist = conf['lower_plate']
hole_type = conf['hole_type']
step_type = conf.get('step_type', 'mid')

cone_types = ['cone', 'cone_rough']
bottom_radius = conf['bottom_diameter'] / 2 if  hole_type in cone_types else radius
bottom_etch = conf.get('bottom_etch', etch)

top_decoration = conf.get('top_decoration', 'none')
bottom_decoration = conf.get('bottom_decoration', 'none')
decoration_size = conf.get('decoration_size', 2 * c_th)
bottom_decoration_size = conf.get('bottom_decoration_size', decoration_size)

# O elmer calcula melhor o campo sem o condutor.
remove_conductor = True

# mesh size
hole_center_mdiv = 10
hole_wall_mdiv = 60
conductor_mdiv = 18
conductor_edge_mdiv = 5
dielectric_mdiv = 12
electrode_mdiv = 15

# constantes auxiliares
dx = pitch
dy = math.sqrt(3) * pitch / 2
eps = d_th * 1e-3
mean_radius = (radius + bottom_radius) / 2
mean_etch = (etch + bottom_etch) / 2

hole_center_msize = min(d_th, 2*radius) / hole_center_mdiv
hole_wall_msize = 2 * math.pi * mean_radius / hole_wall_mdiv
conductor_msize = pitch / conductor_mdiv
conductor_edge_msize = c_th / conductor_edge_mdiv
dielectric_msize = pitch / dielectric_mdiv
upper_msize = u_dist / electrode_mdiv
bottom_msize = b_dist / electrode_mdiv

#funcao de intersecao entre 2 listas
def intersection(list1: list, list2: list):
    return list(set(list1) & set(list2))

#funcao para pegar o segundo elemento de cada lista de dimTags
def get_tags(dimTags):
    return [entity[1] for entity in dimTags]

gmsh.model.add("gemcell")

gmsh.logger.start()

#criando funcoes lambda para chamar os furos no libgeo e armazenando no dicionario hole_funcs
hole_funcs = {
    'cylinder':
        lambda: libgeo.cylinder_hole(radius, d_th),
    'bicone':
        lambda: libgeo.bicone_hole(radius, 5/7*radius, d_th),
    'cone':
        lambda: libgeo.cone_hole(radius, bottom_radius, d_th),
    'bicone_rough':
        lambda: libgeo.rough_hole(
            lambda z: libgeo.bicone_func(z, radius, 5/7*radius, d_th),
            15, d_th),
    'cone_rough':
        lambda: libgeo.rough_hole(
            lambda z: libgeo.cone_func(z, radius, bottom_radius, d_th),
            15, d_th),
    'negbicone_rough':
        lambda: libgeo.rough_hole(
            lambda z: libgeo.bicone_func(z, radius, 7/5*radius, d_th),
            15, d_th),
}

dielectric_size = (dx, dy, d_th)
box = occ.addBox(0, 0, -d_th/2, dx, dy, d_th)
dielectric_box = [(3, box)]

#colocando decoraçao (anel)
top = True
for decor in [top_decoration, bottom_decoration]:
    size = decoration_size if top else bottom_decoration_size
    r = radius + etch if top else bottom_radius + bottom_etch
    # adicionar um espaço entre o furo e decoração para evitar quinas no condutor
    r += min(c_th / 2, d_th / 20)
    if decor == 'ring':
        dielectric_box  = libgeo.ring_decoration(dielectric_box,
                            dielectric_size, r, size, top, height=-size / 3)

    elif decor == 'chamfer':
        dielectric_box  = libgeo.chamfer_decoration(dielectric_box,
                            dielectric_size, r, size, top)

    elif decor != 'none':
        raise KeyError('Decoration type "{}" not supported'.format(decor))

    top = False

#chamar funcao sychronize sempre pq ela sincroniza a geometria e malha
occ.synchronize()

#retorna as entendidades na regiao da box delimitada por essas coordenadas
r = 2 * pitch
top_dielec = occ.getEntitiesInBoundingBox(
    -r, -r, 0, r, r, r, 2)
bottom_dielec = occ.getEntitiesInBoundingBox(
    -r, -r, -r, r, r, 0, 2)

#criando o condutor por extrusao das superficies no topo e no fundo
conductor = []
top = True
for dielec in [top_dielec, bottom_dielec]:
    dz = c_th if top else -c_th
    extrusion = occ.extrude(dielec, 0, 0, dz)
    volumes = [t for t in extrusion if t[0] == 3] #pega só os volumes na extrusao 
    if len(volumes) > 1:
        volumes = occ.fuse(volumes[0:1], volumes[1:])[0] #se achar mais de 1 volume, funde o primeiro com o resto
    conductor += volumes
    top = False

# Define furo do dielétrico
holes = hole_funcs[hole_type]()

# Furo do condutor ou etch
top_etch_tool = occ.addCylinder(0, 0, 0, 0, 0, d_th +2*abs(decoration_size), radius + etch)
bottom_etch_tool = occ.addCylinder(0, 0, 0, 0, 0, -d_th -2*abs(bottom_decoration_size), bottom_radius + bottom_etch)
etch_tools = [(3, top_etch_tool), (3, bottom_etch_tool)]

# Itera sobre demais furos
for i in range(2):
    tx = dx if i == 0 else dx/2
    ty = 0 if i == 0 else dy

    # Copia furos
    hole = occ.copy(holes[0:1])
    occ.translate(hole, tx, ty, 0)
    holes += hole

    # Perfura condutor
    etch_tool = occ.copy(etch_tools)
    occ.translate(etch_tool, tx, ty, 0)
    etch_tools += etch_tool

# Perfura dielétrico
dielectric, _ = occ.cut(dielectric_box, holes, removeTool=False)

# Perfura condutor
conductor, _ = occ.cut(conductor, etch_tools)

# Define caixa de gas
gas_box = occ.addBox(0, 0, -b_dist, dx, dy, u_dist+b_dist)
gas_box = [(3, gas_box)]
holes, _ = occ.intersect(holes, gas_box, removeTool=False)

# Recorta os volumes sobrepostos
gem_volumes = dielectric + conductor + holes
gem_fragments, _ = occ.fragment(gem_volumes, gas_box)
gas = [v for v in gem_fragments if v not in gem_volumes]

# Corte hexagonal, para forçar a simetria hexagonal na mesh
# Cria planos de corte
hex_cut = []
rec = occ.addRectangle(dx/2, dy/3 , -b_dist, u_dist+b_dist, -2*dy/3)
rec = [(2, rec)]
occ.rotate(rec, dx/2, dy/3, -b_dist, 0, 1, 0, -math.pi/2)
occ.rotate(rec, dx/2, dy/3, -b_dist, 0, 0, 1, 2*math.pi/3)
hex_cut += rec
rec = occ.copy(rec)
occ.rotate(rec, dx/2, dy/3, -b_dist, 0, 0, 1, 2*math.pi/3)
hex_cut += rec
rec = occ.addRectangle(dx/2, 0, -b_dist, u_dist+b_dist, dy)
rec = [(2, rec)]
occ.rotate(rec, dx/2, 0, -b_dist, 0, 1, 0, -math.pi/2)
hex_cut += rec

# Recorta volumes
conductor, _ = occ.fragment(conductor, hex_cut, removeTool=False)
dielectric, _ = occ.fragment(dielectric, hex_cut, removeTool=False)
gas, _ = occ.fragment(gas, hex_cut, removeTool=False)
holes, _ = occ.fragment(holes, hex_cut, removeTool=False)

for l in [conductor, dielectric, gas, holes]:
    [l.pop() for i in reversed(range(len(l))) if l[i][0] != 3]

occ.remove(hex_cut, recursive=True)
# O nome da função já explica...
occ.removeAllDuplicates()
# Temos que chamar essa função para "gravar" as alterações na geometria
occ.synchronize()

####### Tamanho da mesh

gmsh.model.mesh.setSize(gmsh.model.getBoundary(conductor, False, False, True),
                        conductor_msize)
gmsh.model.mesh.setSize(gmsh.model.getBoundary(dielectric, False, False, True),
                        dielectric_msize)
gmsh.model.mesh.setSize(gmsh.model.getBoundary(holes, False, False, True),
                        hole_wall_msize)

# Tamanho da mesh nos eletrodos
upper_electrode = gmsh.model.occ.getEntitiesInBoundingBox(
     -eps, -eps, u_dist-eps, dx+eps, dy+eps, u_dist+eps, 2)
bottom_electrode = gmsh.model.occ.getEntitiesInBoundingBox(
    -eps, -eps, -b_dist-eps, dx+eps, dy+eps, -b_dist+eps, 2)
gmsh.model.mesh.setSize(
    gmsh.model.getBoundary(upper_electrode, False, False, True), upper_msize)
gmsh.model.mesh.setSize(
    gmsh.model.getBoundary(bottom_electrode, False, False, True), bottom_msize)

hole_curves = []

# Itera sobre todos os furos
for i in range(3):
    tx = ty = 0
    if i == 1:
        tx = dx
    elif i == 2:
        tx, ty = dx/2, dy

    # Interior dos furos com mesh mais grossa
    dz = d_th / 2
    points = occ.getEntitiesInBoundingBox(tx-eps, ty-eps, -dz-eps,
                                          tx+eps, ty+eps, dz+eps, 0)
    gmsh.model.mesh.setSize(points, hole_center_msize)

    # Obtem curvas próximas aos furos
    dr = max(radius, bottom_radius) + max(etch, bottom_etch)
    dz = d_th + max(abs(decoration_size), abs(bottom_decoration_size))
    hole_curves += occ.getEntitiesInBoundingBox(
        tx-dr-eps, ty-dr-eps, -dz-eps, tx+dr+eps, ty+dr+eps, dz+eps, 1)

# Obtem todas as curvas do condutor
conductor_curves = gmsh.model.getBoundary(conductor, False, False, False)
conductor_curves = gmsh.model.getBoundary(conductor_curves, False, False, False)

# Curvas na borda do condutor
conductor_edge_curves = intersection(hole_curves, conductor_curves)

gmsh.model.mesh.field.add("Distance", 1)
gmsh.model.mesh.field.setNumber(1, "NNodesByEdge", 100)
gmsh.model.mesh.field.setNumbers(1, "EdgesList", get_tags(conductor_edge_curves))

gmsh.model.mesh.field.add("Threshold", 2)
gmsh.model.mesh.field.setNumber(2, "IField", 1)
gmsh.model.mesh.field.setNumber(2, "LcMin", conductor_edge_msize)
gmsh.model.mesh.field.setNumber(2, "LcMax", conductor_msize)
gmsh.model.mesh.field.setNumber(2, "DistMin", c_th / 2)
max_dist = 3*(abs(decoration_size) + abs(bottom_decoration_size)) / 2
gmsh.model.mesh.field.setNumber(2, "DistMax", max_dist)
gmsh.model.mesh.field.setNumber(2, "StopAtDistMax", True)

gmsh.model.mesh.field.setAsBackgroundMesh(2)

####### Obtem superfícies e volumes físicos

# Laterais do volume simulado
sy1 = occ.getEntitiesInBoundingBox(  -eps, -eps, -b_dist-eps,    eps, dy+eps, u_dist+eps, 2)
sy2 = occ.getEntitiesInBoundingBox(dx-eps, -eps, -b_dist-eps, dx+eps, dy+eps, u_dist+eps, 2)

sx1a = occ.getEntitiesInBoundingBox(    -eps, -eps, -b_dist-eps, dx/2+eps, eps, u_dist+eps, 2)
sx1b = occ.getEntitiesInBoundingBox(dx/2-eps, -eps, -b_dist-eps,   dx+eps, eps, u_dist+eps, 2)
sx2b = occ.getEntitiesInBoundingBox(    -eps, dy-eps, -b_dist-eps, dx/2+eps, dy+eps, u_dist+eps, 2)
sx2a = occ.getEntitiesInBoundingBox(dx/2-eps, dy-eps, -b_dist-eps,   dx+eps, dy+eps, u_dist+eps, 2)

r = 2 * pitch
# Superfície do condutor superior
conductor_boundaries = gmsh.model.getBoundary(conductor, False, False)
upper_surfaces = occ.getEntitiesInBoundingBox(-r, -r, 0, r, r, r, 2)
# upper_cond = [s for s in upper_surfaces if s in conductor_boundaries]
upper_cond = intersection(upper_surfaces, conductor_boundaries)
# Superfície do condutor inferior
bottom_surfaces = occ.getEntitiesInBoundingBox(-r, -r, -r, r, r, 0, 2)
bottom_cond = intersection(bottom_surfaces, conductor_boundaries)
# bottom_cond = [s for s in bottom_surfaces if s in conductor_boundaries]

for s in [sy1, sy2, sx1a, sx1b, sx2a, sx2b]:
    [s.pop(i) for i in reversed(range(len(s))) if s[i] in conductor_boundaries]

if remove_conductor:
    occ.remove(conductor, recursive=True)
    occ.synchronize()

# Superfícies físicas
gmsh.model.addPhysicalGroup(2, get_tags(upper_cond), 1)
gmsh.model.addPhysicalGroup(2, get_tags(bottom_cond), 2)
gmsh.model.addPhysicalGroup(2, get_tags(upper_electrode), 3)
gmsh.model.addPhysicalGroup(2, get_tags(bottom_electrode), 4)
gmsh.model.addPhysicalGroup(2, get_tags(sx1a), 5)
gmsh.model.addPhysicalGroup(2, get_tags(sx2a), 6)
gmsh.model.addPhysicalGroup(2, get_tags(sx1b), 7)
gmsh.model.addPhysicalGroup(2, get_tags(sx2b), 8)
gmsh.model.addPhysicalGroup(2, get_tags(sy1), 9)
gmsh.model.addPhysicalGroup(2, get_tags(sy2), 10)

# Volumes físicos
gmsh.model.addPhysicalGroup(3, get_tags(gas + holes), 1)
gmsh.model.addPhysicalGroup(3, get_tags(dielectric), 2)

if not remove_conductor:
    gmsh.model.addPhysicalGroup(3, get_tags(conductor), 3)

# Configurações da mesh
gmsh.option.setNumber("Mesh.CharacteristicLengthMax", pitch)
gmsh.option.setNumber("Mesh.ElementOrder", 2)
gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
gmsh.option.setNumber("Mesh.CharacteristicLengthFactor", conf.get('msize', 1))

# Gera mesh 3D
gmsh.model.mesh.generate(3)
gmsh.write("gemcell.msh")

# Visualizar a malha gerada
#gmsh.fltk.run()

gmsh.logger.stop()
log = gmsh.logger.get()
print(*log, sep='\n')
gmsh.finalize()