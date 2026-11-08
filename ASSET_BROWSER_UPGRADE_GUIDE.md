# Asset Browser v3.0 - Upgrade Guide

## Overview
This guide describes **15+ new features** to add to the existing Asset Browser v2.0 to create a significantly enhanced v3.0. Each feature is designed to be non-existent in the current version and provides real value to Maya artists and TDs.

---

## 🎯 NEW FEATURES TO ADD

### 1. **Tagging System** ⭐
**What it does:** Users can add custom tags to assets (e.g., "character", "prop", "final", "wip")
**Implementation:**
- Add `TagManager` class to store tags in Maya optionVars
- Each asset can have multiple tags
- Tags persist across sessions
- Visual tag display on asset tiles

**Code to add:**
```python
class TagManager:
    def __init__(self):
        self.tags = self._load_tags()  # {asset_path: set(tags)}
        self.favorites = self._load_favorites()  # set(asset_paths)
    
    def add_tag(self, asset_path, tag):
        if asset_path not in self.tags:
            self.tags[asset_path] = set()
        self.tags[asset_path].add(tag.lower())
        self._save_tags()
    
    def get_tags(self, asset_path):
        return list(self.tags.get(asset_path, set()))
    
    def toggle_favorite(self, asset_path):
        # Add/remove from favorites
        pass
```

**UI Changes:**
- Add star icon button on each asset tile
- Add "Tags" section in context menu
- Add "Favorites" filter option

---

### 2. **Custom Collections** 📁
**What it does:** Users can create named collections of assets (e.g., "Character Rig Assets", "Environment Props")
**Implementation:**
- Add `CollectionManager` class
- Collections stored in optionVars as `{name: [asset_path1, asset_path2, ...]}`
- Collections persist across sessions

**Code to add:**
```python
class CollectionManager:
    def __init__(self):
        self.collections = self._load_collections()
    
    def create_collection(self, name, assets=None):
        if name not in self.collections:
            self.collections[name] = []
        if assets:
            self.collections[name].extend(assets)
        self._save_collections()
    
    def add_to_collection(self, collection_name, asset_path):
        if collection_name in self.collections:
            if asset_path not in self.collections[collection_name]:
                self.collections[collection_name].append(asset_path)
                self._save_collections()
```

**UI Changes:**
- Add "Collections" panel/tab
- Add "Add to Collection" in context menu
- Add "New Collection" button

---

### 3. **Custom Metadata Editor** 📝
**What it does:** Users can add custom metadata fields to assets (e.g., "Author", "Version", "License", "Project")
**Implementation:**
- Add `MetadataManager` class
- Metadata stored as `{asset_path: {key: value, ...}}`
- Support for string, number, date values

**Code to add:**
```python
class MetadataManager:
    def __init__(self):
        self.metadata = self._load_metadata()
    
    def set_metadata(self, asset_path, key, value):
        if asset_path not in self.metadata:
            self.metadata[asset_path] = {}
        self.metadata[asset_path][key] = value
        self._save_metadata()
    
    def get_all_metadata(self, asset_path):
        return self.metadata.get(asset_path, {})
```

**UI Changes:**
- Add "Edit Metadata" option in context menu
- Add metadata display in info panel
- Modal dialog for editing metadata

---

### 4. **Asset Info Panel** ℹ️
**What it does:** Shows detailed information about the selected asset in a sidebar
**Implementation:**
- Create `AssetInfoPanel` widget
- Display: file size, modification date, dimensions, tags, custom metadata
- Auto-updates when asset selection changes

**UI Changes:**
- Add info panel to the right side of the browser
- Panel shows when asset is selected
- Organized sections for different info types

---

### 5. **Batch Operations** 🔄
**What it does:** Perform operations on multiple selected assets
**Implementation:**
- Add multi-selection support (Ctrl+Click, Shift+Click)
- Add batch import, batch rename, batch delete
- Add batch tagging

**Code to add:**
```python
# In AssetBrowser class
self._selected_assets = set()

def _batch_import(self):
    for asset_path in self._selected_assets:
        import_asset(asset_path)

def _batch_delete(self):
    for asset_path in self._selected_assets:
        self._delete(asset_path)
    self._selected_assets.clear()
```

**UI Changes:**
- Add selection count display
- Add batch operation buttons/toolbar
- Visual indication of selected assets

---

### 6. **Advanced Search** 🔍
**What it does:** Search with multiple criteria beyond just name
**Implementation:**
- Search by: name, tags, date modified, file size, file type
- Date ranges: today, last 7 days, last 30 days, etc.
- Size ranges: <100KB, <1MB, <10MB, >10MB

**Code to add:**
```python
def _filter_assets(self, assets, filters):
    filtered = assets
    
    # Filter by tag
    if filters.get('tag') and filters['tag'] != 'Any Tag':
        tag_manager = TagManager.get_instance()
        filtered = [a for a in filtered if tag_manager.has_tag(a, filters['tag'])]
    
    # Filter by date
    if filters.get('date') != 'Any Time':
        now = time.time()
        if filters['date'] == 'Today':
            cutoff = now - 86400
        elif filters['date'] == 'Last 7 Days':
            cutoff = now - 7 * 86400
        # ... etc
        filtered = [a for a in filtered if os.path.getmtime(a) >= cutoff]
    
    return filtered
```

**UI Changes:**
- Add "Advanced Search" button
- Modal dialog with search filters
- Apply filters to current view

---

### 7. **Grid/List View Toggle** 📊
**What it does:** Switch between grid view and list view
**Implementation:**
- Add view mode option (Grid/List)
- Grid view: current thumbnail grid
- List view: vertical list with small thumbnails and details

**Code to add:**
```python
# In AssetBrowser class
self.view_mode = "Grid"  # or "List"

def _change_view_mode(self, mode):
    self.view_mode = mode
    if mode == "Grid":
        # Show flow layout
        pass
    else:
        # Show list layout
        pass
    self.refresh_grid()
```

**UI Changes:**
- Add view mode toggle button
- Different layouts for each mode

---

### 8. **Adjustable Thumbnail Size** 📐
**What it does:** Users can adjust thumbnail size with a slider
**Implementation:**
- Add slider control for thumbnail size
- Sizes: Small (64px), Medium (128px), Large (192px), X-Large (256px)
- Auto-refresh grid when size changes

**Code to add:**
```python
# In AssetBrowser class
self.thumb_size = 128

def _change_thumb_size(self, size):
    self.thumb_size = size
    # Recreate tiles with new size
    self.refresh_grid()
```

**UI Changes:**
- Add slider to toolbar
- Label showing current size

---

### 9. **Export Selected to Library** 💾
**What it does:** Export currently selected objects in Maya scene as a new library asset
**Implementation:**
- Add "Export to Library" button
- Export selected objects with thumbnail
- Save to current library folder

**Code to add:**
```python
def export_selection_to_library(self, folder, name=None):
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning("Nothing selected to export.")
        return
    if not name:
        name = sel[0].split("|")[-1].split(":")[-1]
    dest = os.path.join(folder, name + ".ma")
    cmds.file(dest, exportSelected=True, type="mayaAscii", force=True)
    generate_thumbnail(dest)
    self.refresh_grid()
```

**UI Changes:**
- Add "Export to Library" button
- Dialog to choose name and folder

---

### 10. **Version Tracking** 🔢
**What it does:** Track versions of assets with timestamps
**Implementation:**
- Add version history for each asset
- Store in metadata: `{asset_path: {versions: [{date: ..., note: ...}, ...]}}`
- Auto-increment version on save

**Code to add:**
```python
class VersionManager:
    def __init__(self):
        self.versions = self._load_versions()
    
    def add_version(self, asset_path, note=""):
        if asset_path not in self.versions:
            self.versions[asset_path] = []
        self.versions[asset_path].append({
            'date': datetime.now().isoformat(),
            'note': note
        })
        self._save_versions()
    
    def get_versions(self, asset_path):
        return self.versions.get(asset_path, [])
```

**UI Changes:**
- Add "Version History" in context menu
- Show version count in info panel

---

### 11. **Bookmarks for Folders** 🔖
**What it does:** Bookmark frequently used folders for quick access
**Implementation:**
- Add bookmark system
- Bookmarks stored in optionVars
- Quick access from toolbar

**Code to add:**
```python
class BookmarkManager:
    def __init__(self):
        self.bookmarks = self._load_bookmarks()
    
    def add_bookmark(self, folder, name=None):
        if name is None:
            name = os.path.basename(folder)
        self.bookmarks[name] = folder
        self._save_bookmarks()
    
    def get_bookmarks(self):
        return self.bookmarks
```

**UI Changes:**
- Add bookmark button
- Bookmarks menu/dropdown
- Remove bookmark option

---

### 12. **Material/Shader Preview** 🎨
**What it does:** Preview materials/shaders directly in the browser
**Implementation:**
- Detect .mb/.ma files containing shading networks
- Render material ball preview
- Show shader parameters

**UI Changes:**
- Add material preview mode
- Show material ball instead of mesh for material files

---

### 13. **Custom Sorting** 🔽
**What it does:** Sort assets by different criteria
**Implementation:**
- Sort by: Name, Date Modified, File Size, Type, Custom Order
- Ascending/Descending toggle
- Persist sort preference

**Code to add:**
```python
# In AssetBrowser class
self.sort_mode = "Name"
self.sort_ascending = True

def _sort_assets(self, assets):
    if self.sort_mode == "Name":
        assets.sort(key=lambda x: os.path.basename(x), reverse=not self.sort_ascending)
    elif self.sort_mode == "Date Modified":
        assets.sort(key=lambda x: os.path.getmtime(x), reverse=not self.sort_ascending)
    elif self.sort_mode == "File Size":
        assets.sort(key=lambda x: os.path.getsize(x), reverse=not self.sort_ascending)
    return assets
```

**UI Changes:**
- Add sort dropdown
- Add sort direction button

---

### 14. **Quick Actions Toolbar** ⚡
**What it does:** Customizable toolbar with frequently used actions
**Implementation:**
- Add toolbar with common actions
- Actions: Import, Reference, Export, Refresh, etc.
- Customizable action set

**UI Changes:**
- Add toolbar at top
- Configurable buttons

---

### 15. **Drag from Maya to Library** 📥
**What it does:** Drag selected objects from Maya viewport directly into the library
**Implementation:**
- Enable drop target on library folders
- Export dropped objects as new assets
- Auto-generate thumbnails

**Code to add:**
```python
def _container_drop(self, event):
    if not self.current_folder:
        event.ignore()
        return
    
    # Check if drag contains Maya objects
    mime = event.mimeData()
    if mime.hasFormat("application/maya.objects"):
        # Get selected objects
        sel = cmds.ls(selection=True)
        for obj in sel:
            # Export each object
            name = obj.split("|")[-1].split(":")[-1]
            dest = os.path.join(self.current_folder, name + ".ma")
            cmds.select(obj, replace=True)
            cmds.file(dest, exportSelected=True, type="mayaAscii", force=True)
            generate_thumbnail(dest)
        self.refresh_grid()
```

**UI Changes:**
- Visual feedback when dragging over library
- Highlight drop target folders

---

### 16. **Multi-Selection** ✅
**What it does:** Select multiple assets for batch operations
**Implementation:**
- Add Ctrl+Click and Shift+Click support
- Visual selection indication
- Selection count display

**Code to add:**
```python
# In AssetTile class
def mousePressEvent(self, event):
    if event.button() == QtCore.Qt.LeftButton:
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers & QtCore.Qt.ControlModifier:
            # Toggle selection
            self.set_selected(not self.is_selected())
        elif modifiers & QtCore.Qt.ShiftModifier:
            # Range selection
            pass
        else:
            # Single selection
            self.parent().clear_selection()
            self.set_selected(True)
        self.clicked.emit(self.asset_path)
```

**UI Changes:**
- Selected tiles have different background
- Selection count in status bar

---

### 17. **Thumbnail Size Slider** 📏
**What it does:** Slider to adjust thumbnail size in real-time
**Implementation:**
- Add QSlider to toolbar
- Range: 64px to 256px
- Update grid on change

**Code to add:**
```python
# In AssetBrowser.setup_ui()
self.thumb_size_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
self.thumb_size_slider.setRange(64, 256)
self.thumb_size_slider.setValue(128)
self.thumb_size_slider.setFixedWidth(120)
self.thumb_size_slider.valueChanged.connect(self._change_thumb_size)
```

---

### 18. **Dark/Light Theme Toggle** 🌓
**What it does:** Switch between dark and light UI themes
**Implementation:**
- Add theme system
- Dark theme (default)
- Light theme option
- Persist theme preference

**Code to add:**
```python
# In AssetBrowser class
self.themes = {
    'Dark': self._get_dark_theme(),
    'Light': self._get_light_theme()
}
self.current_theme = 'Dark'

def _toggle_theme(self):
    self.current_theme = 'Light' if self.current_theme == 'Dark' else 'Dark'
    self.setStyleSheet(self.themes[self.current_theme])
    cmds.optionVar(sv=('matrixAssetBrowserTheme', self.current_theme))
```

---

### 19. **Custom Actions System** ⚙️
**What it does:** Define custom actions for specific asset types
**Implementation:**
- Add custom action configuration
- Actions: Python scripts, MEL commands, external tools
- Type-specific actions (e.g., only for FBX files)

**Code to add:**
```python
class CustomActionManager:
    def __init__(self):
        self.actions = self._load_actions()
    
    def add_action(self, name, command, file_types=None, icon=None):
        self.actions.append({
            'name': name,
            'command': command,
            'file_types': file_types or [],
            'icon': icon
        })
        self._save_actions()
```

**UI Changes:**
- Add "Custom Actions" in context menu
- Configure actions dialog

---

### 20. **Network/Cloud Library Support** ☁️
**What it does:** Access libraries on network drives or cloud storage
**Implementation:**
- Add network path support
- Caching for remote thumbnails
- Async loading for remote assets

**Code to add:**
```python
# In AssetBrowser class
def _is_network_path(self, path):
    # Check if path is on network drive
    if path.startswith('//') or path.startswith('\\\\'):
        return True
    if os.name == 'nt' and path[1:3] == ':\\':
        # Check if drive is network
        import ctypes
        drive = path[0]
        if ctypes.windll.mpr.WNetGetConnectionW(ctypes.c_wchar_p(drive + ':'), None, 0) == 0:
            return True
    return False
```

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Core Features (High Priority)
1. ✅ Tagging System
2. ✅ Favorites
3. ✅ Custom Collections
4. ✅ Metadata Editor
5. ✅ Asset Info Panel

### Phase 2: Workflow Enhancements (Medium Priority)
6. ✅ Batch Operations
7. ✅ Advanced Search
8. ✅ Grid/List View Toggle
9. ✅ Adjustable Thumbnail Size
10. ✅ Export Selected to Library

### Phase 3: Advanced Features (Lower Priority)
11. ⏳ Version Tracking
12. ⏳ Bookmarks
13. ⏳ Material Preview
14. ⏳ Custom Sorting
15. ⏳ Quick Actions Toolbar
16. ⏳ Drag from Maya to Library
17. ⏳ Multi-Selection
18. ⏳ Thumbnail Size Slider
19. ⏳ Dark/Light Theme Toggle
20. ⏳ Custom Actions System
21. ⏳ Network Library Support

---

## 🔧 INTEGRATION NOTES

### Files to Modify
- `asset_browser.py` - Main file with all changes

### New Classes to Add
1. `TagManager` - Manages tags and favorites
2. `CollectionManager` - Manages custom collections
3. `MetadataManager` - Manages custom metadata
4. `AssetInfoPanel` - Detailed info display
5. `AssetTile` - Enhanced tile with favorites and tags
6. `VersionManager` - (Optional) Version tracking
7. `BookmarkManager` - (Optional) Folder bookmarks

### UI Changes
- Add toolbar with new controls
- Add info panel to layout
- Modify asset tile to include favorite star and tags
- Add context menu items for new features
- Add filter options

### Storage
All new data stored in Maya optionVars:
- `matrixAssetBrowserTags` - Tags data
- `matrixAssetBrowserFavorites` - Favorites data
- `matrixAssetBrowserCollections` - Collections data
- `matrixAssetBrowserMetadata` - Metadata
- `matrixAssetBrowserViewMode` - View mode preference
- `matrixAssetBrowserThumbSize` - Thumbnail size
- `matrixAssetBrowserSortMode` - Sort mode
- `matrixAssetBrowserTheme` - Theme preference

---

## 🎯 RECOMMENDED FIRST IMPLEMENTATIONS

Start with these 5 features for maximum impact:

1. **Tagging & Favorites** - Most requested feature, easy to implement
2. **Asset Info Panel** - Improves usability significantly
3. **Batch Operations** - Saves time for power users
4. **Adjustable Thumbnail Size** - Simple but very useful
5. **Export Selected to Library** - Closes the workflow loop

These 5 features can be added in a weekend and provide immediate value.

---

## 📊 FEATURE COMPARISON

| Feature | Complexity | User Value | Implementation Time |
|---------|------------|------------|---------------------|
| Tagging | Low | High | 2-4 hours |
| Favorites | Low | High | 1-2 hours |
| Collections | Medium | High | 3-5 hours |
| Metadata | Medium | Medium | 3-5 hours |
| Info Panel | Medium | High | 4-6 hours |
| Batch Ops | Medium | High | 4-6 hours |
| Advanced Search | Medium | High | 4-6 hours |
| Grid/List View | Medium | Medium | 3-5 hours |
| Thumbnail Size | Low | Medium | 2-3 hours |
| Export to Library | Low | High | 2-3 hours |
| Version Tracking | Medium | Medium | 4-6 hours |
| Bookmarks | Low | Medium | 2-3 hours |
| Material Preview | High | Medium | 6-8 hours |
| Custom Sorting | Low | Medium | 2-3 hours |
| Quick Actions | Medium | Medium | 3-5 hours |
| Drag to Library | Medium | High | 4-6 hours |
| Multi-Selection | Medium | High | 4-6 hours |
| Theme Toggle | Low | Low | 2-3 hours |
| Custom Actions | High | Medium | 6-8 hours |
| Network Support | High | Medium | 6-8 hours |

---

## 💡 TIPS FOR IMPLEMENTATION

1. **Start Small** - Implement one feature at a time and test thoroughly
2. **Use OptionVars** - Store all user data in Maya's optionVars for persistence
3. **Background Threads** - Keep UI responsive with QThread for slow operations
4. **Error Handling** - Add try/except blocks for all file operations
5. **UI Feedback** - Show loading indicators for background operations
6. **Documentation** - Add tooltips for all new UI elements
7. **Backwards Compatibility** - Ensure existing features still work
8. **Performance** - Cache thumbnails and metadata to avoid repeated disk I/O

---

## 🎉 CONCLUSION

Adding these features will transform the Asset Browser from a basic file viewer into a **professional asset management system** comparable to commercial solutions. The tagging, collections, and metadata features alone will provide enormous value for organizing and finding assets quickly.

Start with the high-impact, low-complexity features and gradually add more advanced capabilities as needed.
