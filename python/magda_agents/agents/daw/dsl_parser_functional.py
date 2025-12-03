"""
DSL Parser with Functional Methods Implementation for REAPER Collections.

This shows how to implement filter, map, etc. that iterate over REAPER data structures
like tracks, FX chains, clips, etc.
"""

import logging
from typing import Any, Callable

from grammar_school import Grammar, method
from grammar_school.ast import Expression, PropertyAccess, Value
from grammar_school.interpreter import Interpreter

from magda_agents.llm.magda_dsl_grammar import get_magda_dsl_grammar

logger = logging.getLogger(__name__)


class ReaperFunctionalInterpreter(Interpreter):
    """
    Custom interpreter that supports iteration variables for functional methods.

    This allows expressions like `track.name == "FX"` where `track` is the
    current item being iterated over in a filter/map operation.
    """

    def __init__(self, dsl_instance: Any):
        """Initialize with DSL instance and iteration context."""
        super().__init__(dsl_instance)
        self._iteration_context: dict[str, Any] = {}

    def set_iteration_context(self, context: dict[str, Any]) -> None:
        """
        Set the current iteration context.

        Used by functional methods to provide iteration variables like 'track', 'fx', etc.

        Args:
            context: Dict mapping iteration variable names to their current values
                     e.g., {"track": {...}, "fx": {...}}
        """
        self._iteration_context = context

    def clear_iteration_context(self) -> None:
        """Clear the iteration context."""
        self._iteration_context = {}

    def _evaluate_property_access(self, prop: PropertyAccess) -> Any:
        """
        Evaluate property access like track.name, checking iteration context first.

        This override checks the iteration context before falling back to
        the standard DSL attribute lookup.
        """
        # First check iteration context (for filter/map iteration variables)
        if prop.object_name in self._iteration_context:
            obj = self._iteration_context[prop.object_name]
        else:
            # Fall back to standard lookup
            obj = getattr(self.dsl, prop.object_name, None)
            if obj is None:
                # Try as a variable in data store
                if hasattr(self.dsl, "data") and isinstance(self.dsl.data, dict):
                    obj = self.dsl.data.get(prop.object_name)
                if obj is None:
                    raise ValueError(f"Unknown object: {prop.object_name}")

        # Navigate through properties
        result = obj
        for prop_name in prop.properties:
            if hasattr(result, prop_name):
                result = getattr(result, prop_name)
            elif isinstance(result, dict):
                result = result.get(prop_name)
            elif isinstance(result, list) and prop_name.isdigit():
                # Handle list indexing like items.0
                index = int(prop_name)
                result = result[index]
            else:
                raise ValueError(f"Property '{prop_name}' not found on {type(result).__name__}")

        return result

    def _evaluate_expression(self, expr: Expression) -> Any:
        """
        Evaluate expression with iteration context support.

        Override to use our custom property access evaluation.
        """
        if expr.operator is None:
            return self._evaluate_value(expr.left)

        # Binary operator expression
        left_val = self._evaluate_value(expr.left)
        right_val = self._evaluate_value(expr.right) if expr.right else None

        # Evaluate based on operator
        operators = {
            "+": lambda a, b: a + b,
            "-": lambda a, b: a - b,
            "*": lambda a, b: a * b,
            "/": lambda a, b: a / b,
            "==": lambda a, b: a == b,
            "!=": lambda a, b: a != b,
            "<": lambda a, b: a < b,
            ">": lambda a, b: a > b,
            "<=": lambda a, b: a <= b,
            ">=": lambda a, b: a >= b,
            "and": lambda a, b: a and b,
            "or": lambda a, b: a or b,
        }

        if expr.operator in operators:
            return operators[expr.operator](left_val, right_val)

        raise ValueError(f"Unknown operator: {expr.operator}")


class ReaperDSLGrammar(Grammar):
    """
    MAGDA DSL Grammar with functional methods for REAPER collections.

    Supports iterating over:
    - tracks (from REAPER state)
    - fx_chain (FX plugins on a track)
    - clips (clips on a track)
    - items (media items in a clip)
    - etc.
    """

    def __init__(self):
        """Initialize with custom interpreter for iteration support."""
        super().__init__(grammar=get_magda_dsl_grammar())
        # Replace interpreter with our custom one
        self.interpreter = ReaperFunctionalInterpreter(self)

        # State and data storage
        self.current_track_index = -1
        self.track_counter = 0
        self.state: dict[str, Any] | None = None
        self.data: dict[str, Any] = {}  # Storage for intermediate results
        self._actions: list[dict[str, Any]] = []

    def set_state(self, state: dict[str, Any]) -> None:
        """
        Set the current REAPER state.

        Args:
            state: REAPER state dict with tracks, clips, etc.
        """
        self.state = state
        # Also populate data with common collections
        if state:
            state_map = state.get("state", state)
            if "tracks" in state_map:
                self.data["tracks"] = state_map["tracks"]
            if "clips" in state_map:
                self.data["clips"] = state_map["clips"]

    # ========== Side-effect methods (omitted for brevity - same as before) ==========

    # ========== Functional methods with iteration support ==========

    @method
    def filter(self, collection: str | list[Any], predicate) -> list[Any]:
        """
        Filter a collection using a predicate expression.

        Iterates over collection items and evaluates predicate for each.
        Predicate can use iteration variable (derived from collection name).

        Examples:
            filter(tracks, track.name == "FX")
            filter(fx_chain, fx.name.contains("EQ"))
            filter(clips, clip.start < 4.0)

        Args:
            collection: Collection name (string) or actual collection (list)
            predicate: Predicate expression (e.g., Expression, PropertyAccess, callable)

        Returns:
            Filtered list
        """
        # Resolve collection
        if isinstance(collection, str):
            actual_collection = self.data.get(collection, [])
            # Derive iteration variable name from collection name
            # tracks -> track, fx_chain -> fx, clips -> clip
            iter_var = collection.rstrip("s").rstrip("_chain")  # Simple heuristic
        else:
            actual_collection = collection
            iter_var = "item"  # Default

        if not isinstance(actual_collection, list):
            raise ValueError(f"Collection must be a list, got {type(actual_collection).__name__}")

        # Evaluate predicate for each item
        filtered = []
        interpreter = self.interpreter  # type: ReaperFunctionalInterpreter

        for item in actual_collection:
            # Set iteration context
            interpreter.set_iteration_context({iter_var: item})

            try:
                # Evaluate predicate
                if isinstance(predicate, (Expression, PropertyAccess, Value)):
                    # AST node - evaluate it
                    result = interpreter._evaluate_value(predicate)
                elif callable(predicate):
                    # Callable function - call it with item
                    result = predicate(item)
                elif isinstance(predicate, bool):
                    # Already evaluated
                    result = predicate
                else:
                    # Try to evaluate as expression
                    result = interpreter._evaluate_value(predicate)

                # If predicate is truthy, include item
                if result:
                    filtered.append(item)

            except Exception as e:
                logger.warning(f"Error evaluating predicate for item: {e}")
                continue
            finally:
                # Clear iteration context after each item
                interpreter.clear_iteration_context()

        logger.debug(f"Filtered {len(actual_collection)} items to {len(filtered)}")
        return filtered

    @method
    def map(self, func: Callable | str, collection: str | list[Any]) -> list[Any]:
        """
        Map a function over a collection.

        Examples:
            map(@process_track, tracks)
            map(@normalize_fx, fx_chain)

        Args:
            func: Function reference (e.g., "@process_track") or callable
            collection: Collection name (string) or actual collection (list)

        Returns:
            Mapped list
        """
        # Resolve collection
        if isinstance(collection, str):
            actual_collection = self.data.get(collection, [])
            iter_var = collection.rstrip("s").rstrip("_chain")
        else:
            actual_collection = collection
            iter_var = "item"

        if not isinstance(actual_collection, list):
            raise ValueError(f"Collection must be a list, got {type(actual_collection).__name__}")

        # Resolve function
        if isinstance(func, str):
            func_name = func.lstrip("@")
            # Try to get from method handlers
            if hasattr(self, func_name):
                func = getattr(self, func_name)
            else:
                raise ValueError(f"Unknown function: {func_name}")

        if not callable(func):
            raise ValueError(f"Function must be callable, got {type(func).__name__}")

        # Map function over collection
        mapped = []
        interpreter = self.interpreter  # type: ReaperFunctionalInterpreter

        for item in actual_collection:
            # Set iteration context
            interpreter.set_iteration_context({iter_var: item})

            try:
                # Call function with item
                result = func(item)
                mapped.append(result)
            except Exception as e:
                logger.warning(f"Error mapping function over item: {e}")
                continue
            finally:
                interpreter.clear_iteration_context()

        logger.debug(f"Mapped {len(actual_collection)} items")
        return mapped

    @method
    def for_each(self, collection: str | list[Any], action_func: Callable | str) -> None:
        """
        Execute an action function for each item in collection.

        Similar to map but for side effects (emits Actions).

        Examples:
            for_each(filtered_tracks, @add_fx)
            for_each(fx_chain, @remove_fx)

        Args:
            collection: Collection name (string) or actual collection (list)
            action_func: Action function reference or callable
        """
        # Resolve collection
        if isinstance(collection, str):
            actual_collection = self.data.get(collection, [])
            iter_var = collection.rstrip("s").rstrip("_chain")
        else:
            actual_collection = collection
            iter_var = "item"

        if not isinstance(actual_collection, list):
            raise ValueError(f"Collection must be a list, got {type(actual_collection).__name__}")

        # Resolve function
        if isinstance(action_func, str):
            func_name = action_func.lstrip("@")
            if hasattr(self, func_name):
                action_func = getattr(self, func_name)
            else:
                raise ValueError(f"Unknown function: {func_name}")

        if not callable(action_func):
            raise ValueError(f"Function must be callable, got {type(action_func).__name__}")

        # Execute for each item
        interpreter = self.interpreter  # type: ReaperFunctionalInterpreter

        for item in actual_collection:
            interpreter.set_iteration_context({iter_var: item})

            try:
                # Execute action function
                action_func(item)
            except Exception as e:
                logger.warning(f"Error executing action for item: {e}")
                continue
            finally:
                interpreter.clear_iteration_context()

    @method
    def reduce(self, func: Callable | str, collection: str | list[Any], initial: Any = None) -> Any:
        """
        Reduce a collection using a function.

        Args:
            func: Reduction function
            collection: Collection name or actual collection
            initial: Initial value

        Returns:
            Reduced value
        """
        # Resolve collection
        if isinstance(collection, str):
            actual_collection = self.data.get(collection, [])
        else:
            actual_collection = collection

        if not isinstance(actual_collection, list):
            raise ValueError(f"Collection must be a list, got {type(actual_collection).__name__}")

        # Resolve function
        if isinstance(func, str):
            func_name = func.lstrip("@")
            if hasattr(self, func_name):
                func = getattr(self, func_name)
            else:
                raise ValueError(f"Unknown function: {func_name}")

        if not callable(func):
            raise ValueError(f"Function must be callable, got {type(func).__name__}")

        # Reduce collection
        from functools import reduce as functools_reduce

        result = functools_reduce(func, actual_collection, initial)
        logger.debug(f"Reduced {len(actual_collection)} items")
        return result

    @method
    def store(self, name: str, value: Any) -> None:
        """
        Store a value for later use.

        Args:
            name: Variable name
            value: Value to store
        """
        self.data[name] = value
        logger.debug(f"Stored {name} = {value}")

    @method
    def get_tracks(self) -> list[dict[str, Any]]:
        """
        Get all tracks from REAPER state.

        Returns:
            List of track dictionaries
        """
        if self.state is None:
            return []

        state_map = self.state.get("state", self.state)
        tracks = state_map.get("tracks", [])
        self.data["tracks"] = tracks
        return tracks

    @method
    def get_fx_chain(self, track_index: int | None = None) -> list[dict[str, Any]]:
        """
        Get FX chain for a track.

        Args:
            track_index: Track index (0-based). Uses current_track_index if None.

        Returns:
            List of FX dictionaries
        """
        if track_index is None:
            track_index = self.current_track_index

        if track_index < 0 or self.state is None:
            return []

        state_map = self.state.get("state", self.state)
        tracks = state_map.get("tracks", [])

        if track_index >= len(tracks):
            return []

        track = tracks[track_index]
        fx_chain = track.get("fx", [])
        self.data["fx_chain"] = fx_chain
        return fx_chain

    @method
    def get_clips(self, track_index: int | None = None) -> list[dict[str, Any]]:
        """
        Get clips for a track.

        Args:
            track_index: Track index (0-based). Uses current_track_index if None.

        Returns:
            List of clip dictionaries
        """
        if track_index is None:
            track_index = self.current_track_index

        if track_index < 0 or self.state is None:
            return []

        state_map = self.state.get("state", self.state)
        tracks = state_map.get("tracks", [])

        if track_index >= len(tracks):
            return []

        track = tracks[track_index]
        clips = track.get("clips", [])
        self.data["clips"] = clips
        return clips

    # Helper method to extract iteration variable name from collection name
    def _get_iter_var_from_collection(self, collection_name: str) -> str:
        """
        Derive iteration variable name from collection name.

        Examples:
            tracks -> track
            fx_chain -> fx
            clips -> clip
            items -> item

        Args:
            collection_name: Name of the collection

        Returns:
            Iteration variable name
        """
        # Remove common suffixes
        var = collection_name.rstrip("s").rstrip("_chain").rstrip("_list")
        # If empty or single char, use default
        if not var or len(var) < 2:
            return "item"
        return var


# Example usage DSL code:
"""
# Filter tracks by name
store(filtered_tracks, filter(tracks, track.name == "FX"))

# Filter FX chain
store(eq_plugins, filter(fx_chain, fx.name.contains("EQ")))

# Map over filtered tracks
store(processed_tracks, map(@process_track, filtered_tracks))

# For each filtered track, add FX
for_each(filtered_tracks, @add_reverb)
"""

