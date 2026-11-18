"""Regression checks for the original recordings and offline speech routing."""
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch
import speech


class SpeechTests(TestCase):
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
