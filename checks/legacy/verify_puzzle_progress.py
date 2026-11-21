"""Verify intermediate checkpoints, old-save compatibility and failure."""
import json
import tempfile
from pathlib import Path
import campaign

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.skip_intro()
    game.tick(None)
    game.evidence={0,1}
    game.position=[9,-17,1.6]
    game.interact()
    game.answer(campaign.correct_answer(4,0,campaign.QUESTIONS))
    assert game.puzzle_stage==1 and not game.solved
    game.resume()
    assert game.puzzle_stage==1 and not game.solved
    game.position=[9,-17,1.6]
    game.interact()
    game.answer(campaign.correct_answer(4,1,campaign.QUESTIONS))
    assert game.puzzle_stage==2 and not game.solved
    game.set_camera()
    for _ in range(3): game.graphicsEngine.renderFrame()
    game.win.saveScreenshot('verification/puzzle_stages.png')
    for _ in range(3): game.answer(1)
    assert game.ending=='failure'
    campaign.SAVE.write_text(json.dumps({'floor':3,'errors':1,'solved':True,'evidence':[0,1],'elapsed':123}))
    game.resume()
    assert game.floor==3 and game.solved and game.puzzle_stage==2
    print('PASS intermediate puzzle save, three-error ending, legacy solved save and panel render')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
