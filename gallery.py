"""Four-storey daylight court and occupied perimeter rooms."""
from pathlib import Path
from platform_paths import panda_path
import math
from panda3d.core import AmbientLight, DirectionalLight
from interiors import desk, glass, planter, rounded, METAL, OAK, WALNUT
from levels import elevation

COURT = (23, 32, -17, -4)


def shared_court(game):
    root = game.render.attachNewNode('four-storey atrium')
    box = lambda pos, size, color: game.box(pos, size, color, root)
    box((27.5,-10.5,-.14),(10,14,.26),(.69,.68,.60))
    for x in (22.85,32.15):
        for y in (-17.15,-3.85):
            box((x,y,8.25),(.32,.32,16.5),(.44,.54,.55))
    for level in range(1,5):
        z=elevation(level)
        for x in (22.42,32.58):
            box((x,-10.5,z-.11),(1.18,15,.24),(.66,.65,.60))
        for y in (-17.56,-3.44):
            box((27.5,y,z-.11),(10,1.12,.24),(.66,.65,.60))
        if level==1:
            continue
        for x in (23,32):
            glass(game,(x,-10.5,z+.54),(.045,13,1.07),(.65,.83,.84),.28,parent=root)
            box((x,-10.5,z+1.08),(.065,13,.07),WALNUT)
        for y in (-17,-4):
            glass(game,(27.5,y,z+.54),(9,.045,1.07),(.65,.83,.84),.28,parent=root)
            box((27.5,y,z+1.08),(9,.065,.07),WALNUT)
        for x in (23,32):
            for y in (-17,-12.7,-8.3,-4):
                box((x,y,z+.54),(.045,.045,1.08),METAL)
    # Recessed wall behind the far galleries gives the lower floors depth.
    for level in range(4):
        z=elevation(level+1)
        box((36.2,-10.5,z+1.72),(.18,14,3.44),(.38,.44,.42))
        for i in range(26):
            box((36.07,-17+i*.52,z+1.72),(.09,.10,3.35),OAK)
        box((34.16,-10.5,z-.12),(4.2,14,.24),(.60,.60,.55))
        box((36.0,-10.5,z+3.30),(.13,13.7,.065),(.95,.85,.61))
    # The suspension frame meets the four atrium columns at its corners.
    for x in (22.85,32.15):
        box((x,-10.5,16.58),(.24,13.54,.24),METAL)
    for y in (-17.15,-3.85):
        box((27.5,y,16.58),(9.54,.24,.24),METAL)
    for i in range(7):
        x=25+(i%3)*2.15
        y=-15+i*1.42
        z=7.2+i*.83
        box((27.5,y,16.58),(9.54,.12,.18),METAL)
        box((x,y,16.43),(.16,.16,.14),METAL)
        bottom=z+.60
        box((x,y,(16.43+bottom)/2),(.038,.038,16.43-bottom),METAL)
        box((x,y,bottom),(.14,.14,.10),METAL)
        rounded(root,(x,y,z),(.76,.76,.64),(.95,.83,.60))
    enclosing_dome(game,root)
    for y in (-14,-8):
        box((27.5,y,.28),(3.6,.85,.56),OAK)
        for i in range(9):
            leaf=rounded(root,(26.12+i*.34,y,.94+.12*(i%3)),(.27,.31,1.22),(.20,.39,.26))
            leaf.setR((i%3-1)*14)
    root.flattenStrong()
    return root


def load_cast(game):
    model=game.loader.loadModel(panda_path(Path(__file__).with_name('assets')/'seated.bam.pz'))
    figures=[]
    for i in (1,2,3):
        figure=model.find(f'**/SM_Student_{i:02d}')
        if figure.isEmpty():
            raise ValueError('Missing seated figure '+str(i))
        figures.append(figure)
    return figures


def seated_person(game, parent, index, x, y, z, heading, scale=1):
    actor=parent.attachNewNode('seated student')
    actor.setPos(x,y,z)
    actor.setH(heading)
    actor.setScale(scale)
    # glTF +Z faces Panda -Y after conversion.
    mount=actor.attachNewNode('pose')
    mount.setH(180)
    figure = game.cast[index%len(game.cast)].copyTo(mount)
    # Colour only garments, leaving face and hair textures intact.
    palettes = ((.70,.83,1),(.85,.68,.58),(.65,.82,.69),(1,.87,.73),(.67,.68,.82))
    for part in figure.findAllMatches('**/+GeomNode'):
        node=part.node()
        from panda3d.core import ColorScaleAttrib, Vec4
        for n in range(node.getNumGeoms()):
            state=node.getGeomState(n)
            # Material names survive the glTF import.
            from panda3d.core import MaterialAttrib
            attr=state.getAttrib(MaterialAttrib)
            name=attr.getMaterial().getName().lower() if attr and attr.getMaterial() else ''
            if 'casual' in name:
                node.setGeomState(n,state.addAttrib(ColorScaleAttrib.make(Vec4(*palettes[index%5],1))))

    return actor


def cast_light(parent):
    ambient=AmbientLight('window fill')
    ambient.setColor((.43,.46,.49,1))
    parent.setLight(parent.attachNewNode(ambient))
    sun=DirectionalLight('window daylight')
    sun.setColor((.44,.41,.36,1))
    direction=parent.attachNewNode(sun)
    direction.setHpr(125,-38,0)
    parent.setLight(direction)


def occupied_rooms(game):
    if game.floor == 4:
        return
    group=game.world.attachNewNode('occupied perimeter')
    cast_light(group)
    for bay,x in enumerate((-2,6,14,22)):
        y=-29.5 if bay in (0,3) else -33
        game.box((x,y,.002),(5.6,4.2,.04),(.40,.46,.45))
        if game.floor in (2,3):
            desk(game,x,y,computers=True)
        else:
            game.box((x,y,.77),(3,.86,.10),OAK)
            for dx in (-1.2,1.2):
                game.box((x+dx,y,.38),(.14,.68,.76),METAL)
            game.obstacles.append((x,y,1.8,.78))
        # Furnish the far side of each bay according to the floor's activity.
        back=y-1.55
        if game.floor == 2:
            for dx in (-.48,.48):
                game.box((x+dx,back,.98),(.90,.59,1.96),(.19,.24,.26))
                for n in range(7):
                    game.box((x+dx,back+.31,.32+n*.23),(.74,.035,.15),(.32,.39,.40))
                    game.box((x+dx+.27,back+.338,.32+n*.23),(.045,.018,.033),(.32,.84,.67))
        elif game.floor == 3:
            for n in range(3):
                game.box((x,back,.38+n*.53),(3.16,.41,.075),OAK)
                for k in range(10):
                    game.box((x-1.27+k*.25,back,.59+n*.53),(.13+.02*(k%3),.27,.33+.04*(k%3)),
                             ((.28,.45,.43),(.59,.37,.26),(.73,.68,.52))[(k+bay+n)%3])
            for dx in (-1.55,1.55):
                game.box((x+dx,back,.91),(.08,.43,1.82),METAL)
        elif game.floor == 4:
            game.box((x,back,1.26),(3.35,.12,2.25),WALNUT)
            for k in range(4):
                px=x-1.20+k*.80
                game.box((px,back+.070,1.31),(.66,.02,1.64),(.83,.82,.73))
                for n in range(4):
                    game.box((px-.07*(n%2),back+.087,1.72-n*.23),(.50-.14*(n%2),.015,.065),
                             (.24,.45,.46) if n==0 else (.50,.53,.49))
        else:
            for k in range(3):
                px=x-.94+k*.94
                game.box((px,back,.43),(.80,.68,.86),(.66,.65,.60))
                rounded(game.world,(px,back,1.13),(.61,.59,.58),(.30,.54,.53))
                glass(game,(px,back,1.20),(.79,.66,.68),(.68,.85,.85),.13)
        game.obstacles.append((x,back,1.95,.64))
        for col,dx in enumerate((-.84,.84)):
            cy=y+1.02
            # Chairs and their occupants face the table.
            seat=game.world.attachNewNode('reading chair')
            game.box((0,0,.45),(.63,.56,.10),(.36,.44,.44),seat)
            game.box((0,.27,.76),(.63,.09,.58),(.36,.44,.44),seat)
            for sx in (-.23,.23):
                game.box((sx,0,.21),(.046,.45,.42),METAL,seat)
            seat.setPos(x+dx,cy,0)
            seated_person(game,group,bay*2+col+game.floor,x+dx,cy,0,180)
            game.obstacles.append((x+dx,cy,.60,.66))
        planter(game,x+2.35,y,.98)
        game.obstacles.append((x+2.35,y,.58,.58))
        game.box((x,y,3.62),(3.5,.23,.09),METAL)
        game.box((x,y,3.56),(3.42,.18,.035),(.98,.91,.77))


def enclosing_dome(game, root):
    """One continuous glazed envelope enclosing all four storeys."""
    from rotunda import surface
    # Full-height bowed walls meet the curved roof at a continuous spring ring.
    rings=[(31.6,0),(32.1,4.2),(32.4,8.4),(32.2,12.6),(31.6,18)]
    rings.extend((31.6*math.cos(i*math.pi/24),18+12*math.sin(i*math.pi/24)) for i in range(1,13))
    segments=72
    def point(radius,z,index):
        angle=index*math.tau/segments
        return (10+radius*math.cos(angle),-10+radius*math.sin(angle),z)
    def member(a,b,width):
        node=game.box(tuple((x+y)/2 for x,y in zip(a,b)),(width,math.dist(a,b),width),(.27,.40,.43),root)
        node.lookAt(*b)
    for row,((r0,z0),(r1,z1)) in enumerate(zip(rings,rings[1:])):
        quads=[]
        for col in range(segments):
            a,b=point(r0,z0,col),point(r0,z0,col+1)
            c,d=point(r1,z1,col+1),point(r1,z1,col)
            quads.append((a,b,c,d))
            member(a,b,.09)
            if col%3==0:
                member(a,d,.14)
        surface(root,'dome wall' if row<4 else 'dome roof',quads,
                (.49,.69,.74) if row<4 else (.64,.77,.79),.26 if row<4 else .62)
    # Vertical ties carry the suspension frame up to the dome's curved skin.
    for x in (22.85,32.15):
        for y in (-17.15,-3.85):
            radius=math.hypot(x-10,y+10)
            roof_z=18+12*math.sqrt(max(0,1-(radius/31.6)**2))
            angle=math.atan2(y+10,x-10)
            rib_angle=round(angle/(math.tau/24))*(math.tau/24)
            roof_x=10+radius*math.cos(rib_angle)
            roof_y=-10+radius*math.sin(rib_angle)
            member((x,y,16.58),(roof_x,roof_y,roof_z),.16)
