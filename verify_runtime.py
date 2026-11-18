"""Exercise normal movement, pause, intro, and render throughput."""
import tempfile
import time
from pathlib import Path
import campaign

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.mouse_locked=False
    game.clock.setMode(game.clock.MNonRealTime)
    game.clock.setDt(1/60)
    assert len(game.audience) == 50 and game.world.isHidden()
    game.messenger.send('physical-key-down', ['w'])
    game.tick(None)
    assert not game.finished and game.scene_time>=32
    assert game.lecture is None and not game.world.isHidden()
    game.messenger.send('physical-key-up', ['w'])
    game.messenger.send('physical-key-down', ['w'])
    start_position = game.position[:]
    game.tick(None)
    assert game.position[1] > start_position[1]
    game.messenger.send('physical-key-up', ['w'])
    assert not game.raw_movement
    heading, pitch = game.heading, game.pitch
    game.messenger.send('arrow_left')
    game.messenger.send('arrow_up')
    game.tick(None)
    game.messenger.send('arrow_left-up')
    game.messenger.send('arrow_up-up')
    assert game.heading > heading and game.pitch > pitch
    game.position=[8,-20,1.6]
    game.heading=0
    game.pitch=-6
    game.keys['w']=True
    for _ in range(10): game.tick(None)
    assert game.position[1]>-20
    game.panel=True
    stopped=game.position[:]
    for _ in range(10): game.tick(None)
    assert game.position==stopped
    game.keys['w']=False
    game.close_panel()
    game.position=[8,-20,1.6]
    game.set_camera()
    start=time.perf_counter()
    for _ in range(180): game.graphicsEngine.renderFrame()
    elapsed=time.perf_counter()-start
    print(f'PASS W skips lecture, physical-key event, normal W movement, keyboard camera, and puzzle movement pause. 180 frames in {elapsed:.2f}s ({180/elapsed:.1f} frames/s).')
    game.win.saveScreenshot('verification/runtime.png')
    game.reset_mission()
    assert len(game.audience) == 50
    game.scene_time = campaign.LECTURE_DURATION - 1/120
    game.tick(None)
    assert game.lecture is None and not game.world.isHidden() and not game.finished
    print('PASS lecture closes and restores walking automatically at the end.')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
