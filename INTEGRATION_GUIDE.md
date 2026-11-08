# Asset Browser v3.0 - Integration Guide

## Overview

This guide explains how to integrate the new features from `asset_browser_v3_additions.py` into the existing `asset_browser.py` to create version 3.0 with enhanced functionality.

---

## 📁 Files Involved

1. **Original file**: `LwJuRkoW-asset_browser.py` (2383 lines)
2. **Additions file**: `asset_browser_v3_additions.py` (contains new feature implementations)
3. **Output**: Enhanced `asset_browser.py` with all new features

---

## 🔧 Integration Steps

### Step 1: Prepare the Files

```bash
# Copy the original file to a working directory
cp /mnt/vibefs/uploads/8789b27d-d1ba-4d9f-8bce-1cfef667936d/LwJuRkoW-asset_browser.py asset_browser_v3.py

# Copy the additions file
cp /workspace/asset_browser_v3_additions.py .
```

---

### Step 2: Add Imports at the Top

At the very top of `asset_browser_v3.py`, add these imports:

```python
from datetime import datetime
```

---

### Step 3: Add New Classes

Find the line that says:
```python
# ==== END PURE MESH CODE ========================================================
```

Add the following classes **AFTER** this line:

```python
# ============================================================
#  NEW FEATURES v3.0
# ============================================================

# Import the new managers from the additions file
from asset_browser_v3_additions import (
    TagManager, 
    CollectionManager, 
    MetadataManager,
    AssetInfoPanel,
    EnhancedAssetTile,
    ExportToLibraryDialog
)

# Initialize managers (singleton instances)
TAG_MANAGER = TagManager.get_instance()
COLLECTION_MANAGER = CollectionManager.get_instance()
METADATA_MANAGER = MetadataManager.get_instance()
```

---

### Step 4: Modify Constants

Find the line with:
```python
FILTER_ALL = "All"
FILTER_SCENES = "Scenes"
FILTER_MODELS = "3D Models"
FILTER_TEXTURES = "Textures"
```

Add this after:
```python
FILTER_FAVORITES = "Favorites"
```

---

### Step 5: Replace AssetTile with EnhancedAssetTile

Find the `AssetTile` class definition (around line 1200). **Replace the entire class** with:

```python
# Use EnhancedAssetTile from additions
AssetTile = EnhancedAssetTile
```

Alternatively, if you want to keep the original class name but use the enhanced version, you can rename the import:

```python
from asset_browser_v3_additions import EnhancedAssetTile as AssetTile
```

---

### Step 6: Add Asset Info Panel to UI

Find the `setup_ui` method in the `AssetBrowser` class. Add the info panel to the right panel layout.

After this line:
```python
splitter.addWidget(right_panel)
```

Add:
```python
# Add info panel to the right of the preview panel
self.info_panel = AssetInfoPanel()
self.info_panel.setVisible(False)  # Hidden by default
splitter.addWidget(self.info_panel)
```

Then update the splitter sizes:
```python
splitter.setSizes([190, 560, 340, 280])  # Added 280 for info panel
```

---

### Step 7: Update Type Filter

Find where `type_filter` is populated:
```python
self.type_filter.addItems([FILTER_ALL, FILTER_SCENES, FILTER_MODELS, FILTER_TEXTURES])
```

Change to:
```python
self.type_filter.addItems([FILTER_ALL, FILTER_SCENES, FILTER_MODELS, FILTER_TEXTURES, FILTER_FAVORITES])
```

---

### Step 8: Modify _type_exts Method

Find the `_type_exts` method:
```python
def _type_exts(self):
    return {FILTER_ALL: ASSET_EXTS, FILTER_SCENES: SCENE_EXTS,
            FILTER_MODELS: MODEL_EXTS, FILTER_TEXTURES: TEXTURE_EXTS}[self.type_filter.currentText()]
```

Change to:
```python
def _type_exts(self):
    filter_text = self.type_filter.currentText()
    if filter_text == FILTER_FAVORITES:
        return ASSET_EXTS  # We'll filter by favorites separately
    return {FILTER_ALL: ASSET_EXTS, FILTER_SCENES: SCENE_EXTS,
            FILTER_MODELS: MODEL_EXTS, FILTER_TEXTURES: TEXTURE_EXTS}[filter_text]
```

---

### Step 9: Update _on_scan_finished Method

Find the `_on_scan_finished` method. Modify it to filter by favorites:

```python
def _on_scan_finished(self, token, payload):
    if token != str(self._scan_token):
        return

    assets, auto_recursed = payload
    self._set_loading_state(False)
    
    # NEW: Filter by favorites if needed
    if self.type_filter.currentText() == FILTER_FAVORITES:
        assets = [a for a in assets if TAG_MANAGER.is_favorite(a)]
    
    self._populate_grid(assets, auto_recursed)
    if self.auto_preview.isChecked():
        self._start_preview_worker(assets)
```

---

### Step 10: Update _show_preview Method

Find the `_show_preview` method. Add info panel update:

After the line:
```python
self.preview_info.setText("\n".join(info))
```

Add:
```python
# Update info panel
self.info_panel.update_info(asset_path)
self.info_panel.setVisible(True)
```

Also, update `_clear_preview` to hide the info panel:

After:
```python
self._set_preview_actions([])
```

Add:
```python
self.info_panel.setVisible(False)
```

---

### Step 11: Update Context Menu Creation

Find the `_tile_context_menu` method. Replace the entire method with this enhanced version:

```python
def _tile_context_menu(self, asset_path, global_pos):
    menu = QtWidgets.QMenu(self)
    actions = {}

    def add(label, fn):
        a = menu.addAction(label)
        actions[a] = fn

    ext = os.path.splitext(asset_path)[1].lower()
    zup = default_zup(ext)

    # NEW: Tag actions
    from asset_browser_v3_additions import (
        add_tag_actions, add_collection_actions, add_metadata_actions,
        toggle_favorite, export_selection_to_library
    )
    
    add_tag_actions(menu, asset_path, self)
    add_collection_actions(menu, asset_path, self)
    add_metadata_actions(menu, asset_path, self)
    
    menu.addSeparator()

    if is_texture(asset_path):
        add("Create File Texture Node",
            lambda: _run("create file node", create_file_texture, asset_path))
        add("Create && Assign to Selected Shader",
            lambda: _run("create/assign file node", create_file_texture, asset_path, True))
        add("Copy File Path", lambda: self._copy_path(asset_path))
        menu.addSeparator()
    else:
        add("Import", lambda: _run("import", import_asset, asset_path))
        if is_scene(asset_path) or ext in _REF_TYPES:
            add("Reference", lambda: _run("reference", reference_asset, asset_path))
        if ext in BUILTIN_IMPORT_EXTS or ext == ".obj":
            add("Import (Built-in Loader)",
                lambda: _run("built-in import", import_model, asset_path,
                             None, self._current_zup(asset_path) if self._preview_path == asset_path else zup,
                             False, True))
        menu.addSeparator()
        add("Generate Preview (via Maya Import)", lambda: self._maya_preview(asset_path))
        add("Generate Thumbnail from Selection", lambda: self._generate_thumb(asset_path))
        add("Clear Thumbnail", lambda: self._clear_thumb(asset_path))
        menu.addSeparator()

    add("Show in Explorer / Finder", lambda: self._reveal(asset_path))
    add("Rename...", lambda: self._rename(asset_path))
    add("Delete Asset...", lambda: self._delete(asset_path))

    chosen = menu.exec_(global_pos)
    if chosen in actions:
        actions[chosen]()
```

---

### Step 12: Add Export to Library Functionality

Add a new method to the `AssetBrowser` class for exporting to library:

```python
def export_to_library(self):
    """Export selected Maya objects to the current library folder."""
    if not self.current_folder:
        cmds.warning("Asset Browser: No library folder selected.")
        return
    
    dialog = ExportToLibraryDialog(self.current_folder, self)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        info = dialog.get_export_info()
        result = export_selection_to_library(
            self.current_folder,
            name=info['name'],
            description=info['description'],
            tags=info['tags']
        )
        if result:
            self.refresh_grid()
            cmds.inViewMessage(
                amg="Exported to library: <hl>%s</hl>" % os.path.basename(result),
                pos="topCenter",
                fade=True
            )
```

Then add a button to trigger this. In the `setup_ui` method, after creating the `btn_refresh` button:

```python
# Add Export to Library button
self.btn_export = QtWidgets.QPushButton("Export to Library")
self.btn_export.clicked.connect(self.export_to_library)
top_bar.addWidget(self.btn_export)
```

---

### Step 13: Add Thumbnail Size Slider

In the filter bar section of `setup_ui`, add the slider:

After:
```python
filter_bar.addStretch()
```

Add:
```python
# NEW: Thumbnail size slider
filter_bar.addWidget(QtWidgets.QLabel("Thumb Size:"))
self.thumb_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
self.thumb_size_slider.setRange(64, 192)
self.thumb_size_slider.setValue(THUMB_SIZE)
self.thumb_size_slider.setFixedWidth(120)
self.thumb_size_slider.valueChanged.connect(self._change_thumb_size)
filter_bar.addWidget(self.thumb_size_slider)
```

Then add the handler method:

```python
def _change_thumb_size(self, value):
    """Change thumbnail size and refresh grid."""
    global THUMB_SIZE
    THUMB_SIZE = value
    self.refresh_grid()
```

---

### Step 14: Update AssetTile Initialization

Find where `AssetTile` is instantiated in `_populate_grid`:

```python
tile = AssetTile(asset_path, self.grid_container)
```

Change to pass the thumb_size:

```python
tile = AssetTile(asset_path, self.grid_container, thumb_size=THUMB_SIZE)
```

---

### Step 15: Add Batch Operations Support

Add multi-selection support. First, add to the `AssetTile` class (in EnhancedAssetTile):

```python
# Add to __init__:
self._selected = False
self.setStyleSheet(self._get_style())

# Add methods:
def set_selected(self, selected):
    self._selected = selected
    self.setStyleSheet(self._get_style())

def is_selected(self):
    return self._selected

def _get_style(self):
    if self._selected:
        return """
            EnhancedAssetTile { background-color: #4a7a4a; border-radius: 6px; }
            EnhancedAssetTile:hover { background-color: #5a8a5a; }
        """
    return """
        EnhancedAssetTile { background-color: #2d2d2d; border-radius: 6px; }
        EnhancedAssetTile:hover { background-color: #3a3a3a; }
    """
```

Then in `AssetBrowser`, add:

```python
def __init__(self, parent=None):
    # ... existing code ...
    self._selected_assets = set()

# Add to _populate_grid, after creating each tile:
tile.set_selected(asset_path in self._selected_assets)

# Add method for clearing selection:
def clear_selection(self):
    self._selected_assets.clear()
    for tile in self._tiles.values():
        tile.set_selected(False)
    self._update_selection_info()

# Add method for updating selection info:
def _update_selection_info(self):
    count = len(self._selected_assets)
    if count > 0:
        self.status_label.setText(f"{count} asset(s) selected")
    else:
        # Restore original status
        kind = "asset"
        assets = list(self._tiles.keys())
        if assets:
            self.status_label.setText("%d %s(s)" % (len(assets), kind))

# Update _tile_clicked to handle multi-selection:
def _tile_clicked(self, asset_path):
    modifiers = QtWidgets.QApplication.keyboardModifiers()
    
    if modifiers & QtCore.Qt.ControlModifier:
        # Toggle selection
        if asset_path in self._selected_assets:
            self._selected_assets.remove(asset_path)
        else:
            self._selected_assets.add(asset_path)
        if asset_path in self._tiles:
            self._tiles[asset_path].set_selected(asset_path in self._selected_assets)
        self._update_selection_info()
    elif modifiers & QtCore.Qt.ShiftModifier:
        # Range selection - would need implementation
        pass
    else:
        # Single selection
        self.clear_selection()
        self._selected_assets.add(asset_path)
        if asset_path in self._tiles:
            self._tiles[asset_path].set_selected(True)
        self._update_selection_info()
    
    # Still show preview
    self._show_preview(asset_path)
```

---

### Step 16: Add Batch Operation Methods

Add these methods to `AssetBrowser`:

```python
def batch_import(self):
    """Import all selected assets."""
    if not self._selected_assets:
        cmds.warning("Asset Browser: No assets selected.")
        return
    
    for asset_path in self._selected_assets:
        if is_texture(asset_path):
            create_file_texture(asset_path)
        else:
            import_asset(asset_path, quiet=True)
    
    cmds.inViewMessage(
        amg="Imported %d asset(s)" % len(self._selected_assets),
        pos="topCenter",
        fade=True
    )

def batch_delete(self):
    """Delete all selected assets."""
    if not self._selected_assets:
        cmds.warning("Asset Browser: No assets selected.")
        return
    
    confirm = QtWidgets.QMessageBox.question(
        self, "Delete Assets",
        "Permanently delete %d selected asset(s) and their thumbnails?" % len(self._selected_assets),
        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
    )
    
    if confirm == QtWidgets.QMessageBox.Yes:
        for asset_path in list(self._selected_assets):
            self._delete(asset_path)
        self._selected_assets.clear()
        self._update_selection_info()
```

Then add buttons for batch operations in the UI setup:

```python
# Add to filter_bar or create a new toolbar
batch_toolbar = QtWidgets.QHBoxLayout()
batch_toolbar.addWidget(QtWidgets.QLabel("Batch:"))

self.btn_batch_import = QtWidgets.QPushButton("Import Selected")
self.btn_batch_import.clicked.connect(self.batch_import)
self.btn_batch_import.setEnabled(False)
batch_toolbar.addWidget(self.btn_batch_import)

self.btn_batch_delete = QtWidgets.QPushButton("Delete Selected")
self.btn_batch_delete.clicked.connect(self.batch_delete)
self.btn_batch_delete.setEnabled(False)
batch_toolbar.addWidget(self.btn_batch_delete)

# Add to main layout
main_layout.addLayout(batch_toolbar)

# Update selection info to enable/disable batch buttons
def _update_selection_info(self):
    count = len(self._selected_assets)
    if count > 0:
        self.status_label.setText(f"{count} asset(s) selected")
        self.btn_batch_import.setEnabled(True)
        self.btn_batch_delete.setEnabled(True)
    else:
        assets = list(self._tiles.keys())
        if assets:
            self.status_label.setText("%d asset(s)" % len(assets))
        self.btn_batch_import.setEnabled(False)
        self.btn_batch_delete.setEnabled(False)
```

---

### Step 17: Add Advanced Search

Add a new button and dialog for advanced search. In `setup_ui`, after the search box:

```python
# Advanced search button
self.btn_advanced_search = QtWidgets.QPushButton("🔍")
self.btn_advanced_search.setFixedWidth(30)
self.btn_advanced_search.setToolTip("Advanced Search")
self.btn_advanced_search.clicked.connect(self._show_advanced_search)
top_bar.addWidget(self.btn_advanced_search)
```

Then add the method:

```python
def _show_advanced_search(self):
    """Show advanced search dialog."""
    from asset_browser_v3_additions import ExportToLibraryDialog
    
    # Create a dialog for advanced search
    dialog = QtWidgets.QDialog(self)
    dialog.setWindowTitle("Advanced Search")
    dialog.setFixedWidth(350)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)
    
    # Tag filter
    layout.addWidget(QtWidgets.QLabel("Tag:"))
    tag_combo = QtWidgets.QComboBox()
    tag_combo.addItem("Any Tag")
    tag_combo.addItems(TAG_MANAGER.get_all_tags())
    layout.addWidget(tag_combo)
    
    # Date filter
    layout.addWidget(QtWidgets.QLabel("Modified:"))
    date_combo = QtWidgets.QComboBox()
    date_combo.addItems(["Any Time", "Today", "Last 7 Days", "Last 30 Days"])
    layout.addWidget(date_combo)
    
    # Size filter
    layout.addWidget(QtWidgets.QLabel("Size:"))
    size_combo = QtWidgets.QComboBox()
    size_combo.addItems(["Any Size", "< 100 KB", "< 1 MB", "> 1 MB"])
    layout.addWidget(size_combo)
    
    # Buttons
    button_layout = QtWidgets.QHBoxLayout()
    button_layout.addStretch()
    
    cancel_btn = QtWidgets.QPushButton("Cancel")
    cancel_btn.clicked.connect(dialog.reject)
    button_layout.addWidget(cancel_btn)
    
    search_btn = QtWidgets.QPushButton("Search")
    search_btn.clicked.connect(lambda: self._apply_advanced_search(
        tag_combo.currentText(),
        date_combo.currentText(),
        size_combo.currentText(),
        dialog
    ))
    button_layout.addWidget(search_btn)
    
    layout.addLayout(button_layout)
    dialog.exec_()

def _apply_advanced_search(self, tag, date_filter, size_filter, dialog):
    """Apply advanced search filters."""
    dialog.accept()
    
    # Build search query
    query = self.search_box.text().strip().lower()
    
    # Apply filters to current assets
    assets = list(self._tiles.keys())
    
    # Filter by tag
    if tag != "Any Tag":
        assets = [a for a in assets if TAG_MANAGER.has_tag(a, tag)]
    
    # Filter by date
    if date_filter != "Any Time":
        now = time.time()
        if date_filter == "Today":
            cutoff = now - 86400
        elif date_filter == "Last 7 Days":
            cutoff = now - 7 * 86400
        elif date_filter == "Last 30 Days":
            cutoff = now - 30 * 86400
        else:
            cutoff = 0
        assets = [a for a in assets if os.path.getmtime(a) >= cutoff]
    
    # Filter by size
    if size_filter != "Any Size":
        if size_filter == "< 100 KB":
            max_size = 100 * 1024
            assets = [a for a in assets if os.path.getsize(a) < max_size]
        elif size_filter == "< 1 MB":
            max_size = 1 * 1024 * 1024
            assets = [a for a in assets if os.path.getsize(a) < max_size]
        elif size_filter == "> 1 MB":
            min_size = 1 * 1024 * 1024
            assets = [a for a in assets if os.path.getsize(a) > min_size]
    
    # Update grid with filtered assets
    self._populate_grid(assets, False)
```

---

### Step 18: Final Cleanup

Make sure all the imports are correct and there are no naming conflicts. The main things to check:

1. `THUMB_SIZE` should be defined as a global variable (it already is in the original)
2. All the helper functions from the additions file are accessible
3. The new managers are initialized properly

---

## 🎯 Quick Start: Minimal Integration

If you want to start with just the most essential features, do these steps:

1. Add the imports and managers (Step 2-3)
2. Replace AssetTile with EnhancedAssetTile (Step 5)
3. Update the type filter to include Favorites (Step 7)
4. Update _type_exts method (Step 8)
5. Update _on_scan_finished to filter favorites (Step 9)
6. Update context menu (Step 11)

This gives you:
- ✅ Tagging system
- ✅ Favorites
- ✅ Tags display on tiles
- ✅ Favorite star button on tiles
- ✅ Filter by favorites

---

## 📊 Feature Checklist

- [ ] Tagging System
- [ ] Favorites
- [ ] Custom Collections
- [ ] Metadata Editor
- [ ] Asset Info Panel
- [ ] Enhanced Asset Tiles (with tags and favorites)
- [ ] Export to Library
- [ ] Adjustable Thumbnail Size
- [ ] Multi-Selection
- [ ] Batch Operations (Import, Delete)
- [ ] Advanced Search

---

## 🐛 Troubleshooting

### Issue: Module not found
**Solution**: Make sure `asset_browser_v3_additions.py` is in the same directory or in Python's path.

### Issue: Attribute errors
**Solution**: Check that all the new methods and attributes are properly added to the classes.

### Issue: UI not updating
**Solution**: Make sure signal-slot connections are correct. Use `QtCore.Signal` and `QtCore.Slot` decorators if needed.

### Issue: Data not persisting
**Solution**: Verify that the managers are using `get_instance()` to access the singleton instances.

---

## 🎉 Testing Your Integration

After integrating, test these features:

1. **Tagging**: Right-click an asset → Tags → Add a tag
2. **Favorites**: Click the star icon on an asset tile
3. **Filter by Favorites**: Select "Favorites" from the type filter
4. **Info Panel**: Click an asset to see info in the panel
5. **Export to Library**: Select objects in Maya, click "Export to Library"
6. **Batch Operations**: Ctrl+Click to select multiple, click "Import Selected"
7. **Advanced Search**: Click the 🔍 button and try different filters

---

## 📝 Notes

- All new data (tags, collections, metadata) is stored in Maya's optionVars, so it persists across sessions
- The enhanced features work alongside the existing functionality
- The original features should continue to work as before
- Performance should not be significantly impacted for normal usage

---

## 🚀 Next Steps

Once you have the basic integration working, consider adding:

1. **Version Tracking** - Track changes to assets over time
2. **Bookmarks** - Bookmark frequently used folders
3. **Custom Sorting** - Sort by name, date, size, etc.
4. **Grid/List View Toggle** - Switch between different view modes
5. **Theme Toggle** - Dark/light theme support
6. **Network Library Support** - Access libraries on network drives

These can be added incrementally as needed.
