"""Procedural surface materials and fitted interiors for the campaign rooms."""
import math
import random
from functools import lru_cache

from panda3d.core import PNMImage, Texture, TextureStage


@lru_cache
def finish(name):
    size = 256
    image = PNMImage(size,size,3)
    rng = random.Random(703)
    for y in range(size):
        for x in range(size):
            u,v = x/size,y/size
            noise = rng.uniform(-.026,.026)
            if name == 'wood':
                w = 2*math.pi*(v*7+.08*math.sin(u*math.tau))
                grain = .047*math.sin(w)+.019*math.sin(w*5+u*math.tau)
                value = .87+grain+noise*.7
            elif name == 'ceiling':
                seam = min(x%64,64-x%64,y%64,64-y%64)<2
                perforation = x%8 in (0,1) and y%8 in (0,1)
                # Warmer light at the center of each recessed fixture bay.
                bounce = .12*math.exp(-9*((u-.5)**2+(v-.5)**2))
                value = .78+bounce+noise-(.16 if seam else .12 if perforation else 0)
            elif name == 'metal':
                value = .86+.035*math.sin(y*.7)+.05*math.sin(u*math.pi)+noise*.7
            elif name == 'stone':
                mottling = math.sin(u*math.tau*3)*math.cos(v*math.tau*2)
                vein = math.exp(-((math.sin(u*7.0+v*4.2+.36*mottling))/.14)**2)
                value = .87+.028*mottling+.045*vein+noise
            else:
                value = .88+noise-(.065 if (x+y)%4==0 else 0)
            image.setXel(x,y,value,value,value)
    return texture(name,image)


def texture(name, image):
    surface = Texture(name)
    surface.load(image)
    surface.generateRamMipmapImages()
    surface.setMinfilter(Texture.FTLinearMipmapLinear)
    surface.setAnisotropicDegree(4)
    return surface


def material(node, name, faces, repeats=(1,1)):
    stage = TextureStage.getDefault()
    for face_index in faces:
        face = node.getChild(face_index)
        face.setTexture(finish(name))
        face.setTexScale(stage,*repeats)
    return node


def trace_line(image, x0, y0, x1, y1, color):
    count = max(abs(x1-x0), abs(y1-y0), 1)
    for i in range(count+1):
        t = i/count
        x,y = round(x0+(x1-x0)*t),round(y0+(y1-y0)*t)
        for dx,dy in ((0,0),(1,0),(0,1)):
            image.setXel(x+dx,y+dy,*color)


@lru_cache
def display(floor):
    image = PNMImage(256,128,3)
    image.fill(.073,.13,.158)
    for y in range(10,115):
        for x in range(8,247):
            if x < 60:
                color = (.095,.175,.205) if (y//14)%2 else (.087,.15,.18)
            elif x%20==0 or y%16==0:
                color = (.13,.21,.24)
            else:
                continue
            image.setXel(x,y,*color)
    for y in (20,35,51,63,79,93):
        trace_line(image,14,y,43+(y%8),y,(.34,.57,.60))
    if floor==3:
        points = ((72,100),(98,87),(119,93),(144,72),(161,81),(190,46),(212,58),(237,31))
        for first,last in zip(points,points[1:]):
            trace_line(image,*first,*last,(.35,.87,.77))
    else:
        for i,height in enumerate((29,61,44,73,49,82,62,90)):
            x = 77+20*i
            for row in range(108-height,108):
                for col in range(x,x+11):
                    image.setXel(col,row,.29+.032*i,.53+.022*i,.75)
    return texture('workstation display',image)


def ceiling(game):
    ceiling_panel = game.box((10,-10,3.72),(24,24,.22),(.88,.87,.82))
    material(ceiling_panel,'ceiling',(5,),(5,5))
    for y in (-17,-11,-5):
        game.box((10,y,3.53),(24,.21,.22),(.37,.39,.38))
        game.box((10,y,3.414),(24,.11,.020),(.68,.66,.60))
    for x in (3.1,10,16.9):
        for y in (-19,-13,-7,-2):
            game.box((x,y,3.57),(3.58,.42,.093),(.22,.24,.25))
            game.box((x,y,3.517),(3.45,.31,.033),(.73,.73,.68))
            game.box((x,y,3.493),(3.32,.235,.021),(.98,.94,.79))
    for x in (1.3,18.7):
        for y in (-16,-7):
            game.box((x,y,3.586),(.70,.44,.042),(.34,.37,.38))
            for i in range(7):
                game.box((x-.27+i*.09,y,3.56),(.036,.36,.015),(.59,.59,.55))


def divider(game,x,y):
    """Glazed and acoustically clad rooms inside the existing blocked cells."""
    from interiors import METAL, OAK, STONE, glass

    game.box((x,y,.036),(3.72,3.72,.071),(.40,.39,.35))
    game.box((x,y,2.92),(3.83,3.83,.17),(.34,.37,.37))
    for dx in (-1.81,1.81):
        for dy in (-1.81,1.81):
            game.box((x+dx,y+dy,1.45),(.098,.098,2.89),METAL)
    for offset in (-1.81,1.81):
        for z,height in ((.18,.34),(1.15,.060),(2.60,.072)):
            game.box((x+offset,y,z),(.072,3.64,height),METAL)
            game.box((x,y+offset,z),(3.64,.072,height),METAL)
        glass(game,(x+offset,y,1.88),(.020,3.57,1.39),(.56,.71,.73),.18)
        glass(game,(x,y+offset,1.88),(3.57,.020,1.39),(.56,.71,.73),.18)
        glass(game,(x+offset,y,.75),(.020,3.57,.74),(.65,.73,.73),.48)
        glass(game,(x,y+offset,.75),(3.57,.020,.74),(.65,.73,.73),.48)
    # The front pair of panels reads as a glass door.
    for dx in (-.59,0,.59):
        game.box((x+dx,y-1.86,1.47),(.050,.09,2.31),METAL)
    for dx in (-.12,.12):
        game.box((x+dx,y-1.92,1.07),(.033,.12,.27),(.62,.66,.66))
    game.box((x,y,2.79),(1.68,.17,.030),(.91,.90,.76))
    if game.floor == 2:
        rack(game,x-.84,y+.19)
        rack(game,x+.84,y+.19)
    else:
        top = game.box((x,y,.77),(2.15,.81,.09),OAK)
        material(top,'wood',(0,1,4))
        for dx in (-.77,.77):
            game.box((x+dx,y,.37),(.07,.60,.74),METAL)
        for dx,dy in ((-.58,-.61),(.58,-.61),(-.58,.61),(.58,.61)):
            game.box((x+dx,y+dy,.46),(.44,.46,.10),(.30,.42,.39))
            game.box((x+dx,y+dy+math.copysign(.23,dy),.67),(.43,.095,.48),(.30,.42,.39))
            game.box((x+dx,y+dy,.22),(.10,.25,.44),METAL)
        game.box((x-.37,y-.14,.824),(.31,.23,.025),STONE)


def rack(game,x,y):
    game.box((x,y,1.04),(.62,.69,2.08),(.19,.21,.22))
    panel = game.box((x,y-.352,1.03),(.54,.030,1.91),(.32,.35,.36))
    material(panel,'ceiling',(0,),(1,2))
    for row in range(7):
        z = .32+row*.218
        game.box((x,y-.374,z),(.48,.027,.128),(.19,.23,.24))
        game.box((x-.13,y-.393,z),(.19,.015,.025),(.35,.38,.36))
        game.box((x+.15,y-.393,z),(.026,.016,.025),(.31,.76,.50))


def reception(game):
    from interiors import METAL, OAK, STONE

    base = game.box((10,-8,.49),(4.64,1.53,.94),(.70,.67,.59))
    material(base,'stone',(0,1,2,3),(2,1))
    desk = game.box((10,-8,1.01),(4.96,1.70,.15),STONE)
    material(desk,'stone',(0,1,4),(2,1))
    game.box((10,-8.78,.18),(4.60,.08,.13),METAL)
    for x in (8.22,11.78):
        for index in range(10):
            game.box((x-.28+index*.065,-8.79,.53),(.039,.072,.62),OAK)
    game.box((10,-8.81,.65),(2.05,.064,.36),(.27,.33,.32))
    game.label('RECEPTION',(10,-8.856,.60),.20)
    for x in (8.82,11.18):
        game.box((x,-7.81,1.15),(.085,.095,.25),METAL)
        monitor = game.box((x,-7.81,1.41),(.73,.060,.44),(.22,.25,.26))
        monitor.setH(10 if x<10 else -10)
