"""Architectural enclosures and persistent lower-storey views."""
from levels import elevation, FLOOR_SPACING
from interiors import METAL, STONE, OAK, glass
from finishes import material
from gallery import seated_person, cast_light


def elevator_lobby(game):
    # A continuous shaft has depth behind the doors and meets both slabs.
    # Keep the complete shaft east of Qairu (outer wall x=18.41).
    # The entrance faces the unobstructed south circulation area.
    x, front = 22, -24
    game.elevator_front = (x, front)
    for side in (-1, 1):
        game.box((x+side*1.85,front+1.45,2.0),(.34,3.3,4.0),STONE)
    game.box((x,front+3,2),(4,.28,4),STONE)
    game.box((x,front+1.45,3.95),(4,3.3,.2),STONE)
    for side in (-1,1):
        jamb=game.box((x+side*1.38,front,1.36),(.18,.20,2.72),(.47,.51,.53))
        material(jamb,'metal',(0,2,3))
        door=game.box((x+side*.635,front+.04,1.32),(1.25,.12,2.58),(.58,.62,.64))
        material(door,'metal',(0,1))
    game.box((x,front-.01,2.73),(2.95,.22,.15),(.44,.49,.51))
    game.box((x,front-.09,.025),(2.95,.40,.05),(.49,.52,.53))
    game.box((x,front-.09,3.13),(3.45,.12,.52),(.075,.12,.14))
    game.label('ELEVATORS ARE BLOCKED',(x,front-.16,3.17),.125)
    game.label('FLOOR '+str(game.floor)+' / OUT OF SERVICE',(x,front-.16,2.98),.085)
    game.box((x-1.65,front-.07,1.25),(.22,.09,.43),(.29,.34,.36))
    for z in (1.18,1.32):
        game.box((x-1.65,front-.124,z),(.10,.025,.09),(.73,.75,.70))
    light=game.box((x,front-.16,2.84),(.46,.04,.045),(.9,.12,.06))
    game.warning_lights.append(light)
    game.obstacles.append((x,front+1.4,2.08,1.85))


def lower_storeys(game):
    """Render lower floors around the atrium in the same world coordinates."""
    from rotunda import disc, RADIUS, beam
    original_world, original_floor = game.world, game.floor
    root=original_world.attachNewNode('visible lower storeys')
    try:
        for level in range(1,original_floor):
            group=root.attachNewNode('lower floor '+str(level))
            group.setZ(elevation(level)-elevation(original_floor))
            game.world, game.floor = group, level
            disc(game,-.03,RADIUS,(.59,.62,.60),'circular floor')
            # Slab thickness and complete occupied bays on both sides of court.
            for x in (21,34.5):
                game.box((x,-10.5,-.16),(3,15,.30),STONE)
                game.box((x,-10.5,3.95),(3,15,.20),(.67,.70,.68))
                for y in (-15,-10,-5):
                    game.box((x,y,.76),(1.6,1.0,.10),OAK)
                    for dx in (-.58,.58):
                        game.box((x+dx,y,.36),(.09,.7,.72),METAL)
                    game.box((x,y+.3,1.16),(.75,.09,.47),METAL)
                    game.box((x,y+.24,1.16),(.66,.02,.38),(.12,.47,.53))
                    chair=game.box((x,y-1,.43),(.6,.6,.12),(.32,.43,.43))
                    game.box((x,y-1.27,.76),(.6,.10,.58),(.32,.43,.43))
                    seated_person(game,group,level+int(y),x,y-1,0,0)
                game.box((x+(-1.45 if x<23 else 1.45),-10.5,1.9),(.18,15,3.8),(.43,.48,.46))
            cast_light(group)
            # Flights rest on inclined structural stringers and real landings.
            if level>1:
                for x in (0,20):
                    for step in range(24):
                        game.box((x,1.85+step*.31,-step*FLOOR_SPACING/23),(2.6,.31,.18),STONE)
                    for side in (-1,1):
                        beam(game,(x+side*1.1,1.7,-.22),(x+side*1.1,9.15,-FLOOR_SPACING-.22),.22,METAL)
                        game.box((x+side*1.56,5.6,-.3),(.22,9.7,7.8),STONE)
                    game.box((x,9.55,-FLOOR_SPACING),(3,1.5,.25),STONE)
                    game.box((x,10.35,-.3),(3.3,.22,7.8),STONE)
    finally:
        game.world, game.floor=original_world, original_floor
    return root
