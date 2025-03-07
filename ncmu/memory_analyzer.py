#!/usr/bin/env python3

import logging
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

import psutil
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Label


# Configure logging (only to file if --log is specified)
def setup_logging(log_to_file: bool):
    logger = logging.getLogger("MemoryAnalyzer")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler (only if --log is specified)
    if log_to_file:
        file_handler = logging.FileHandler("memory_analyzer.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


@dataclass
class ProcessNode:
    pid: int
    name: str
    memory: float  # Memory usage in MB
    user: str
    children: List["ProcessNode"]
    parent: Optional["ProcessNode"] = None  # To track parent for navigation
    self_memory: float = 0.0  # Memory usage of the process itself (excluding children)
    cmdline: str = ""  # Store the full command line string


class GruvboxColors:
    """Gruvbox color theme constants."""

    BG1 = "#3c3836"
    BG2 = "#504945"
    FG = "#ebdbb2"
    BLUE = "#83a598"
    GREEN = "#b8bb26"


class ColumnConfig:
    """Table column configuration."""

    MEMORY = ("Memory", "column-memory", 12)
    USAGE_BAR = ("Usage Bar", "column-usage-bar", 24)
    PROCESS = ("Process", "column-process", 40)
    PID = ("PID", "column-pid", 6)
    USER = ("User", "column-user", 10)

    @classmethod
    def all(cls) -> List[tuple]:
        return [cls.MEMORY, cls.USAGE_BAR, cls.PROCESS, cls.PID, cls.USER]


class ProcessTree:
    """Process tree management."""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.process_map: Dict[int, ProcessNode] = {}
        self.root: Optional[ProcessNode] = None

    def build(self) -> ProcessNode:
        """Build and return the process tree."""
        self.logger.info("Building process tree...")

        # Create a root node for the process tree
        root = ProcessNode(
            pid=0,
            name="System",
            memory=0.0,
            user="root",
            children=[],
            self_memory=0.0,
            cmdline="System",
        )

        # Logic to populate the process tree goes here
        # For example, you can call a method to populate the children of the root node

        return root  # Return the root node


@dataclass
class ProcessRow:
    """Represents a row in the process table."""

    memory: str
    usage_bar: str
    process_name: str
    pid: str
    user: str

    @classmethod
    def from_process(cls, process: ProcessNode, usage_bar: str) -> "ProcessRow":
        # Check if memory exceeds 1024 MiB and convert to GB if so
        memory_display = (
            f"{process.memory / 1024:.2f} GB"
            if process.memory > 1024
            else f"{process.memory:.1f} MiB"
        )
        return cls(
            memory=memory_display,
            usage_bar=usage_bar,
            process_name=process.name[:40],
            pid=f"{process.pid:>5}",
            user=process.user[:10],
        )


class MemoryAnalyzer(App):
    """A Textual app to analyze Linux system memory usage by process tree."""

    # Update the CSS path to be relative to the package
    CSS_PATH = "memory_analyzer.css"

    # Add BINDINGS class variable for better key handling
    BINDINGS = [
        ("escape", "go_back", "Go back to parent"),
        ("enter", "expand_node", "Show children"),
    ]

    def __init__(self, logger: logging.Logger):
        super().__init__()
        self.logger = logger
        self.process_table = DataTable(
            id="process_table",
            cursor_type="row",
            cursor_foreground_priority="renderable",
        )
        self.info_bar = Label(
            "Select a process to view its command line", id="info_bar"
        )
        self.process_map: Dict[int, ProcessNode] = {}
        self.root_node: Optional[ProcessNode] = None  # Root of the process tree
        self.current_node: Optional[ProcessNode] = None  # Current node being viewed

    def calculate_total_memory(self, node: ProcessNode) -> float:
        """Recursively calculate total memory including children."""
        total = node.self_memory  # Start with the process's own memory
        for child in node.children:
            total += self.calculate_total_memory(child)
        node.memory = total  # Update node's total memory to include children
        self.logger.debug(
            f"Calculated total memory for PID {node.pid} ({node.name}): {total:.1f} MB, self_memory: {node.self_memory:.1f} MB"
        )
        return total

    def build_process_tree(self) -> ProcessNode:
        """Build process tree from running processes."""
        self.logger.info("Building process tree...")
        # First pass: create nodes for all processes
        for proc in psutil.process_iter(
            ["pid", "name", "memory_info", "ppid", "username", "cmdline"]
        ):
            try:
                memory_mb = proc.info["memory_info"].rss / 1024 / 1024  # Convert to MB
                cmdline = (
                    " ".join(proc.info["cmdline"])
                    if proc.info["cmdline"]
                    else proc.info["name"]
                )
                node = ProcessNode(
                    pid=proc.info["pid"],
                    name=proc.info["name"],
                    memory=memory_mb,
                    self_memory=memory_mb,  # Store the process's own memory
                    user=proc.info["username"],
                    children=[],
                    cmdline=cmdline,
                )
                self.process_map[proc.info["pid"]] = node
                self.logger.debug(
                    f"Added process: PID {node.pid}, Name {node.name}, Memory {memory_mb:.1f} MB, Cmdline: {cmdline}"
                )
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.warning(
                    f"Failed to access process {proc.info['pid']}: {str(e)}"
                )
                continue

        # Second pass: build tree structure
        root = ProcessNode(
            0, "System", 0.0, "root", [], self_memory=0.0, cmdline="System"
        )
        for pid, node in self.process_map.items():
            try:
                parent_pid = psutil.Process(pid).ppid()
                if parent_pid in self.process_map:
                    node.parent = self.process_map[parent_pid]
                    self.process_map[parent_pid].children.append(node)
                elif pid != 0:  # PID 0 is the root
                    node.parent = root
                    root.children.append(node)
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                self.logger.warning(f"Failed to get parent for PID {pid}: {str(e)}")
                continue

        # Calculate total memory for each node (including children)
        self.calculate_total_memory(root)
        return root

    def create_usage_bar(
        self, node: ProcessNode, siblings_total: float, max_width: int = 20
    ) -> str:
        """Create a visual bar representing memory usage relative to siblings' total."""
        self.logger.debug(
            f"Creating usage bar for PID {node.pid} ({node.name}), total memory: {node.memory:.1f} MB, self_memory: {node.self_memory:.1f} MB, siblings_total: {siblings_total:.1f} MB"
        )
        try:
            if siblings_total == 0:
                bar = "-" * max_width
                self.logger.debug(f"siblings_total is 0, returning empty bar: [{bar}]")
                return f"[{bar}]"

            # Calculate proportions
            total_proportion = (
                node.memory / siblings_total
            )  # Proportion of total memory (self + children)
            self_proportion = (
                node.self_memory / siblings_total
            )  # Proportion of self memory

            # Calculate the number of characters for each part
            total_filled = int(
                total_proportion * max_width
            )  # Total bar length (self + children)
            self_filled = int(self_proportion * max_width)  # Self bar length
            children_filled = total_filled - self_filled  # Children bar length

            # Ensure non-negative lengths
            total_filled = min(total_filled, max_width)
            self_filled = min(self_filled, total_filled)
            children_filled = max(0, total_filled - self_filled)

            # Create the bar with colors using Gruvbox theme
            bar = (
                f"[#83a598]{'#' * self_filled}[/]"  # Gruvbox blue
                + f"[#b8bb26]{'=' * children_filled}[/]"  # Gruvbox green
                + " " * (max_width - total_filled)
            )
            self.logger.debug(
                f"Generated bar: [{bar}], total_filled: {total_filled}, self_filled: {self_filled}, children_filled: {children_filled}, total width: {max_width}"
            )
            return f"[{bar}]"
        except Exception as e:
            self.logger.error(f"Error in create_usage_bar: {str(e)}")
            # Return a default bar in case of error
            bar = "-" * max_width
            self.logger.debug(f"Returning default bar due to error: [{bar}]")
            return f"[{bar}]"

    def populate_table(self, table: DataTable, node: ProcessNode):
        """Populate the DataTable with processes from the current node."""
        self.logger.info(f"Populating table for node: PID {node.pid} ({node.name})")
        # Clear existing rows
        table.clear()

        # Sort children by memory usage (descending)
        children = sorted(node.children, key=lambda x: x.memory, reverse=True)

        # Calculate total memory usage of all siblings in this view
        siblings_total = sum(child.memory for child in children)
        self.logger.debug(
            f"Siblings total memory for this view: {siblings_total:.1f} MB"
        )

        # Add rows for each child
        for child in children:
            # Combine process name and command line arguments
            process_display = (
                f"{child.name} {child.cmdline[len(child.name) :]}"
                if child.cmdline.startswith(child.name)
                else child.cmdline
            )
            process_display = f"{process_display:<40}"[:40]  # Left-align, max 40 chars
            pid = f"{child.pid:>5}"  # Right-align PID
            memory = f"{child.memory:>8.1f} MB"  # Right-align memory
            user = f"{child.user:<10}"[:10]  # Left-align user, max 10 chars
            bar = self.create_usage_bar(
                child, siblings_total
            )  # Generate bar relative to siblings

            # Add row to the table
            row_data = (memory, bar, process_display, pid, user)
            table.add_row(*row_data, key=str(child.pid))
            self.logger.debug(f"Added row: {row_data}")

        # Update info bar for the first row if there are rows
        if table.row_count > 0:
            self.update_info_bar(0)

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        yield Header()
        yield Vertical(
            self.process_table,
            self.info_bar,  # Move info bar to the bottom
        )
        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the app after mounting."""
        # Define column labels, keys, and widths
        columns = ColumnConfig.all()

        # Add columns one by one with their keys and widths
        for label, key, width in columns:
            self.process_table.add_column(label, key=key, width=width)
            self.logger.debug(f"Added column: {label}, key={key}, width={width}")

        # Build the process tree
        self.root_node = self.build_process_tree()
        self.current_node = self.root_node

        # Populate the table with the root node's children
        self.populate_table(self.process_table, self.current_node)

        # Focus the table for navigation
        self.process_table.focus()

    def update_info_bar(self, row_index: int) -> None:
        """Update the info bar with the command line of the selected row."""
        if self.process_table.row_count > 0:
            try:
                # Get the PID of the selected row
                selected_pid = int(
                    self.process_table.get_row_at(row_index)[3]
                )  # PID column
                if selected_pid in self.process_map:
                    selected_node = self.process_map[selected_pid]
                    cmdline = (
                        selected_node.cmdline
                        if selected_node.cmdline
                        else "No command line available"
                    )
                    self.info_bar.update(f"Command: {cmdline}")
                    self.logger.debug(
                        f"Updated info bar for PID {selected_pid}: {cmdline}"
                    )
                else:
                    self.logger.warning(f"PID {selected_pid} not found in process_map")
                    self.info_bar.update("Command: [Not found]")
            except Exception as e:
                self.logger.error(f"Error updating info bar: {str(e)}")
                self.info_bar.update("Command: [Error]")

    def on_key(self, event: events.Key) -> None:
        """Handle key presses."""
        # Rely on Ctrl+C to exit (no 'q' binding)
        if event.key == "enter":
            # Expand the selected process (show its children)
            if self.process_table.row_count > 0:
                cursor_row = self.process_table.cursor_row
                if cursor_row is not None:
                    # Get the PID of the selected row
                    selected_pid = int(
                        self.process_table.get_row_at(cursor_row)[3]
                    )  # PID column
                    if selected_pid in self.process_map:
                        selected_node = self.process_map[selected_pid]
                        if selected_node.children:  # Only expand if there are children
                            self.current_node = selected_node
                            self.populate_table(self.process_table, self.current_node)
                            self.logger.info(
                                f"Expanded to node: PID {selected_pid} ({selected_node.name})"
                            )
        elif event.key == "escape":
            # Go back to parent view
            if self.current_node is not None and self.current_node.parent is not None:
                self.current_node = self.current_node.parent
                self.populate_table(self.process_table, self.current_node)
                self.logger.info(
                    f"Returned to parent node: PID {self.current_node.pid} ({self.current_node.name})"
                )


def main():
    """Entry point for the ncmu command."""
    # Check for --log argument
    log_to_file = "--log" in sys.argv
    logger = setup_logging(log_to_file)

    logger.info("Starting NCMU (NCurses Memory Usage)...")
    app = MemoryAnalyzer(logger)
    app.run()
    logger.info("NCMU stopped.")


if __name__ == "__main__":
    main()
