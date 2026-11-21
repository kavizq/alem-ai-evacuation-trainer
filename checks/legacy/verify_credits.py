"""Regression checks for removed phantom barriers and ending cards."""
from pathlib import Path
import tempfile
import wave
import campaign
from credits import CARDS
with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro(); game.tick(None)
    assert (4,-16,2.25,2.25) not in game.obstacles
    assert game.can_walk(24,12), 'Gate collision extends across unrelated corridor'
    game.floor=1; game.make_level()
    game.solved=False
    before=game.can_walk(6,-6)
    game.solved=True
    assert game.can_walk(6,-6)==before
    game.end(True)
    for index,time in enumerate((12,20,31)):
        game.ending_time=time
        game.tick(None)
        assert game.credits.text.getText()==CARDS[index]
        for _ in range(3): game.graphicsEngine.renderFrame()
        game.win.saveScreenshot(f'verification/credits{index+1}.png')
    with wave.open('audio/credits.wav') as music:
        assert music.getnframes()/music.getframerate()==40
    game.reset_mission()
    assert not game.credits.started and game.credits.background.isHidden()
    game.scene_time=33; game.finished=False
    game.end(False)
    assert not game.credits.started
    print('PASS phantom barriers, all exact credit cards, music length, restart and failure')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
