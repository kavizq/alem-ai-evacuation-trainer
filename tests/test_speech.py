"""Regression checks for the original recordings and offline speech routing."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
import speech


class SpeechTests(TestCase):
    def setUp(self):
        bank = patch('speech._approved_voice_bank', return_value=None)
        bank.start()
        self.addCleanup(bank.stop)

    def game(self, muted=False):
        return SimpleNamespace(voice=None, voice_sound=None, voice_muted=muted,
                               voice_manifest={}, loader=SimpleNamespace(loadSfx=Mock()))

    def test_original_recording_uses_game_audio(self):
        game=self.game()
        game.voice_manifest={'original line':'537d3826e1cc9b26cc05.wav'}
        sound=Mock();game.loader.loadSfx.return_value=sound
        with patch('speech.ConfigVariableString') as config, patch('speech.subprocess.Popen') as process:
            config.return_value.getValue.return_value='p3openal_audio'
            self.assertEqual(speech.speak(game,'original line'),'recording')
            sound.play.assert_called_once()
            process.assert_not_called()
            self.assertIs(game.voice_sound,sound)

    def test_mute_stops_recording_and_system_voice(self):
        game=self.game(muted=True)
        sound=Mock();process=Mock();process.poll.return_value=None
        game.voice_sound=sound;game.voice=process
        self.assertEqual(speech.speak(game,'line'),'muted')
        sound.stop.assert_called_once();process.terminate.assert_called_once()
        game.loader.loadSfx.assert_not_called()

    def test_offscreen_audio_does_not_start_system_voice(self):
        game=self.game()
        with patch('speech.ConfigVariableString') as config, patch('speech.subprocess.Popen') as process:
            config.return_value.getValue.return_value='null'
            self.assertEqual(speech.speak(game,'new line'),'disabled')
            process.assert_not_called()

    def test_windows_new_line_is_data_not_command_text(self):
        game=self.game();message='New training message with "quotes" and $() characters.'
        process=Mock()
        with patch('speech.ConfigVariableString') as config, patch('speech.sys.platform','win32'), patch('speech.shutil.which',return_value='powershell.exe'), patch('speech.subprocess.Popen',return_value=process) as start:
            config.return_value.getValue.return_value='p3openal_audio'
            self.assertEqual(speech.speak(game,message),'system')
            process.stdin.write.assert_called_once_with(message)
            process.stdin.close.assert_called_once()
            self.assertNotIn(message,' '.join(start.call_args.args[0]))
            self.assertEqual(start.call_args.kwargs['creationflags'],getattr(speech.subprocess,'CREATE_NO_WINDOW',0))


class ApprovedVoiceTests(TestCase):
    def test_dynamic_route_uses_the_chosen_voice_without_speaking_wrong_numbers(self):
        import re
        pattern = re.compile(r'Left route selected, [0-9]+ m\. Modeled blockage risk [0-9]+%\. Follow the cyan guide\. U checks for a route update\.')
        entry = {'file':'route.wav'}
        bank = {'lines':{}, 'compiled_patterns':[(pattern,entry)]}
        game = SimpleNamespace(voice=None,voice_sound=None,voice_muted=False,
                               voice_manifest={},loader=SimpleNamespace(loadSfx=Mock()))
        with patch('speech._approved_voice_bank',return_value=bank), patch('speech.Path.is_file',return_value=True), patch('speech.ConfigVariableString') as config, patch('speech.subprocess.Popen') as process:
            config.return_value.getValue.return_value='p3openal_audio'
            line='Left route selected, 27 m. Modeled blockage risk 50%. Follow the cyan guide. U checks for a route update.'
            self.assertEqual(speech.speak(game,line),'recording')
            process.assert_not_called()
            game.loader.loadSfx.return_value.play.assert_called_once()

    def test_unknown_line_does_not_switch_to_a_different_system_voice(self):
        game = SimpleNamespace(voice=None,voice_sound=None,voice_muted=False,
                               voice_manifest={},loader=SimpleNamespace(loadSfx=Mock()))
        with patch('speech._approved_voice_bank',return_value={'lines':{},'compiled_patterns':[]}), patch('speech.ConfigVariableString') as config, patch('speech.subprocess.Popen') as process:
            config.return_value.getValue.return_value='p3openal_audio'
            self.assertEqual(speech.speak(game,'Future message without a recording.'),'text')
            process.assert_not_called()
