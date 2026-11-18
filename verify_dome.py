"""Render upward atrium views on every floor."""
from pathlib import Path
import tempfile
import campaign
with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro()
    game.tick(None)
    for floor in (4,3,2,1):
        game.floor=floor
        game.make_level()
        z=game.world.getZ()
        game.position=[22,-8,1.6]
        game.camera.setPos(22,-8,z+1.6)
        game.camera.lookAt(28,-11,23)
        game.update_hud()
        for _ in range(4): game.graphicsEngine.renderFrame()
        game.win.saveScreenshot(f'verification/dome_floor{floor}.png')
        print('Rendered dome from floor',floor)
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
