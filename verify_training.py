"""Integration check: actual movement, all floors/scenarios, updates and saves.

Run from the project folder: python verify_training.py
The offscreen Panda3D window still uses the real graphics pipeline.
"""
import json
import math
import tempfile
from pathlib import Path
from panda3d.core import loadPrcFileData
loadPrcFileData('', 'window-type offscreen\naudio-library-name null')
from training import Trainer
from navigation import walking_path
from platform_paths import panda_path
from credits import CARDS


def run():
    output=Path('verification');output.mkdir(exist_ok=True)
    records=[]
    with tempfile.TemporaryDirectory(dir=output) as folder:
        game=Trainer(data_dir=folder)
        game.clock.setMode(game.clock.MNonRealTime)
        game.clock.setDt(.02)
        game.mouse_locked=False
        def walk(target):
            path=walking_path(game.position[:2],target,game.can_walk)
            assert path,('unreachable',game.floor,game.position,target)
            assert all(game.can_walk(*p) for p in path),('path crosses collision',game.floor)
            for x,y in path[1:]:
                for _ in range(80):
                    dx,dy=x-game.position[0],y-game.position[1]
                    if math.hypot(dx,dy)<.055:break
                    game.heading=math.degrees(math.atan2(-dx,dy));game.keys['w']=True
                    game.tick(None)
                else:raise AssertionError(('stuck',game.floor,game.position,(x,y)))
            game.keys['w']=False
        for scenario in ('smoke','clear','blocked'):
            game.session.scenario=scenario;game.reset_mission();game.skip_intro()
            for floor in (4,3,2,1):
                assert game.floor==floor
                walk((9.,-17.))
                game.interact();assert game.panel
                assert game.decision['available']
                assert game.decision['residual']<1e-8
                for side,path in game.training_routes.items():
                    assert all(game.can_walk(*p) for p in path)
                game.answer(3);assert game.review
                if scenario=='smoke' and floor==4:
                    game.set_camera()
                    for _ in range(3):game.graphicsEngine.renderFrame()
                    game.win.saveScreenshot(panda_path(output/'ai-details.png'))
                game.answer(1);assert game.selected_side
                if scenario=='smoke' and floor==2:
                    previous=game.selected_side
                    game.trigger_update()
                    assert previous in game.closed_sides
                    assert game.selected_side!=previous
                    assert game.selected_side not in game.closed_sides
                    saved=game.session.to_dict()
                    game.save();game.resume()
                    assert game.live_update_done and previous in game.closed_sides
                    assert game.session.to_dict()==saved
                    assert game.selected_side not in game.closed_sides
                records.append({'scenario':scenario,'floor':floor,
                                'lengths_m':game.decision['lengths'],
                                'recommendation':game.selected_side,
                                'posterior':game.decision['posterior'],
                                'baseline':game.decision['baseline'],
                                'baseline_risk':game.decision['baseline_risk'],
                                'selected_risk':game.decision['selected_risk'],
                                'iterations':game.decision['iterations']})
                if scenario=='smoke':
                    game.heading=-45;game.pitch=-15;game.set_camera()
                    for _ in range(3):game.graphicsEngine.renderFrame()
                    game.win.saveScreenshot(panda_path(output/f'floor-{floor}.png'))
                walk(game.gate_targets[game.selected_side])
                game.interact()
                if floor>1:
                    assert game.transition
                    for _ in range(int(6/.02)+2):game.tick(None)
                else:
                    assert game.ending=='success'
                    assert len(game.session.floors_completed)==4
                    assert json.loads((Path(folder)/'last_result.json').read_text())['completed']
                    assert not game.results_shown
                    # Preserve the exact original closing cards and dedication.
                    for index,when in enumerate((12.,20.,31.)):
                        game.ending_time=when
                        game.tick(None)
                        assert game.credits.started
                        assert game.credits.text.getText()==CARDS[index]
                        if scenario=='smoke':
                            for _ in range(3):game.graphicsEngine.renderFrame()
                            game.win.saveScreenshot(panda_path(output/f'trainer-credit-{index+1}.png'))
                    game.messenger.send('enter')
                    assert game.results_shown and not game.credits.started
                    if scenario=='smoke':
                        for _ in range(3):game.graphicsEngine.renderFrame()
                        game.win.saveScreenshot(panda_path(output/'results.png'))
            print('PASS scenario',scenario,flush=True)
        # Invalid checkpoint must not mutate the active state.
        game.reset_mission();game.skip_intro()
        before=(game.floor,game.position[:],game.session.to_dict())
        (Path(folder)/'training_save.json').write_text('{"floor":2,"session":{"scenario":"smoke","elapsed_s":"bad"}}')
        game.resume()
        assert (game.floor,game.position[:],game.session.to_dict())==before
        print('PASS invalid checkpoint, live closure, explanation panel, complete collision-safe movement',flush=True)
        game.destroy()
    (output/'training_checks.json').write_text(json.dumps({'passed':True,'records':records},indent=2),encoding='utf-8')


if __name__=='__main__':run()
