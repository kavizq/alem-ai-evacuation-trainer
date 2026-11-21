"""Render the four user-reported architectural views with isolated saves."""
from pathlib import Path
import tempfile
import campaign

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro()
    game.tick(None)
    game.mouse_locked=False
    for name,pos,target in (
        ('elevator',(22,-29,1.7),(22,-24,1.65)),
        ('elevator_side',(26,-28,1.7),(22,-24,1.65)),
        ('elevator_approach',(19.5,-28,1.7),(22,-24,1.65)),
        ('atrium',(22,-11,1.7),(31,-10,-6)),
        ('partition',(6,-11,1.7),(4,-16,1.5)),
    ):
        z=game.world.getZ()
        game.camera.setPos(pos[0],pos[1],pos[2]+z)
        game.camera.lookAt(target[0],target[1],target[2]+z)
        for _ in range(4): game.graphicsEngine.renderFrame()
        game.win.saveScreenshot('verification/repaired_'+name+'.png')
    from navigation import walking_path
    assert walking_path(game.position[:2],(22,-25.5),game.can_walk), 'Elevator approach is blocked'
    assert game.can_walk(22,-25.5)
    assert not game.can_walk(22,-23)
    assert game.world.find('**/visible lower storeys').getNumChildren()==3
    print('PASS lower-storey geometry present and all three reported views rendered')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
