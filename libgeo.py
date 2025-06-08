# Biblioteca de geometrias do gmsh em python
# Furos bordas etc...

import math
import gmsh

occ = gmsh.model.occ

def cylinder_hole(radius: float, dielectric_th: float):
    hole = occ.addCylinder(0, 0, -dielectric_th/2, 0, 0, dielectric_th, radius)
    return [(3, hole)]

def bicone_hole(radius: float, mid_radius: float, dielectric_th: float):
    cone1 = occ.addCone(0, 0, dielectric_th/2, 0, 0, -dielectric_th/2, radius, mid_radius)
    cone2 = occ.addCone(0, 0, -dielectric_th/2, 0, 0, dielectric_th/2, radius, mid_radius)
    return occ.fuse([(3, cone1)], [(3, cone2)])[0]

def cone_hole(top_radius: float, bottom_radius: float, dielectric_th: float):
    cone = occ.addCone(0, 0, dielectric_th/2, 0, 0, -dielectric_th, top_radius, bottom_radius)
    return [(3, cone)]


def rough_hole(func: callable, n: int, dielectric_th: float, step_type='mid'):
    bottom_z = -dielectric_th / 2
    dz = dielectric_th / n
    steps = []
    for i in range(n):
        top_z = bottom_z + dz

        top_r = func(top_z)
        bottom_r = func(bottom_z)
        mid_r = func((top_z + bottom_z)/2)

        if i == 0:
            r = bottom_r
        elif i == n -1:
            r = top_r
        elif step_type == 'min':
            r = min(top_r, bottom_r, mid_r)
        elif step_type == 'max':
            r = max(top_r, bottom_r, mid_r)
        else:
            r = mid_r

        h = occ.addCylinder(0, 0, bottom_z, 0, 0, dz, r)
        steps.append((3, h))
        bottom_z = top_z

    return occ.fuse(steps[0:1], steps[1:])[0]


def bicone_func(z, radius, mid_radius, dielectric_th):
    return (radius - mid_radius) / (dielectric_th / 2) * abs(z) + mid_radius

def cone_func(z, top_radius, bottom_radius, dielectric_th):
    return (top_radius - bottom_radius) / dielectric_th * (z + dielectric_th/2) + bottom_radius

def ring_decoration(dielectric_dimtag, dielectric_size, hole_radius, ring_radius,
                top, height=0):
    dx, dy, d_th = dielectric_size
    major_radius = hole_radius + math.sqrt(ring_radius**2 - height**2)

    z = d_th/2 + height
    if not top:
        z *= -1
    ring_tags = []
    ring_tags.append(occ.addTorus(0, 0, z, major_radius, ring_radius))
    ring_tags.append(occ.addTorus(dx/2, dy, z, major_radius, ring_radius))
    ring_tags.append(occ.addTorus(dx, 0, z, major_radius, ring_radius))
    rings = [(3, i) for i in ring_tags]

    box = occ.addBox(0, 0, -4*z, dx, dy, 8*z)
    decor_tags, _ = occ.intersect(rings, [(3, box)])

    return occ.fuse(dielectric_dimtag, decor_tags)[0]

def chamfer_decoration(dielectric_dimtag, dielectric_size, hole_radius, chamfer_size, top):
    dx, dy, d_th = dielectric_size
    positive = chamfer_size > 0

    bottom_radius = hole_radius
    top_radius = bottom_radius + abs(chamfer_size)

    z = d_th/2
    if not top:
        z *= -1
        chamfer_size *= -1

    fill = occ.addBox(0, 0, z, dx, dy, chamfer_size)
    chamfer_tags = []
    chamfer_tags.append(occ.addCone(0, 0, z, 0, 0, chamfer_size, bottom_radius,top_radius))
    chamfer_tags.append(occ.addCone(dx/2, dy, z, 0, 0, chamfer_size, bottom_radius,top_radius))
    chamfer_tags.append(occ.addCone(dx, 0, z, 0, 0, chamfer_size, bottom_radius,top_radius))
    chamfers = [(3, i) for i in chamfer_tags]

    if positive:
        dielectric_dimtag, _ = occ.fuse(dielectric_dimtag, [(3, fill)])
        result, _ = occ.cut(dielectric_dimtag, chamfers)
    else:
        dielectric_dimtag, _ = occ.cut(dielectric_dimtag, [(3, fill)])
        box = occ.addBox(0, 0, -2*z, dx, dy, 4*z)
        decor_tags, _ = occ.intersect(chamfers, [(3, box)])
        result, _ = occ.fuse(dielectric_dimtag, decor_tags)

    return result
