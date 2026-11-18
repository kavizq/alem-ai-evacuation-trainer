"""Four-floor fictional educational campaign using the original Panda3D foundation."""
import json
import math
from pathlib import Path
import subprocess
import shutil
import wave
import struct
import textwrap
from platform_paths import panda_path
from speech import speak, stop_speech
from navigation import walking_path
from credits import Credits
from building_repairs import elevator_lobby, lower_storeys
from puzzle_stages import stage_question, correct_answer
from interiors import architecture, desk, glass, STONE, METAL
from people import student
from gallery import COURT, load_cast, occupied_rooms, shared_court
from expo import build_expo
from finishes import divider, material
from levels import elevation, FLOOR_SPACING
from lecture import DURATION as LECTURE_DURATION, animate_lecture, lecture_room, ROOM_Y, PLAYER_SEAT
from environment import bake_floor, build_surroundings, lower_terraces
from direct.task import Task
from panda3d.core import TextNode, LineSegs, NodePath, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, Geom, GeomNode, TransparencyAttrib, WindowProperties, loadPrcFileData
from main_before_campaign import Game as Foundation, cell_at, xyz, WORLD_FACE_GEOM
from ai_core import START, SUSPECT_CORRIDOR, analyze, astar, bayesian_update, one_step_mdp

SAVE = Path(__file__).with_name('autosave.json')
NAMES = {4: 'Qairu classroom', 3: 'Computer coworking', 2: 'Computer workspace', 1: 'Glass atrium'}
QUESTIONS = {
 4: ('A* route planning\nCount the shortest route from S to either E on the map.\nEach horizontal or vertical move costs one. Walls are blocked.\n\n1. Five steps     2. Seven steps     3. Nine steps', 2,
     'Use f = g + h. Count moves, including the last move into an exit.'),
 3: ('Bayesian inference\nPrior blockage 20%. Alert sensitivity 80%.\nFalse alarm rate 20%. The sensor reports ALERT.\n\nP(blocked | alert)?\n1. 20%     2. 80%     3. 50%', 3,
     'Compare alert-and-blocked with all ways an alert can occur.'),
 2: ('One-step MDP\nUse the posterior from floor 3.\nProceed gives +10 if clear, -20 if blocked.\nDetour gives +3 in either state.\n\n1. Proceed     2. Detour     3. Both have equal utility', 2,
     'Weight each reward by its state probability, then add.'),
 1: ('Final evacuation decision\nThe sensor still reports ALERT. Students await your plan.\nWhich sequence combines the three algorithms?\n\n1. Shortest route, ignore the sensor\n2. Treat every alert as certain blockage\n3. Update belief, compare utility, route around the suspect cell', 3,
     'Consider how evidence changes a belief and how a decision constrains a route.')}

EVIDENCE = {
    4: ('A star uses f equals g plus h. For four-direction movement, Manhattan distance counts horizontal and vertical separation. Inspect the map. S is your original classroom position.',
        'Known obstacles are gray. Green cells are exits. Each move costs one. Count edges between cells, not the cells themselves. Both exits are valid goals.'),
    3: ('The sensor calibration reports sensitivity of eighty percent and a false alarm rate of twenty percent. An alert is evidence, not certainty.',
        'Before the alert, twenty percent of corridors were blocked. Bayes rule divides alert-and-blocked probability by the total probability of an alert. Include false alarms.'),
    2: ('This classroom model has a one-step horizon. Proceed rewards ten when clear and minus twenty when blocked. Detour rewards three in either state.',
        'The previous sensor alert produced a blockage posterior of fifty percent. Multiply each outcome reward by its probability. Choose the action with the larger expected total.'),
    1: ('Students have reached the atrium. The sensor still reports an alert. Your belief and reward model must inform the final route constraints.',
        'A star accepts a set of forbidden cells. A decision to detour excludes the suspect corridor. Check the evidence, choose the action, then calculate a traversable route.')}

WALK_SPEED = 2.7
from rotunda import build_rotunda, RADIUS, STAIR_DURATION


class Campaign(Foundation):
    def __init__(self):
        self.raw_movement = set()
        self.mouse_primed = False
        self.puzzle_stage = 0
        self.evidence = set()
        self.ending = None
        self.ending_time = 0
        self.elapsed = 0
        self.floor = 4
        self.errors = 0
        self.solved = False
        self.panel = False
        self.scene_time = 0
        self.lecture = None
        self.transition = 0
        self.voice = None
        manifest_path = Path(__file__).with_name('audio') / 'adeka_en' / 'manifest.json'
        self.voice_manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {}
        self.sounds = {}
        self.walk_distance = 0.
        self.walk_weight = 0.
        self.npc_gaits = []
        self.npcs = []
        self.world = None
        self.gate_panels=[]
        self.warning_lights=[]
        self.gate_open=0
        self.floor_card = WORLD_FACE_GEOM
        self.floor_textures = {}
        loadPrcFileData('', 'framebuffer-multisample true\nmultisamples 4')
        super().__init__()
        self.setBackgroundColor(.73, .77, .78, 1)
        build_surroundings(self)
        self.camLens.setNearFar(.05, 180)
        self.camLens.setFov(75)
        if self.buttonThrowers:
            keyboard = self.buttonThrowers[0].node()
            keyboard.setRawButtonDownEvent('physical-key-down')
            keyboard.setRawButtonUpEvent('physical-key-up')
        self.accept('physical-key-down', self.physical_key, [True])
        self.accept('physical-key-up', self.physical_key, [False])
        # Use physical keys for actions too, including when macOS reports a
        # character that Panda's logical keyboard does not map.
        self.physical_actions = {
            'e': self.interact, 'h': self.hint, 'q': self.close_panel,
            'c': self.resume, 'r': self.reset_mission, 'm': self.mute_audio,
        }
        # Use one event stream for movement so a layout change cannot leave
        # the logical key down after the physical key has been released.
        for key in ('w', 'a', 's', 'd'):
            self.ignore(key)
            self.ignore(key+'-up')
        for key in self.physical_actions:
            self.ignore(key)
        for number in (1, 2, 3):
            self.accept(str(number), self.answer, [number])
        self.accept('tab', self.hint)
        self.accept('space', self.skip_intro)
        self.accept('window-event', self.window_changed)
        self.play_controls = 'WASD move | Mouse / arrows look | E interact | 1-3 answer | H hint | Q close | C resume | R new | Esc mouse'
        self.ui_controls.setText(self.play_controls)
        self.say('Welcome to Qairu. Today we connect A star search, Bayesian inference and expected utility. Press W A S D or Space to skip the lecture and move.')
        self.finished = True
        self.setup_audio()
        self.credits=Credits(self)
        self.show_lecture()

    def physical_key(self, pressed, button):
        # Cocoa's ButtonThrower emits a string. ButtonHandle also has a
        # string representation equal to its physical key name.
        key = str(button)
        if key in ('w', 'a', 's', 'd', 'shift', 'lshift', 'rshift'):
            if pressed:
                self.raw_movement.add(key)
                self.skip_intro()
            else:
                self.raw_movement.discard(key)
        elif pressed and key in self.physical_actions:
            self.physical_actions[key]()

    def key_set(self, key, value):
        super().key_set(key, value)
        if value and key in ('w', 'a', 's', 'd'):
            self.skip_intro()

    def skip_intro(self):
        if self.scene_time < LECTURE_DURATION:
            self.scene_time = LECTURE_DURATION
            self.begin_evacuation()

    def show_lecture(self):
        self.lecture = self.classroom
        self.audience = self.classroom_audience
        self.presenter = self.classroom_presenter
        self.world.show()
        for element in self.lecture_hud:
            element.hide()
        self.lecture_caption.setSz(.60)
        self.lecture_caption.setZ(-.72)
        self.ui_message.setPos(self.ui_message.getPos()[0],-.775)
        self.ui_controls.setPos(self.ui_controls.getPos()[0],-.927)
        self.ui_controls.setText('WASD / SPACE  Skip lecture')
        animate_lecture(self.camera, self.audience, self.presenter, 0)

    def close_lecture(self):
        if self.lecture is None:
            return
        self.lecture = None
        self.audience = []
        self.presenter = None
        self.world.show()
        for element in self.lecture_hud:
            element.show()
        self.lecture_caption.setSz(1)
        self.lecture_caption.setZ(-.57)
        self.ui_message.setPos(self.ui_message.getPos()[0],-.63)
        self.ui_controls.setPos(self.ui_controls.getPos()[0],-.87)
        self.ui_controls.setText(self.play_controls)

    def begin_evacuation(self):
        self.position = [2.35, ROOM_Y-10.35, 1.6]
        self.heading = -45
        self.pitch = -3
        self.close_lecture()
        self.set_camera()
        self.finished = False
        self.set_mouse_capture(True)
        self.sounds['alarm'].play()
        self.say('Technical malfunction. Elevators are blocked. Inspect both amber stations before using the cyan terminal.')

    def lock_mouse(self):
        self.set_mouse_capture(True)

    def toggle_mouse(self):
        self.set_mouse_capture(not self.mouse_locked)

    def set_mouse_capture(self, captured):
        if not hasattr(self.win, 'requestProperties'):
            self.mouse_locked = False
            return
        self.mouse_locked = captured
        self.mouse_primed = False
        self.previous_pointer = None
        props = WindowProperties()
        active=captured and not self.panel and not self.ending
        props.setCursorHidden(active)
        props.setMouseMode(WindowProperties.MRelative if active else WindowProperties.MAbsolute)
        self.win.requestProperties(props)

    def update_look(self, dt):
        if not hasattr(self.win, 'getProperties'):
            self.heading += 110 * dt * (self.keys['arrow_left'] - self.keys['arrow_right'])
            self.pitch = max(-70, min(70, self.pitch + 75 * dt * (self.keys['arrow_up'] - self.keys['arrow_down'])))
            return
        props = self.win.getProperties()
        if self.mouse_locked and props.getForeground():
            cx, cy = props.getXSize() // 2, props.getYSize() // 2
            pointer = self.win.getPointer(0)
            position = (pointer.getX(), pointer.getY())
            previous = getattr(self, 'previous_pointer', None)
            if pointer.getInWindow() and previous is not None:
                relative=props.getMouseMode()==WindowProperties.MRelative
                origin = previous if relative else ((cx, cy) if self.mouse_primed else previous)
                dx, dy = position[0] - origin[0], position[1] - origin[1]
                self.heading -= dx * .15
                self.pitch -= dy * .12
            if props.getMouseMode()==WindowProperties.MRelative:
                self.mouse_primed=False
                self.previous_pointer=position
            else:
                self.mouse_primed = self.win.movePointer(0, cx, cy)
                self.previous_pointer = (cx, cy) if self.mouse_primed else position
        else:
            self.previous_pointer = None
            self.mouse_primed = False
        self.heading += 110 * dt * (self.keys['arrow_left'] - self.keys['arrow_right'])
        self.pitch += 75 * dt * (self.keys['arrow_up'] - self.keys['arrow_down'])
        self.pitch = max(-70, min(70, self.pitch))

    def move_player(self, dt):
        active = self.raw_movement.union(key for key, down in self.keys.items() if down)
        forward = ('w' in active) - ('s' in active)
        sideways = ('d' in active) - ('a' in active)
        if not (forward or sideways):
            return
        heading = math.radians(self.heading)
        speed = self.walk_speed()
        if active.intersection({'shift','lshift','rshift'}):
            speed *= 1.45
        distance = speed * dt / math.hypot(forward, sideways)
        dx = (math.cos(heading) * sideways - math.sin(heading) * forward) * distance
        dy = (math.sin(heading) * sideways + math.cos(heading) * forward) * distance
        x, y, _ = self.position
        if self.can_walk(x + dx, y):
            x += dx
        if self.can_walk(x, y + dy):
            y += dy
        self.position[:2] = x, y

    def walk_speed(self):
        return WALK_SPEED * (1 + .10*(4-self.floor) + (.25 if self.solved else 0))

    def mute_audio(self):
        active=self.sfxManagerList[0].getActive()
        self.sfxManagerList[0].setActive(not active)
        self.voice_muted=active
        if active:
            stop_speech(self)

    def window_changed(self, window):
        if not hasattr(window, 'getProperties'):
            return
        if window != self.win:
            return
        foreground = window.getProperties().getForeground()
        if foreground != getattr(self, 'window_foreground', None):
            self.mouse_primed = False
            self.previous_pointer = None
        self.window_foreground = foreground
        if not foreground:
            self.raw_movement.clear()
            for key in self.keys:
                self.keys[key]=False

    def build_floor(self):
        self.obstacles=[]
        tint = {4:(.64,.54,.43), 3:(.62,.64,.61), 2:(.59,.59,.55), 1:(.69,.66,.58)}[self.floor]
        build_rotunda(self)
        from ai_core import MAP
        for row, line in enumerate(MAP):
            for col, tile in enumerate(line):
                x,y,_ = xyz((row,col))
                if tile == '#' and self.floor != 1:
                    if not (self.floor==4 and row==4 and col==1):
                        divider(self,x,y)
                        self.obstacles.append((x,y,2.10,2.10))
        for x in (0,20):
            self.box((x,0,.013),(2.8,2.8,.022),(.25,.48,.34))
        self.terminal_xy = (9,-16)
        self.station(9,-16, (.15,.75,.77), 'DECISION TERMINAL / E')
        self.evidence_positions = [(1,-12),(19,-4)]
        for i, (x,y) in enumerate(self.evidence_positions,1):
            self.station(x,y,(.90,.59,.22),f'EVIDENCE {i} / E')
        if self.floor == 1:
            self.obstacles.append((10,-8,2.85,1.85))
        if self.floor != 4:
            architecture(self)
        if self.floor == 1:
            self.obstacles.extend((27.5,y,2.10,.75) for y in (-14,-8))
        self.obstacles.append((36.2,-10.5,.4,7.3))


    def station(self, x, y, accent, caption):
        self.box((x,y,.045),(.9,.76,.09),METAL)
        self.box((x,y,.77),(.48,.50,1.46),METAL)
        self.box((x,y,1.27),(.79,.56,.51),(.24,.26,.25))
        self.box((x,y-.286,1.29),(.67,.025,.34),(.10,.17,.19))
        self.box((x,y-.304,1.397),(.598,.017,.052),accent)
        for offset in (-.09,-.025,.040):
            self.box((x-.05,y-.304,1.29+offset),(.39+offset,.013,.018),accent)
        self.box((x,y-.256,.97),(.53,.035,.028),accent)
        self.box((x,y-.28,1.66),(.80,.11,.24),(.23,.28,.29))
        name = caption.replace('DECISION TERMINAL','DECISION\nTERMINAL')
        self.label(name,(x,y-.343,1.698 if '\n' in name else 1.632),.090)
        self.obstacles.append((x,y,.71,.64))

    def can_walk(self,x,y):
        if math.hypot(x-10,y+10) >= RADIUS-1.4:
            return False
        if self.floor > 1 and COURT[0]-.3 < x < COURT[1]+.3 and COURT[2]-.3 < y < COURT[3]+.3:
            return False
        gate_y=17 if self.floor==1 else .54
        if not self.solved and abs(y-gate_y)<.42 and any(abs(x-gx)<1.6 for gx in (0,20)):
            return False
        return all(abs(x-ox)>=rx or abs(y-oy)>=ry for ox,oy,rx,ry in self.obstacles)

    def shell(self, roof=False):
        rows, cols = 12, 36
        lower = .24 if roof else math.asin(-8/20)
        def point(row, col):
            lat = lower + (math.pi/2-lower)*row/rows
            lon = col*math.tau/cols
            radius = 20*math.cos(lat)
            return (10+radius*math.cos(lon), -10+radius*math.sin(lon), 8+20*math.sin(lat))

        data = GeomVertexData('glazed shell',GeomVertexFormat.getV3c4(),Geom.UHStatic)
        vertex = GeomVertexWriter(data,'vertex')
        colors = GeomVertexWriter(data,'color')
        triangles = GeomTriangles(Geom.UHStatic)
        for row in range(rows):
            for col in range(cols):
                a = vertex.getWriteRow()
                shade = .5+.5*math.sin(col*1.9+row*3.3)
                for r,c in ((row,col),(row,col+1),(row+1,col),(row+1,col+1)):
                    vertex.addData3(*point(r,c))
                    colors.addData4(.30+shade*.36,.55+shade*.23,.65+shade*.22,.14+shade*.17)
                triangles.addVertices(a,a+1,a+2)
                triangles.addVertices(a+1,a+3,a+2)
        geometry = Geom(data)
        geometry.addPrimitive(triangles)
        node = GeomNode('glazed shell')
        node.addGeom(geometry)
        shell = self.world.attachNewNode(node)
        shell.setTransparency(TransparencyAttrib.MAlpha)
        shell.setTwoSided(True)
        shell.setDepthWrite(False)

        frame = LineSegs('shell mullions')
        frame.setColor(.24,.34,.37,1)
        frame.setThickness(1.7)
        for row in range(rows):
            frame.moveTo(*point(row,0))
            for col in range(1,cols+1):
                frame.drawTo(*point(row,col))
        for col in range(0,cols,2):
            frame.moveTo(*point(0,col))
            for row in range(1,rows+1):
                frame.drawTo(*point(row,col))
        self.world.attachNewNode(frame.create())

    def setup_audio(self):
        folder = Path(__file__).with_name('audio')
        folder.mkdir(exist_ok=True)
        for name, duration, frequency, volume in [('ambient', 4, 90, .035), ('alarm', 2, 660, .12), ('step', .15, 110, .2)]:
            path = folder / (name + '.wav')
            if not path.exists():
                samples = []
                for i in range(int(22050 * duration)):
                    t = i / 22050
                    envelope = min(1, t * 30) * min(1, (duration-t)*30)
                    if name == 'alarm':
                        envelope *= .5 + .5 * math.sin(t * math.tau * 2)
                    if name == 'step':
                        envelope *= math.exp(-t*35)
                    samples.append(int(32767*volume*envelope*math.sin(math.tau*frequency*t)))
                with wave.open(str(path), 'wb') as output:
                    output.setparams((1, 2, 22050, 0, 'NONE', 'not compressed'))
                    output.writeframes(struct.pack('<' + 'h'*len(samples), *samples))
            self.sounds[name] = self.loader.loadSfx(panda_path(path))
        self.sounds['ambient'].setLoop(True)
        self.sounds['ambient'].play()

    def box(self, location, scale, rgb, parent=None):
        item = (parent or self.world or self.render).attachNewNode('cuboid')
        item.setPos(*location)
        item.setScale(*scale)
        item.setColor(*rgb, 1)
        for index, (position, rotation) in enumerate((
            ((0,-.5,0),(0,0,0)), ((0,.5,0),(180,0,0)),
            ((-.5,0,0),(90,0,0)), ((.5,0,0),(-90,0,0)),
            ((0,0,.5),(0,-90,0)), ((0,0,-.5),(0,90,0)))):
            face = NodePath(WORLD_FACE_GEOM).copyTo(item)
            face.setPos(*position)
            face.setHpr(*rotation)
            face.setTwoSided(True)
            shade = (.92,.71,.80,.85,1,.64)[index]
            face.setColorScale(shade,shade,shade,1)
        return item

    def label(self, body, position, size=.45):
        text = TextNode('sign')
        text.setText(body)
        text.setAlign(TextNode.ACenter)
        node = self.world.attachNewNode(text)
        node.setPos(*position)
        node.setScale(size)
        node.setColor(.94, .96, .89, 1)
        node.setTwoSided(True)

    def make_level(self):
        self.close_lecture()
        if self.world:
            self.world.removeNode()
        self.world = self.render.attachNewNode('floor')
        self.world.setZ(elevation(self.floor))
        self.walk_distance = self.walk_weight = 0.
        self.npcs = []
        self.npc_gaits = []
        self.gate_panels=[]
        self.warning_lights=[]
        self.gate_open=0
        if not hasattr(self,"cast"):
            self.cast = load_cast(self)
            self.court = shared_court(self)
        self.court.show()
        self.build_floor()
        occupied_rooms(self)
        # Enclosed stair cores replace the former outdoor terraces.
        self.label(f'FLOOR {self.floor} / {NAMES[self.floor]}', (10,1.59,2.70), .33)
        self.box((10,1.72,2.68),(13,.14,1.01),METAL)
        elevator_lobby(self)
        gate_y = 17 if self.floor == 1 else 0
        for x in (0,20):
            for side in (-1,1):
                self.box((x+side*1.48,gate_y+.57,1.38),(.18,.34,2.76),METAL)
                panel = glass(self,(x+side*.65,gate_y+.54,1.18),(1.25,.10,2.30),(.29,.49,.46),.80)
                self.gate_panels.append((panel,x+side*.65,side))
            self.warning_lights.append(self.box((x,gate_y+.50,2.54),(2.9,.21,.23),(.9,.12,.06)))
            self.label('EXIT / E' if self.floor == 1 else 'STAIRS / E',(x,gate_y+.30,2.87),.25)
            if self.floor == 1:
                for side in (-1,1):
                    self.box((x+side*2,16,1.7),(.20,4.5,3.4),(.67,.70,.69))
                    self.obstacles.append((x+side*2,16,.4,2.4))
                self.box((x,16,3.42),(4.2,4.5,.20),METAL)
                self.box((x,17.75,1.7),(4.2,.15,3.4),(.65,.73,.74))
                self.label('EXIT TO PLAZA',(x,14,3.03),.22)
            if self.floor > 1:
                from rotunda import beam
                for side in (-1,1):
                    beam(self,(x+side*1.1,1.7,-.22),(x+side*1.1,9.15,-FLOOR_SPACING-.22),.22,METAL)
                count = 23
                rise = FLOOR_SPACING / count
                tread = .31
                for step in range(count + 1):
                    self.box((x,1.85+step*tread,-step*rise),(2.60,tread,.21),STONE)
                self.box((x,9.51,-FLOOR_SPACING),(2.60,1.1,.21),STONE)
                for side in (-1,1):
                    for step in (0,5,10,15,20,23):
                        self.box((x+side*1.26,1.85+step*tread,.42-step*rise),(.075,.075,.84),METAL)
                    rail = self.box((x+side*1.26,1.85+count*tread/2,.84-FLOOR_SPACING/2),
                                    (.075,math.hypot(count*tread,FLOOR_SPACING),.075),METAL)
                    rail.setP(-math.degrees(math.atan2(rise,tread)))
        if self.floor in (2,3):
            for x in (2.9,16.8):
                for y in (-6.8,-11.0,-16.5):
                    desk_x = .9 if x < 3 and y < -16 else x
                    desk(self,desk_x,y,computers=self.floor in (2,3),lecture=self.floor==4)
        self.classroom = None
        self.classroom_audience = []
        self.classroom_presenter = None
        if self.floor == 4:
            self.classroom, self.classroom_audience, self.classroom_presenter = lecture_room(self)
        lower_storeys(self)
        bake_floor(self)
        for i in range(6):
            node, gait = student(self,i)
            self.npcs.append(node)
            self.npc_gaits.append(gait)
        self.student_routes=[]
        for i,node in enumerate(self.npcs):
            cell=(2, i)
            node.setPos(*xyz(cell))
            start=xyz(cell)[:2]
            if not self.can_walk(*start):
                start=(6+i*1.5,-20)
            node.setPos(*start,0)
            self.student_routes.append(walking_path(start,(0 if i<3 else 20,0),self.can_walk)[1:])

    def build_exterior(self):
        self.close_lecture()
        self.court.hide()
        interior = self.world
        self.world = self.render.attachNewNode('exterior')
        for student_node in self.npcs:
            student_node.reparentTo(self.world)
        interior.removeNode()
        self.gate_panels.clear()
        self.warning_lights.clear()
        build_expo(self)

    def say(self, message):
        self.message='ADEKA: '+message
        self.last_speech_backend = speak(self, message)
        self.update_hud()

    def destroy(self):
        stop_speech(self)
        super().destroy()

    def make_ui(self):
        super().make_ui()
        # High-resolution glyph atlas keeps question text crisp on Retina displays.
        font_path = Path(__file__).with_name('assets') / 'Arial.ttf'
        self.question_font = self.loader.loadFont(panda_path(font_path))
        self.question_font.setPixelsPerUnit(120)
        self.question_font.setPageSize(1024, 1024)
        self.overlay_text.setFont(self.question_font)
        self.overlay_text.setScale(.052)
        self.overlay_text.setWordwrap(31)
        self.overlay_text.setPos(-.82, .53)
        # Keep the legacy widgets' positions and reduce the opaque screen area.
        cards = [child for child in self.aspect2d.getChildren() if child.getName() == 'hud-panel']
        if len(cards) >= 3:
            cards[0].setSz(.59)
            cards[0].setSx(.76)
        self.ui_stats.setScale(.038)
        self.ui_message.setScale(.041)
        self.ui_event.setScale(.034)
        self.ui_event.setPos(self.ui_event.getPos()[0],-.813)
        self.ui_event.setFg((.48,.82,.89,1))
        self.map_markers = {}
        for (r,c), card in self.map_cells.items():
            self.map_markers[(r,c)] = self.text('',self.getAspectRatio()-.595+c*.085+.014,.78-r*.084-.051,.032,(.04,.08,.11,1))
        self.nav_text = self.text('',-.62,.87,.038,(.98,.86,.47,1))
        crosshair = self.text('+',-.011,-.011,.037,(.98,.95,.85,.90))
        self.stair_fade = self.card(-aspect if (aspect:=self.getAspectRatio()) else -2,1,aspect*2,2,(.025,.04,.05,0))
        self.stair_fade.setBin('fixed',30)
        self.stair_fade.hide()
        self.arrival_fade=0.
        self.lecture_caption = cards[2]
        self.lecture_hud = [*cards[:2], self.ui_title, self.ui_stats, self.ui_map_title,
                            self.ui_event, crosshair, self.nav_text, *self.map_markers.values(), *self.map_cells.values()]

    def redraw(self):
        self.show_route=False
        super().redraw()
        if self.floor == 1 and self.solved:
            for cell in analyze(START, True)['path']:
                self.map_cells[cell].setColor(.22,.63,.46,1)
            self.map_cells[SUSPECT_CORRIDOR].setColor(.82,.28,.16,1)
        for index,(x,y) in enumerate(self.evidence_positions):
            cell=(round(-y/4),round(x/4))
            self.map_cells[cell].setColor(.95,.65,.15,1)
        self.map_cells[(4,2)].setColor(.12,.78,.82,1)
        self.map_cells[START].setColor(.7,.7,.7,1)
        self.map_cells[cell_at(*self.position[:2])].setColor(1,1,1,1)
        if hasattr(self,'map_markers'):
            for cell,marker in self.map_markers.items():
                marker.setText('S' if cell==START else ('E' if cell in ((0,0),(0,5)) else ('T' if cell==(4,2) else '')))
            for i,(ex,ey) in enumerate(self.evidence_positions):
                self.map_markers[(round(-ey/4),round(ex/4))].setText('OK' if i in self.evidence else str(i+1))
            self.map_markers[cell_at(*self.position[:2])].setText('S@' if cell_at(*self.position[:2])==START else '@')
        if self.floor==1:
            from ai_core import walls
            for cell in walls():
                self.map_cells[cell].setColor(.2,.29,.4,1)

    def update_hud(self):
        if not hasattr(self,'ui_stats'):
            return
        self.ui_map_title.setText('TASK GRID / S = START / E = EXIT')
        self.ui_map_title.setScale(.032)
        self.ui_stats.setText(f'FLOOR {self.floor} / {NAMES[self.floor]}\nSecurity errors {self.errors}/3\n'+('LECTURE / WASD or SPACE to begin' if self.scene_time < LECTURE_DURATION else (('Exits unlocked' if self.floor == 1 else 'Stairs unlocked') if self.solved else 'Find the cyan decision terminal')))
        self.update_navigation()
        self.ui_message.setText(textwrap.fill(self.message, 102))
        self.ui_event.setText(f'Evidence {len(self.evidence)}/2 | H hint | M sound | SHIFT run | Time {int(self.elapsed)//60}:{int(self.elapsed)%60:02d}')

    def update_navigation(self):
        if not hasattr(self,'nav_text'):
            return
        x,y=self.position[:2]
        if self.solved:
            target=min(((0,17 if self.floor==1 else 0),(20,17 if self.floor==1 else 0)),key=lambda p: math.hypot(p[0]-x,p[1]-y))
            name='EXIT' if self.floor==1 else 'STAIRS'
        elif len(self.evidence)<2:
            index=min((i for i in (0,1) if i not in self.evidence),key=lambda i: math.dist((x,y),self.evidence_positions[i]))
            target=self.evidence_positions[index]; name=f'EVIDENCE {index+1}'
        else:
            target=self.terminal_xy; name='TERMINAL'
        dx,dy=target[0]-x,target[1]-y
        angle=(math.degrees(math.atan2(-dx,dy))-self.heading+180)%360-180
        direction='AHEAD' if abs(angle)<25 else ('BEHIND' if abs(angle)>145 else ('LEFT' if angle>0 else 'RIGHT'))
        self.nav_text.setText(f'{name}  {math.hypot(dx,dy):.0f} m  {direction}\nSpeed {self.walk_speed()/WALK_SPEED:.0%} | SHIFT run')

    def set_stair_hud(self, visible):
        for item in [*self.lecture_hud,self.lecture_caption,self.ui_message,self.ui_controls]:
            item.show() if visible else item.hide()

    def close_panel(self):
        self.panel=False
        self.overlay.hide()
        self.overlay_text.hide()
        self.set_mouse_capture(self.mouse_locked)

    def hint(self):
        self.say(stage_question(self.floor,self.puzzle_stage,QUESTIONS)[2])

    def interact(self):
        if self.finished or self.transition or self.panel:
            return
        x,y,_=self.position
        for index, (ex, ey) in enumerate(self.evidence_positions):
            if math.hypot(x-ex,y-ey)<2.5:
                self.evidence.add(index)
                self.say(EVIDENCE[self.floor][index])
                self.save()
                return
        if math.hypot(x-self.terminal_xy[0],y-self.terminal_xy[1])<3.3:
            if self.solved:
                self.say('The decision is already recorded. Continue to a green gate.')
                return
            if len(self.evidence)<2:
                self.say('Inspect both amber evidence stations first. Their locations are marked on the map.')
                return
            self.panel=True
            self.set_mouse_capture(self.mouse_locked)
            self.overlay.show()
            self.show_question()
            self.overlay_text.show()
        elif any(math.hypot(x-gx,y-(17 if self.floor==1 else 0))<2 for gx in (0,20)):
            if self.solved:
                if self.floor==1:
                    self.end(True)
                else:
                    self.stair_x = 0 if x < 2 else 20
                    self.set_stair_hud(False)
                    self.transition=STAIR_DURATION
                    self.say('Descending the interior staircase. Your progress is saved on the next floor.')
            else:
                self.say('The stair gate needs a decision from the terminal.')
        else:
            self.say('Explore the floor. The cyan terminal controls the stair gate.')

    def show_question(self):
        self.overlay.setZ(.64)
        self.overlay.setSz(1.2)
        question=stage_question(self.floor,self.puzzle_stage,QUESTIONS)[0]
        self.overlay_text.setText(f'DECISION {self.puzzle_stage+1} / 3\n\n'+question+'\n\nQ close / H hint')

    def answer(self, number):
        if not self.panel or self.solved or self.finished:
            return
        if number==correct_answer(self.floor,self.puzzle_stage,QUESTIONS):
            if self.puzzle_stage<2:
                self.puzzle_stage+=1
                self.save()
                self.show_question()
                self.say('Calculation accepted. Continue with the next decision.')
                return
            self.solved=True
            self.save()
            self.close_panel()
            self.redraw()
            if self.floor == 1:
                result = analyze(START, True)
                self.say(f"Bayes: {result['posterior']:.0%} blocked. MDP: {result['action'].lower()}. A star: {result['steps']} grid moves. Follow the safe route to an exit.")
            else:
                self.say('Decision accepted. Movement speed increased. Follow the STAIRS direction above, then press E at a green gate.')
        else:
            self.errors+=1
            self.save()
            if self.errors>=3:
                self.end(False)
            else:
                self.say('That decision increased the security lock level. Reconsider the evidence.')

    def save(self):
        temp=SAVE.with_suffix('.tmp')
        try:
            temp.write_text(json.dumps({'floor':self.floor,'errors':self.errors,'solved':self.solved,'puzzle_stage':self.puzzle_stage,'evidence':sorted(self.evidence),'elapsed':self.elapsed,'ending':self.ending}))
            temp.replace(SAVE)
        except OSError as error:
            self.message='Checkpoint could not be written. You can continue this session.'
            print('Checkpoint error:', error)
            self.update_hud()

    def resume(self):
        try:
            state=json.loads(SAVE.read_text())
            if state.get('ending'):
                self.say('This run has ended. Press R to start again.')
                return
            floor=state['floor']
            errors=state['errors']
            solved=state['solved']
            evidence=state.get('evidence', [])
            elapsed=state.get('elapsed', 0)
            puzzle_stage=state.get('puzzle_stage',2 if solved else 0)
            if type(puzzle_stage) is not int or not 0<=puzzle_stage<=2:
                raise ValueError('Invalid puzzle stage')
            if type(floor) is not int or floor not in NAMES or type(errors) is not int or not 0 <= errors < 3 or type(solved) is not bool:
                raise ValueError('Invalid checkpoint types')
            if not isinstance(evidence,list) or any(type(item) is not int or item not in (0,1) for item in evidence):
                raise ValueError('Invalid evidence')
            if type(elapsed) not in (int,float) or not math.isfinite(elapsed) or elapsed<0:
                raise ValueError('Invalid elapsed time')
            self.puzzle_stage=puzzle_stage
            self.floor=floor
            self.errors=errors
            self.solved=solved
            self.evidence=set(evidence)
            self.elapsed=elapsed
            self.ending=None
        except (OSError, ValueError, KeyError, TypeError):
            self.say('No valid checkpoint is available.')
            return
        self.credits.hide()
        self.sounds['ambient'].play()
        self.set_stair_hud(True)
        self.stair_fade.hide(); self.arrival_fade=0
        self.scene_time=33
        self.heading=0
        self.pitch=-6
        self.transition=0
        self.finished=False
        self.make_level()
        self.position=list(xyz(START,1.6))
        self.close_panel()
        self.last_cell = None
        self.set_camera()
        self.set_mouse_capture(True)
        self.say('Checkpoint restored. Continue to the terminal or stair gate.')

    def reset_mission(self):
        self.credits.hide()
        self.sounds['ambient'].play()
        self.set_stair_hud(True)
        self.stair_fade.hide(); self.arrival_fade=0
        self.puzzle_stage=0
        self.floor=4; self.errors=0; self.solved=False; self.finished=True
        self.evidence=set(); self.ending=None; self.elapsed=0
        self.scene_time=0; self.transition=0
        self.heading=0
        self.pitch=-6
        self.raw_movement.clear()
        for key in self.keys:
            self.keys[key]=False
        self.position=list(xyz(START,1.6))
        self.make_level(); self.close_panel(); self.save()
        self.last_cell = None
        self.redraw()
        self.show_lecture()
        self.say('Welcome to Qairu. Today we connect A star search, Bayesian inference and expected utility. Press W A S D or Space to skip the lecture and move.')

    def end(self, success):
        self.finished=True
        self.ending='success' if success else 'failure'
        self.ending_time=0
        self.close_panel()
        self.say('You and the students escaped. Look back at the glass sphere. Press R to replay.' if success else 'All exits are locked after three wrong decisions. Press R to try again.')
        self.set_mouse_capture(self.mouse_locked)
        if not success:
            for x in (0,20):
                self.box((x,0,1.4),(2.8,.3,2.8),(.65,.12,.12))
            self.overlay.show()
            self.overlay_text.setText('ALL EXITS LOCKED\n\nThree incorrect decisions triggered the security lockdown.\nReview the evidence and expected consequences.\n\nR starts a new run.')
            self.overlay_text.show()
        if success:
            self.build_exterior()
            self.position=[10,-53,4]
            self.heading=0; self.pitch=12
            self.set_camera()
            for node, (x,y,heading) in zip(self.npcs, (
                    (7.3,-47.5,163), (8.2,-46.7,128), (10.1,-48.0,184),
                    (11.3,-47.8,207), (13.2,-46.5,229), (13.9,-47.2,201))):
                node.setPos(x,y,0)
                node.setH(heading)
            for gait in self.npc_gaits:
                gait.reset()
        self.save()

    def animate_environment(self, dt):
        target=1 if self.solved and self.ending!='failure' else 0
        self.gate_open += (target-self.gate_open)*min(1,dt*3)
        for panel, origin, side in self.gate_panels:
            panel.setX(origin+side*1.25*self.gate_open)
        pulse=.55+.45*math.sin(self.scene_time*5)
        for light in self.warning_lights:
            if self.solved and self.ending!='failure':
                light.setColor(.12,.75,.4,1)
            else:
                light.setColor(.5+.4*pulse,.08+.08*pulse,.04,1)

    def set_camera(self):
        x,y,z = self.position
        self.camera.setPos(x,y,z+(self.world.getZ() if self.world is not None else 0))
        self.camera.setHpr(self.heading, self.pitch, 0)

    def tick(self, task):
        dt=min(self.clock.getDt(),.06)
        self.animate_environment(dt)
        if self.arrival_fade>0:
            self.arrival_fade=max(0,self.arrival_fade-dt)
            self.stair_fade.setColor(.025,.04,.05,self.arrival_fade/.45)
            if not self.arrival_fade: self.stair_fade.hide()
        self.scene_time+=dt
        if not self.ending:
            self.elapsed+=dt
        if self.ending:
            self.ending_time+=dt
            if self.ending=='success':
                t=min(self.ending_time/10,1)
                ease = t*t*(3-2*t)
                self.camera.setPos(10+5*ease,-53-27*ease,2.1+5.9*ease)
                self.camera.lookAt(10,-18,4.7+12.5*ease)
                self.credits.update(self.ending_time)
            return Task.cont
        if self.scene_time < LECTURE_DURATION:
            if self.lecture is not None:
                animate_lecture(self.camera, self.audience, self.presenter, self.scene_time)
            for threshold, line in [(8, 'A star compares distance travelled with an estimate to the goal. Its heuristic must never overestimate.'), (17, 'Bayesian inference updates a prior belief using evidence. Expected utility weighs the possible consequences of each action.'), (26, 'Technical malfunction detected. Please remain calm. The elevators are blocked.')]:
                if self.scene_time-dt < threshold <= self.scene_time:
                    self.say(line)
            return Task.cont
        if self.finished:
            self.begin_evacuation()
        else:
            self.close_lecture()
        if self.transition:
            self.transition=max(0,self.transition-dt)
            progress=1-self.transition/STAIR_DURATION
            smooth=progress*progress*(3-2*progress)
            self.stair_fade.show()
            self.stair_fade.setColor(.025,.04,.05,max(0,(progress-.90)/.10))
            x, y, z = self.position
            camera_y = y + (9.1-y)*smooth
            drop = min(FLOOR_SPACING, max(0,camera_y-1.85)*FLOOR_SPACING/(23*.31))
            self.camera.setPos(x+(self.stair_x-x)*min(1,smooth*4),
                               camera_y,self.world.getZ()+z-drop)
            self.camera.setHpr(0,-30-8*math.sin(progress*math.pi),0)
            if not self.transition:
                self.set_stair_hud(True)
                self.floor-=1; self.solved=False
                self.puzzle_stage=0
                self.evidence=set()
                self.heading=0; self.pitch=-6
                self.position=[self.stair_x,-.8,1.6]
                self.heading=180
                self.arrival_fade=.45
                self.make_level(); self.save()
                self.last_cell = None
                self.set_camera()
                self.say('Floor '+str(self.floor)+'. '+NAMES[self.floor]+'. Inspect the terminal.')
            return Task.cont
        previous_position = self.position[:]
        if not self.panel:
            self.update_look(dt)
            self.move_player(dt)
        self.set_camera()
        current_cell = cell_at(*self.position[:2])
        if current_cell != self.last_cell:
            self.last_cell = current_cell
            self.redraw()
        self.update_hud()
        travelled = math.hypot(self.position[0]-previous_position[0],
                               self.position[1]-previous_position[1])
        self.animate_player_walk(travelled, dt)
        if not self.finished:
            self.walk_students(dt)
        return Task.cont


    def animate_player_walk(self, travelled, dt):
        step_length = .76
        old_step = self.walk_distance / step_length
        self.walk_distance += travelled
        step = self.walk_distance / step_length
        if int(step) > int(old_step):
            self.sounds['step'].play()
        target = min(1., travelled / (WALK_SPEED*dt)) if dt else 0.
        self.walk_weight += (target-self.walk_weight) * (1-math.exp(-13*dt))
        self.camera.setZ(self.camera.getZ()-.014*math.cos(math.tau*step)*self.walk_weight)
        self.camera.setR(.19*math.sin(math.pi*step)*self.walk_weight)

    def walk_students(self, dt):
        for i, (node, route, gait) in enumerate(zip(self.npcs,self.student_routes,self.npc_gaits)):
            remaining = dt*(.65+i*.04)
            travelled = 0.
            while route and remaining > 0:
                tx,ty = route[0]
                dx,dy = tx-node.getX(),ty-node.getY()
                distance = math.hypot(dx,dy)
                if distance < .001:
                    route.pop(0)
                    continue
                stride = min(remaining,distance)
                node.setX(node.getX()+dx/distance*stride)
                node.setY(node.getY()+dy/distance*stride)
                desired = math.degrees(math.atan2(-dx,dy))
                delta = (desired-node.getH()+180)%360-180
                node.setH(node.getH()+max(-310*dt,min(310*dt,delta)))
                travelled += stride
                remaining -= stride
                if stride == distance:
                    route.pop(0)
            gait.update(travelled,dt)
