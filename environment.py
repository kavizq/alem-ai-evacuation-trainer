"""Baked daylight and the view beyond the glass facade."""
import math
import random

from panda3d.core import (
    AntialiasAttrib, Fog, Geom, GeomNode, GeomTriangles, GeomVertexData,
    GeomVertexFormat, GeomVertexWriter, NodePath, PNMImage, Texture,
)

from interiors import METAL, STONE, rounded


def texture_from_image(name, pixels):
    texture = Texture(name)
    texture.load(pixels)
    texture.generateRamMipmapImages()
    texture.setMinfilter(Texture.FTLinearMipmapLinear)
    texture.setAnisotropicDegree(4)
    return texture


def bake_floor(game):
    """Paint window light, frame shadows and soft contact shadows in world space."""
    if game.floor not in game.floor_textures:
        game.floor_textures[game.floor] = floor_texture(game)
    floor = NodePath(game.floor_card).copyTo(game.world)
    floor.setPos(10,-10.75,.004)
    floor.setP(-90)
    floor.setScale(24,1,22.5)
    floor.setTwoSided(True)
    floor.setTexture(game.floor_textures[game.floor])


def floor_texture(game):
    size = 512
    pixels = PNMImage(size, size, 3)
    rng = random.Random(331)
    tint = {4:(.61,.43,.27), 3:(.58,.60,.57), 2:(.48,.51,.50), 1:(.71,.68,.61)}[game.floor]
    step = 24 / size
    shadows = [0.] * (size * size)
    for ox, oy, rx, ry in game.obstacles:
        # The collision bounds include player clearance; contract them for shading.
        rx, ry = max(.17, rx-.32), max(.17, ry-.32)
        for row in range(max(0,int((2-oy-ry-.65)/step)), min(size,math.ceil((2-oy+ry+.65)/step))):
            y = 2-(row+.5)*step
            dy = max(0,abs(y-oy)-ry)
            for col in range(max(0,int((ox+2-rx-.65)/step)), min(size,math.ceil((ox+2+rx+.65)/step))):
                x = -2+(col+.5)*step
                dx = max(0,abs(x-ox)-rx)
                shade = .31 * math.exp(-10*(dx*dx+dy*dy))
                index = row*size+col
                shadows[index] = max(shadows[index], shade)
    for row in range(size):
        y = 2-(row+.5)*step
        for col in range(size):
            x = -2+(col+.5)*step
            window = (y + .46*(x+2) + 22) % 4
            frame = 1 - .36*math.exp(-((window-2)/.12)**2)
            daylight = .48*math.exp(-((x+2)/11)**2)*frame
            light = .80+daylight-shadows[row*size+col]
            noise = rng.uniform(-.042,.042)
            if game.floor == 4:
                plank = int((x+2)/.64)
                seam = min((x+2)%.64,.64-(x+2)%.64) < .032
                joint = (y + plank*1.73) % 4.6 < .052
                grain = math.sin(x*65+1.4*math.sin(y*2.1))*math.sin(x*31+y*.7)
                material = 1+.06*grain+.064*math.sin(plank*4.7)+noise
            else:
                seam = (x+2)%1.5 < .048
                joint = (y+.75*int((x+2)/1.5))%1.5 < .048
                material = 1 + noise + .038*math.sin(4*x+2*y)
                if rng.random() < .09:
                    material -= rng.uniform(.07,.19)
            if seam or joint:
                material *= .82
            warm = (1+.18*daylight, 1+.04*daylight, 1-.12*daylight)
            pixels.setXel(col,row,*(min(1,c*light*material*w) for c,w in zip(tint,warm)))
    return texture_from_image('baked floor', pixels)


def sky(parent):
    data = GeomVertexData('sky', GeomVertexFormat.getV3c4(), Geom.UHStatic)
    points = GeomVertexWriter(data,'vertex')
    colors = GeomVertexWriter(data,'color')
    triangles = GeomTriangles(Geom.UHStatic)
    bands = ((-.24,(.75,.73,.68)), (0,(.88,.82,.72)),
             (.13,(.67,.75,.79)), (.32,(.42,.61,.73)),
             (.65,(.27,.49,.65)), (1.55,(.21,.40,.58)))
    segments = 64
    sky_radius = 101
    for elevation, color in bands:
        for col in range(segments):
            azimuth = math.tau*col/segments
            radius = sky_radius*math.cos(elevation)
            points.addData3(10+radius*math.cos(azimuth),-10+radius*math.sin(azimuth),sky_radius*math.sin(elevation))
            glare = .22 * max(0,math.cos(azimuth-2.78))**10 * max(0,1-abs(elevation-.12))
            colors.addData4(*(min(1,value+glare*weight) for value,weight in zip(color,(1,.82,.56))),1)
    for row in range(len(bands)-1):
        for col in range(segments):
            a = row*segments+col
            b = row*segments+(col+1)%segments
            triangles.addVertices(a,b,a+segments)
            triangles.addVertices(b,b+segments,a+segments)
    geom = Geom(data)
    geom.addPrimitive(triangles)
    node = GeomNode('sky')
    node.addGeom(geom)
    dome = parent.attachNewNode(node)
    dome.setFogOff()
    dome.setTwoSided(True)
    dome.setDepthWrite(False)
    dome.setBin('background',0)


def facade_texture():
    pixels = PNMImage(64, 64, 3)
    for row in range(64):
        for col in range(64):
            if 5 <= col%16 < 13 and 5 <= row%16 < 14:
                color = (.49,.59,.62) if (col//16+row//16)%5 else (.67,.67,.58)
            else:
                color = (.85,.84,.78)
            pixels.setXel(col,row,*color)
    return texture_from_image('distant windows', pixels)


def build_surroundings(game):
    site = game.render.attachNewNode('campus surroundings')
    game.render.setAntialias(AntialiasAttrib.MMultisample)
    fog = Fog('distance haze')
    fog.setColor(.73,.77,.78)
    fog.setLinearRange(30,128)
    site.setFog(fog)
    sky(site)
    rng = random.Random(23)
    windows = facade_texture()
    game.box((10,-12,-.39),(280,280,.4),(.42,.43,.35),site)
    for index in range(34):
        angle = index*math.tau/34
        radius = rng.uniform(72,108)
        x = 10 + radius*math.cos(angle)
        y = -10 + radius*math.sin(angle)
        width, depth, height = rng.uniform(5,13), rng.uniform(5,12), rng.uniform(7,23)
        color = rng.choice(((.68,.68,.63),(.59,.63,.63),(.72,.71,.67)))
        building = game.box((x,y,height*.5),(width,depth,height),color,site)
        for face in range(4):
            building.getChild(face).setTexture(windows)
        game.box((x,y,height+.2),(width*.7,depth*.7,.45),color,site)
    for x in (-18,38):
        for y in (-48,-38,-28,-15,0,13,24):
            tree_x = x+rng.uniform(-2,2)
            height = rng.uniform(3.8,5.6)
            game.box((tree_x,y,height*.23),(.27,.27,height*.47),(.32,.24,.15),site)
            for dx,dy,z in ((0,0,.85),(-.9,.2,.64),(.87,-.4,.68),(0,1,.73)):
                color = rng.choice(((.29,.38,.21),(.40,.47,.23),(.34,.42,.21)))
                rounded(site,(tree_x+dx,y+dy,z*height),(2.7,2.6,height*.52),color)
    for x in (-8.4,28.4):
        game.box((x,-36,-.12),(1.1,32,.18),STONE,site)
        for y in (-47,-35,-24):
            game.box((x,y,1.46),(.08,.08,3.1),METAL,site)
            game.box((x,y,3.05),(.43,.26,.09),METAL,site)
    approach(game,site)
    site.flattenStrong()


def approach(game, site):
    """Landmarks close enough to judge the height from the upper windows."""
    asphalt = (.31,.34,.34)
    paving = (.62,.61,.56)
    court = game.box((10,19,-.125),(44,30,.12),paving,site)
    pixels = PNMImage(512,384,3)
    rng = random.Random(191)
    for row in range(384):
        for col in range(512):
            seam = row%18==0 or (col+(row//18%2)*12)%24==0
            grain = rng.uniform(-.04,.04)
            tile = .90 + .062*math.sin((row//18)*2.23+(col//24)*4.31)
            value = .73 if seam else tile+grain
            pixels.setXel(col,row,value,value,value)
    court.getChild(4).setTexture(texture_from_image('courtyard paving',pixels))
    game.box((10,46,-.12),(125,6,.13),(.60,.59,.54),site)
    game.box((10,38,-.13),(125,8,.09),asphalt,site)
    for y in (33.6,42.4):
        game.box((10,y,-.045),(126,.80,.23),STONE,site)
    for x in range(-46,69,6):
        game.box((x,38,-.079),(2.7,.12,.006),(.76,.73,.62),site)
    for x in (5.8,6.75,7.7,8.65,9.6,10.55):
        game.box((x,38,-.077),(.48,7.65,.007),(.79,.77,.69),site)
    for x,y,color in ((-6,36,(.70,.72,.69)),(22,40,(.27,.36,.44)),
                      (34,36,(.54,.27,.20)),(-23,40,(.41,.47,.43))):
        car = site.attachNewNode('car')
        car.setPos(x,y,0)
        car.setH(180 if y > 38 else 0)
        game.box((0,0,.43),(4.42,1.74,.60),color,car)
        game.box((-.18,0,.92),(2.32,1.50,.51),color,car)
        for side in (-1,1):
            game.box((-.25,side*.758,.94),(1.76,.024,.30),(.16,.24,.28),car)
            for wheel in (-1.48,1.48):
                rounded(car,(wheel,side*.83,.25),(.59,.21,.57),(.12,.14,.14))
        game.box((2.216,0,.57),(.025,1.46,.14),(.84,.83,.70),car)
    for x in (-9.8,29.8):
        for y in (12,20,28):
            game.box((x,y,.06),(2.7,4.12,.31),STONE,site)
            game.box((x,y,.23),(2.52,3.94,.07),(.37,.41,.26),site)
            game.box((x,y,1.11),(.16,.16,1.91),(.35,.27,.17),site)
            rounded(site,(x,y,2.23),(1.74,1.6,2.7),(.36,.46,.24))
            game.box((x+(1.75 if x<10 else -1.75),y,.32),(.44,1.83,.18),(.59,.43,.25),site)
    for x in (-14,34):
        for y in (9,18,27):
            game.box((x,y,1.82),(.10,.10,3.77),METAL,site)
            game.box((x,y,3.67),(.58,.26,.10),METAL,site)
    for x in (-15,35):
        game.box((x,48,1.32),(9.75,4.1,2.68),(.38,.43,.42),site)
        game.box((x,47.68,2.69),(10.08,5.17,.22),(.55,.56,.53),site)
        for offset in (-3.86,-1.92,0,1.92,3.86):
            game.box((x+offset,45.91,1.51),(1.79,.085,1.85),(.28,.39,.42),site)
    for x in (2.3,17.7):
        for y in (9,14,19,24,29):
            game.box((x,y,.19),(.14,.14,.53),METAL,site)
    for x in (-5,25):
        game.box((x,11,-.050),(9.8,.07,.011),(.46,.46,.42),site)
        game.box((x,24,-.050),(9.8,.07,.011),(.46,.46,.42),site)


def lower_terraces(game):
    """Show the occupied building volume below the current north overlook."""
    from levels import FLOOR_SPACING, elevation
    from interiors import glass

    for floor in range(1, game.floor):
        z = elevation(floor)-elevation(game.floor)
        edge = {1:10.8,2:8.8,3:6.8}[floor]
        length = edge-1.65
        game.box((10,edge-length/2,z-.12),(15.35,length,.36),STONE)
        game.box((10,edge,z+.86),(15.35,.12,.08),METAL)
        for x in (2.35,17.65):
            game.box((x,edge-length/2,z+.86),(.10,length,.08),METAL)
            glass(game,(x,edge-length/2,z+.45),(.035,length,.78),(.61,.73,.75),.23)
        game.box((10,1.83,z+FLOOR_SPACING*.48),(15.4,.12,FLOOR_SPACING-.36),(.42,.49,.50))
        glass(game,(10,edge,z+.45),(15.23,.037,.78),(.61,.73,.75),.28)
        for x in (2.35,6.18,10,13.82,17.65):
            game.box((x,edge-.02,z+.46),(.095,.09,.91),METAL)
            game.box((x,1.75,z+FLOOR_SPACING*.51),(.12,.14,FLOOR_SPACING-.1),METAL)
        for x in (4.15,15.85):
            game.box((x,edge-1.12,z+.26),(1.3,.61,.52),(.49,.49,.43))
            rounded(game.world,(x,edge-1.12,z+.62),(1.18,.66,.41),(.34,.44,.24))
