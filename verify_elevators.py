"""Check elevator access and all floor-specific neighbors."""
from pathlib import Path
import tempfile
import campaign
from navigation import walking_path
from ai_core import START
from main_before_campaign import xyz

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro()
    game.tick(None)
    game.mouse_locked=False
    for floor in (4,3,2,1):
        game.floor=floor
        game.solved=False
        game.make_level()
        assert walking_path(xyz(START)[:2],(22,-25.5),game.can_walk), ('approach blocked',floor)
        assert not game.can_walk(22,-23)
        z=game.world.getZ()
        for name,pos in (('front',(22,-29,1.7)),('side',(26,-28,1.7))):
            game.camera.setPos(pos[0],pos[1],z+pos[2])
            game.camera.lookAt(22,-24,z+1.65)
            game.update_hud()
            for _ in range(4): game.graphicsEngine.renderFrame()
            game.win.saveScreenshot(f'verification/elevator_floor{floor}_{name}.png')
        print(f'PASS floor {floor}: reachable frontage, solid shaft, front and side rendered')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
