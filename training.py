"""Practical evacuation training on the preserved four-floor 3D environment."""
import json
import math
import textwrap
import sys
from pathlib import Path
from direct.task import Task
from panda3d.core import LineSegs, PNMImage, Texture
from campaign import Campaign, NAMES, WALK_SPEED, LECTURE_DURATION, STAIR_DURATION
from navigation import walking_path
from training_core import SCENARIOS, TrainingSession, route_decision


ROOT = Path(__file__).parent


class Trainer(Campaign):
    def __init__(self, scenario='smoke', data_dir=None):
        if scenario not in SCENARIOS:
            raise ValueError('Unknown scenario')
        self.session = TrainingSession(scenario)
        self.data_dir = Path(data_dir) if data_dir else (Path(sys.executable).parent if getattr(sys,'frozen',False) else ROOT)/'user_data'
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.training_routes = {}
        self.decision = None
        self.selected_side = None
        self.closed_sides = set()
        self.suspect_side = None
        self.route_node = None
        self.live_update_done = False
        self.plan_age = 0.
        self.exposure_active = False
        self.map_age = 0.
        self.review = False
        super().__init__()
        self.play_controls = 'WASD move | Mouse/arrows look | E inspect | 1/2 choose route | 3 AI details | U update | F5 scenario | R new'
        self.ui_controls.setText(self.play_controls)
        self.accept('f5', self.next_scenario)
        self.physical_actions['u'] = self.trigger_update
        self.ui_title.setText('ALEM AI  /  EVACUATION TRAINER')
        self.ui_title.setScale(.039)
        self.say('Training exercise. Possible smoke near a technical room. Elevators are offline. Press SPACE to begin.')

    def say(self, message):
        if message.startswith('Welcome to'):
            message = 'Training exercise in Qairu. Practise choosing a route with uncertain sensor readings. SPACE begins.'
        elif message.startswith('Technical malfunction'):
            message = 'Training alarm: possible smoke near a technical room. Elevators are offline. Find the cyan route terminal.'
        elif message.startswith('A star compares') or message.startswith('Bayesian inference updates'):
            message = 'ADEKA combines A* route search, Bayesian sensor inference and a sequential MDP decision model.'
        self.message = 'ADEKA: '+message
        self.update_hud()

    def make_ui(self):
        super().make_ui()
        for element in (*self.map_cells.values(), *self.map_markers.values()):
            element.hide()
        aspect = self.getAspectRatio()
        self.floor_map = self.card(aspect-.60,.79,.51,.51,(1,1,1,1))
        self.map_texture = Texture('actual-collision-map')
        self.floor_map.setTexture(self.map_texture)
        self.lecture_hud.append(self.floor_map)
        self.overlay_text.setScale(.043)
        self.overlay_text.setWordwrap(39)
        self.overlay_text.setPos(-.84,.64)

    def make_level(self):
        self.selected_side = None
        self.decision = None
        self.closed_sides = set()
        self.route_node = None
        self.plan_age = 0.
        self.live_update_done = False
        self.training_routes = {}
        super().make_level()
        # Training gates are open. Route feedback never creates an emergency lock.
        self.solved = True
        self.gate_open = 1.
        self.route_node = self.world.attachNewNode('training-route')
        self.gate_targets = {'LEFT': (0.,15. if self.floor == 1 else -1.),
                             'RIGHT': (20.,15. if self.floor == 1 else -1.)}
        self.sensor_alert = SCENARIOS[self.session.scenario]['alert']
        if self.session.scenario == 'smoke' and self.floor == 3:
            self.sensor_alert = False
        self.suspect_side = None
        self.hazard_box = None
        self.map_base = None
        if hasattr(self,'floor_map'):
            self.refresh_map()

    def begin_evacuation(self):
        super().begin_evacuation()
        self.elapsed = 0.
        self.session.elapsed_s = 0.
        self.refresh_map()
        self.say('Exercise alarm: possible smoke. Elevators are offline. Visit the cyan terminal for a route, then lead the group downstairs.')

    def walk_speed(self):
        return WALK_SPEED

    def can_walk(self,x,y):
        if not super().can_walk(x,y):
            return False
        for side in self.closed_sides:
            if not hasattr(self,'gate_targets'):
                break
            gx,gy=self.gate_targets[side]
            if abs(x-gx)<1.7 and abs(y-(gy+.55))<.4:
                return False
        return True

    def _path(self, start, goal):
        # This is the same predicate used by move_player, on a half-metre grid.
        return walking_path(start, goal, self.can_walk)

    def calculate(self):
        origin = tuple(self.position[:2])
        routes = {side: self._path(origin, target) for side,target in self.gate_targets.items()}
        lengths = {side: sum(math.dist(a,b) for a,b in zip(path,path[1:]))
                   for side,path in routes.items() if path}
        if not lengths:
            self.decision = {'available': False, 'reason': 'No traversable route from this position'}
            return self.decision
        if self.suspect_side is None:
            self.suspect_side = min(lengths, key=lengths.get)
            if SCENARIOS[self.session.scenario]['closed']:
                self.closed_sides.add(self.suspect_side)
            self.add_hazard_marker()
        self.training_routes = routes
        self.decision = route_decision(lengths, self.suspect_side, self.sensor_alert, self.closed_sides)
        return self.decision

    def add_hazard_marker(self):
        if self.hazard_box:
            self.hazard_box.removeNode()
        x,y = self.gate_targets[self.suspect_side]
        self.hazard_center = (x,y-2.)
        # A sensor zone, not a confirmed fire. Its actual traversal is recorded.
        self.hazard_box = self.box((x,y-2.,.03),(3.,3.,.035),(.94,.55,.13))
        self.label('SENSOR ZONE',(x,y-2.,2.6),.13)
        for side in self.closed_sides:
            gx,gy = self.gate_targets[side]
            self.box((gx,gy+.55,1.3),(2.7,.18,2.6),(.67,.15,.12))
            self.label('UNAVAILABLE',(gx,gy+.40,2.85),.16)
        self.map_base = None

    def interact(self):
        if self.ending:
            return
        if self.finished or self.transition or self.panel:
            return
        x,y = self.position[:2]
        for index,(ex,ey) in enumerate(self.evidence_positions):
            if math.hypot(x-ex,y-ey) < 2.5:
                self.evidence.add(index)
                if index == 0:
                    self.say(f'Sensor report: {"ALERT" if self.sensor_alert else "NO ALERT"}. Sensitivity 80%, false-alarm rate 20%. The report is uncertain.')
                else:
                    self.say('Route board: both stairs lead down. An unavailable exit is excluded. Use E at the cyan terminal to compare the routes.')
                self.save()
                return
        if math.dist((x,y),self.terminal_xy) < 3.3:
            self.open_terminal()
            return
        for side,(gx,gy) in self.gate_targets.items():
            if math.hypot(x-gx,y-gy) < 2.2:
                if side in self.closed_sides:
                    self.say('This exit is unavailable in the exercise. Press U to calculate a new route from your current position.')
                    return
                if self.decision is None:
                    self.calculate()
                if not self.decision.get('available'):
                    self.say('No route available. Move back into the hall and rescan.')
                    return
                if self.selected_side != side:
                    self.session.unguided_exits += 1
                    self.session.record(self.floor,side,self.decision,'unguided exit')
                if self.floor not in self.session.floors_completed:
                    self.session.floors_completed.append(self.floor)
                if self.floor == 1:
                    self.end(True)
                else:
                    self.stair_x = 0 if side == 'LEFT' else 20
                    self.set_stair_hud(False)
                    self.transition = STAIR_DURATION
                    self.say('The group is descending the stairs. A new floor brings a new sensor report.')
                self.save()
                return
        self.say('E inspects amber stations and the cyan terminal. Follow the cyan floor route. H explains the next step.')

    def open_terminal(self):
        self.calculate()
        self.review = False
        self.panel = True
        self.set_mouse_capture(self.mouse_locked)
        self.overlay.setZ(.78)
        self.overlay.setSz(1.50)
        self.overlay.show()
        self.show_question()
        self.overlay_text.show()

    def show_question(self):
        d = self.decision
        if not d or not d.get('available'):
            body = 'NO TRAVERSABLE ROUTE\n\nMove to the open hall and try again.\n\nQ close'
        else:
            lengths = '   '.join(f'{s.title()} {v:.0f} m' for s,v in d['lengths'].items())
            q = d['qvalues']['JUNCTION']
            body = (f'FLOOR {self.floor} / ROUTE DECISION\n\n'
                    f'Sensor: {"ALERT" if self.sensor_alert else "NO ALERT"}\n'
                    f'Bayes: {d["posterior"]:.1%} blockage risk in {d["suspect"].lower()} approach\n'
                    f'A* collision-aware routes: {lengths}\n'
                    f'MDP recommends {d["recommendation"]} exit\n\n'
                    '1  Follow the AI recommendation\n'
                    '2  Choose the other available exit\n'
                    '3  Explain the algorithms\n\nQ close')
            if self.review:
                values = ' / '.join(f'{s}: {v:.1f}' for s,v in q.items())
                body = ('HOW ADEKA CHOOSES\n\n'
                        'Bayes: prior 20%, sensitivity 80%,\nfalse-alarm rate 20%. One current observation.\n\n'
                        f'MDP: {d["iterations"]} Bellman sweeps, discount 0.98.\n'
                        f'Expected return: {values}\n'
                        'Travel time costs reward. A blocked attempt\nreturns to the junction with a 90-unit penalty.\n\n'
                        'A* uses actual collision geometry at 0.5 m\nspacing. Closed exits have no MDP action.\n\n'
                        '1 use recommendation / 2 other route / Q close')
        self.overlay_text.setText(body)

    def answer(self, number):
        if not self.panel or self.ending or not self.decision or not self.decision.get('available'):
            return
        if number == 3:
            self.review = not self.review
            self.show_question()
            return
        if number not in (1,2):
            return
        d = self.decision
        side = d['recommendation']
        if number == 2:
            options = [s for s in d['lengths'] if s != side]
            if not options:
                self.say('Only one exit is available. Choose 1 or close the panel.')
                return
            side = options[0]
        self.select_route(side)
        self.close_panel()

    def select_route(self, side):
        if side not in self.decision['lengths'] or side in self.closed_sides:
            raise ValueError('Exit unavailable')
        if self.selected_side and self.selected_side != side:
            self.session.route_changes += 1
        self.selected_side = side
        self.session.record(self.floor,side,self.decision)
        self.plan_age = 0.
        self.draw_route()
        # Students share the selected actual-world destination and collision map.
        self.student_routes = [self._path((n.getX(),n.getY()),self.gate_targets[side])[1:] for n in self.npcs]
        risk = self.decision['posterior'] if side == self.suspect_side else 0.
        self.say(f'{side.title()} route selected, {self.decision["lengths"][side]:.0f} m. Modeled blockage risk {risk:.0%}. Follow the cyan guide. U checks for a route update.')
        self.save()

    def draw_route(self):
        if not self.route_node:
            return
        self.route_node.getChildren().detach()
        path = self.training_routes.get(self.selected_side, [])
        if not path:
            return
        line = LineSegs('collision-aware A-star route')
        line.setThickness(4)
        line.setColor(.10,.91,.97,1)
        line.moveTo(path[0][0],path[0][1],.065)
        for x,y in path[1:]:
            line.drawTo(x,y,.065)
        self.route_node.attachNewNode(line.create())
        for x,y in path[::5]:
            self.box((x,y,.055),(.23,.23,.035),(.08,.83,.90),self.route_node)
        self.refresh_map()

    def trigger_update(self):
        if self.ending or self.transition or self.scene_time < LECTURE_DURATION:
            return
        if self.session.scenario == 'smoke' and self.floor == 2 and not self.live_update_done:
            if not self.selected_side:
                self.say('Choose a route first. Then U demonstrates an exit becoming unavailable.')
                return
            self.closed_sides.add(self.selected_side)
            self.live_update_done = True
            self.session.route_changes += 1
            self.selected_side = None
            self.add_hazard_marker()
            self.calculate()
            if self.decision.get('available'):
                self.select_route(self.decision['recommendation'])
                self.say('Exercise update: the planned exit is unavailable. ADEKA excluded it and recalculated the route. Follow the new cyan guide.')
            else:
                self.route_node.getChildren().detach()
                self.say('No traversable route. Stay in the hall and ask the exercise instructor for help.')
            self.save()
        else:
            self.calculate()
            if self.decision.get('available'):
                self.select_route(self.decision['recommendation'])
            if self.panel:
                self.show_question()

    def hint(self):
        self.session.hints += 1
        self.say('Find the cyan terminal, press E, then 1 to accept ADEKA. Follow the cyan floor line to the chosen stairs. On floor 2, U demonstrates replanning.')

    def update_hud(self):
        if not hasattr(self,'ui_stats'):
            return
        self.ui_map_title.setText('FLOOR PLAN / LIVE ROUTE')
        self.ui_map_title.setScale(.029)
        d = self.decision or {}
        status = (f'Risk {d["posterior"]:.0%} / AI {d["recommendation"]}' if d.get('available') else 'Find the cyan route terminal')
        self.ui_stats.setText(f'FLOOR {self.floor} / {NAMES[self.floor]}\n{SCENARIOS[self.session.scenario]["name"]}\n{status}\n'+(f'Follow {self.selected_side} exit' if self.selected_side else 'E inspect / F5 change scenario'))
        self.ui_stats.setScale(.032)
        self.ui_message.setText(textwrap.fill(self.message,112))
        self.ui_message.setScale(.035)
        self.ui_event.setText(f'Time {int(self.session.elapsed_s)} s / Distance {self.session.distance_m:.0f} m / Replans {self.session.route_changes} / U route update')
        self.update_navigation()

    def update_navigation(self):
        if not hasattr(self,'nav_text') or not hasattr(self,'gate_targets'):
            return
        if self.selected_side:
            path = self.training_routes.get(self.selected_side,[])
            nearest = min(range(len(path)), key=lambda i: math.dist(self.position[:2],path[i])) if path else 0
            target = path[min(nearest+4,len(path)-1)] if path else self.gate_targets[self.selected_side]
            name = self.selected_side+' / CYAN ROUTE'
        else:
            target = (9.,-17.)
            name = 'CYAN TERMINAL'
        x,y = self.position[:2]
        dx,dy = target[0]-x,target[1]-y
        angle = (math.degrees(math.atan2(-dx,dy))-self.heading+180)%360-180
        direction = 'AHEAD' if abs(angle)<25 else ('BEHIND' if abs(angle)>145 else ('LEFT' if angle>0 else 'RIGHT'))
        self.nav_text.setText(f'{name}\n{math.hypot(dx,dy):.0f} m to next point / {direction}')
        self.nav_text.setScale(.032)

    def redraw(self):
        self.refresh_map()
        self.update_hud()

    def refresh_map(self):
        if not hasattr(self,'floor_map') or not hasattr(self,'gate_targets'):
            return
        size=132
        if self.map_base is None:
            self.map_base = PNMImage(size,size,3)
            for iy in range(size):
                for ix in range(size):
                    x,y = -21+ix*.5, 21-iy*.5
                    color = (.31,.39,.43) if self.can_walk(x,y) else (.07,.11,.15)
                    self.map_base.setXel(ix,iy,*color)
        image=PNMImage(self.map_base)
        def dot(point,color,radius=1):
            ix,iy = round((point[0]+21)*2),round((21-point[1])*2)
            for yy in range(iy-radius,iy+radius+1):
                for xx in range(ix-radius,ix+radius+1):
                    if 0<=xx<size and 0<=yy<size:
                        image.setXel(xx,yy,*color)
        for p in self.training_routes.get(self.selected_side,[]):
            dot(p,(.1,.91,.97),0)
        for side,p in self.gate_targets.items():
            dot(p,(.95,.2,.15) if side in self.closed_sides else (.19,.9,.42),2)
        dot((9,-16),(.1,.8,.9),2)
        if self.suspect_side:
            dot(self.hazard_center,(1.,.6,.15),2)
        dot(self.position[:2],(1.,1.,1.),2)
        self.map_texture.load(image)

    def tick(self,task):
        if self.ending:
            self.ending_time += min(self.clock.getDt(),.06)
            return Task.cont
        before = tuple(self.position[:2])
        previous_floor = self.floor
        active = self.scene_time >= LECTURE_DURATION and not self.ending
        outcome = super().tick(task)
        dt = min(self.clock.getDt(),.06)
        if active:
            self.session.elapsed_s += dt
            if not self.transition and self.floor == previous_floor:
                self.session.distance_m += math.dist(before,self.position[:2])
            if self.suspect_side and self.sensor_alert:
                exposed = math.dist(self.position[:2],self.hazard_center) < 1.6
                if exposed and not self.exposure_active:
                    self.session.risk_entries += 1
                    self.say('You entered the sensor zone. This records a training risk event. Consider the alternative route.')
                self.exposure_active = exposed
        self.map_age += dt
        if self.map_age > .3 and not self.ending:
            self.map_age = 0.
            self.refresh_map()
        return outcome

    def walk_students(self,dt):
        if self.selected_side:
            super().walk_students(dt)

    def save(self):
        if not hasattr(self,'position'):
            return
        data = {'version':1, 'floor':self.floor, 'position':list(self.position),
                'heading':self.heading, 'session':self.session.to_dict(),
                'closed':sorted(self.closed_sides), 'suspect':self.suspect_side,
                'selected':self.selected_side, 'live_update':self.live_update_done,
                'ending':self.ending}
        target=self.data_dir/'training_save.json'
        temp=target.with_suffix('.tmp')
        try:
            temp.write_text(json.dumps(data,indent=2),encoding='utf-8')
            temp.replace(target)
        except OSError:
            self.say('The checkpoint could not be saved. You can continue this session.')

    def resume(self):
        try:
            data=json.loads((self.data_dir/'training_save.json').read_text(encoding='utf-8'))
            session=TrainingSession.from_dict(data['session'])
            floor=data['floor']; position=data['position']; heading=data['heading']
            if type(floor) is not int or floor not in (1,2,3,4) or data.get('ending'):
                raise ValueError('Checkpoint is not an active run')
            if not isinstance(position,list) or len(position)!=3 or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in position):
                raise ValueError('Invalid checkpoint position')
            if math.hypot(position[0]-10,position[1]+10)>30 or not 1<=position[2]<=2:
                raise ValueError('Checkpoint outside floor')
            if isinstance(heading,bool) or not isinstance(heading,(int,float)) or not math.isfinite(heading):
                raise ValueError('Invalid heading')
            closed=set(data.get('closed',[]))
            if not closed <= {'LEFT','RIGHT'} or data.get('selected') not in (None,'LEFT','RIGHT') or data.get('suspect') not in (None,'LEFT','RIGHT'):
                raise ValueError('Invalid exits')
        except (OSError,ValueError,KeyError,TypeError):
            self.say('No valid training checkpoint. Your current session is unchanged.')
            return
        self.credits.hide()
        self.session=session; self.floor=floor
        self.make_level()
        self.scene_time=LECTURE_DURATION;self.finished=False;self.ending=None;self.transition=0
        self.position=position;self.heading=heading
        self.closed_sides=closed;self.suspect_side=data.get('suspect')
        self.live_update_done=bool(data.get('live_update'))
        if not self.can_walk(*position[:2]):
            self.position=[9.,-17.,1.6]
        if self.suspect_side:
            self.add_hazard_marker()
        self.calculate()
        selected=data.get('selected')
        if selected and self.decision.get('available') and selected in self.decision['lengths']:
            self.selected_side=selected;self.draw_route()
            self.student_routes=[self._path((n.getX(),n.getY()),self.gate_targets[selected])[1:] for n in self.npcs]
        self.close_lecture();self.close_panel();self.set_stair_hud(True);self.set_camera()
        self.set_mouse_capture(True)
        self.say('Training checkpoint restored. Continue along the cyan route.')

    def reset_mission(self):
        self.session=TrainingSession(self.session.scenario)
        self.credits.hide()
        self.set_stair_hud(True)
        self.ending=None;self.floor=4;self.transition=0;self.elapsed=0.;self.scene_time=0.
        self.finished=True;self.evidence=set();self.heading=0;self.pitch=-6
        self.raw_movement.clear()
        for key in self.keys:self.keys[key]=False
        self.make_level();self.close_panel();self.show_lecture();self.save()
        self.say('New training exercise. SPACE begins. F5 changes the scenario.')

    def next_scenario(self):
        keys=list(SCENARIOS)
        self.session.scenario=keys[(keys.index(self.session.scenario)+1)%len(keys)]
        self.reset_mission()

    def end(self,success):
        if not success:
            self.say('Training continues. Recheck the route at the terminal.')
            return
        super().end(True)
        report=self.session.to_dict()
        report['completed']=True
        report['scope']='Synthetic exercise metrics. No measured learning or real-world safety claim.'
        try:
            (self.data_dir/'last_result.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        except OSError:
            self.message='ADEKA: Exercise completed. Results could not be written; the summary remains on screen.'
        self.show_results()

    def show_results(self):
        self.credits.hide()
        self.overlay.setZ(.78);self.overlay.setSz(1.5);self.overlay.show()
        final_by_floor={d['floor']:d for d in self.session.decisions}
        risks=sum(d['modeled_risk'] for d in final_by_floor.values())
        baseline=sum(d['baseline_risk'] for d in final_by_floor.values())
        self.overlay_text.setText('TRAINING COMPLETE\n\n'
            f'Floors completed: {len(self.session.floors_completed)} / 4\n'
            f'Time: {self.session.elapsed_s:.0f} s\nDistance walked: {self.session.distance_m:.0f} m\n'
            f'Route changes: {self.session.route_changes}\n'
            f'Sensor-zone entries: {self.session.risk_entries}\n'
            f'Exits used without selected guidance: {self.session.unguided_exits}\n\n'
            f'Summed modeled route risk: {risks:.2f}\n'
            f'Shortest-only baseline at same decisions: {baseline:.2f}\n'
            'These are model scores, not incident probabilities.\n\n'
            'Results saved in user_data/last_result.json\nR new exercise / F5 next scenario')
        self.overlay_text.show()
        self.set_mouse_capture(False)

    def close_panel(self):
        if self.ending:
            return
        super().close_panel()

    def set_stair_hud(self,visible):
        super().set_stair_hud(visible)
        for element in (*self.map_cells.values(),*self.map_markers.values()):
            element.hide()
