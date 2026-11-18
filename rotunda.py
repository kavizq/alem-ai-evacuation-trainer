"""Circular interiors inspired by supplied Alem.ai photographs; not a surveyed plan."""
import math
from panda3d.core import Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat, GeomVertexWriter, TransparencyAttrib
from interiors import glass, rounded, desk, METAL
from finishes import material

from gallery import COURT

RADIUS = 30.5
STAIR_DURATION = 6.0


def surface(parent, name, quads, color, alpha=1):
    data = GeomVertexData(name, GeomVertexFormat.getV3c4(), Geom.UHStatic)
    vertices, colors = GeomVertexWriter(data,'vertex'), GeomVertexWriter(data,'color')
    triangles = GeomTriangles(Geom.UHStatic)
    for quad in quads:
        offset = vertices.getWriteRow()
        for point in quad:
            vertices.addData3(*point)
            colors.addData4(*color,alpha)
        triangles.addVertices(offset,offset+1,offset+2)
        triangles.addVertices(offset,offset+2,offset+3)
    geometry=Geom(data); geometry.addPrimitive(triangles)
    node=GeomNode(name); node.addGeom(geometry)
    result=parent.attachNewNode(node); result.setTwoSided(True)
    if alpha<1:
        result.setTransparency(TransparencyAttrib.MAlpha); result.setDepthWrite(False)
    return result


def disc(game, z, radius, color, name):
    quads=[]
    if name == 'circular floor':
        # Horizontal strips leave actual apertures over both descending flights.
        # A full disc here would cut through the stair camera at the upper slab.
        for row in range(196):
            y0=-10-radius+row*(2*radius/196)
            y1=y0+2*radius/196
            half0=math.sqrt(max(0,radius**2-(y0+10)**2))
            half1=math.sqrt(max(0,radius**2-(y1+10)**2))
            half=min(half0,half1)
            spans=[(10-half,10+half)]
            holes = []
            if game.floor > 1:
                if y1 > .50 and y0 < 10.45:
                    holes.extend([(x-1.47,x+1.47) for x in (0,20)])
                if y1 > COURT[2] and y0 < COURT[3]:
                    holes.append(COURT[:2])
            for lo,hi in holes:
                clipped=[]
                for left,right in spans:
                    if right<=lo or left>=hi:
                        clipped.append((left,right))
                    else:
                        if left<lo:clipped.append((left,lo))
                        if right>hi:clipped.append((hi,right))
                spans=clipped
            for left,right in spans:
                quads.append(((left,y0,z),(right,y0,z),(right,y1,z),(left,y1,z)))
        return surface(game.world,name,quads,color)
    for i in range(96):
        a,b=i*math.tau/96,(i+1)*math.tau/96
        quads.append(((10,-10,z),(10+radius*math.cos(a),-10+radius*math.sin(a),z),
                      (10+radius*math.cos(b),-10+radius*math.sin(b),z),(10,-10,z)))
    return surface(game.world,name,quads,color)


def beam(game, a, b, thickness, color):
    node=game.box(tuple((x+y)/2 for x,y in zip(a,b)),(thickness,math.dist(a,b),thickness),color)
    node.lookAt(*b)
    return node


def build_rotunda(game):
    disc(game,-.025,RADIUS,(.62,.65,.65),'circular floor')
    # Spherical facade narrows toward the crown; all gameplay remains within it.
    quads=[]
    top_radius=RADIUS-1.15
    for i in range(72):
        a,b=i*math.tau/72,(i+1)*math.tau/72
        p=lambda r,t,z:(10+r*math.cos(t),-10+r*math.sin(t),z)
        quads.append((p(RADIUS,a,0),p(RADIUS,b,0),p(top_radius,b,4.2),p(top_radius,a,4.2)))
        beam(game,p(RADIUS,a,0),p(top_radius,a,4.2),.075,(.25,.43,.47))
        for z,r in ((.12,RADIUS),(1.12,RADIUS-.3),(4.12,top_radius)):
            beam(game,p(r,a,z),p(r,b,z),.065,(.30,.46,.49))
        if i%6==0:
            beam(game,p(RADIUS,a,0),p(top_radius,b,4.2),.18,(.68,.76,.75))
    surface(game.world,'curved glass facade',quads,(.46,.72,.78),.13)
    # A shallow vaulted ceiling with exposed radial beams and suspended luminaires.
    roof=[]
    for i in range(72):
        a,b=i*math.tau/72,(i+1)*math.tau/72
        for band in range(24):
            r0=top_radius*band/24
            r1=top_radius*(band+1)/24
            corners=[p(r,t,6.2-2*r/top_radius) for r,t in ((r0,a),(r1,a),(r1,b),(r0,b))]
            if max(v[0] for v in corners)>22 and min(v[0] for v in corners)<33 and max(v[1] for v in corners)>-18 and min(v[1] for v in corners)<-3:
                continue
            roof.append(corners)
        if i%6==0:
            beam(game,(10,-10,6.05),(10+top_radius*math.cos(a),-10+top_radius*math.sin(a),4.14),.13,(.22,.32,.34))
    surface(game.world,'vaulted ceiling',roof,(.40,.47,.48))
    for radius in (9,17):
        for i in range(12):
            a=i*math.tau/12
            x,y=10+radius*math.cos(a),-10+radius*math.sin(a)
            if game.floor == 4 and -1.8 < x < 18.5 and -35.5 < y < -15.5:
                continue
            # No ceiling exists across the open atrium. Its lights belong to
            # the shared roof frame, not the current floor's vaulted ceiling.
            if 22 < x < 33 and -18 < y < -3:
                continue
            rounded(game.world,(x,y,3.87),(1.1,1.1,.10),(.91,.96,.94))
            ceiling_z = 6.2 - 2 * radius / top_radius
            lamp_top = 3.97
            game.box((x,y,(ceiling_z+lamp_top)/2),
                     (.035,.035,ceiling_z-lamp_top),METAL)
            game.box((x,y,ceiling_z-.035),(.18,.18,.07),METAL)
    # Quiet booths and white planters reference the pink seating / yellow wayfinding photo.
    for side in (-1,1):
        x=10+side*18
        for y in ((-22,1,5) if side==1 else (-16,-11,-6)):
            booth=game.box((x,y,.38),(1.5,1.5,.55),(.57,.36,.38))
            material(booth,'fabric',(0,1,2,3,4))
            for dx in (-.70,.70):
                panel=game.box((x+dx,y,1.14),(.13,1.5,1.95),(.60,.42,.43))
                material(panel,'fabric',(0,1,2,3))
            game.box((x,y+.68,1.14),(1.5,.13,1.95),(.60,.42,.43))
            game.obstacles.append((x,y,1.05,1.05))
        for y in (-20,-2):
            game.box((x,y,.44),(1.6,.7,.88),(.84,.86,.83))
            for i in range(13):
                leaf=rounded(game.world,(x-.65+i*.105,y,1.08+.09*(i%3)),(.08,.12,1.0),(.20,.34,.16))
                leaf.setR((i%5-2)*7)
            game.obstacles.append((x,y,1.1,.65))
    if game.floor in (2,3):
        for x in (-3.7,21.0):
            for y in (-17,-11,-5):
                desk(game,x,y,True)
    # Tactile strip follows a clear circulation lane, outside the puzzle obstacles.
    for x in (-5,21.9):
        for dx in (-.10,0,.10):
            game.box((x+dx,-11,.008),(.028,18,.012),(.85,.66,.12))
    # Enclosed stairs, including lower-floor arrival landing. No exterior flight.
    for x in (0,20):
        if game.floor==1:
            continue
        game.obstacles.append((x,5.6,1.85,5.1))
        for side in (-1,1):
            wall=game.box((x+side*1.56,5.6,-.3),(.22,9.7,7.8),(.68,.72,.71))
            material(wall,'stone',(0,1,2,3))
            beam(game,(x+side*1.39,1.85,.88),(x+side*1.39,8.98,-3.32),.065,(.10,.31,.43))
        game.box((x,5.6,3.55),(3.3,9.7,.24),(.27,.35,.38))
        game.box((x,10.35,-.3),(3.3,.22,7.8),(.64,.69,.68))
        for y in (2.6,5.6,8.6):
            game.box((x,y,3.39),(1.2,.25,.035),(.94,.96,.90))
        game.box((x,9.55,-4.20),(3.0,1.5,.22),(.62,.65,.65))
        game.label(f'FLOOR {game.floor-1}',(x,10.20,-2.65),.28)
        for step in range(24):
            game.box((x,1.72+step*.31,-step*4.2/23+.115),(2.60,.035,.012),(.81,.70,.30))
