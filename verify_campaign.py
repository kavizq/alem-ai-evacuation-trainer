"""Local graphics and campaign integration verification with isolated saves."""
import tempfile
from pathlib import Path
import campaign
from ai_core import START
from main_before_campaign import xyz

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE = Path(folder)/'save.json'
    game = campaign.Campaign()
    game.scene_time = 33
    game.finished = False
    for floor in (4,3,2,1):
        assert game.floor == floor
        for index, point in enumerate(game.evidence_positions):
            game.position = [point[0], point[1]-1, 1.6]
            game.interact()
        assert len(game.evidence)==2
        game.position = [game.terminal_xy[0], game.terminal_xy[1]-1, 1.6]
        game.interact()
        assert game.panel
        for stage in range(3):
            game.answer(campaign.correct_answer(floor,stage,campaign.QUESTIONS))
        assert game.solved
        game.position = [0,17 if floor==1 else 0,1.6]
        game.interact()
        if floor > 1:
            assert game.transition
            game.transition = .001
            game.clock.setDt(.02)
            game.tick(None)
    assert game.finished and game.position[1] == -53
    for _ in range(5):
        game.graphicsEngine.renderFrame()
    game.win.saveScreenshot('verification/success.png')
    game.reset_mission()
    game.scene_time=33
    game.finished=False
    game.evidence={0,1}
    game.position = [game.terminal_xy[0],game.terminal_xy[1]-1,1.6]
    game.interact()
    for _ in range(3):
        game.answer(1)
    assert game.finished and game.errors == 3
    game.reset_mission()
    game.floor = 3
    game.errors = 1
    game.save()
    game.floor = 4
    game.resume()
    assert game.floor == 3 and game.errors == 1
    game.set_camera()
    for _ in range(5):
        game.graphicsEngine.renderFrame()
    game.win.saveScreenshot('verification/floor3.png')
    print('PASS: four floors, successful exit, three-error failure, checkpoint restore, graphics frames')
    if game.voice and game.voice.poll() is None:
        game.voice.terminate()
    game.destroy()
