from unittest.mock import patch

from generator.tts import (
    VOICE_BY_ID,
    AVAILABLE_VOICES,
    EdgeTTSConfig,
    ModalTTSConfig,
    synthesize_voice,
)


def test_registry_has_female_alina_voice():
    assert "alina" in VOICE_BY_ID
    alina = VOICE_BY_ID["alina"]
    assert alina.gender == "female"
    assert alina.backend == "edge"
    assert isinstance(alina.config, EdgeTTSConfig)
    assert alina.config.voice == "ro-RO-AlinaNeural"


def test_registry_exposes_expected_voices():
    ids = {v.id for v in AVAILABLE_VOICES}
    assert ids == {"alina", "emil", "cristi"}
    edge_ids = {v.id for v in AVAILABLE_VOICES if v.backend == "edge"}
    assert edge_ids == {"alina", "emil"}


def test_registry_has_cloned_cristi_voice():
    assert "cristi" in VOICE_BY_ID
    cristi = VOICE_BY_ID["cristi"]
    assert cristi.gender == "male"
    assert cristi.backend == "modal"
    assert isinstance(cristi.config, ModalTTSConfig)
    assert cristi.config.speaker == "cristi"
    assert cristi.config.language == "ro"


def test_synthesize_voice_dispatches_to_edge_for_alina(tmp_path):
    out = tmp_path / "latest-alina.mp3"
    with patch("generator.tts.synthesize_edge", return_value=12.3) as edge_mock:
        dur = synthesize_voice(text="Salut", out_mp3=out, voice=VOICE_BY_ID["alina"])
    assert dur == 12.3
    assert edge_mock.called


def test_synthesize_voice_passes_text_through_unchanged(tmp_path):
    out = tmp_path / "latest.mp3"
    original = "Manchester City a câștigat"
    with patch("generator.tts.synthesize_edge", return_value=1.0) as edge_mock:
        synthesize_voice(text=original, out_mp3=out, voice=VOICE_BY_ID["alina"])
    assert edge_mock.call_args.kwargs["text"] == original


def test_synthesize_voice_dispatches_to_modal_for_cristi(tmp_path):
    out = tmp_path / "latest-cristi.mp3"
    with patch("generator.tts.synthesize_modal", return_value=42.0) as modal_mock:
        dur = synthesize_voice(text="Salut", out_mp3=out, voice=VOICE_BY_ID["cristi"])
    assert dur == 42.0
    assert modal_mock.called
    assert modal_mock.call_args.kwargs["text"] == "Salut"
