"""Drive the actual movement loop along collision-aware routes on all floors."""
import math
import tempfile
from pathlib import Path
import campaign
from navigation import walking_path

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.mouse_locked=False
    game.clock.setMode(game.clock.MNonRealTime)
    game.clock.setDt(1/60)
    game.skip_intro()
    game.tick(None)
    frames=0
    def walk(target):
        global frames
        path=walking_path(game.position[:2],target,game.can_walk)
        assert path, (game.floor,target)
        for x,y in path[1:]:
            for _ in range(120):
                dx,dy=x-game.position[0],y-game.position[1]
                if math.hypot(dx,dy)<.09:
                    break
                game.heading=math.degrees(math.atan2(-dx,dy))
                game.keys['w']=True
                game.tick(None)
                frames+=1
            else:
                raise AssertionError(('movement stuck',game.floor,game.position,(x,y)))
        game.keys['w']=False
    for floor in (4,3,2,1):
        assert game.floor==floor
        for x,y in game.evidence_positions:
            walk((x,y-1))
            game.interact()
        walk((9,-17))
        game.interact()
        assert game.panel
        for stage in range(3):
            game.answer(campaign.correct_answer(floor,stage,campaign.QUESTIONS))
        walk((0,17 if floor==1 else 0))
        game.interact()
        if floor>1:
            for _ in range(int(campaign.STAIR_DURATION*60)+2): game.tick(None)
    assert game.ending=='success'
    print(f'PASS four-floor campaign using ordinary movement ticks: {frames/60:.1f}s moving, excluding reading/thinking.')
    game.reset_mission()
    before=(game.floor,game.errors,game.solved)
    campaign.SAVE.write_text('{"floor": 2, "errors": 1, "solved": false, "elapsed": "bad"}')
    game.resume()
    assert (game.floor,game.errors,game.solved)==before
    print('PASS invalid checkpoint leaves active run unchanged')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
