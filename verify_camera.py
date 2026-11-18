"""Exercise camera control through the current graphical game loop."""
from pathlib import Path
import tempfile
import campaign
with tempfile.TemporaryDirectory() as directory:
    campaign.SAVE=Path(directory)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro()
    game.clock.setMode(game.clock.MNonRealTime)
    game.clock.setDt(1/60)
    game.mouse_locked=False
    heading=game.heading
    game.messenger.send('arrow_right')
    for _ in range(30): game.tick(None)
    game.messenger.send('arrow_right-up')
    assert game.heading<heading-40
    game.save()
    game.resume()
    assert game.mouse_locked
    game.messenger.send('escape')
    assert not game.mouse_locked
    game.messenger.send('mouse1')
    assert game.mouse_locked
    for _ in range(4): game.graphicsEngine.renderFrame()
    print('PASS graphical camera rotation, checkpoint capture, Escape release, click recapture')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
