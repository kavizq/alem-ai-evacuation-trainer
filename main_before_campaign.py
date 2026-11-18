"""ADEKA — fictional 3D AI Fundamentals learning simulation, macOS compatibility edition (card-based world geometry).

Uses Panda3D's fixed-function OpenGL 2.1 renderer rather than Ursina generated
GLSL shaders. Preserves ai_core.py completely: A*, Bayes, one-step MDP.
Not a real building layout or a real-life emergency navigation system.

Run: python main.py   (place beside ai_core.py)
"""
from panda3d.core import loadPrcFileData

# macOS compatibility renderer: no automatic GLSL 130/140 generation.
loadPrcFileData('', 'gl-version 2 1')
loadPrcFileData('', 'win-size 1152 720')
loadPrcFileData('', 'window-title Alem.ai | ADEKA | AI Fundamentals')
loadPrcFileData('', 'sync-video true')
loadPrcFileData('', 'show-frame-rate-meter false')

import math
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenText import OnscreenText
from direct.task import Task
from panda3d.core import (
    ClockObject, TextNode, CardMaker,
    TransparencyAttrib, WindowProperties,
)
from ai_core import (
    MAP, START, EXITS, SUSPECT_CORRIDOR, SENSOR_TERMINAL,
    PRIOR_BLOCKED, SENSOR_SENSITIVITY, SENSOR_FALSE_ALARM, analyze,
)

CELL = 4.0
ROWS, COLS = len(MAP), len(MAP[0])


def xyz(cell, z=0.0):
    """Grid row goes north (+Y); columns go east (+X)."""
    return (cell[1] * CELL, -cell[0] * CELL, z)


def cell_at(x, y):
    r = max(0, min(ROWS - 1, round(-y / CELL)))
    c = max(0, min(COLS - 1, round(x / CELL)))
    return (r, c)


# Use Panda3D CardMaker geometry for every world object. This is the same
# primitive type successfully used by the 2D HUD; it avoids custom mesh
# vertex/normal/index handling and auto-generated GLSL shaders on macOS.
WORLD_CARD = CardMaker('adeka-world-face')
WORLD_CARD.setFrame(-0.5, 0.5, -0.5, 0.5)
WORLD_FACE_GEOM = WORLD_CARD.generate()



class Game(ShowBase):
    def __init__(self):
        super().__init__()
        self.disableMouse()
        self.setBackgroundColor(.055, .095, .15, 1)
        self.render.setShaderOff(1)
        self.aspect2d.setShaderOff(1)
        self.render.setLightOff(1)

        self.heading = 0.0
        self.pitch = -6.0
        self.position = list(xyz(START, 1.60))
        self.keys = {'w':False,'a':False,'s':False,'d':False,
                     'arrow_left':False,'arrow_right':False,
                     'arrow_up':False,'arrow_down':False}
        self.alert = None
        self.result = None
        self.show_route = True
        self.lesson_visible = False
        self.finished = False
        self.last_cell = None
        self.route_parts = []
        self.map_cells = {}
        self.mouse_locked = False
        self.message = 'Approach the cyan terminal and press E to scan.'
        self.last_event = '[A* Search] A route to an exit has been calculated.'
        self.clock = ClockObject.getGlobalClock()
        self.set_camera()
        self.make_level()
        print("[3D] Created floor, walls and objects from standard Panda3D cards")
        self.make_ui()
        self.register_controls()
        self.redraw()
        self.lock_mouse()
        self.taskMgr.add(self.tick, 'adeka_player_and_ai_update')

    def box(self, location, scale, rgb, parent=None):
        """Make a world-space cuboid from six standard CardMaker quads.

        CardMaker is known to work because the HUD/map use the same Panda3D
        primitive. This avoids a custom Geom that was invisible on the Mac.
        The unit cuboid is centered at the origin and scaled as one parent.
        """
        item = (parent or self.render).attachNewNode('world-cuboid')
        item.setPos(*location)
        item.setScale(*scale)
        item.setColor(rgb[0], rgb[1], rgb[2], 1)
        item.setShaderOff(1)
        item.setLightOff(1)
        item.setTwoSided(True)
        faces = (
            ((0, -0.5, 0), (0, 0, 0)),       # front
            ((0,  0.5, 0), (180, 0, 0)),     # rear
            ((-0.5, 0, 0), (90, 0, 0)),      # left
            (( 0.5, 0, 0), (-90, 0, 0)),     # right
            ((0, 0,  0.5), (0, -90, 0)),     # ceiling/top
            ((0, 0, -0.5), (0, 90, 0)),      # bottom
        )
        for pos, hpr in faces:
            face = item.attachNewNode(WORLD_FACE_GEOM)
            face.setPos(*pos)
            face.setHpr(*hpr)
            face.setTwoSided(True)
        return item

    def make_level(self):
        self.box((10, -10, -.24), (27, 27, .35), (.13, .19, .27))
        for row, line in enumerate(MAP):
            for col, char in enumerate(line):
                loc = xyz((row,col))
                tint = .02 if (row + col) % 2 else 0
                self.box((loc[0],loc[1], .015), (3.98,3.98,.065),
                         (.30+tint,.40+tint,.49+tint))
                if char == '#':
                    self.box((loc[0],loc[1],1.65), (3.95,3.95,3.3),
                             (.38,.50,.62))
                    self.box((loc[0],loc[1],3.34), (3.96,3.96,.10),
                             (.10,.80,.91))
        # Perimeter is imaginary: intentionally not a real Alem.ai floor plan.
        for x in (-2.15,22.15):
            self.box((x,-10,1.75),(.35,25.3,3.5),(.27,.39,.50))
        for y in (-22.15,2.15):
            self.box((10,y,1.75),(25.3,.35,3.5),(.27,.39,.50))
        # Decorative display beams. No roof mesh hides the view.
        for n in range(6):
            p = n * 4
            self.box((p,-10,3.75),(.11,24,.11),(.12,.60,.75))
            self.box((10,-p,3.75),(24,.11,.11),(.12,.60,.75))
        for exit_cell in EXITS:
            x,y,_ = xyz(exit_cell)
            self.box((x,y,.15),(2.7,2.7,.12),(.14,.85,.39))
            self.box((x,y,2.2),(2.9,.16,.50),(.10,.86,.41))
            for side in (-1.4,1.4):
                self.box((x+side,y,1.2),(.15,.15,2.1),(.12,.80,.41))
        x,y,_ = xyz(SUSPECT_CORRIDOR)
        self.box((x,y,.16),(2.8,2.8,.10),(.95,.52,.10))
        sx,sy,_ = xyz(SENSOR_TERMINAL)
        self.terminal_xy = (sx+1.0,sy)
        self.box((sx+1.0,sy,1.10),(.90,.70,2.20),(.08,.55,.66))
        self.box((sx+1.0,sy-.38,1.44),(.74,.10,.80),(.20,.95,.98))

    def card(self, x, top, width, height, rgba):
        cm = CardMaker('hud-panel')
        cm.setFrame(0,width,-height,0)
        node = self.aspect2d.attachNewNode(cm.generate())
        node.setPos(x, 0, top)
        node.setColor(*rgba)
        node.setTransparency(TransparencyAttrib.MAlpha)
        node.setBin('fixed',10)
        node.setDepthTest(False)
        node.setDepthWrite(False)
        return node

    def text(self, body, x, y, scale=.045, fg=(1,1,1,1)):
        item = OnscreenText(parent=self.aspect2d, text=body,
                            pos=(x,y), align=TextNode.ALeft, scale=scale,
                            fg=fg, mayChange=True, shadow=(0,0,0,.7),
                            shadowOffset=(.002,-.002))
        item.setBin('fixed',15)
        item.setDepthTest(False)
        return item

    def make_ui(self):
        # In Panda3D aspect2d uses ±(window width/window height) horizontally.
        aspect = self.getAspectRatio()
        left, right = -aspect+.045, aspect-.045
        self.card(left-.025,.97,1.11,.53,(.035,.065,.12,.91))
        self.card(right-.59,.97,.64,.69,(.035,.065,.12,.93))
        self.card(left-.025,-.57,aspect*2-.04,.39,(.035,.065,.12,.90))
        self.ui_title = self.text('ALEM.AI  |  ADEKA',left,.90,.058,(.22,.96,.98,1))
        self.ui_stats = self.text('',left,.79,.042)
        self.ui_map_title = self.text('FICTIONAL MAP 6x6',right-.55,.88,.041,(.22,.96,.98,1))
        start_x,start_y = right-.55,.78
        for r in range(ROWS):
            for c in range(COLS):
                self.map_cells[(r,c)] = self.card(start_x+c*.085,start_y-r*.084,
                                                     .074,.073,(.20,.29,.40,1))
        self.ui_message = self.text('',left,-.63,.046,(.95,.97,.99,1))
        self.ui_event = self.text('',left,-.72,.039,(.29,.78,1,1))
        self.ui_controls = self.text('WASD: MOVE | MOUSE/ARROWS: LOOK | E: SCAN | 1/2: TEST | TAB: PATH | Q: AI | R: RESTART | ESC: MOUSE',
                                      left,-.87,.032,(.74,.81,.91,1))
        self.overlay = self.card(-.90,.46,1.80,.96,(.015,.04,.09,.96))
        self.overlay_text = self.text('',-.82,.36,.045,(.93,.98,1,1))
        self.overlay.hide()
        self.overlay_text.hide()

    def register_controls(self):
        for key in self.keys:
            self.accept(key, self.key_set, [key, True])
            self.accept(key+'-up', self.key_set, [key, False])
        self.accept('e', self.scan, [None])
        self.accept('1', self.scan, [True])
        self.accept('2', self.scan, [False])
        self.accept('tab', self.toggle_route)
        self.accept('q', self.toggle_lecture)
        self.accept('r', self.reset_mission)
        self.accept('escape', self.toggle_mouse)
        self.accept('mouse1', self.lock_mouse)

    def key_set(self, key, value):
        self.keys[key] = value

    def set_camera(self):
        self.camera.setPos(*self.position)
        self.camera.setHpr(self.heading, self.pitch, 0)
        self.camLens.setFov(85)
        self.camLens.setNearFar(.05,180)

    def lock_mouse(self):
        if self.mouse_locked:
            return
        self.mouse_locked = True
        props = WindowProperties()
        props.setCursorHidden(True)
        self.win.requestProperties(props)
        props2 = self.win.getProperties()
        self.win.movePointer(0,props2.getXSize()//2,props2.getYSize()//2)

    def toggle_mouse(self):
        self.mouse_locked = not self.mouse_locked
        props = WindowProperties()
        props.setCursorHidden(self.mouse_locked)
        self.win.requestProperties(props)

    def toggle_route(self):
        self.show_route = not self.show_route
        self.last_event = '[A* Search] Route highlighting toggled.'
        self.redraw()

    def toggle_lecture(self):
        self.lesson_visible = not self.lesson_visible
        if self.lesson_visible:
            self.overlay.show()
            self.overlay_text.show()
        else:
            self.overlay.hide()
            self.overlay_text.hide()

    def scan(self, specified):
        if self.finished:
            return
        x,y,_ = self.position
        tx,ty = self.terminal_xy
        if specified is None:
            if math.hypot(x-tx,y-ty) > 3.3:
                self.message = 'ADEKA: Approach the cyan terminal before pressing E.'
                self.update_hud()
                return
            specified = True if self.alert is None else not self.alert
        self.alert = specified
        self.message = 'ADEKA: Sensor checked. Follow the blue route to the green exit.'
        self.redraw()
        self.last_event = (f'[BAYES] Sensor: {self.result["sensor"]} | '
                           f'{PRIOR_BLOCKED:.0%} -> {self.result["posterior"]:.2%}\n'
                           f'[MDP] {self.result["action"]} | '
                           f'[A*] {self.result["steps"]} steps to an exit.')
        self.update_hud()
        print('[Bayes] P(blocked) =',round(self.result['posterior'],6))
        print('[MDP] Decision =',self.result['action'],self.result['utilities'])
        print('[A* Search] Route =',self.result['path'])

    def redraw(self):
        for part in self.route_parts:
            part.removeNode()
        self.route_parts = []
        current = cell_at(self.position[0],self.position[1])
        self.result = analyze(current,self.alert)
        route = self.result['path']
        if self.show_route:
            for p in route[1:-1]:
                x,y,_ = xyz(p)
                self.route_parts.append(self.box((x,y,.21),(1.35,1.35,.12),(.16,.68,.99)))
        for grid_cell, card in self.map_cells.items():
            r,c = grid_cell
            if MAP[r][c]=='#': shade=(.55,.57,.60,1)
            elif grid_cell in EXITS: shade=(.12,.80,.36,1)
            elif grid_cell == SUSPECT_CORRIDOR: shade=(.97,.51,.10,1)
            elif grid_cell in route and self.show_route: shade=(.14,.64,.95,1)
            else: shade=(.20,.29,.40,1)
            card.setColor(*shade)
        self.map_cells[current].setColor(1,1,1,1)
        self.update_hud()

    def update_hud(self):
        if not self.result:
            return
        out = self.result
        self.ui_stats.setText(
            'MISSION: FIND AN EXIT\n'
            f'Sensor: {out["sensor"]}\n'
            f'[A* Search] Route length: {out["steps"]} steps\n'
            f'[Bayesian Inference] Blocked: {out["posterior"]:.2%}\n'
            f'[MDP] Proceed: {out["utilities"]["PROCEED"]:.2f}\n'
            f'[MDP] Detour: {out["utilities"]["DETOUR"]:.2f}\n'
            f'ADEKA recommends: {out["action"]}'
        )
        self.ui_message.setText(self.message)
        self.ui_event.setText(self.last_event)
        self.overlay_text.setText(
            'AI FUNDAMENTALS — THREE ALGORITHMS\n\n'
            '1. A* SEARCH: f(n) = g(n) + h(n)\n'
            '   Finds a path through known obstacles.\n\n'
            '2. BAYESIAN INFERENCE\n'
            f'   Prior {PRIOR_BLOCKED:.0%}, sensitivity {SENSOR_SENSITIVITY:.0%}, '
            f'false alarm {SENSOR_FALSE_ALARM:.0%}.\n'
            f'   Updated blockage probability: {out["posterior"]:.2%}.\n\n'
            '3. ONE-STEP MDP\n'
            '   Compare expected rewards of Proceed and Detour.\n'
            f'   Decision: {out["action"]}.\n\n'
            'Press Q to close. All values are classroom assumptions.'
        )

    # Panda3D ShowBase already defines restart(). Do not override it.
    def reset_mission(self):
        self.alert = None
        self.finished = False
        self.position = list(xyz(START, 1.60))
        self.heading = 0
        self.pitch = -6
        self.last_cell = None
        self.message = 'Approach the cyan terminal and press E to scan.'
        self.last_event = '[A* Search] A route to an exit has been calculated.'
        self.set_camera()
        self.redraw()

    def can_walk(self,x,y):
        # Simple geometric wall collisions; this is a fictional toy map.
        radius=.34
        if not (-1.6 < x < (COLS-1)*CELL+1.6): return False
        if not (-(ROWS-1)*CELL-1.6 < y < 1.6): return False
        for r,line in enumerate(MAP):
            for c,char in enumerate(line):
                if char=='#':
                    wx,wy,_=xyz((r,c))
                    if abs(x-wx)<CELL/2+radius and abs(y-wy)<CELL/2+radius:
                        return False
        return True

    def tick(self, task):
        dt=min(self.clock.getDt(),.06)
        if self.mouse_locked and self.win.getProperties().getForeground():
            props=self.win.getProperties()
            cx,cy=props.getXSize()//2,props.getYSize()//2
            mouse=self.win.getPointer(0)
            dx,dy=mouse.getX()-cx,mouse.getY()-cy
            if abs(dx)<250 and abs(dy)<200:
                self.heading-=dx*.15
                self.pitch=max(-70,min(70,self.pitch-dy*.12))
            self.win.movePointer(0,cx,cy)
        if self.keys['arrow_left']:self.heading+=110*dt
        if self.keys['arrow_right']:self.heading-=110*dt
        if self.keys['arrow_up']:self.pitch=min(70,self.pitch+75*dt)
        if self.keys['arrow_down']:self.pitch=max(-70,self.pitch-75*dt)

        if not self.finished:
            forward=(int(self.keys['w'])-int(self.keys['s']))
            sideways=(int(self.keys['d'])-int(self.keys['a']))
            if forward or sideways:
                rad=math.radians(self.heading)
                dx=(-math.sin(rad)*forward+math.cos(rad)*sideways)
                dy=(math.cos(rad)*forward+math.sin(rad)*sideways)
                norm=max(1.0,math.hypot(dx,dy))
                dx=dx/norm*5.2*dt
                dy=dy/norm*5.2*dt
                nx,ny=self.position[0]+dx,self.position[1]+dy
                if self.can_walk(nx,self.position[1]):self.position[0]=nx
                if self.can_walk(self.position[0],ny):self.position[1]=ny
        self.set_camera()
        current=cell_at(self.position[0],self.position[1])
        if current!=self.last_cell:
            self.last_cell=current
            self.redraw()
            if current in EXITS and not self.finished:
                if self.alert is None:
                    self.message='ADEKA: First check the sensor terminal, then reach an exit.'
                else:
                    self.finished=True
                    self.message='MISSION COMPLETE — You reached an exit! Press R to replay.'
                    self.last_event='[A* + BAYES + MDP] Path + probability + decision worked together.'
                self.update_hud()
        return Task.cont


if __name__ == '__main__':
    Game().run()
