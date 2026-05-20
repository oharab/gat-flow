"""Unit tests for Config (template parsing from environment variables)."""

import pytest

from config import Config

BUILTIN_TEMPLATE_NAMES = {"vacation", "sick", "conference", "training"}


@pytest.fixture
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    """Strip any CUSTOM_TEMPLATE_* env vars set in the test environment."""
    import os

    for key in list(os.environ):
        if key.startswith("CUSTOM_TEMPLATE_"):
            monkeypatch.delenv(key, raising=False)
    return monkeypatch


@pytest.fixture
def config(tmp_path) -> Config:
    """Return a Config that doesn't try to load a real .env file."""
    return Config(config_file=str(tmp_path / "nonexistent.env"))


class TestBuiltinTemplates:
    def test_includes_all_builtin_templates(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        templates = config.get_message_templates()
        assert set(templates) == BUILTIN_TEMPLATE_NAMES

    def test_each_builtin_has_subject_and_message(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        templates = config.get_message_templates()
        for name in BUILTIN_TEMPLATE_NAMES:
            assert templates[name]["subject"]
            assert templates[name]["message"]


class TestCustomTemplates:
    def test_adds_well_formed_custom_template(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        isolated_env.setenv("CUSTOM_TEMPLATE_REMOTE_SUBJECT", "Working remotely")
        isolated_env.setenv(
            "CUSTOM_TEMPLATE_REMOTE_MESSAGE",
            "I'm working from home today.",
        )

        templates = config.get_message_templates()

        assert "remote" in templates
        assert templates["remote"] == {
            "subject": "Working remotely",
            "message": "I'm working from home today.",
        }

    def test_lowercases_template_name(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        isolated_env.setenv("CUSTOM_TEMPLATE_LOUDNAME_SUBJECT", "s")
        isolated_env.setenv("CUSTOM_TEMPLATE_LOUDNAME_MESSAGE", "m")
        assert "loudname" in config.get_message_templates()

    def test_skips_template_with_subject_but_no_message(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        isolated_env.setenv("CUSTOM_TEMPLATE_ORPHAN_SUBJECT", "Only a subject")
        # no matching _MESSAGE var
        assert "orphan" not in config.get_message_templates()

    def test_skips_template_with_message_but_no_subject(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        isolated_env.setenv("CUSTOM_TEMPLATE_ORPHAN_MESSAGE", "Only a body")
        # no matching _SUBJECT var, so the regex never picks it up
        assert "orphan" not in config.get_message_templates()

    def test_custom_does_not_clobber_builtin_by_default(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        isolated_env.setenv("CUSTOM_TEMPLATE_BRANDNEW_SUBJECT", "x")
        isolated_env.setenv("CUSTOM_TEMPLATE_BRANDNEW_MESSAGE", "y")
        templates = config.get_message_templates()
        assert BUILTIN_TEMPLATE_NAMES.issubset(set(templates))
        assert "brandnew" in templates

    def test_custom_template_overrides_builtin_with_same_name(
        self,
        config: Config,
        isolated_env: pytest.MonkeyPatch,
    ) -> None:
        # Documents current behavior: env-var loop runs after builtins and replaces.
        isolated_env.setenv("CUSTOM_TEMPLATE_VACATION_SUBJECT", "overridden subject")
        isolated_env.setenv("CUSTOM_TEMPLATE_VACATION_MESSAGE", "overridden message")
        templates = config.get_message_templates()
        assert templates["vacation"]["subject"] == "overridden subject"
