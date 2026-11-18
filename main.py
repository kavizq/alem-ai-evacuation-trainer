"""Launch the practical trainer or the preserved original quiz campaign."""
import argparse
from pathlib import Path
import faulthandler
import sys
import json
import traceback
from panda3d.core import loadPrcFileData


def main():
    parser=argparse.ArgumentParser(description='Alem AI evacuation training')
    parser.add_argument('--scenario',choices=('clear','smoke','blocked'),default='smoke')
    parser.add_argument('--legacy',action='store_true',help='Original quiz campaign')
    parser.add_argument('--offscreen',action='store_true',help='Render without a desktop window')
    parser.add_argument('--self-test',action='store_true',help='Verify packaged resources and route calculation, then exit')
    args=parser.parse_args()
    if args.offscreen:
        loadPrcFileData('', 'window-type offscreen\naudio-library-name null')
    folder=(Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).parent)/'user_data'
    folder.mkdir(exist_ok=True)
    with (folder/'runtime_errors.log').open('a',buffering=1,encoding='utf-8') as log:
        faulthandler.enable(log)
        if args.legacy:
            import campaign
            campaign.SAVE=folder/'legacy_save.json'
            from campaign import Campaign
            game=Campaign()
        else:
            from training import Trainer
            game=Trainer(args.scenario)
        if args.self_test:
            if args.legacy:
                raise ValueError('Use the trainer for package verification')
            game.skip_intro()
            results=[]
            for floor in (4,3,2,1):
                if floor!=4:
                    game.floor=floor;game.make_level()
                game.position=[9.,-17.,1.6]
                decision=game.calculate()
                assert decision['available']
                game.select_route(decision['recommendation'])
                assert all(game.can_walk(*p) for p in game.training_routes[game.selected_side])
                results.append({'floor':floor,'route':game.selected_side})
            for _ in range(3):game.graphicsEngine.renderFrame()
            (folder/'package_check.json').write_text(json.dumps({'passed':True,'floors':results},indent=2),encoding='utf-8')
            game.destroy()
            return
        game.run()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        folder=(Path(sys.executable).parent if getattr(sys,'frozen',False) else Path(__file__).parent)/'user_data'
        try:
            folder.mkdir(exist_ok=True)
            with (folder/'runtime_errors.log').open('a',encoding='utf-8') as log:
                traceback.print_exc(file=log)
        except OSError:
            pass
        raise
