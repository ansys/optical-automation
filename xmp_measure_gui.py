"""Measure XMP region averages with a hidden Speos Labs COM viewer on Windows."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
import gc
import math
import os
from pathlib import Path
import queue
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any


@dataclass(frozen=True)
class Region:
    """Store full width/height in map axis units, including for ellipses."""

    shape: str
    x: float
    y: float
    width: float
    height: float

    def __post_init__(self) -> None:
        """Reject unsupported shapes and non-finite or non-positive dimensions."""
        if self.shape not in {"rectangle", "ellipse"}:
            raise ValueError("The measurement region must be a rectangle or an ellipse.")
        if not all(math.isfinite(v) for v in (self.x, self.y, self.width, self.height)):
            raise ValueError("Center coordinates and dimensions must be finite numbers.")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Dimensions must be greater than zero.")

    @classmethod
    def from_dimensions(
        cls, shape: str, x: float, y: float, width: float, height: float,
    ) -> Region:
        """Convert GUI ellipse radii to full API dimensions exactly once."""
        factor = 2 if shape == "ellipse" else 1
        return cls(shape, x, y, width * factor, height * factor)


@dataclass(frozen=True)
class MapInfo:
    """Keep map metadata alongside the numerical average."""

    axis_unit: str
    value_type: int
    unit_type: int
    xmin: float
    xmax: float
    ymin: float
    ymax: float

    @property
    def value_unit(self) -> str:
        """Label common photometric/radiometric quantities without converting them."""
        units = {
            (0, 0): "W/m²", (0, 1): "lx",
            (1, 0): "W/sr", (1, 1): "cd",
            (2, 0): "W/(sr·m²)", (2, 1): "cd/m²",
        }
        return units.get(
            (self.value_type, self.unit_type),
            f"ValueType={self.value_type}, ReturnUnitType={self.unit_type}",
        )


@dataclass(frozen=True)
class Measurement:
    """Represent either one valid average or one explicit file error."""

    filename: str
    average: float | None = None
    info: MapInfo | None = None
    error: str = ""

    @property
    def text_value(self) -> str:
        """Return a compact number or a single-line failure explanation."""
        if self.error:
            return "ERROR (" + " ".join(self.error.split()) + ")"
        if self.average is None:
            raise ValueError("No average value is available.")
        return format(self.average, ".15g")


def find_xmp_files(folder: Path) -> list[Path]:
    """Find XMP files directly in the selected folder, case insensitively."""
    if not folder.is_dir():
        raise ValueError("Please select a valid XMP folder.")
    files = sorted(
        (p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".xmp"),
        key=lambda p: p.name.casefold(),
    )
    if not files:
        raise ValueError("No XMP files found in the selected folder. Subfolders are not searched.")
    return files


def com_value(viewer: Any, name: str) -> Any:
    """Accept pywin32's method or property representation of no-argument members."""
    member = getattr(viewer, name)
    return member() if callable(member) else member


@contextmanager
def hidden_viewer(progid: str) -> Iterator[Any]:
    """Create and release a private COM instance in the calling worker thread."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise RuntimeError(
            "pywin32 is required. See the user guide for Python environment setup."
        ) from exc

    pythoncom.CoInitialize()
    viewer = None
    try:
        # DispatchEx avoids attaching to a user's already open viewer.
        viewer = win32com.client.DispatchEx(progid)
        if not viewer.Show(0):
            raise RuntimeError("Failed to hide the XMP Viewer window.")
        yield viewer
    finally:
        # Release only this instance; never kill existing viewer processes.
        viewer = None
        gc.collect()
        pythoncom.CoUninitialize()


def open_map(viewer: Any, path: Path) -> MapInfo:
    """Open without saving and read the map's native measurement metadata."""
    if not viewer.OpenFile(str(path)):
        raise RuntimeError("OpenFile failed: unable to read the XMP file.")
    if not viewer.Show(0):
        raise RuntimeError("Failed to hide the XMP Viewer window.")
    if int(com_value(viewer, "GetIntensityType")) == 3:
        raise ValueError("Conoscopic maps do not support this rectangle/ellipse coordinate input.")
    info = MapInfo(
        axis_unit=str(com_value(viewer, "GetAxisUnitName")),
        value_type=int(com_value(viewer, "ValueType")),
        unit_type=int(com_value(viewer, "ReturnUnitType")),
        xmin=float(com_value(viewer, "XMin")),
        xmax=float(com_value(viewer, "XMax")),
        ymin=float(com_value(viewer, "YMin")),
        ymax=float(com_value(viewer, "YMax")),
    )
    if not all(math.isfinite(v) for v in (info.xmin, info.xmax, info.ymin, info.ymax)):
        raise ValueError("Invalid map coordinate bounds.")
    if info.xmin >= info.xmax or info.ymin >= info.ymax:
        raise ValueError("Invalid map coordinate bounds.")
    return info


def measure_map(viewer: Any, region: Region, info: MapInfo) -> float:
    """Read the eighth API result (Average), not a Python-computed approximation."""
    if (
        region.x - region.width / 2 < info.xmin
        or region.x + region.width / 2 > info.xmax
        or region.y - region.height / 2 < info.ymin
        or region.y + region.height / 2 > info.ymax
    ):
        raise ValueError(
            f"The measurement region exceeds the map bounds: "
            f"X=[{info.xmin:g}, {info.xmax:g}], Y=[{info.ymin:g}, {info.ymax:g}] "
            f"({info.axis_unit})"
        )
    # Measure the entire region, not a threshold-filtered subset saved in an XMP.
    for name in ("RemoveSurfaceThresholdMin", "RemoveSurfaceThresholdMax"):
        if not com_value(viewer, name):
            raise RuntimeError(f"{name} failed")
    method = (
        viewer.SurfaceRectangleCalculation
        if region.shape == "rectangle"
        else viewer.SurfaceEllipseCalculation
    )
    values = method(region.x, region.y, region.width, region.height)
    if not isinstance(values, (tuple, list)) or len(values) < 8:
        raise RuntimeError("The Speos API did not return a valid measurement result array.")
    if values[7] is None or isinstance(values[7], bool):
        raise RuntimeError("The Speos API did not return a valid average.")
    average = float(values[7])
    if not math.isfinite(average):
        raise RuntimeError("The average is NaN or infinite.")
    return average


def measure_files(
    viewer: Any,
    files: list[Path],
    region: Region,
    stop: threading.Event,
    on_result: Callable[[Measurement], None],
) -> list[Measurement]:
    """Process files independently and keep failures out of numerical results."""
    results: list[Measurement] = []
    baseline: tuple[str, int, int] | None = None
    for path in files:
        if stop.is_set():
            break
        info = None
        try:
            info = open_map(viewer, path)
            signature = (info.axis_unit, info.value_type, info.unit_type)
            if baseline is not None and signature != baseline:
                raise ValueError(
                    "Axis units or measurement quantity/units differ "
                    "from the first successful file."
                )
            average = measure_map(viewer, region, info)
            baseline = signature
            item = Measurement(path.name, average, info)
        except Exception as exc:
            item = Measurement(path.name, info=info, error=str(exc) or type(exc).__name__)
        results.append(item)
        on_result(item)
    return results


def save_results(path: Path, results: list[Measurement]) -> None:
    """Atomically save filename : value lines as UTF-8, leaving no partial final file."""
    if path.suffix.lower() != ".txt":
        raise ValueError("The output file must have a .txt extension.")
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8-sig", newline="\n", dir=path.parent,
            prefix=".xmp_measure_", suffix=".tmp", delete=False,
        ) as stream:
            temporary = Path(stream.name)
            for item in results:
                stream.write(f"{item.filename} : {item.text_value}\n")
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class MeasureApp:
    """Provide a separate Tk GUI; all Speos COM calls stay on a worker thread."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("XMP Region Average Extraction · Speos Labs")
        root.geometry("1040x740")
        root.minsize(880, 660)
        style = ttk.Style(root)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
        style.configure("Treeview", rowheight=28)

        self.folder = tk.StringVar()
        self.output = tk.StringVar()
        self.shape = tk.StringVar(value="rectangle")
        self.dimension_x = tk.StringVar(value="Width (full width)")
        self.dimension_y = tk.StringVar(value="Height (full height)")
        self.coords = {name: tk.StringVar() for name in ("x", "y", "width", "height")}
        self.status = tk.StringVar(value="Select a folder and enter the measurement region.")
        self.map_info = tk.StringVar()
        self.events: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.stop = threading.Event()
        self.busy = False
        self.controls: list[ttk.Widget] = []
        self.last_results: list[Measurement] = []
        self._build()
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.after(100, self._poll)

    def _build(self) -> None:
        panel = ttk.Frame(self.root, padding=20)
        panel.pack(fill="both", expand=True)
        panel.columnconfigure(0, weight=1)
        panel.rowconfigure(5, weight=1)
        ttk.Label(panel, text="XMP Region Average Batch Extraction", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 12)
        )
        paths = ttk.LabelFrame(panel, text="1. Input / Output", padding=(12, 8))
        paths.grid(row=1, column=0, sticky="ew")
        paths.columnconfigure(1, weight=1)
        for row, (label, var, command) in enumerate((
            ("XMP folder", self.folder, self._browse_folder),
            ("Output TXT", self.output, self._browse_output),
        )):
            ttk.Label(paths, text=label).grid(row=row, column=0, sticky="w", padx=(0, 10))
            entry = ttk.Entry(paths, textvariable=var)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            button = ttk.Button(paths, text="Browse…", command=command)
            button.grid(row=row, column=2, padx=(8, 0))
            self.controls.extend((entry, button))
        region = ttk.LabelFrame(panel, text="2. Measurement Region", padding=12)
        region.grid(row=2, column=0, sticky="ew", pady=12)
        region.columnconfigure((0, 1), weight=1, uniform="measure")
        for col, (text, value) in enumerate((("Rectangle", "rectangle"), ("Ellipse", "ellipse"))):
            radio = ttk.Radiobutton(
                region, text=text, value=value, variable=self.shape,
                command=self._update_dimension_labels,
            )
            radio.grid(row=0, column=col, sticky="w", pady=(0, 10))
            self.controls.append(radio)
        center = ttk.LabelFrame(region, text="Center", padding=8)
        center.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
        dimension = ttk.LabelFrame(region, text="Dimension", padding=8)
        dimension.grid(row=1, column=1, sticky="nsew", padx=(6, 0))
        for frame, fields in (
            (center, (("x", "X"), ("y", "Y"))),
            (dimension, (("width", self.dimension_x), ("height", self.dimension_y))),
        ):
            frame.columnconfigure(1, weight=1)
            for row, (key, label) in enumerate(fields):
                caption = (
                    ttk.Label(frame, textvariable=label)
                    if isinstance(label, tk.StringVar)
                    else ttk.Label(frame, text=label)
                )
                caption.grid(row=row, column=0, sticky="w", padx=(0, 10))
                entry = ttk.Entry(frame, textvariable=self.coords[key], width=12)
                entry.grid(row=row, column=1, sticky="ew", pady=3)
                self.controls.append(entry)
        ttk.Label(
            region,
            text=(
                "Enter Center / Dimension values in the same way as in XMP Measures.\n"
                "Original XMP files are not modified. "
                "The average is read over the entire specified region."
            ),
            wraplength=900,
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10, 0))

        actions = ttk.Frame(panel)
        actions.grid(row=3, column=0, sticky="ew")
        start = ttk.Button(actions, text="Extract Averages and Save TXT", command=self._start)
        start.pack(side="left")
        self.controls.append(start)
        self.cancel = ttk.Button(actions, text="Stop", command=self._cancel, state="disabled")
        self.cancel.pack(side="left", padx=8)
        self.progress = ttk.Progressbar(actions, mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=(8, 0))
        ttk.Label(panel, textvariable=self.status, wraplength=950).grid(
            row=4, column=0, sticky="w", pady=10
        )
        table = ttk.Frame(panel)
        table.grid(row=5, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(
            table, columns=("file", "value", "unit", "status"), show="headings"
        )
        for key, title, width in (
            ("file", "XMP filename", 270), ("value", "Average", 140),
            ("unit", "Value unit", 130), ("status", "Status / Error", 390),
        ):
            self.tree.heading(key, text=title)
            self.tree.column(key, width=width, minwidth=80)
        self.tree.grid(row=0, column=0, sticky="nsew")
        self.tree.tag_configure("error", foreground="#b42318")
        vertical = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)

    def _update_dimension_labels(self) -> None:
        ellipse = self.shape.get() == "ellipse"
        self.dimension_x.set("Rx (X radius)" if ellipse else "Width (full width)")
        self.dimension_y.set("Ry (Y radius)" if ellipse else "Height (full height)")

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(parent=self.root, title="Select XMP Folder")
        if folder:
            self.folder.set(folder)
            self.output.set(str(Path(folder) / "xmp_average_results.txt"))
            self.map_info.set("")

    def _browse_output(self) -> None:
        path = filedialog.asksaveasfilename(
            parent=self.root, title="Save Output TXT", defaultextension=".txt",
            filetypes=[("Text files", "*.txt")], initialfile="xmp_average_results.txt",
        )
        if path:
            self.output.set(path)

    def _inputs(self) -> tuple[list[Path], str]:
        if not self.folder.get().strip():
            raise ValueError("Please select an XMP folder.")
        return (
            find_xmp_files(Path(self.folder.get().strip()).expanduser().resolve()),
            "XmpViewer.Application",
        )

    def _inspect(self) -> None:
        try:
            files, progid = self._inputs()
        except (ValueError, OSError) as exc:
            messagebox.showerror("Check Input", str(exc), parent=self.root)
            return
        self._launch(files, progid, None, None)

    def _start(self) -> None:
        try:
            files, progid = self._inputs()
            try:
                values = {key: float(var.get().strip()) for key, var in self.coords.items()}
            except ValueError as exc:
                raise ValueError("Enter numeric values for Center X/Y and Dimension.") from exc
            region = Region.from_dimensions(self.shape.get(), **values)
            if not self.output.get().strip():
                raise ValueError("Please select an output TXT file path.")
            output = Path(self.output.get().strip()).expanduser().resolve()
            if output.suffix.lower() != ".txt" or not output.parent.is_dir() or output.is_dir():
                raise ValueError("Specify a .txt file path in an existing folder.")
            if output.exists() and not messagebox.askyesno(
                "Confirm Overwrite", f"Overwrite the existing results?\n{output}", parent=self.root
            ):
                return
        except (ValueError, OSError) as exc:
            messagebox.showerror("Check Input", str(exc), parent=self.root)
            return
        self.tree.delete(*self.tree.get_children())
        self.last_results = []
        self.progress.configure(value=0, maximum=len(files))
        self._launch(files, progid, region, output)

    def _launch(
        self, files: list[Path], progid: str, region: Region | None, output: Path | None,
    ) -> None:
        self.busy = True
        self.stop.clear()
        for control in self.controls:
            control.configure(state="disabled")
        self.cancel.configure(state="normal" if region else "disabled")
        self.status.set("Connecting to Speos Labs… (viewer window hidden)")
        threading.Thread(
            target=self._worker, args=(files, progid, region, output), daemon=True,
        ).start()

    def _worker(
        self, files: list[Path], progid: str, region: Region | None, output: Path | None,
    ) -> None:
        try:
            with hidden_viewer(progid) as viewer:
                try:
                    if region is None:
                        info = open_map(viewer, files[0])
                        self.events.put(("info", (files[0].name, info, len(files))))
                        return
                    results = measure_files(
                        viewer, files, region, self.stop,
                        lambda item: self.events.put(("result", item)),
                    )
                finally:
                    # Drop the caller's reference before the context uninitializes COM.
                    viewer = None
            if output is not None and results:
                save_results(output, results)
                self.events.put(("saved", (output, results, len(files))))
            else:
                self.events.put((
                    "notice", "Processing stopped. No output file was saved.",
                ))
        except Exception as exc:
            self.events.put(("error", str(exc) or type(exc).__name__))
        finally:
            self.events.put(("done", None))

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "result":
                    self.last_results.append(payload)
                    self.tree.insert("", "end", values=(
                        payload.filename, "—" if payload.error else payload.text_value,
                        payload.info.value_unit if payload.info else "",
                        payload.error or "Completed",
                    ), tags=("error",) if payload.error else ())
                    self.progress.configure(value=len(self.last_results))
                    self.status.set(
                        f"{len(self.last_results)} file(s) processed: {payload.filename}"
                    )
                elif kind == "info":
                    name, info, count = payload
                    self.map_info.set(
                        f"{name} | Axis unit: {info.axis_unit} | Value unit: {info.value_unit}\n"
                        f"X: [{info.xmin:g}, {info.xmax:g}] / Y: [{info.ymin:g}, {info.ymax:g}]"
                    )
                    self.status.set(
                        f"Found {count} XMP files. Enter the region in the units above."
                    )
                elif kind == "saved":
                    path, results, total = payload
                    failed = sum(bool(item.error) for item in results)
                    state = (
                        "Stopped · Partial results saved" if len(results) < total else "Completed"
                    )
                    summary = (
                        f"{state}: {len(results)}/{total} files processed, "
                        f"Succeeded {len(results) - failed} / Failed {failed}\n{path}"
                    )
                    self.status.set(summary)
                    show = (
                        messagebox.showwarning
                        if failed or len(results) < total
                        else messagebox.showinfo
                    )
                    show("Processing Results", summary, parent=self.root)
                elif kind == "notice":
                    self.status.set(payload)
                elif kind == "error":
                    self.status.set("Processing failed. Any existing results remain in the table.")
                    messagebox.showerror(
                        "Processing Failed",
                        payload + "\n\nCheck the Speos installation, license, and COM ProgID.",
                        parent=self.root,
                    )
                elif kind == "done":
                    self.busy = False
                    self.cancel.configure(state="disabled")
                    for control in self.controls:
                        control.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _cancel(self) -> None:
        self.stop.set()
        self.cancel.configure(state="disabled")
        self.status.set("Stopping after the current file. Only processed results will be saved.")

    def _close(self) -> None:
        if self.busy:
            messagebox.showinfo(
                "Processing",
                "Please wait for the current task to finish before closing. "
                "Use Stop to stop batch extraction.",
                parent=self.root,
            )
            return
        self.root.destroy()


def main() -> None:
    """Launch the standalone measure configuration window."""
    root = tk.Tk()
    MeasureApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
