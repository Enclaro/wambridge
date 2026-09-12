from argparse import Namespace
from unittest import TestCase
from unittest.mock import patch

from wambridge.radio_cli import (
    _play_custom_station,
    _play_tunein_safely,
    _print_tunein_presets_after_write,
    _radio_action,
    build_parser,
)
from wambridge.stations import RadioStation
from wambridge.stream import StreamError
from wambridge.tunein import WamPreset


class RadioControlCliTests(TestCase):
    def test_radio_add_accepts_fallback_urls(self) -> None:
        args = build_parser().parse_args(
            [
                "--radio-add",
                "radio",
                "http://one.example/live",
                "http://two.example/live",
            ]
        )

        self.assertEqual(
            args.radio_add,
            [
                "radio",
                "http://one.example/live",
                "http://two.example/live",
            ],
        )

    @patch("wambridge.radio_cli.cli.run")
    def test_custom_station_tries_fallback_after_stream_error(
        self,
        run_mock,
    ) -> None:
        run_mock.side_effect = [StreamError("primary failed"), 0]
        args = Namespace(source=None)
        station = RadioStation(
            "Radio",
            "http://one.example/live",
            ("http://two.example/live",),
        )

        result = _play_custom_station(args, station)

        self.assertEqual(result, 0)
        self.assertEqual(run_mock.call_count, 2)
        self.assertIsNone(args.source)

    @patch("wambridge.radio_cli._wait_for_tunein_playback")
    @patch("wambridge.radio_cli.play_tunein_preset")
    @patch("wambridge.radio_cli.get_mute", return_value=False)
    @patch("wambridge.radio_cli.get_volume", return_value=37)
    @patch("wambridge.radio_cli.find_tunein_preset")
    @patch("wambridge.radio_cli.get_tunein_presets")
    @patch("wambridge.radio_cli.set_mute")
    @patch("wambridge.radio_cli.set_volume")
    def test_tunein_play_uses_volume_safety(
        self,
        volume_mock,
        mute_mock,
        presets_mock,
        find_mock,
        _get_volume_mock,
        _get_mute_mock,
        play_mock,
        wait_mock,
    ) -> None:
        preset = WamPreset(content_id="0", title="Paradise", kind="my")
        presets_mock.return_value = [preset]
        find_mock.return_value = preset
        args = Namespace(
            tunein_play="Paradise",
            volume=None,
            max_start_volume=10,
        )

        result = _play_tunein_safely(args, "10.0.0.118", 55001)

        self.assertEqual(result, 0)
        play_mock.assert_called_once_with(
            "10.0.0.118",
            preset,
            port=55001,
        )
        wait_mock.assert_called_once_with("10.0.0.118", port=55001)
        self.assertEqual(
            [call.args[1] for call in volume_mock.call_args_list],
            [0, 10],
        )
        self.assertEqual(
            [call.args[1] for call in mute_mock.call_args_list],
            [True, False],
        )

    @patch(
        "wambridge.radio_cli.play_tunein_preset",
        side_effect=RuntimeError("boom"),
    )
    @patch("wambridge.radio_cli.get_mute", return_value=True)
    @patch("wambridge.radio_cli.get_volume", return_value=7)
    @patch("wambridge.radio_cli.find_tunein_preset")
    @patch("wambridge.radio_cli.get_tunein_presets")
    @patch("wambridge.radio_cli.set_mute")
    @patch("wambridge.radio_cli.set_volume")
    def test_tunein_failure_keeps_speaker_muted(
        self,
        volume_mock,
        mute_mock,
        presets_mock,
        find_mock,
        _get_volume_mock,
        _get_mute_mock,
        _play_mock,
    ) -> None:
        preset = WamPreset(content_id="0", title="Paradise", kind="my")
        presets_mock.return_value = [preset]
        find_mock.return_value = preset
        args = Namespace(
            tunein_play="0",
            volume=None,
            max_start_volume=10,
        )

        with self.assertRaisesRegex(RuntimeError, "boom"):
            _play_tunein_safely(args, "10.0.0.118", 55001)

        self.assertEqual(
            [call.args[1] for call in volume_mock.call_args_list],
            [0, 0],
        )
        self.assertEqual(
            [call.args[1] for call in mute_mock.call_args_list],
            [True, True],
        )


class TuneInPresetWriteCliTests(TestCase):
    def test_tunein_save_flag_parses(self) -> None:
        args = build_parser().parse_args(["--tunein-save"])
        self.assertTrue(args.tunein_save)

    def test_tunein_remove_flag_parses(self) -> None:
        args = build_parser().parse_args(["--tunein-remove", "3"])
        self.assertEqual(args.tunein_remove, 3)

    def test_tunein_remove_flag_rejects_negative(self) -> None:
        with self.assertRaises(SystemExit):
            build_parser().parse_args(["--tunein-remove", "-1"])

    def test_tunein_move_flag_parses(self) -> None:
        args = build_parser().parse_args(["--tunein-move", "1", "2", "0"])
        self.assertEqual(args.tunein_move, [1, 2, 0])

    def test_radio_action_recognises_the_three_new_flags(self) -> None:
        base = dict(
            radio_add=None,
            radio_import=None,
            radio_list=False,
            radio_remove=None,
            radio_play=None,
            tunein_list=False,
            tunein_play=None,
            tunein_browse=None,
            tunein_search=None,
            tunein_save=False,
            tunein_remove=None,
            tunein_move=None,
        )
        self.assertTrue(_radio_action(Namespace(**{**base, "tunein_save": True})))
        self.assertTrue(_radio_action(Namespace(**{**base, "tunein_remove": 0})))
        self.assertTrue(_radio_action(Namespace(**{**base, "tunein_move": [1, 2, 0]})))
        self.assertFalse(_radio_action(Namespace(**base)))

    @patch("wambridge.radio_cli.sleep")
    @patch("wambridge.radio_cli.get_tunein_presets")
    def test_reread_after_write_retries_on_empty(self, presets_mock, sleep_mock) -> None:
        preset = WamPreset(content_id="1", title="Custom", kind="my")
        presets_mock.side_effect = [[], [], [preset]]

        result = _print_tunein_presets_after_write("10.0.0.118", port=55001, settle=0.0)

        self.assertEqual(result, 0)
        self.assertEqual(presets_mock.call_count, 3)
        self.assertEqual(sleep_mock.call_count, 2)

    @patch("wambridge.radio_cli.sleep")
    @patch("wambridge.radio_cli.get_tunein_presets", return_value=[])
    def test_reread_after_write_gives_up_after_attempts(self, presets_mock, sleep_mock) -> None:
        result = _print_tunein_presets_after_write(
            "10.0.0.118", port=55001, attempts=2, settle=0.0
        )

        self.assertEqual(result, 0)
        self.assertEqual(presets_mock.call_count, 2)
        self.assertEqual(sleep_mock.call_count, 1)
