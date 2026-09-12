from unittest import TestCase
from unittest.mock import patch

from wambridge.samsung import WamResponse
from wambridge.tunein import (
    WamPreset,
    find_tunein_preset,
    get_tunein_presets,
    move_tunein_preset,
    parse_tunein_presets,
    play_tunein_preset,
    remove_tunein_preset,
    save_tunein_preset,
)


class TuneInPresetTests(TestCase):
    def test_parses_repeated_presets(self) -> None:
        body = (
            '<CPM><method>PresetList</method><response result="ok">'
            "<cpname>TuneIn</cpname><presetlist>"
            "<preset><contentid>0</contentid><kind>my</kind>"
            "<title>Radio Paradise</title><mediaid>s123</mediaid></preset>"
            "<preset><contentid>3</contentid><kind>speaker</kind>"
            "<title>Default</title></preset>"
            "</presetlist></response></CPM>"
        )

        presets = parse_tunein_presets(body)

        self.assertEqual(len(presets), 2)
        self.assertEqual(presets[0].title, "Radio Paradise")
        self.assertEqual(presets[0].preset_type, 0)
        self.assertEqual(presets[1].preset_type, 1)

    def test_finds_preset_by_id_or_title(self) -> None:
        presets = [
            WamPreset(content_id="0", title="Radio Paradise", kind="my")
        ]

        self.assertEqual(find_tunein_preset(presets, "0"), presets[0])
        self.assertEqual(
            find_tunein_preset(presets, "radio paradise"),
            presets[0],
        )

    @patch("wambridge.tunein.request")
    @patch("wambridge.tunein.select_tunein")
    def test_gets_tunein_presets(self, select_mock, request_mock) -> None:
        request_mock.return_value = WamResponse(
            method="PresetList",
            result="ok",
            body=(
                '<CPM><method>PresetList</method><response result="ok">'
                "<presetlist><preset><contentid>1</contentid>"
                "<kind>my</kind><title>Custom</title></preset>"
                "</presetlist></response></CPM>"
            ),
        )

        presets = get_tunein_presets("10.0.0.118")

        select_mock.assert_called_once_with(
            "10.0.0.118",
            port=55001,
            timeout=10.0,
        )
        self.assertEqual(presets[0].title, "Custom")

    @patch("wambridge.tunein.request")
    @patch("wambridge.tunein.select_tunein")
    def test_plays_tunein_preset(self, select_mock, request_mock) -> None:
        request_mock.return_value = WamResponse(
            method="RadioInfo",
            result="ok",
            body="",
        )
        preset = WamPreset(content_id="2", title="Custom", kind="my")

        play_tunein_preset("10.0.0.118", preset)

        select_mock.assert_called_once_with(
            "10.0.0.118",
            port=55001,
            timeout=10.0,
        )
        request_mock.assert_called_once_with(
            "10.0.0.118",
            "SetPlayPreset",
            [("presettype", 0, "dec"), ("presetindex", 2, "dec")],
            port=55001,
            timeout=25.0,
            api_type="CPM",
        )

    @patch("wambridge.tunein.request")
    def test_saves_preset_with_no_arguments(self, request_mock) -> None:
        request_mock.return_value = WamResponse(method="SavePreset", result="ok", body="")

        save_tunein_preset("10.0.0.118")

        request_mock.assert_called_once_with(
            "10.0.0.118",
            "SetSavePreset",
            port=55001,
            timeout=5.0,
            api_type="CPM",
        )

    @patch("wambridge.tunein.request")
    def test_removes_preset_by_index(self, request_mock) -> None:
        request_mock.return_value = WamResponse(method="RemovePreset", result="ok", body="")

        remove_tunein_preset("10.0.0.118", 3)

        request_mock.assert_called_once_with(
            "10.0.0.118",
            "SetRemovePreset",
            [("presetindex", 3, "dec")],
            port=55001,
            timeout=5.0,
            api_type="CPM",
        )

    def test_remove_preset_rejects_negative_index(self) -> None:
        with self.assertRaises(ValueError):
            remove_tunein_preset("10.0.0.118", -1)

    def test_remove_preset_rejects_bool_index(self) -> None:
        with self.assertRaises(ValueError):
            remove_tunein_preset("10.0.0.118", True)

    @patch("wambridge.tunein.request")
    def test_moves_preset(self, request_mock) -> None:
        request_mock.return_value = WamResponse(method="MovePreset", result="ok", body="")

        move_tunein_preset("10.0.0.118", 1, 2, 0)

        request_mock.assert_called_once_with(
            "10.0.0.118",
            "SetMovePreset",
            [
                ("presetfromindex", 1, "dec"),
                ("presettoindex", 2, "dec"),
                ("movedirection", 0, "dec"),
            ],
            port=55001,
            timeout=5.0,
            api_type="CPM",
        )

    def test_move_preset_rejects_negative_indices(self) -> None:
        with self.assertRaises(ValueError):
            move_tunein_preset("10.0.0.118", -1, 2, 0)
