"""The seated opening sequence, staged separately from the evacuation map."""
import math
import random

from panda3d.core import PNMImage, TextNode

from environment import texture_from_image

from interiors import METAL, OAK, STONE, WALNUT, glass
from people import student
from gallery import seated_person, cast_light
from levels import elevation


ROOM_Y = -17

PLAYER_SEAT = (2.35,-11.05,1.34)
DURATION = 32
START = (PLAYER_SEAT,(8.8,-2.35,1.88))
SIDE = ((1.70,-11.15,1.72),(9.8,-10.20,1.46))
WIDE = ((-.50,-11.95,4.12),(9.30,-10.10,1.22))
FRONT = ((.70,-3.00,3.58),(8.9,-10.63,1.24))
REAR = ((1.45,-15.55,3.35),(9.4,-6.70,1.34))


def shot(time):
    """Interpolate both the camera and its point of attention."""
    keyframes = ((0,START),(3.6,START),(8.4,SIDE),(15,WIDE),
                 (21.5,FRONT),(24.5,REAR),(28,START),(31.5,START),(DURATION,START))
    for (t0, first),(t1, last) in zip(keyframes,keyframes[1:]):
        if time <= t1:
            u = max(0,(time-t0)/(t1-t0))
            u = u*u*(3-2*u)
            return tuple(tuple(a+(b-a)*u for a,b in zip(v,w)) for v,w in zip(first,last))
    return START


def label(parent, text, position, scale, color, align=TextNode.ACenter):
    node = TextNode('lecture display')
    node.setText(text)
    node.setAlign(align)
    sign = parent.attachNewNode(node)
    sign.setPos(*position)
    sign.setScale(scale)
    sign.setColor(*color,1)
    return sign


def material_textures():
    rng = random.Random(404)
    wood, fabric = PNMImage(128,64,3), PNMImage(128,64,3)
    for y in range(64):
        for x in range(128):
            grain = math.sin(y*.48+1.5*math.sin(x*.024))*math.sin(y*1.76+x*.024)
            tone = .88+.08*grain+rng.uniform(-.028,.028)
            wood.setXel(x,y,tone,tone,tone)
            tone = .91 + rng.uniform(-.072,.043) - (.07 if (x+y)%5 == 0 else 0)
            fabric.setXel(x,y,tone,tone,tone)
    return texture_from_image('lecture oak grain',wood), texture_from_image('lecture seat fabric',fabric)


def seat(game, room, x, y, z, style, wood, fabric):
    upholstery = ((.24,.31,.30),(.27,.34,.34),(.30,.36,.34))[style%3]
    game.box((x,y,.435+z),(.62,.55,.105),upholstery,room)
    back = game.box((x,y-.28,.74+z),(.62,.12,.58),upholstery,room)
    back.setP(-8)
    back.getChild(0).setTexture(fabric)
    back.getChild(1).setTexture(fabric)
    for dx in (-.24,.24):
        game.box((x+dx,y,.214+z),(.051,.43,.42),METAL,room)
        game.box((x+dx,y+.70,.36+z),(.055,.27,.72),METAL,room)
    tabletop = game.box((x,y+.70,.765+z),(.91,.53,.068),OAK,room)
    tabletop.getChild(4).setTexture(wood)
    game.box((x,y+.43,.765+z),(.91,.022,.068),WALNUT,room)
    if style%8 == 1:
        game.box((x+.045,y+.694,.806+z),(.30,.235,.022),METAL,room)
        screen = game.box((x+.045,y+.801,.924+z),(.30,.020,.224),METAL,room)
        screen.setP(-13)
        game.box((x+.046,y+.786,.926+z),(.275,.011,.197),(.27,.39,.42),room).setP(-13)
    elif style%4 != 1:
        paper = game.box((x+.07,y+.66,.81+z),(.25,.24,.016),(.85,.83,.73),room)
        paper.setH(-8 if style%2 else 6)
        game.box((x-.104,y+.68,.817+z),(.012,.177,.011),METAL,room)


def lecture_room(game):
    lecture = game.world.attachNewNode('Qairu lecture hall')
    lecture.setY(ROOM_Y)
    room = lecture.attachNewNode('interior')
    wood, fabric = material_textures()
    box = lambda pos, size, color: game.box(pos,size,color,room)
    box((8.3,-8.5,-.22),(20,20,.42),(.37,.38,.34))
    box((8.3,-8.5,4.15),(20,20,.24),(.67,.66,.61))
    for left,right in ((-1.7,-.9),(1.3,15.6),(17.9,18.4)):
        box(((left+right)/2,1.34,2.53),(right-left,.22,5.06),(.48,.47,.42))
        game.obstacles.append(((left+right)/2,ROOM_Y+1.34,(right-left)/2+.25,.35))
    for x in (.2,16.78):
        box((x,1.34,3.95),(2.2,.22,2.2),(.48,.47,.42))
    game.obstacles.extend([(-1.57,ROOM_Y-8.5,.35,10),(18.30,ROOM_Y-8.5,.35,10),
                           (8.3,ROOM_Y-18.4,10.2,.35),(8.5,ROOM_Y-1.6,6.8,.45),
                           (4.1,ROOM_Y-2.55,.7,.65)])

    box((8.3,-18.4,2.53),(20,.22,5.06),(.45,.44,.39))
    for x in range(0,18,2):
        acoustic = box((x,-18.24,2.77),(1.91,.10,2.32),(.34,.39,.37))
        acoustic.getChild(1).setTexture(fabric)
        box((x,-18.16,3.98),(1.91,.08,.045),OAK)
    box((18.30,-8.5,.46),(.22,20,.92),(.47,.39,.30))
    box((18.30,-8.5,4.78),(.22,20,.55),(.47,.39,.30))
    for y in (-16.2,-12.4,-8.6,-4.8,-1.0):
        glass(game,(18.30,y,2.72),(.027,3.73,3.62),(.61,.72,.74),.12,parent=room)
        box((18.27,y-1.9,2.73),(.16,.10,3.65),METAL)
    for z in (1.00,4.52):
        box((18.21,-8.5,z),(.17,20,.085),METAL)
    for y in range(-17,1):
        box((18.15,y,.46),(.14,.15,.87),WALNUT)
    for y in (-16,-13,-10,-7,-4,-1):
        glass(game,(-1.57,y,2.73),(.036,2.85,3.98),(.56,.67,.68),.18, parent=room)
        box((-1.57,y+1.48,2.70),(.13,.13,4.10),METAL)
    for z in (.66,2.12,4.74):
        box((-1.57,-8.5,z),(.15,19.8,.12),METAL)
    box((-1.57,-8.5,.27),(.14,19.8,.54),STONE)

    for x in range(0,19):
        box((x,-8.5,4.02),(.035,19,.06),(.14,.18,.20))
    for y in range(-18,2):
        box((8.3,y,4.02),(20,.035,.06),(.14,.18,.20))
    from interiors import rounded
    for x in (2,7,12,17):
        for y in (-15,-10,-5):
            rounded(room,(x,y,3.96),(.9,.9,.065),(.96,.96,.91))
    for x in (1.6,3.9,6.2,8.5,10.8,13.1,15.4):
        box((x,-2.6,.095),(2.25,2.15,.19),OAK).getChild(4).setTexture(wood)
    box((8.50,-1.51,2.36),(13.25,.21,3.10),METAL)
    for x in (2.02,2.25,2.48,14.55,14.78,15.01):
        box((x,-1.65,2.36),(.076,.09,3.02),OAK)
    box((8.5,-1.66,2.39),(11.7,.09,2.69),(.08,.19,.37))
    box((8.5,-1.75,3.77),(11.8,.17,.074),METAL)
    box((8.5,-1.843,3.736),(11.66,.027,.026),(.97,.89,.67))
    label(room,'QAIRU CLASSROOM',(8.5,-1.723,3.16),.40,(.88,.92,.87))
    label(room,'AI Fundamentals',(8.5,-1.724,2.55),.30,(.76,.88,.84))
    label(room,'A* SEARCH     /     BAYESIAN INFERENCE     /     EXPECTED UTILITY',
          (8.5,-1.724,1.86),.205,(.66,.79,.76))
    box((4.1,-2.55,.72),(.78,.60,1.05),WALNUT)
    box((4.1,-2.55,1.28),(1.01,.76,.089),OAK)
    box((4.24,-2.61,1.37),(.35,.25,.09),METAL)
    for x in (.20,16.78):

        box((x,1.07,2.75),(.81,.08,.23),(.23,.44,.33))
        label(room,'ATRIUM / FLOOR 4',(x,1.02,2.71),.13,(.86,.95,.83))
        outside = label(room,'QAIRU / LECTURE HALL',(x,1.52,2.71),.13,(.86,.95,.83))
        outside.setH(180)

    rng = random.Random(812)
    # The presenter uses the articulated standing rig.
    prototypes = lecture.attachNewNode('seated prototypes')
    class Stage:
        world = prototypes
    audience = lecture.attachNewNode('audience')
    cast_light(audience)
    heads = []
    for row in range(5):
        y = -6.70-row*1.76
        z = row*.26
        for left,right in ((2.95,9.15),(9.95,15.6)):
            box(((left+right)/2,y+.2,z+.18),(right-left,1.65,.36),(.10,.34,.59))
            box(((left+right)/2,y,z+.43),(right-left,.62,.11),(.70,.75,.76))
        for col in range(10):
            x = 3.53+col*1.15+(.92 if col>=5 else 0)

            game.obstacles.append((x,ROOM_Y+y+.25,.57,.86))
            h = rng.uniform(-9,9)
            actor = seated_person(game,audience,row*10+col,
                                  x+rng.uniform(-.025,.025),y,z,h,rng.uniform(.97,1.025))
            heads.append((actor,h,rng.uniform(0,math.tau)))
    prototypes.detachNode()
    seat(game,room,2.35,-11.05,0,0,wood,fabric)
    presenter = student(Stage,4)[0]
    presenter.reparentTo(lecture)
    presenter.setPos(5.00,-2.36,.19)
    presenter.setH(167)
    room.flattenStrong()
    return lecture, heads, presenter


def animate_lecture(camera, heads, presenter, time):
    eye, target = shot(time)
    room = presenter.getParent()
    offset = room.getZ(camera.getTop())
    camera.setPos(eye[0],eye[1]+ROOM_Y,eye[2]+offset)
    camera.lookAt(target[0],target[1]+ROOM_Y,target[2]+offset)
    for actor, base, phase in heads:
        actor.setH(base+1.4*math.sin(time*.66+phase))
    presenter.setH(167+12*math.sin(time*.30))
