"""Nur Alem-inspired exterior and EXPO plaza for the evacuation ending."""
import math
import random

from panda3d.core import (
    Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter,
    LineSegs, NodePath, PNMImage, TextNode,
)

from environment import texture_from_image
from interiors import rounded

ALUMINUM = (.53,.58,.61)
FRAME = (.23,.29,.33)


def sphere(parent):
    rows, columns = 34, 96
    radius, center_z = 24, 17
    base = math.asin(-center_z/radius)
    data = GeomVertexData('reflective glazing', GeomVertexFormat.getV3c4(), Geom.UHStatic)
    points = GeomVertexWriter(data, 'vertex')
    colors = GeomVertexWriter(data, 'color')
    triangles = GeomTriangles(Geom.UHStatic)
    grid = LineSegs('panel joints')
    grid.setColor(.24,.36,.43,1)

    def panel_point(row, col, offset=0):
        lat = base + (math.pi/2-base)*row/rows
        azimuth = col*math.tau/columns
        x, y, z = math.cos(lat)*math.cos(azimuth), math.cos(lat)*math.sin(azimuth), math.sin(lat)
        r = radius+offset
        return (10+r*x,-10+r*y,center_z+r*z), (x,y,z)

    for row in range(rows):
        for col in range(columns):
            first = points.getWriteRow()
            panel = .022*math.sin(row*3.8+col*2.7)
            for r,c in ((row,col),(row,col+1),(row+1,col),(row+1,col+1)):
                point, (nx, ny, nz) = panel_point(r,c)
                points.addData3(*point)
                # Approximate the view and reflected horizon for the exterior camera.
                vx,vy,vz = 14-point[0],-76-point[1],6-point[2]
                length = math.sqrt(vx*vx+vy*vy+vz*vz)
                incidence = max(0,(vx*nx+vy*ny+vz*nz)/length)
                reflected_z = 2*incidence*nz-vz/length
                reflected_x = 2*incidence*nx-vx/length
                sky = max(0,min(1, .50+reflected_z*2.0))
                horizon = math.exp(-(reflected_z/.13)**2)
                wing = .10*horizon*abs(reflected_x)**.65
                glint = .24*max(0,(-.49*nx-.65*ny+.58*nz))**29
                colors.addData4(.22+.20*sky+.16*horizon+wing+glint+panel,
                                .32+.24*sky+.13*horizon+wing+glint+panel,
                                .39+.27*sky+.10*horizon+wing+glint+panel,1)
            triangles.addVertices(first,first+1,first+2)
            triangles.addVertices(first+1,first+3,first+2)
    geometry = Geom(data)
    geometry.addPrimitive(triangles)
    node = GeomNode('Nur Alem sphere')
    node.addGeom(geometry)
    shell = parent.attachNewNode(node)
    shell.setTwoSided(True)
    for row in range(0,rows,2):
        grid.moveTo(*panel_point(row,0,.018)[0])
        for col in range(1,columns+1):
            grid.drawTo(*panel_point(row,col,.018)[0])
    for col in range(0,columns,2):
        grid.moveTo(*panel_point(0,col,.018)[0])
        for row in range(1,rows+1):
            grid.drawTo(*panel_point(row,col,.018)[0])
    parent.attachNewNode(grid.create())


def entry(game, site):
    lobby = site.attachNewNode('entrance canopy and doors')
    lobby.setY(-6.35)
    game.box((10,-25.1,1.18),(24.4,5.9,2.35),(.25,.30,.31),lobby)
    game.box((10,-28.05,3.05),(24.8,.25,1.85),(.25,.30,.34),lobby)
    game.box((10,-28.26,3.86),(25.2,1.85,.20),ALUMINUM,lobby)
    game.box((10,-28.84,3.74),(24.9,.19,.09),(.73,.77,.76),lobby)
    for index in range(12):
        x = -1.12+index*2.02
        tone = .035*math.cos(index*1.83)
        game.box((x,-28.18,1.21),(1.92,.10,2.32),(.20+tone,.32+tone,.39+tone),lobby)
        for offset in (-.91,0,.91):
            game.box((x+offset,-28.265,1.20),(.037,.08,2.34),ALUMINUM,lobby)
        game.box((x,-28.25,1.08),(1.88,.045,.035),ALUMINUM,lobby)
        for dx in (-.12,.12):
            game.box((x+dx,-28.30,1.20),(.025,.078,.21),ALUMINUM,lobby)
    sign = TextNode('entrance lettering')
    sign.setText('alem.ai')
    sign.setAlign(TextNode.ACenter)
    lettering = lobby.attachNewNode(sign)
    lettering.setPos(10,-28.23,2.78)
    lettering.setScale(1.34)
    lettering.setColor(.99,.98,.94,1)


def pavilion(game, site, side):
    """Sweeping wings frame the plaza like the adjacent EXPO pavilions."""
    for index in range(18):
        distance = 20+index*2.45
        x = 10+side*distance
        y = -12.5 - .014*(distance-27)**2
        height = 7.8+1.2*math.cos(index*.14)
        heading = math.degrees(math.atan(-side*.028*(distance-27)))
        section = site.attachNewNode('pavilion section')
        section.setPos(x,y,0)
        section.setH(heading)
        game.box((0,3,height*.5),(2.53,7.8,height),(.40,.46,.47),section)
        for level in range(4):
            z = 1.18+level*1.99
            tint = .034*math.sin(index*.94+level*2.4)
            game.box((0,-.93,z),(2.42,.19,1.84),(.26+tint,.42+tint,.49+tint),section)
            for dx in (-.96,-.31,.31,.96):
                rib = game.box((dx,-1.06,z),(.045,.09,1.94),ALUMINUM,section)
                rib.setR(side*9)
            game.box((0,-1.085,z+.97),(2.50,.25,.084),FRAME,section)
        game.box((0,-.79,height+.03),(2.56,.68,.33),ALUMINUM,section)


def plaza(game, site):
    size = 768
    pixels = PNMImage(size,size,3)
    rng = random.Random(403)
    for row in range(size):
        y = -12-(row+.5)*74/size
        for col in range(size):
            x = -29+(col+.5)*78/size
            slab_x = (x+29)/1.35
            slab_y = (-12-y)/1.35
            joint = min(slab_x%1,slab_y%1)<.065
            stripe = .036*math.sin(int(slab_x)*1.9+int(slab_y)*5.4)
            shadow = .15*math.exp(-((x-12)/14)**2-((y+24)/8)**2)
            light = .64+stripe+rng.uniform(-.024,.024)-shadow
            if joint:
                light *= .82
            if abs(x-10) > 25:
                light *= .83
            pixels.setXel(col,row,light,light*.98,light*.92)
    floor = NodePath(game.floor_card).copyTo(site)
    floor.setPos(10,-49,-.06)
    floor.setP(-90)
    floor.setScale(78,1,74)
    floor.setTwoSided(True)
    floor.setTexture(texture_from_image('EXPO stone paving',pixels))
    for side in (-1,1):
        for index in range(5):
            x,y = 10+side*(17.8+index*1.18), -34-index*5.4
            game.box((x,y,.08),(3.2,2.28,.23),(.48,.48,.44),site)
            game.box((x,y,.21),(2.94,2.05,.12),(.37,.41,.28),site)
            for offset in (-.83,0,.83):
                game.box((x+offset,y,.78),(.09,.09,1.24),(.32,.27,.20),site)
                for level in range(4):
                    spread = .95-.17*level
                    leaf = rounded(site,(x+offset,y,.72+level*.32),
                                   (spread,spread,.62),(.23+.017*level,.34+.024*level,.24))
                    leaf.setH(35*level)
            game.box((x-side*2.12,y,.235),(.44,1.55,.10),(.52,.36,.23),site)
            for dy in (-.53,.53):
                game.box((x-side*2.12,y+dy,.11),(.18,.11,.22),FRAME,site)
        for y in (-37,-49,-61,-73):
            x = 10+side*13.6
            game.box((x,y,1.31),(.105,.105,2.68),FRAME,site)
            game.box((x-side*.22,y,2.64),(.53,.21,.095),ALUMINUM,site)
    game.box((10,-82,-.042),(75,6.9,.045),(.29,.31,.31),site)
    for x in range(5,16,2):
        game.box((x,-82,-.016),(.77,5.4,.007),(.77,.76,.69),site)


def build_expo(game):
    site = game.world.attachNewNode('EXPO district')
    sphere(site)
    entry(game,site)
    pavilion(game,site,-1)
    pavilion(game,site,1)
    plaza(game,site)
    site.flattenStrong()
