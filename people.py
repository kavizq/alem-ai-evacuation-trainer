"""Student meshes and clothing for the existing four-pivot walk cycle."""
import math

from panda3d.core import (
    CardMaker, Geom, GeomNode, GeomTriangles, GeomVertexData, GeomVertexFormat,
    GeomVertexWriter, PNMImage, Texture, TransparencyAttrib,
)
from interiors import rounded
from finishes import finish
from gait import HIP, SHIN, THIGH, StudentGait


def contact_shadow():
    image = PNMImage(48,48,4)
    for y in range(48):
        for x in range(48):
            distance = ((x-23.5)/23.5)**2+((y-23.5)/23.5)**2
            image.setXelA(x,y,.12,.13,.13,.48*max(0,math.exp(-3.9*distance)-.03))
    texture = Texture('student contact shadow')
    texture.load(image)
    return texture


SHADOW = contact_shadow()
SHADOW_CARD = CardMaker('contact shadow')
SHADOW_CARD.setFrame(-.31,.31,-.28,.28)
SHADOW_GEOMETRY = SHADOW_CARD.generate()


def loft(parent, name, rings, color, sides=24):
    """Build a smooth form from elliptical sections, including its end caps."""
    data = GeomVertexData(name, GeomVertexFormat.getV3c4t2(), Geom.UHStatic)
    points = GeomVertexWriter(data, 'vertex')
    colors = GeomVertexWriter(data, 'color')
    uv = GeomVertexWriter(data, 'texcoord')
    triangles = GeomTriangles(Geom.UHStatic)
    sections = [(rings[0][0],.001,.001,rings[0][3]), *rings,
                (rings[-1][0],.001,.001,rings[-1][3])]
    for row, (z, rx, ry, cy) in enumerate(sections):
        for col in range(sides):
            angle = col * math.tau / sides
            x, y = math.cos(angle), math.sin(angle)
            points.addData3(rx*x, cy+ry*y, z)
            uv.addData2(col/sides,z*3)
            light = .72+.27*max(0,-.52*x+.82*y)+.07*row/(len(sections)-1)
            colors.addData4(*(min(1,c*light) for c in color),1)
    for row in range(len(sections)-1):
        for col in range(sides):
            a = row*sides+col
            b = row*sides+(col+1)%sides
            triangles.addVertices(a,b,a+sides)
            triangles.addVertices(b,b+sides,a+sides)
    geometry = Geom(data)
    geometry.addPrimitive(triangles)
    node = GeomNode(name)
    node.addGeom(geometry)
    result = parent.attachNewNode(node)
    if name in ('garment','sleeve','trousers','scarf'):
        result.setTexture(finish('fabric'))
    return result


def face(head, skin, hair, style):
    loft(head,'face',[
        (1.438,.038,.043,.037),(1.466,.065,.063,.020),
        (1.512,.079,.074,.010),(1.552,.083,.076,.004),
        (1.605,.080,.074,-.003),(1.650,.049,.050,-.007)],skin,24)
    for x in (-.081,.081):
        rounded(head,(x,.000,1.535),(.032,.040,.063),skin)
    # Subtle cheek, eyelid and chin volumes keep features integrated with the head.
    for side in (-1,1):
        rounded(head,(side*.036,.075,1.566),(.044,.017,.013),skin)
        rounded(head,(side*.036,.073,1.546),(.043,.015,.008),skin)
        rounded(head,(side*.086,.012,1.535),(.016,.022,.037),tuple(c*.80 for c in skin))
    rounded(head,(0,.060,1.470),(.065,.030,.031),skin)
    nose = tuple(min(1,c*1.07) for c in skin)
    loft(head,'nose',[(1.516,.017,.012,.078),(1.530,.020,.024,.083),
                     (1.550,.010,.012,.083),(1.571,.008,.006,.077)],nose)
    rounded(head,(0,.081,1.488),(.046,.008,.007),(.66*skin[0],.57*skin[1],.57*skin[2]))
    for side in (-1,1):
        x = side*.035
        rounded(head,(x,.076,1.555),(.030,.011,.012),(.72,.70,.66))
        rounded(head,(x,.083,1.555),(.012,.008,.012),(.13,.09,.06))
        rounded(head,(x,.075,1.573),(.041,.012,.009),hair)
    if style in (2,4):
        loft(head,'long hair',[(1.36,.074,.048,-.045),(1.45,.088,.054,-.048),
                             (1.54,.096,.069,-.041),(1.65,.066,.064,-.023)],hair)
    elif style == 1:
        rounded(head,(0,-.085,1.617),(.122,.094,.101),hair)
    loft(head,'hair cap',[(1.586,.084,.079,-.014),(1.62,.087,.080,-.010),
                          (1.660,.065,.065,-.012),(1.678,.026,.038,-.015)],hair,24)
    if style in (0,3,5):
        fringe = rounded(head,(-.035,.055,1.605),(.101,.071,.044),hair)
        fringe.setR(-20 if style != 5 else 16)
    for i in range(11):
        strand=rounded(head,(-.069+i*.013,-.005,1.650+ .012*math.sin(i*.4)),
                       (.016,.116,.039),tuple(min(1,c*(.85+.025*i)) for c in hair))
        strand.setR(-12)
    if style == 4:
        for x in (-.038,.038):
            for z in (1.540,1.571):
                rounded(head,(x,.087,z),(.049,.012,.008),(.10,.09,.075))
            for dx in (-.023,.023):
                rounded(head,(x+dx,.086,1.556),(.009,.011,.030),(.10,.09,.075))
        rounded(head,(0,.093,1.555),(.032,.011,.008),(.10,.09,.075))


# Hoodie, puffer jacket, long coat, denim jacket, blazer, sweater and scarf.
OUTFITS = (
    ((.24,.32,.26),(.24,.28,.35),(.81,.79,.71),(.76,.55,.38),(.10,.075,.05),1.06,1.08),
    ((.57,.24,.18),(.18,.21,.24),(.24,.24,.24),(.56,.36,.25),(.10,.08,.05),.96,.96),
    ((.65,.48,.32),(.30,.32,.37),(.21,.18,.17),(.78,.58,.45),(.27,.15,.09),1.02,.92),
    ((.27,.40,.53),(.21,.24,.30),(.77,.74,.64),(.70,.49,.32),(.18,.12,.08),1.10,1.02),
    ((.23,.27,.35),(.27,.27,.30),(.82,.77,.65),(.80,.65,.53),(.27,.18,.12),.94,.93),
    ((.68,.57,.39),(.32,.34,.31),(.38,.20,.22),(.60,.42,.31),(.13,.10,.08),1.00,1.08),
)


def student(game, index, seated=False):
    jacket, trousers, accent, skin, hair, height, width = OUTFITS[index]
    root = game.world.attachNewNode('student')
    if not seated:
        shadow = root.attachNewNode('shadow position')
        shadow.setZ(.013)
        shadow.setP(-90)
        plane = shadow.attachNewNode(SHADOW_GEOMETRY)
        shadow.setTexture(SHADOW)
        shadow.setTransparency(TransparencyAttrib.MAlpha)
        shadow.setDepthWrite(False)
        plane.setTwoSided(True)
    rig = root.attachNewNode('body')
    rig.setScale(width,width,height)
    if seated:
        rig.setZ(.53-.88*height)
    torso = rig.attachNewNode('clothing')
    hem = .84 if index != 2 else .68
    loft(torso,'garment',[(hem,.158,.094,-.01),(.93,.157,.103,-.015),
                          (1.09,.150,.100,-.009),(1.25,.202,.112,-.014),
                          (1.33,.157,.085,-.012),(1.376,.071,.067,0)],jacket)
    loft(torso,'neck',[(1.32,.060,.054,0),(1.447,.051,.048,.014)],skin)
    if index in (0,1):
        rounded(torso,(0,-.078,1.336),(.265,.145,.197),jacket)
    if index == 1:
        for z in (.94,1.04,1.14,1.24):
            loft(torso,'quilt stitching',[(z,.174,.108,-.011),(z+.012,.174,.108,-.011)],
                 (.44,.18,.135))
    if index in (0,1,3):
        rounded(torso,(0,.093,1.11),(.016,.012,.40),accent)
    if index in (2,4):
        for side in (-1,1):
            lapel = rounded(torso,(side*.058,.080,1.239),(.075,.047,.239),accent)
            lapel.setR(side*26)
        for z in (.94,1.03,1.12):
            rounded(torso,(0,.101,z),(.020,.017,.020),accent)
    if index == 5:
        loft(torso,'scarf',[(1.329,.088,.072,0),(1.365,.092,.074,0),(1.405,.076,.068,0)],accent)
        rounded(torso,(.045,.108,1.219),(.096,.040,.288),accent)
    if index in (0,3):
        for side in (-1,1):
            rounded(torso,(side*.119,.088,1.08),(.026,.020,.27),tuple(c*.72 for c in jacket))
        rounded(torso,(0,-.132,1.08),(.33,.18,.46),(.26,.25,.21))
    torso.flattenStrong()

    head = rig.attachNewNode('head')
    head.setZ(1.55)
    head.setH((-7,4,0,-8,8,3)[index])
    head.setScale((1.02,.96,.90,1.05,.94,1.08)[index],1,
                  (.97,1.02,1.07,1.01,.96,.92)[index])
    features = head.attachNewNode('features')
    features.setZ(-1.55)
    face(features,skin,hair,index)
    head.flattenStrong()

    legs = []
    shoulders = []
    shoe = (.15,.16,.17) if index % 2 else (.42,.39,.33)
    for x in (-.083,.083):
        hip = rig.attachNewNode('hip')
        hip.setPos(x,-.014,.88)
        if seated:
            thigh = hip.attachNewNode('bent thigh')
            thigh.setP(87)
            loft(thigh,'trousers',[(-.41,.064,.064,0),(-.24,.072,.075,0),
                                   (0,.081,.082,0),(.045,.081,.079,0)],trousers)
            shin = hip.attachNewNode('shin')
            shin.setY(.39)
            loft(shin,'trousers',[(-.48,.043,.045,0),(-.33,.052,.054,-.018),
                                  (-.14,.058,.060,-.012),(0,.063,.063,0)],trousers)
            loft(shin,'shoe',[(-.53,.055,.121,.061),(-.49,.055,.115,.061),
                              (-.43,.045,.072,.028)],shoe)
            hip.flattenStrong()
        else:
            hip.setZ(HIP)
            upper = hip.attachNewNode('thigh mesh')
            loft(upper,'trousers',[(-THIGH-.027,.060,.064,0),(-.27,.069,.071,-.010),
                                   (-.10,.081,.080,0),(.045,.084,.083,0)],trousers)
            knee = hip.attachNewNode('knee')
            knee.setZ(-THIGH)
            lower = knee.attachNewNode('shin mesh')
            loft(lower,'trousers',[(-SHIN+.009,.045,.051,0),(-.25,.051,.057,-.008),
                                   (-.10,.057,.060,0),(.042,.061,.063,0)],trousers)
            ankle = knee.attachNewNode('ankle')
            ankle.setZ(-SHIN)
            loft(ankle,'shoe',[(-.065,.055,.116,.054),(-.045,.055,.116,.054),
                               (.032,.045,.067,.020)],shoe)
            legs.append((hip,knee,ankle))
    for side in (-1,1):
        shoulder = rig.attachNewNode('shoulder')
        shoulder.setPos(side*.188,-.012,1.287)
        if seated:
            shoulder.setP(34 if side < 0 else 23)
        arm = shoulder.attachNewNode('sleeve')
        arm.setR(-side*9)
        loft(arm,'sleeve',[(-.255,.043,.047,0),(-.15,.055,.059,0),
                           (-.035,.070,.070,0),(.044,.053,.055,0)],jacket)
        elbow=arm.attachNewNode('elbow')
        elbow.setZ(-.25)
        elbow.setP(64 if seated else 12)
        loft(elbow,'sleeve',[(-.225,.033,.035,0),(-.12,.043,.044,0),(.022,.046,.047,0)],jacket)
        loft(elbow,'cuff',[(-.235,.035,.037,0),(-.210,.035,.037,0)],tuple(c*.78 for c in jacket))
        rounded(elbow,(0,0,-.273),(.065,.039,.082),skin)
        for finger in range(4):
            rounded(elbow,(-.023+finger*.015,.002,-.324+abs(1.5-finger)*.008),
                    (.013,.025,.067-abs(1.5-finger)*.006),skin)
        thumb=rounded(elbow,(-side*.035,.010,-.275),(.023,.030,.065),skin)
        thumb.setR(side*24)
        arm.flattenStrong()
        shoulders.append(shoulder)
    gait = None if seated else StudentGait(rig,torso,legs,shoulders,width)
    if gait is not None:
        gait.reset()
    return root, gait
