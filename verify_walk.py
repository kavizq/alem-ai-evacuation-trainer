"""Verify continuous collision-safe routes and render each floor and puzzle."""
from collections import deque
from pathlib import Path
import tempfile
import campaign

def route(game, start, goal):
    start=(round(start[0]*2),round(start[1]*2))
    goal=(round(goal[0]*2),round(goal[1]*2))
    previous={start:None}
    queue=deque([start])
    while queue:
        current=queue.popleft()
        if current==goal:
            path=[]
            while current is not None:
                path.append((current[0]/2,current[1]/2))
                current=previous[current]
            return path[::-1]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            point=(current[0]+dx,current[1]+dy)
            if point not in previous and game.can_walk(point[0]/2,point[1]/2):
                previous[point]=current
                queue.append(point)
    raise AssertionError(('unreachable',game.floor,start,goal))

with tempfile.TemporaryDirectory() as folder:
    campaign.SAVE=Path(folder)/'save.json'
    game=campaign.Campaign()
    game.voice_muted=True
    game.scene_time=33
    game.finished=False
    for floor in (4,3,2,1):
        game.floor=floor
        game.solved=False
        game.puzzle_stage=0
        game.evidence=set()
        game.make_level()
        game.position=[8,-20,1.6]
        for x,y in game.evidence_positions:
            for px,py in route(game,game.position,(x,y-1)):
                game.position=[px,py,1.6]
            game.interact()
        for px,py in route(game,game.position,(9,-17)):
            game.position=[px,py,1.6]
        game.interact()
        assert game.panel and len(game.evidence)==2
        game.set_camera()
        for _ in range(3): game.graphicsEngine.renderFrame()
        game.win.saveScreenshot(f'verification/puzzle{floor}.png')
        for stage in range(3):
            game.answer(campaign.correct_answer(floor,stage,campaign.QUESTIONS))
        assert game.solved
        for px,py in route(game,game.position,(0,0)):
            game.position=[px,py,1.6]
        game.position=[10,-20,1.6]
        game.set_camera()
        for _ in range(3): game.graphicsEngine.renderFrame()
        game.win.saveScreenshot(f'verification/walk{floor}.png')
    game.end(True)
    game.clock.setDt(.02)
    for _ in range(500): game.tick(None)
    for _ in range(3): game.graphicsEngine.renderFrame()
    game.win.saveScreenshot('verification/exterior.png')
    print('PASS collision-safe routes through evidence, terminal, exit on all floors; panels and cinematic rendered')
    if game.voice and game.voice.poll() is None: game.voice.terminate()
    game.destroy()
