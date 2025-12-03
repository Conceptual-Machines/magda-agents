"""
DSL Parser with Action Paradigm for MAGDA DSL using Grammar School.

This demonstrates how to use the Action paradigm with functional methods.

**Key Design Patterns:**

1. **Side-effect methods** (track, new_clip, add_midi, etc.):
   - Create Action objects representing "what to do"
   - Actions are emitted via Runtime or stored in self._actions
   - Actions can be executed later or converted to REAPER API format
   - Methods are "pure" in that they don't execute side effects directly

2. **Functional methods** (map, filter, reduce, etc.):
   - Execute immediately to transform data
   - Return transformed data for use by subsequent operations
   - These DON'T return Actions because they're data transformations, not side effects
   - They operate on data stored in self.data (via store() method)

**Usage Pattern:**
```python
# Side-effect operations emit Actions
track(instrument="Serum").new_clip(bar=1).add_midi(notes=[...])

# Functional operations transform data immediately
store(tracks=[...])
filter(tracks, track.name == "FX")  # Returns filtered data immediately
map(@process_track, tracks)  # Returns transformed data immediately
```

This separation allows:
- Side-effects to be deferred/collected/tested
- Functional transformations to execute immediately (needed for data flow)
"""

import logging
from typing import Any

from grammar_school import Action, Grammar, method

from magda_agents.llm.magda_dsl_grammar import get_magda_dsl_grammar

logger = logging.getLogger(__name__)


class MagdaDSLGrammar(Grammar):
    """
    Grammar School grammar for parsing MAGDA DSL using Action paradigm.

    Methods return Action objects instead of executing side effects directly.
    Functional methods execute immediately but can also emit Actions.
    """

    def __init__(self, runtime=None):
        """
        Initialize the MAGDA DSL grammar with state tracking.

        Args:
            runtime: Optional Runtime instance to collect/execute actions.
                     If provided, Actions will be passed to runtime.execute().
                     If None, actions are stored in self._actions list.
        """
        super().__init__(grammar=get_magda_dsl_grammar())
        self._runtime = runtime
        self._actions = [] if runtime is None else []
        self.current_track_index = -1
        self.track_counter = 0
        self.state: dict[str, Any] | None = None
        # Track data for functional operations
        self.data: dict[str, Any] = {}

    def set_state(self, state: dict[str, Any]) -> None:
        """
        Set the current REAPER state for track resolution.

        Args:
            state: Current REAPER state dictionary
        """
        self.state = state

    # ========== Side-effect methods (emit Actions via Runtime) ==========

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

        Emits an Action for track creation via the Runtime, or sets context for reference.

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
            return  # No action for reference

        if selected is True:
            # track(selected=true) - reference currently selected track
            selected_index = self._get_selected_track_index()
            if selected_index >= 0:
                self.current_track_index = selected_index
                logger.debug(f"Referencing selected track (index {self.current_track_index})")
                return  # No action for reference
            raise ValueError("No selected track found in state")

        # This is a track creation call - emit Action via Runtime
        action_payload: dict[str, Any] = {}

        if instrument is not None:
            action_payload["instrument"] = instrument
        if name is not None:
            action_payload["name"] = name

        if index is not None:
            action_payload["index"] = index
            self.track_counter = index + 1
        else:
            action_payload["index"] = self.track_counter
            self.track_counter += 1

        self.current_track_index = action_payload["index"]

        # Emit Action via Runtime (if available)
        if hasattr(self, "interpreter") and hasattr(self.interpreter, "dsl") and hasattr(self.interpreter.dsl, "_runtime"):
            runtime = self.interpreter.dsl._runtime
            if runtime is not None:
                runtime.execute(Action(kind="create_track", payload=action_payload))
        else:
            # Fallback: store in actions list if no runtime
            if not hasattr(self, "_actions"):
                self._actions = []
            self._actions.append(Action(kind="create_track", payload=action_payload))

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
        Handle .new_clip() calls.

        Emits an Action for clip creation via the Runtime.

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

        payload: dict[str, Any] = {
            "track": track_index,
        }

        if bar is not None:
            action_kind = "create_clip_at_bar"
            payload["bar"] = bar
            payload["length_bars"] = length_bars if length_bars is not None else 4
        elif start is not None:
            action_kind = "create_clip"
            payload["position"] = start
            payload["length"] = length if length is not None else 4.0
        elif position is not None:
            action_kind = "create_clip"
            payload["position"] = position
            payload["length"] = length if length is not None else 4.0
        else:
            raise ValueError("clip call must specify bar, start, or position")

        action = Action(kind=action_kind, payload=payload)
        self._emit_action(action)

    @method
    def add_midi(self, notes: list[Any] | None = None, note: dict[str, Any] | None = None) -> None:
        """
        Handle .add_midi() calls.

        Emits an Action for MIDI addition via the Runtime.

        Args:
            notes: List of MIDI notes
            note: Single MIDI note dictionary
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for midi call")

        payload: dict[str, Any] = {
            "track": self.current_track_index,
            "notes": notes if notes is not None else [],
        }

        if note is not None:
            payload["notes"] = [note]

        self._emit_action(Action(kind="add_midi", payload=payload))

    @method
    def add_fx(self, fxname: str | None = None, instrument: str | None = None) -> None:
        """
        Handle .add_fx() calls.

        Emits an Action for FX addition via the Runtime.

        Args:
            fxname: FX plugin name
            instrument: Instrument name (alias for fxname)
        """
        if self.current_track_index < 0:
            raise ValueError("No track context for FX call")

        payload: dict[str, Any] = {
            "track": self.current_track_index,
        }

        if fxname is not None:
            payload["fxname"] = fxname
            self._emit_action(Action(kind="add_track_fx", payload=payload))
        elif instrument is not None:
            payload["fxname"] = instrument
            self._emit_action(Action(kind="add_instrument", payload=payload))
        else:
            raise ValueError("FX call must specify fxname or instrument")

    @method
    def set_volume(self, volume_db: float) -> None:
        """Handle .set_volume() calls. Emits an Action."""
        if self.current_track_index < 0:
            raise ValueError("No track context for volume call")
        self._emit_action(
            Action(
                kind="set_track_volume",
                payload={"track": self.current_track_index, "volume_db": volume_db},
            )
        )

    @method
    def set_pan(self, pan: float) -> None:
        """Handle .set_pan() calls. Emits an Action."""
        if self.current_track_index < 0:
            raise ValueError("No track context for pan call")
        self._emit_action(
            Action(
                kind="set_track_pan",
                payload={"track": self.current_track_index, "pan": pan},
            )
        )

    @method
    def set_mute(self, mute: bool) -> None:
        """Handle .set_mute() calls. Emits an Action."""
        if self.current_track_index < 0:
            raise ValueError("No track context for mute call")
        self._emit_action(
            Action(
                kind="set_track_mute",
                payload={"track": self.current_track_index, "mute": mute},
            )
        )

    @method
    def set_solo(self, solo: bool) -> None:
        """Handle .set_solo() calls. Emits an Action."""
        if self.current_track_index < 0:
            raise ValueError("No track context for solo call")
        self._emit_action(
            Action(
                kind="set_track_solo",
                payload={"track": self.current_track_index, "solo": solo},
            )
        )

    @method
    def set_name(self, name: str) -> None:
        """Handle .set_name() calls. Emits an Action."""
        if self.current_track_index < 0:
            raise ValueError("No track context for name call")
        self._emit_action(
            Action(
                kind="set_track_name",
                payload={"track": self.current_track_index, "name": name},
            )
        )

    # ========== Functional methods (execute immediately, optionally return Actions) ==========

    @method
    def map(self, func, data) -> Any:
        """
        Functional method: Map a function over data.

        This executes immediately because the transformed data might be needed
        by subsequent operations. However, you can also emit an Action if you
        want to defer the transformation.

        Args:
            func: Function reference (e.g., @square) or function name
            data: Data to map over (can be a variable name or actual data)

        Returns:
            Transformed data (executed immediately)
        """
        # Resolve data reference if it's a string (variable name)
        actual_data = self.data.get(data, data) if isinstance(data, str) else data

        # Resolve function reference
        if isinstance(func, str):
            # Function name like "@square" - try to get from data
            func_name = func.lstrip("@")
            # For now, just return the data (would need actual function lookup)
            logger.debug(f"Map function {func_name} over {actual_data}")
            return actual_data  # Placeholder - would apply function

        # If func is callable, apply it
        if callable(func):
            result = [func(item) for item in actual_data]
            logger.debug(f"Mapped function over {len(actual_data)} items")
            return result

        # Fallback: return data as-is
        return actual_data

    @method
    def filter(self, predicate, data) -> Any:
        """
        Functional method: Filter data using a predicate.

        Executes immediately because filtered data might be needed next.
        The predicate can be an expression that gets evaluated.

        Args:
            predicate: Predicate function or expression (e.g., track.name == "FX")
            data: Data to filter (can be a variable name or actual data)

        Returns:
            Filtered data (executed immediately)
        """
        # Resolve data reference
        actual_data = self.data.get(data, data) if isinstance(data, str) else data

        # If predicate is a boolean (evaluated expression), use it directly
        if isinstance(predicate, bool):
            # For simplicity, if predicate is True, return all items
            # (In real implementation, would evaluate per-item)
            return actual_data if predicate else []

        # If predicate is callable, apply it
        if callable(predicate):
            result = [item for item in actual_data if predicate(item)]
            logger.debug(f"Filtered {len(actual_data)} items to {len(result)}")
            return result

        # Fallback: return data as-is
        return actual_data

    @method
    def reduce(self, func, data, initial=None) -> Any:
        """
        Functional method: Reduce data using a function.

        Executes immediately for data transformation.

        Args:
            func: Reduction function
            data: Data to reduce
            initial: Initial value for reduction

        Returns:
            Reduced value
        """
        actual_data = self.data.get(data, data) if isinstance(data, str) else data

        if callable(func):
            from functools import reduce as functools_reduce

            result = functools_reduce(func, actual_data, initial)
            logger.debug(f"Reduced {len(actual_data)} items")
            return result

        return initial if initial is not None else None

    @method
    def store(self, name: str, value: Any) -> None:
        """
        Store a value for later use in functional operations.

        This is useful for storing intermediate results that can be
        used by map, filter, reduce, etc.

        Args:
            name: Variable name to store
            value: Value to store
        """
        self.data[name] = value
        logger.debug(f"Stored {name} = {value}")

    def _emit_action(self, action: Action) -> None:
        """
        Helper method to emit an Action via Runtime or store it.

        This works with Grammar School's current implementation where
        @method handlers execute immediately. Actions can be:
        1. Passed to a Runtime (if provided) via runtime.execute(action)
        2. Stored in self._actions for later retrieval

        Args:
            action: The action to emit
        """
        # Use Runtime if available
        if self._runtime is not None:
            self._runtime.execute(action)
        else:
            # Store in actions list for later retrieval
            self._actions.append(action)

    def _get_selected_track_index(self) -> int:
        """
        Get the index of the currently selected track from state.

        Returns:
            int: Track index (0-based), or -1 if not found
        """
        if self.state is None:
            return -1

        state_map = self.state.get("state", self.state)
        tracks = state_map.get("tracks", [])

        for i, track in enumerate(tracks):
            if isinstance(track, dict) and track.get("selected", False):
                return i

        return -1


# Custom Runtime for MAGDA that collects actions
class MagdaActionCollector:
    """
    Runtime that collects Actions instead of executing them immediately.

    This allows you to build up a list of actions that can be executed later,
    or converted to the REAPER API format.

    This implements the Runtime protocol from Grammar School.
    """

    def __init__(self):
        """Initialize the action collector."""
        self.actions: list[Action] = []

    def execute(self, action: Action) -> None:
        """
        Collect an action for later execution.

        This method is called by Grammar School's interpreter when methods
        emit Actions through the Runtime.

        Args:
            action: The action to collect
        """
        self.actions.append(action)
        logger.debug(f"Collected action: {action.kind}")

    def get_actions(self) -> list[dict[str, Any]]:
        """
        Convert collected Actions to REAPER API format.

        Returns:
            list: List of REAPER API action dictionaries
        """
        result = []
        for action in self.actions:
            # Convert Action to dict format expected by REAPER API
            api_action = {
                "action": action.kind,
                **action.payload,
            }
            result.append(api_action)
        return result

    def clear(self) -> None:
        """Clear all collected actions."""
        self.actions = []


class DSLParserActionParadigm:
    """
    DSL Parser using Action paradigm.

    This parser collects Actions instead of executing them directly,
    allowing for deferred execution and better testability.

    Example:
        ```python
        parser = DSLParserActionParadigm()
        parser.set_state({"state": {"tracks": [...]}})
        actions = parser.parse_dsl('track(instrument="Serum").new_clip(bar=1)')
        # actions is a list of REAPER API action dictionaries
        ```
    """

    def __init__(self):
        """Initialize the DSL parser with action collection."""
        self.collector = MagdaActionCollector()
        self.grammar = MagdaDSLGrammar(runtime=self.collector)

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

        # Clear previous actions
        self.collector.clear()

        try:
            # Execute DSL code - Actions will be collected by Runtime
            # Functional methods (map, filter, etc.) execute immediately
            # Side-effect methods (track, new_clip, etc.) emit Actions via Runtime
            self.grammar.execute(dsl_code)
            actions = self.collector.get_actions()

            if not actions:
                raise ValueError("no actions found in DSL code")

            logger.info(
                f"✅ DSL Parser (Action Paradigm): Translated {len(actions)} actions from DSL"
            )
            return actions
        except Exception as e:
            logger.error(f"Failed to parse DSL: {e}")
            raise ValueError(f"failed to parse DSL: {e}") from e

    def get_collected_actions(self) -> list[Action]:
        """
        Get the raw Action objects collected by the Runtime.

        Returns:
            list: List of Action objects
        """
        return self.collector.actions

