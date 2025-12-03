"""
DSL Parser for MAGDA DSL using Grammar School.

This module provides a parser that uses Grammar School to parse MAGDA DSL code
and translate it to REAPER API actions.
"""

import logging
from typing import Any

from grammar_school import Grammar, method

from magda_agents.llm.magda_dsl_grammar import get_magda_dsl_grammar

logger = logging.getLogger(__name__)


class MagdaDSLGrammar(Grammar):
    """
    Grammar School grammar for parsing MAGDA DSL.

    Methods in this class are used to translate DSL calls into REAPER API actions.
    """

    def __init__(self):
        """Initialize the MAGDA DSL grammar with state tracking."""
        super().__init__()
        self.actions: list[dict[str, Any]] = []
        self.current_track_index = -1
        self.track_counter = 0
        self.state: dict[str, Any] | None = None

    def set_state(self, state: dict[str, Any]) -> None:
        """
        Set the current REAPER state for track resolution.

        Args:
            state: Current REAPER state dictionary
        """
        self.state = state

    def reset(self) -> None:
        """Reset parser state for a new parse."""
        self.actions = []
        self.current_track_index = -1
        self.track_counter = 0

    def get_actions(self) -> list[dict[str, Any]]:
        """
        Get the parsed actions.

        Returns:
            list: List of REAPER API action dictionaries
        """
        return self.actions

    @method
    def track(
        self,
        instrument: str | None = None,
        name: str | None = None,
        index: int | None = None,
        id: int | None = None,  # noqa: A002
        selected: bool | None = None,
    ) -> None:
        """
        Handle track() calls - either creation or reference.

        Args:
            instrument: Instrument name for new track
            name: Track name
            index: Track index for new track
            id: Existing track ID (1-based) for reference
            selected: Whether to reference currently selected track
        """
        # Check if this is a track reference
        if id is not None:
            # track(id=1) - reference existing track
            self.current_track_index = id - 1  # Convert 1-based to 0-based
            logger.debug(f"Referencing existing track {id} (index {self.current_track_index})")
            return

        if selected is True:
            # track(selected=true) - reference currently selected track
            selected_index = self._get_selected_track_index()
            if selected_index >= 0:
                self.current_track_index = selected_index
                logger.debug(f"Referencing selected track (index {self.current_track_index})")
                return
            raise ValueError("No selected track found in state")

        # This is a track creation call
        action: dict[str, Any] = {
            "action": "create_track",
        }

        if instrument is not None:
            action["instrument"] = instrument
        if name is not None:
            action["name"] = name

        if index is not None:
            action["index"] = index
            self.track_counter = index + 1
        else:
            action["index"] = self.track_counter
            self.track_counter += 1

        self.current_track_index = action["index"]
        self.actions.append(action)
        logger.debug(f"Created track action: {action}")

    @method
    def new_clip(
        self,
        bar: int | None = None,
        start: float | None = None,
        end: float | None = None,
        length_bars: int | None = None,
        length: float | None = None,
        position: float | None = None,
    ) -> None:
        """
        Handle .newClip() calls.

        Args:
            bar: Bar number for clip placement
            start: Start time in seconds
            end: End time in seconds
            length_bars: Length in bars
            length: Length in seconds
            position: Position in seconds (alias for start)
        """
        track_index = self.current_track_index
        if track_index < 0:
            # Try fallback to selected track
            track_index = self._get_selected_track_index()
            if track_index < 0:
                raise ValueError("No track context for clip call and no selected track found")

        action: dict[str, Any] = {
            "track": track_index,
        }

        if bar is not None:
            # Use create_clip_at_bar
            action["action"] = "create_clip_at_bar"
            action["bar"] = bar
            action["length_bars"] = length_bars if length_bars is not None else 4
        elif start is not None:
            # Use create_clip with time-based positioning
            action["action"] = "create_clip"
            action["position"] = start
            action["length"] = length if length is not None else 4.0
        elif position is not None:
            # Alias for start
            action["action"] = "create_clip"
            action["position"] = position
            action["length"] = length if length is not None else 4.0
        else:
            raise ValueError("clip call must specify bar, start, or position")

        self.actions.append(action)
        logger.debug(f"Created clip action: {action}")

    @method
    def add_midi(self, notes: list[Any] | None = None, note: dict[str, Any] | None = None) -> None:
        """
        Handle .addMidi() calls.

        Args:
            notes: List of MIDI notes
            note: Single MIDI note dictionary
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for midi call")

        action: dict[str, Any] = {
            "action": "add_midi",
            "track": self.current_track_index,
            "notes": notes if notes is not None else [],
        }

        if note is not None:
            action["notes"] = [note]

        self.actions.append(action)
        logger.debug(f"Created MIDI action: {action}")

    @method
    def add_fx(self, fxname: str | None = None, instrument: str | None = None) -> None:
        """
        Handle .addFX() calls.

        Args:
            fxname: FX plugin name
            instrument: Instrument name (alias for fxname)
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for FX call")

        action: dict[str, Any] = {
            "action": "add_track_fx",
            "track": self.current_track_index,
        }

        if fxname is not None:
            action["fxname"] = fxname
        elif instrument is not None:
            action["action"] = "add_instrument"
            action["fxname"] = instrument
        else:
            raise ValueError("FX call must specify fxname or instrument")

        self.actions.append(action)
        logger.debug(f"Created FX action: {action}")

    @method
    def set_volume(self, volume_db: float) -> None:
        """
        Handle .setVolume() calls.

        Args:
            volume_db: Volume in decibels
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for volume call")

        action: dict[str, Any] = {
            "action": "set_track_volume",
            "track": self.current_track_index,
            "volume_db": volume_db,
        }

        self.actions.append(action)
        logger.debug(f"Created volume action: {action}")

    @method
    def set_pan(self, pan: float) -> None:
        """
        Handle .setPan() calls.

        Args:
            pan: Pan value (-1.0 to 1.0)
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for pan call")

        action: dict[str, Any] = {
            "action": "set_track_pan",
            "track": self.current_track_index,
            "pan": pan,
        }

        self.actions.append(action)
        logger.debug(f"Created pan action: {action}")

    @method
    def set_mute(self, mute: bool) -> None:
        """
        Handle .setMute() calls.

        Args:
            mute: Whether to mute the track
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for mute call")

        action: dict[str, Any] = {
            "action": "set_track_mute",
            "track": self.current_track_index,
            "mute": mute,
        }

        self.actions.append(action)
        logger.debug(f"Created mute action: {action}")

    @method
    def set_solo(self, solo: bool) -> None:
        """
        Handle .setSolo() calls.

        Args:
            solo: Whether to solo the track
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for solo call")

        action: dict[str, Any] = {
            "action": "set_track_solo",
            "track": self.current_track_index,
            "solo": solo,
        }

        self.actions.append(action)
        logger.debug(f"Created solo action: {action}")

    @method
    def set_name(self, name: str) -> None:
        """
        Handle .setName() calls.

        Args:
            name: Track name
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for name call")

        action: dict[str, Any] = {
            "action": "set_track_name",
            "track": self.current_track_index,
            "name": name,
        }

        self.actions.append(action)
        logger.debug(f"Created name action: {action}")

    def _get_selected_track_index(self) -> int:
        """
        Get the index of the currently selected track from state.

        Returns:
            int: Track index (0-based), or -1 if not found
        """
        if self.state is None:
            return -1

        # Navigate to tracks array - state might be wrapped
        state_map = self.state.get("state", self.state)
        tracks = state_map.get("tracks", [])

        # Find first selected track
        for i, track in enumerate(tracks):
            if isinstance(track, dict) and track.get("selected", False):
                return i

        return -1


class DSLParser:
    """
    DSL Parser that uses Grammar School to parse MAGDA DSL code.

    This parser translates DSL code like:
    track(instrument="Serum").newClip(bar=3, length_bars=4).addMidi(notes=[...])
    into REAPER API actions.
    """

    def __init__(self):
        """Initialize the DSL parser with Grammar School."""
        grammar_string = get_magda_dsl_grammar()
        # Initialize grammar with custom grammar string
        self.grammar = MagdaDSLGrammar(grammar=grammar_string)

    def set_state(self, state: dict[str, Any]) -> None:
        """
        Set the current REAPER state for track resolution.

        Args:
            state: Current REAPER state dictionary
        """
        self.grammar.set_state(state)

    def parse_dsl(self, dsl_code: str) -> list[dict[str, Any]]:
        """
        Parse DSL code and return REAPER API actions.

        Args:
            dsl_code: DSL code string to parse

        Returns:
            list: List of REAPER API action dictionaries

        Raises:
            ValueError: If parsing fails or DSL code is invalid
        """
        dsl_code = dsl_code.strip()
        if not dsl_code:
            raise ValueError("empty DSL code")

        # Reset grammar state for new parse
        self.grammar.reset()

        try:
            # Execute DSL code using Grammar School
            self.grammar.execute(dsl_code)
            actions = self.grammar.get_actions()

            if not actions:
                raise ValueError("no actions found in DSL code")

            logger.info(f"✅ DSL Parser: Translated {len(actions)} actions from DSL")
            return actions
        except Exception as e:
            logger.error(f"Failed to parse DSL: {e}")
            raise ValueError(f"failed to parse DSL: {e}") from e

