"""Fixed-function meshes and furnishings for the four campaign interiors."""
import math

from panda3d.core import (
    Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat,
    GeomVertexWriter, TransparencyAttrib, NodePath,
)

from finishes import ceiling, display, material, reception

OAK = (.61, .41, .24)
WALNUT = (.36, .23, .15)
STONE = (.78, .76, .70)
METAL = (.19, .22, .23)
GREEN = (.21, .39, .30)
TEAL = (.10, .43, .45)


def rounded_mesh():
    """Shared shaded ellipsoid with a neutral baked light direction."""
    data = GeomVertexData('rounded furnishing', GeomVertexFormat.getV3c4(), Geom.UHStatic)
    vertex = GeomVertexWriter(data, 'vertex')
    color = GeomVertexWriter(data, 'color')
    indices = GeomTriangles(Geom.UHStatic)
    rings, segments = 10, 16
    for row in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * row / rings
        for col in range(segments):
            longitude = math.tau * col / segments
            x = math.cos(latitude) * math.cos(longitude)
            y = math.cos(latitude) * math.sin(longitude)
            z = math.sin(latitude)
            vertex.addData3(x * .5, y * .5, z * .5)
            light = .70 + .28 * max(0, -.32*x - .44*y + .84*z)
            color.addData4(light, light, light, 1)
    for row in range(rings):
        for col in range(segments):
            a = row * segments + col
            b = row * segments + (col + 1) % segments
            indices.addVertices(a, b, a + segments)
            indices.addVertices(b, b + segments, a + segments)
    geometry = Geom(data)
    geometry.addPrimitive(indices)
    node = GeomNode('rounded form')
    node.addGeom(geometry)
    return node


ROUNDED = rounded_mesh()


def rounded(parent, position, size, rgb):
    shape = parent.attachNewNode('shape')
    NodePath(ROUNDED).copyTo(shape)
    shape.setPos(*position)
    shape.setScale(*size)
    shape.setColorScale(*rgb, 1)
    return shape


def glass(game, position, size, color=(.49, .70, .73), alpha=.15, parent=None):
    pane = game.box(position, size, color, parent)
    pane.setColor(*color, alpha)
    # A thin panel needs one two-sided surface. Extra faces darken overlapping glass.
    if min(size) < .15 and min(size) != size[2]:
        face = 2 if size[0] < size[1] else 0
        for index, side in enumerate(pane.getChildren()):
            if index != face:
                side.hide()
    pane.setTransparency(TransparencyAttrib.MAlpha)
    pane.setDepthWrite(False)
    return pane


def desk(game, x, y, computers, lecture=False):
    length = 2.0 if lecture else 2.35
    top = game.box((x, y, .77), (length, .90, .085), OAK)
    material(top,'wood',(0,1,4))
    game.box((x,y-.454,.77),(length,.013,.062),WALNUT)
    game.box((x,y+.26,.64),(length*.83,.065,.19),(.38,.34,.28))
    for dx in (-length*.40, length*.40):
        game.box((x+dx,y,.37), (.075,.71,.74), METAL)
        game.box((x+dx,y,.025), (.15,.76,.05), METAL)
    chair(game, x-.52, y-.55)
    if lecture:
        chair(game, x+.52, y-.55)
        game.box((x+.40,y,.824), (.38,.27,.022), (.84,.79,.67))
        game.box((x-.50,y-.10,.83), (.28,.20,.035), TEAL)
        for offset in (-.08,-.04,0,.04):
            game.box((x+.38,y+offset,.837),(.24,.009,.005),(.55,.52,.44))
        pen = game.box((x+.66,y+.02,.836),(.018,.21,.018),METAL)
        pen.setH(14)
    if computers:
        for dx in (-.55,.55):
            game.box((x+dx,y+.19,.82), (.38,.27,.035), METAL)
            game.box((x+dx,y+.23,1.03), (.075,.09,.42), METAL)
            game.box((x+dx,y+.23,1.26), (.92,.075,.54), METAL)
            screen = game.box((x+dx,y+.184,1.26),(.85,.013,.47),(.97,.98,.98))
            screen.getChild(0).setTexture(display(game.floor))
            game.box((x+dx,y-.19,.83), (.49,.18,.026), METAL)
            for row in range(3):
                game.box((x+dx-.028,y-.24+.043*row,.846),(.35,.020,.005),(.40,.42,.41))
            game.box((x+dx+.38,y+.05,.88),(.11,.11,.12),(.72,.69,.61))
            rounded(game.world,(x+dx+.34,y-.18,.841),(.105,.16,.05),METAL)
        chair(game, x+.55, y-.55)
    game.obstacles.append((x,y-.24,length/2+.29,1.02))


def chair(game, x, y):
    upholstery=(.46,.53,.53)
    rounded(game.world,(x,y,.47),(.57,.55,.11),upholstery)
    back=rounded(game.world,(x,y-.24,.79),(.53,.10,.58),upholstery)
    back.setP(-7)
    rounded(game.world,(x,y-.28,1.15),(.30,.11,.19),upholstery)
    for side in (-1,1):
        game.box((x+side*.29,y-.02,.68),(.065,.34,.055),METAL)
        game.box((x+side*.27,y-.15,.57),(.045,.045,.22),METAL)
        game.box((x+side*.245,y-.28,.78),(.027,.035,.45),METAL)
    game.box((x,y,.26),(.065,.065,.37),(.48,.53,.54))
    for i in range(5):
        angle=i*math.tau/5
        foot=game.box((x+.15*math.sin(angle),y+.15*math.cos(angle),.085),(.045,.34,.042),METAL)
        foot.setH(-math.degrees(angle))
        rounded(game.world,(x+.29*math.sin(angle),y+.29*math.cos(angle),.046),(.10,.10,.09),(.13,.15,.15))


def planter(game, x, y, size=1, base=0):
    rounded(game.world,(x,y,base+.28*size),(.75*size,.75*size,.63*size),(.43,.30,.21))
    rounded(game.world,(x,y,base+.51*size),(.69*size,.69*size,.08*size),WALNUT)
    for index in range(7):
        angle = index * math.tau / 7
        leaf = rounded(game.world,
                       (x+math.sin(angle)*.22*size,y+math.cos(angle)*.22*size,base+(.80+.1*(index%3))*size),
                       (.22*size,.65*size,.085*size),
                       (.18+.025*(index%3),.34+.05*(index%3),.18))
        leaf.setHpr(-math.degrees(angle), 39+index%3*10, 0)


def architecture(game):
    if game.floor == 1:
        for y in (-12,-5):
            for x in (-1.35,21.35):
                rounded(game.world,(x,y,6.3),(.32,.32,12.6),STONE)
        for z in (4.2,8.4,12.6):
            for x in (-.1,20.1):
                game.box((x,-10,z),(3.5,23,.21),STONE)
                edge=x+1.75 if x<10 else x-1.75
                game.box((edge,-10,z+.95),(.07,23,.07),METAL)
                glass(game,(edge,-10,z+.49),(.035,23,.87))
            game.box((10,-20.7,z),(19,2.0,.21),STONE)
        reception(game)
        for x in (8.1,11.9):
            planter(game,x,-7.12,.82,base=1.08)
        for x in (3.2,16.8):
            game.box((x,-9,.38),(1.55,3.0,.43),WALNUT)
            rounded(game.world,(x,-9,.65),(1.45,2.85,.35),GREEN)
            game.obstacles.append((x,-9,1.0,1.75))
        game.box((10,-8,12.54),(19.9,.18,.17),METAL)
        for x in (7.9,10,12.1):
            game.box((x,-8,8.45),(.025,.025,8.3),METAL)
            rounded(game.world,(x,-8,4.30),(.75,.75,.28),(.93,.85,.62))
            rounded(game.world,(x,-8,4.43),(.75,.75,.17),METAL)
        game.box((10,-8,3.68),(3.5,.14,.56),(.27,.34,.33))
        for x in (8.65,11.35):
            game.box((x,-8,8.22),(.026,.026,8.58),METAL)
        game.label('GLASS ATRIUM',(10,-8.082,3.60),.30)
    elif game.floor == 4:
        # Leave a physical gap between the teaching area and the meeting pod.
        x = 7.55
        platform = game.box((x,-2.94,.115),(4.77,1.55,.23),OAK)
        material(platform,'wood',(0,4))
        backing = game.box((x,-2.08,1.79),(4.83,.24,3.42),(.58,.43,.29))
        material(backing,'wood',(0,1),(1,2))
        for offset in (-2.30,-2.17,2.17,2.30):
            game.box((x+offset,-2.225,1.76),(.058,.11,3.2),WALNUT)
        game.box((x,-2.42,3.19),(4.30,.21,.057),METAL)
        game.box((x,-2.51,3.16),(4.18,.025,.024),(.98,.91,.72))
        game.box((x,-2.5,2.0),(4.37,.22,2.23),WALNUT)
        game.box((x,-2.63,2.02),(4.18,.045,2.0),(.13,.22,.20))
        game.obstacles.append((x,-2.5,2.70,.45))
        game.label('QAIRU CLASSROOM',(x,-2.68,2.62),.29)
        game.label('A*  /  BAYES  /  MDP',(x,-2.68,1.93),.24)
        game.label('f(n) = g(n) + h(n)',(x,-2.68,1.42),.19)
        game.box((x,-2.80,.94),(4.12,.29,.05),METAL)
        game.box((x-.99,-2.84,.99),(.22,.06,.04),(.87,.84,.73))
        game.box((5.93,-3.55,.65),(.64,.57,1.08),WALNUT)
        game.box((5.93,-3.55,1.22),(.84,.75,.08),OAK)
        game.obstacles.append((5.93,-3.55,.58,.56))
    elif game.floor == 3:
        plinth = game.box((9.4,-6.1,.42),(3.4,1.06,.52),WALNUT)
        material(plinth,'wood',(0,1,2,3))
        for x in (8.35,9.4,10.45):
            cushion = game.box((x,-6.1,.64),(.98,.89,.22),(.30,.43,.38))
            material(cushion,'fabric',(0,4))
        rounded(game.world,(9.4,-5.68,1.03),(3.30,.22,.65),GREEN)
        game.obstacles.append((9.4,-6.1,1.99,.84))
    else:
        game.box((9.3,-5.2,.62),(2.8,.62,1.18),METAL)
        for dx in (-.91,0,.91):
            game.box((9.3+dx,-5.53,.64),(.82,.058,1.04),(.37,.41,.43))
            game.box((9.3+dx,-5.57,.84),(.24,.04,.045),(.78,.72,.59))
        game.obstacles.append((9.3,-5.2,1.69,.61))
    for x in (3.6,16.4):
        planter(game,x,-20.5)
        game.obstacles.append((x,-20.5,.66,.66))

