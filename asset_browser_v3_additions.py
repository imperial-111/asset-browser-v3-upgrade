# ============================================================
#  ASSET BROWSER v3.0 - KEY ADDITIONS
#  This file contains the new feature implementations that can be added
#  to the existing asset_browser.py to upgrade it to v3.0
# 
#  TO USE:
#  1. Copy the classes and functions from this file
#  2. Integrate them into asset_browser.py
#  3. Update the UI and connections as described
# ============================================================

import os
import json
import time
from datetime import datetime

import maya.cmds as cmds

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    _QT = "PySide2"
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    _QT = "PySide6"

# ============================================================
#  FEATURE 1: Tag Manager
# ============================================================

class TagManager:
    """
    Manages user-defined tags and favorites for assets.
    
    Usage:
        tag_manager = TagManager()
        tag_manager.add_tag("/path/to/asset.ma", "character")
        tag_manager.add_tag("/path/to/asset.ma", "final")
        tag_manager.toggle_favorite("/path/to/asset.ma")
        
        tags = tag_manager.get_tags("/path/to/asset.ma")
        is_fav = tag_manager.is_favorite("/path/to/asset.ma")
        all_tags = tag_manager.get_all_tags()
        favs = tag_manager.get_favorites()
    """
    
    _INSTANCE = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance."""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE
    
    def __init__(self):
        self.tags = self._load_tags()
        self.favorites = self._load_favorites()
    
    def _load_tags(self):
        """Load tags from Maya optionVars."""
        if cmds.optionVar(exists="matrixAssetBrowserTags"):
            try:
                return json.loads(cmds.optionVar(query="matrixAssetBrowserTags"))
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def _save_tags(self):
        """Save tags to Maya optionVars."""
        try:
            cmds.optionVar(sv=("matrixAssetBrowserTags", json.dumps(self.tags)))
        except Exception:
            pass  # Silently fail if Maya is in a bad state
    
    def _load_favorites(self):
        """Load favorites from Maya optionVars."""
        if cmds.optionVar(exists="matrixAssetBrowserFavorites"):
            try:
                data = json.loads(cmds.optionVar(query="matrixAssetBrowserFavorites"))
                return set(data) if isinstance(data, list) else set()
            except (json.JSONDecodeError, TypeError):
                return set()
        return set()
    
    def _save_favorites(self):
        """Save favorites to Maya optionVars."""
        try:
            cmds.optionVar(sv=("matrixAssetBrowserFavorites", json.dumps(list(self.favorites))))
        except Exception:
            pass
    
    def add_tag(self, asset_path, tag):
        """Add a tag to an asset."""
        if not isinstance(asset_path, str) or not isinstance(tag, str):
            return
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        tag = tag.strip().lower()
        if not tag:
            return
        if asset_path not in self.tags:
            self.tags[asset_path] = set()
        self.tags[asset_path].add(tag)
        self._save_tags()
    
    def remove_tag(self, asset_path, tag):
        """Remove a tag from an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        tag = tag.strip().lower()
        if asset_path in self.tags:
            self.tags[asset_path].discard(tag)
            if not self.tags[asset_path]:
                del self.tags[asset_path]
            self._save_tags()
    
    def get_tags(self, asset_path):
        """Get all tags for an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        return sorted(self.tags.get(asset_path, set()))
    
    def has_tag(self, asset_path, tag):
        """Check if an asset has a specific tag."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        tag = tag.strip().lower()
        return tag in self.tags.get(asset_path, set())
    
    def get_all_tags(self):
        """Get all unique tags across all assets."""
        all_tags = set()
        for tags in self.tags.values():
            all_tags.update(tags)
        return sorted(all_tags)
    
    def get_assets_by_tag(self, tag):
        """Get all assets with a specific tag."""
        tag = tag.strip().lower()
        return [path for path, tags in self.tags.items() if tag in tags]
    
    def toggle_favorite(self, asset_path):
        """Toggle favorite status for an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if asset_path in self.favorites:
            self.favorites.remove(asset_path)
        else:
            self.favorites.add(asset_path)
        self._save_favorites()
    
    def is_favorite(self, asset_path):
        """Check if an asset is a favorite."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        return asset_path in self.favorites
    
    def get_favorites(self):
        """Get all favorite assets."""
        return list(self.favorites)
    
    def clear_all(self):
        """Clear all tags and favorites."""
        self.tags = {}
        self.favorites = set()
        self._save_tags()
        self._save_favorites()


# ============================================================
#  FEATURE 2: Collection Manager
# ============================================================

class CollectionManager:
    """
    Manages custom collections of assets.
    
    Usage:
        coll_manager = CollectionManager()
        coll_manager.create_collection("My Characters", ["/path/to/char1.ma", "/path/to/char2.ma"])
        coll_manager.add_to_collection("My Characters", "/path/to/char3.ma")
        
        assets = coll_manager.get_collection("My Characters")
        collections = coll_manager.get_all_collections()
    """
    
    _INSTANCE = None
    
    @classmethod
    def get_instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE
    
    def __init__(self):
        self.collections = self._load_collections()
    
    def _load_collections(self):
        """Load collections from Maya optionVars."""
        if cmds.optionVar(exists="matrixAssetBrowserCollections"):
            try:
                return json.loads(cmds.optionVar(query="matrixAssetBrowserCollections"))
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def _save_collections(self):
        """Save collections to Maya optionVars."""
        try:
            # Normalize paths before saving
            normalized = {}
            for name, assets in self.collections.items():
                normalized[name] = [os.path.normcase(os.path.abspath(a)) for a in assets]
            cmds.optionVar(sv=("matrixAssetBrowserCollections", json.dumps(normalized)))
        except Exception:
            pass
    
    def create_collection(self, name, assets=None):
        """Create a new collection."""
        if not isinstance(name, str) or not name.strip():
            return
        name = name.strip()
        if name not in self.collections:
            self.collections[name] = []
        if assets:
            existing = set(self.collections[name])
            for a in assets:
                a = os.path.normcase(os.path.abspath(a))
                if a not in existing:
                    self.collections[name].append(a)
        self._save_collections()
    
    def delete_collection(self, name):
        """Delete a collection."""
        if name in self.collections:
            del self.collections[name]
            self._save_collections()
    
    def rename_collection(self, old_name, new_name):
        """Rename a collection."""
        if old_name in self.collections and new_name.strip():
            self.collections[new_name.strip()] = self.collections.pop(old_name)
            self._save_collections()
    
    def add_to_collection(self, collection_name, asset_path):
        """Add an asset to a collection."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if collection_name in self.collections:
            if asset_path not in self.collections[collection_name]:
                self.collections[collection_name].append(asset_path)
                self._save_collections()
    
    def remove_from_collection(self, collection_name, asset_path):
        """Remove an asset from a collection."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if collection_name in self.collections:
            if asset_path in self.collections[collection_name]:
                self.collections[collection_name].remove(asset_path)
                self._save_collections()
    
    def get_collection(self, name):
        """Get all assets in a collection."""
        return list(self.collections.get(name, []))
    
    def get_all_collections(self):
        """Get all collection names."""
        return sorted(self.collections.keys())
    
    def asset_in_collection(self, collection_name, asset_path):
        """Check if an asset is in a collection."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        return collection_name in self.collections and asset_path in self.collections[collection_name]
    
    def get_collections_for_asset(self, asset_path):
        """Get all collections that contain an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        return [name for name, assets in self.collections.items() if asset_path in assets]
    
    def clear_all(self):
        """Clear all collections."""
        self.collections = {}
        self._save_collections()


# ============================================================
#  FEATURE 3: Metadata Manager
# ============================================================

class MetadataManager:
    """
    Manages custom metadata for assets.
    
    Usage:
        meta_manager = MetadataManager()
        meta_manager.set_metadata("/path/to/asset.ma", "Author", "John Doe")
        meta_manager.set_metadata("/path/to/asset.ma", "Version", "1.0")
        meta_manager.set_metadata("/path/to/asset.ma", "License", "CC-BY")
        
        author = meta_manager.get_metadata("/path/to/asset.ma", "Author")
        all_meta = meta_manager.get_all_metadata("/path/to/asset.ma")
    """
    
    _INSTANCE = None
    
    @classmethod
    def get_instance(cls):
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE
    
    def __init__(self):
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """Load metadata from Maya optionVars."""
        if cmds.optionVar(exists="matrixAssetBrowserMetadata"):
            try:
                return json.loads(cmds.optionVar(query="matrixAssetBrowserMetadata"))
            except (json.JSONDecodeError, TypeError):
                return {}
        return {}
    
    def _save_metadata(self):
        """Save metadata to Maya optionVars."""
        try:
            cmds.optionVar(sv=("matrixAssetBrowserMetadata", json.dumps(self.metadata)))
        except Exception:
            pass
    
    def set_metadata(self, asset_path, key, value):
        """Set metadata for an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if asset_path not in self.metadata:
            self.metadata[asset_path] = {}
        self.metadata[asset_path][key] = value
        self._save_metadata()
    
    def get_metadata(self, asset_path, key=None):
        """Get metadata for an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if key:
            return self.metadata.get(asset_path, {}).get(key)
        return self.metadata.get(asset_path, {})
    
    def get_all_metadata(self, asset_path):
        """Get all metadata for an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        return self.metadata.get(asset_path, {})
    
    def remove_metadata(self, asset_path, key):
        """Remove a metadata key from an asset."""
        asset_path = os.path.normcase(os.path.abspath(asset_path))
        if asset_path in self.metadata and key in self.metadata[asset_path]:
            del self.metadata[asset_path][key]
            if not self.metadata[asset_path]:
                del self.metadata[asset_path]
            self._save_metadata()
    
    def get_assets_by_metadata(self, key, value):
        """Get all assets with specific metadata."""
        return [path for path, meta in self.metadata.items() 
                if key in meta and meta[key] == value]
    
    def clear_all(self):
        """Clear all metadata."""
        self.metadata = {}
        self._save_metadata()


# ============================================================
#  FEATURE 4: Asset Info Panel Widget
# ============================================================

class AssetInfoPanel(QtWidgets.QWidget):
    """
    Detailed information panel for the selected asset.
    
    Usage:
        info_panel = AssetInfoPanel()
        info_panel.update_info("/path/to/selected/asset.ma")
    """
    
    def __init__(self, parent=None):
        super(AssetInfoPanel, self).__init__(parent)
        self.setFixedWidth(280)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI layout."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        
        # Title
        title = QtWidgets.QLabel("Asset Information")
        title.setStyleSheet("color: #eee; font-weight: bold; font-size: 14px;")
        layout.addWidget(title)
        
        # Scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background-color: #2d2d2d; border: none;")
        
        container = QtWidgets.QWidget()
        self.info_layout = QtWidgets.QVBoxLayout(container)
        self.info_layout.setContentsMargins(4, 4, 4, 4)
        self.info_layout.setSpacing(6)
        
        scroll.setWidget(container)
        layout.addWidget(scroll, stretch=1)
    
    def clear(self):
        """Clear all information."""
        while self.info_layout.count():
            item = self.info_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            layout = item.layout()
            if layout:
                self._clear_layout(layout)
    
    def _clear_layout(self, layout):
        """Recursively clear a layout."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            sub_layout = item.layout()
            if sub_layout:
                self._clear_layout(sub_layout)
    
    def update_info(self, asset_path):
        """Update the panel with asset information."""
        self.clear()
        
        if not asset_path or not os.path.exists(asset_path):
            return
        
        # Basic info section
        basic_group = QtWidgets.QGroupBox("Basic Info")
        basic_group.setStyleSheet(
            "QGroupBox { color: #ccc; border: 1px solid #444; border-radius: 4px; margin-top: 4px; padding-top: 6px; }"
        )
        basic_layout = QtWidgets.QVBoxLayout()
        
        try:
            size_bytes = os.path.getsize(asset_path)
            size_str = self._human_size(size_bytes)
            mtime = datetime.fromtimestamp(os.path.getmtime(asset_path)).strftime("%Y-%m-%d %H:%M:%S")
            ext = os.path.splitext(asset_path)[1].lower()
            
            self._add_info_row(basic_layout, "File Size:", size_str)
            self._add_info_row(basic_layout, "Modified:", mtime)
            self._add_info_row(basic_layout, "Type:", ext.upper().strip(".") if ext else "Unknown")
            self._add_info_row(basic_layout, "Path:", os.path.dirname(asset_path))
        except OSError:
            self._add_info_row(basic_layout, "Error:", "Could not read file info")
        
        basic_group.setLayout(basic_layout)
        self.info_layout.addWidget(basic_group)
        
        # Tags section
        self._add_tags_section(asset_path)
        
        # Metadata section
        self._add_metadata_section(asset_path)
        
        self.info_layout.addStretch()
    
    def _add_tags_section(self, asset_path):
        """Add tags section to the info panel."""
        tag_manager = TagManager.get_instance()
        tags = tag_manager.get_tags(asset_path)
        
        tags_group = QtWidgets.QGroupBox("Tags")
        tags_group.setStyleSheet(
            "QGroupBox { color: #ccc; border: 1px solid #444; border-radius: 4px; margin-top: 4px; padding-top: 6px; }"
        )
        tags_layout = QtWidgets.QVBoxLayout()
        
        if tags:
            tag_flow = QtWidgets.QHBoxLayout()
            tag_flow.setSpacing(4)
            tag_flow.setContentsMargins(0, 0, 0, 0)
            for tag in tags:
                tag_label = QtWidgets.QLabel(tag)
                tag_label.setStyleSheet(
                    "background-color: #4a7a4a; color: #eee; font-size: 10px; "
                    "padding: 2px 6px; border-radius: 3px;"
                )
                tag_label.setFixedHeight(20)
                tag_flow.addWidget(tag_label)
            tags_layout.addLayout(tag_flow)
        else:
            no_tags = QtWidgets.QLabel("No tags assigned")
            no_tags.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            tags_layout.addWidget(no_tags)
        
        # Favorites indicator
        if tag_manager.is_favorite(asset_path):
            fav_label = QtWidgets.QLabel("⭐ Favorite")
            fav_label.setStyleSheet("color: #ffd700; font-size: 11px;")
            tags_layout.addWidget(fav_label)
        
        tags_group.setLayout(tags_layout)
        self.info_layout.addWidget(tags_group)
    
    def _add_metadata_section(self, asset_path):
        """Add metadata section to the info panel."""
        metadata_manager = MetadataManager.get_instance()
        metadata = metadata_manager.get_all_metadata(asset_path)
        
        metadata_group = QtWidgets.QGroupBox("Custom Metadata")
        metadata_group.setStyleSheet(
            "QGroupBox { color: #ccc; border: 1px solid #444; border-radius: 4px; margin-top: 4px; padding-top: 6px; }"
        )
        metadata_layout = QtWidgets.QVBoxLayout()
        
        if metadata:
            for key, value in sorted(metadata.items()):
                self._add_info_row(metadata_layout, key + ":", str(value))
        else:
            no_meta = QtWidgets.QLabel("No custom metadata")
            no_meta.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            metadata_layout.addWidget(no_meta)
        
        metadata_group.setLayout(metadata_layout)
        self.info_layout.addWidget(metadata_group)
    
    def _add_info_row(self, layout, label, value):
        """Add a key-value row to a layout."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(8)
        
        label_widget = QtWidgets.QLabel(label)
        label_widget.setStyleSheet("color: #999; font-size: 10px;")
        label_widget.setFixedWidth(80)
        label_widget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Preferred)
        
        value_widget = QtWidgets.QLabel(value)
        value_widget.setStyleSheet("color: #eee; font-size: 10px;")
        value_widget.setWordWrap(True)
        value_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        
        row.addWidget(label_widget)
        row.addWidget(value_widget, stretch=1)
        layout.addLayout(row)
    
    def _human_size(self, num_bytes):
        """Convert bytes to human-readable format."""
        size = float(num_bytes)
        for unit in ("B", "KB", "MB", "GB"):
            if size < 1024.0:
                return "%.1f %s" % (size, unit) if unit != "B" else "%d B" % size
            size /= 1024.0
        return "%.1f TB" % size


# ============================================================
#  FEATURE 5: Enhanced Asset Tile with Favorites & Tags
# ============================================================

class EnhancedAssetTile(QtWidgets.QFrame):
    """
    Enhanced asset tile with favorite star and tags display.
    
    This replaces the original AssetTile class with additional features.
    
    Usage:
        tile = EnhancedAssetTile(asset_path, parent)
        tile.clicked.connect(self.on_tile_clicked)
        tile.doubleClicked.connect(self.on_tile_double_clicked)
        tile.rightClicked.connect(self.on_tile_right_clicked)
    """
    
    clicked = QtCore.Signal(str)
    doubleClicked = QtCore.Signal(str)
    rightClicked = QtCore.Signal(str, "QPoint")

    def __init__(self, asset_path, parent=None, thumb_size=128):
        super(EnhancedAssetTile, self).__init__(parent)
        self.asset_path = asset_path
        self.thumb_size = thumb_size
        self.setFixedSize(thumb_size + 16, thumb_size + 40)
        self.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self._drag_start = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        # Thumbnail container
        self.thumb_container = QtWidgets.QWidget()
        self.thumb_container.setFixedSize(thumb_size, thumb_size)
        self.thumb_container.setStyleSheet("background-color: #3a3a3a; border: 1px solid #222; border-radius: 4px;")
        layout.addWidget(self.thumb_container, alignment=QtCore.Qt.AlignHCenter)

        # Thumbnail label
        self.thumb_label = QtWidgets.QLabel(self.thumb_container)
        self.thumb_label.setFixedSize(thumb_size, thumb_size)
        self.thumb_label.setAlignment(QtCore.Qt.AlignCenter)

        # Favorite star button
        self.fav_button = QtWidgets.QPushButton(self.thumb_container)
        self.fav_button.setFixedSize(20, 20)
        self.fav_button.move(4, 4)
        self.fav_button.setIcon(self._get_fav_icon())
        self.fav_button.setIconSize(QtCore.QSize(14, 14))
        self.fav_button.setStyleSheet("background-color: transparent; border: none; padding: 0; margin: 0;")
        self.fav_button.setToolTip("Toggle Favorite")
        self.fav_button.clicked.connect(self._toggle_favorite)

        # Format badge
        ext = os.path.splitext(asset_path)[1].lower().strip(".").upper()
        self.badge = QtWidgets.QLabel(ext, self.thumb_container)
        self.badge.setStyleSheet(
            "background-color: rgba(0,0,0,160); color: #ddd; font-size: 9px; "
            "padding: 1px 4px; border: none; border-radius: 3px;")
        self.badge.adjustSize()
        self.badge.move(26, 4)
        self.badge.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)

        # Name label
        name = os.path.splitext(os.path.basename(asset_path))[0]
        self.name_label = QtWidgets.QLabel(name)
        self.name_label.setAlignment(QtCore.Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setToolTip(os.path.basename(asset_path))
        self.name_label.setStyleSheet("color: #ddd; font-size: 11px;")
        layout.addWidget(self.name_label)

        # Tags display
        self.tags_layout = QtWidgets.QHBoxLayout()
        self.tags_layout.setSpacing(2)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.tags_layout)

        self.setStyleSheet("""
            EnhancedAssetTile { background-color: #2d2d2d; border-radius: 6px; }
            EnhancedAssetTile:hover { background-color: #3a3a3a; }
        """)

        self.refresh_thumbnail()
        self._update_fav_icon()
        self._update_tags()

    def _get_fav_icon(self):
        """Create star icon for favorite button."""
        is_fav = TagManager.get_instance().is_favorite(self.asset_path)
        pix = QtGui.QPixmap(14, 14)
        pix.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pix)
        
        if is_fav:
            painter.setPen(QtGui.QColor(255, 215, 0))
            painter.setBrush(QtGui.QColor(255, 215, 0))
        else:
            painter.setPen(QtGui.QColor(100, 100, 100))
            painter.setBrush(QtCore.Qt.NoBrush)
        
        # Star points
        points = [
            QtCore.QPoint(7, 0), QtCore.QPoint(9, 5), QtCore.QPoint(14, 5),
            QtCore.QPoint(10, 8), QtCore.QPoint(12, 13), QtCore.QPoint(7, 10),
            QtCore.QPoint(2, 13), QtCore.QPoint(4, 8), QtCore.QPoint(0, 5), QtCore.QPoint(5, 5)
        ]
        painter.drawPolygon(QtGui.QPolygon(points))
        painter.end()
        return QtGui.QIcon(pix)

    def _update_fav_icon(self):
        """Update the favorite icon."""
        self.fav_button.setIcon(self._get_fav_icon())

    def _update_tags(self):
        """Update tags display."""
        # Clear existing tags
        while self.tags_layout.count():
            item = self.tags_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Add current tags (max 3)
        tags = TagManager.get_instance().get_tags(self.asset_path)
        for tag in tags[:3]:
            tag_label = QtWidgets.QLabel(tag)
            tag_label.setStyleSheet(
                "background-color: #4a7a4a; color: #eee; font-size: 8px; "
                "padding: 1px 4px; border-radius: 2px;")
            self.tags_layout.addWidget(tag_label)

    def _toggle_favorite(self):
        """Toggle favorite status."""
        TagManager.get_instance().toggle_favorite(self.asset_path)
        self._update_fav_icon()

    def _set_cached_pixmap(self, image_path, thumb_cache):
        """Set pixmap from cache."""
        cached = thumb_cache.get(image_path, self.thumb_size)
        if cached is not None:
            self.thumb_label.setPixmap(cached)
            return True
        return False

    def refresh_thumbnail(self, thumb_cache=None, find_thumbnail_func=None):
        """Refresh the thumbnail display."""
        if thumb_cache is None:
            # Import from main module
            from asset_browser import THUMB_CACHE, find_thumbnail, SCENE_EXTS, MODEL_EXTS, QT_PREVIEWABLE_EXTS
        else:
            SCENE_EXTS = (".ma", ".mb")
            MODEL_EXTS = (".obj", ".fbx", ".abc", ".usd", ".usda", ".usdc", ".usdz", ".stl", ".ply", ".dae", ".gltf", ".glb")
            QT_PREVIEWABLE_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
        
        ext = os.path.splitext(self.asset_path)[1].lower()
        
        if ext in QT_PREVIEWABLE_EXTS:
            if self._set_cached_pixmap(self.asset_path, thumb_cache):
                return
            pix = QtGui.QPixmap(self.asset_path)
            if not pix.isNull():
                pix = pix.scaled(self.thumb_size, self.thumb_size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                thumb_cache.put(self.asset_path, self.thumb_size, pix)
                self.thumb_label.setPixmap(pix)
                return
        
        if ext in SCENE_EXTS or ext in MODEL_EXTS:
            thumb = find_thumbnail_func(self.asset_path) if find_thumbnail_func else None
            if thumb and self._set_cached_pixmap(thumb, thumb_cache):
                return
        
        # Placeholder
        pix = QtGui.QPixmap(self.thumb_size, self.thumb_size)
        pix.fill(QtGui.QColor(58, 58, 58))
        painter = QtGui.QPainter(pix)
        painter.setPen(QtGui.QColor(150, 150, 150))
        font = painter.font()
        font.setPointSize(10)
        painter.setFont(font)
        painter.drawText(pix.rect(), QtCore.Qt.AlignCenter, ext.upper().strip("."))
        painter.end()
        self.thumb_label.setPixmap(pix)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_start = event.pos()
            self.clicked.emit(self.asset_path)
        super(EnhancedAssetTile, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self._drag_start is not None:
            if (event.pos() - self._drag_start).manhattanLength() > QtWidgets.QApplication.startDragDistance():
                self._start_drag()
        super(EnhancedAssetTile, self).mouseMoveEvent(event)

    def _start_drag(self):
        drag = QtGui.QDrag(self)
        mime = QtCore.QMimeData()
        mime.setUrls([QtCore.QUrl.fromLocalFile(self.asset_path)])
        mime.setText(self.asset_path)
        drag.setMimeData(mime)
        if not self.thumb_label.pixmap().isNull():
            drag.setPixmap(self.thumb_label.pixmap().scaled(64, 64, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))
        drag.exec_(QtCore.Qt.CopyAction)
        self._drag_start = None

    def mouseDoubleClickEvent(self, event):
        self.doubleClicked.emit(self.asset_path)
        super(EnhancedAssetTile, self).mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        self.rightClicked.emit(self.asset_path, event.globalPos())


# ============================================================
#  FEATURE 6: Export to Library Dialog
# ============================================================

class ExportToLibraryDialog(QtWidgets.QDialog):
    """
    Dialog for exporting selected Maya objects to the library.
    
    Usage:
        dialog = ExportToLibraryDialog(folder, parent)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Export completed
            pass
    """
    
    def __init__(self, folder, parent=None):
        super(ExportToLibraryDialog, self).__init__(parent)
        self.folder = folder
        self.setWindowTitle("Export to Library")
        self.setFixedWidth(400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Name field
        layout.addWidget(QtWidgets.QLabel("Asset Name:"))
        self.name_edit = QtWidgets.QLineEdit()
        self.name_edit.setPlaceholderText("Enter name for the exported asset")
        layout.addWidget(self.name_edit)
        
        # Description field
        layout.addWidget(QtWidgets.QLabel("Description (optional):"))
        self.desc_edit = QtWidgets.QLineEdit()
        self.desc_edit.setPlaceholderText("Brief description of the asset")
        layout.addWidget(self.desc_edit)
        
        # Tags field
        layout.addWidget(QtWidgets.QLabel("Tags (comma-separated):"))
        self.tags_edit = QtWidgets.QLineEdit()
        self.tags_edit.setPlaceholderText("e.g., character, prop, final")
        layout.addWidget(self.tags_edit)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        export_btn = QtWidgets.QPushButton("Export")
        export_btn.setStyleSheet("background-color: #4a7a4a;")
        export_btn.clicked.connect(self.accept)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
    
    def get_export_info(self):
        """Get the export information from the dialog."""
        return {
            'name': self.name_edit.text().strip(),
            'description': self.desc_edit.text().strip(),
            'tags': [t.strip() for t in self.tags_edit.text().split(',') if t.strip()]
        }


# ============================================================
#  UTILITY FUNCTIONS
# ============================================================

def export_selection_to_library(folder, name=None, description="", tags=None):
    """
    Export currently selected objects in Maya scene as a new library asset.
    
    Args:
        folder: Destination folder for the exported asset
        name: Name for the exported file (defaults to first selected object)
        description: Optional description
        tags: Optional list of tags
    
    Returns:
        Path to the exported file, or None if export failed
    """
    import maya.cmds as cmds
    
    sel = cmds.ls(selection=True)
    if not sel:
        cmds.warning("Asset Browser: Nothing selected to export.")
        return None
    
    if not name:
        name = sel[0].split("|")[-1].split(":")[-1]
    
    # Clean name
    name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
    if not name or name[0].isdigit():
        name = "_" + name
    
    dest = os.path.join(folder, name + ".ma")
    
    try:
        cmds.file(dest, exportSelected=True, type="mayaAscii", force=True)
        
        # Generate thumbnail
        try:
            from asset_browser import generate_thumbnail
            generate_thumbnail(dest)
        except Exception as e:
            cmds.warning("Asset Browser: Could not generate thumbnail - %s" % e)
        
        # Add metadata
        if description or tags:
            meta_manager = MetadataManager.get_instance()
            if description:
                meta_manager.set_metadata(dest, "Description", description)
            if tags:
                tag_manager = TagManager.get_instance()
                for tag in tags:
                    tag_manager.add_tag(dest, tag)
        
        return dest
    
    except Exception as e:
        cmds.warning("Asset Browser: Export failed - %s" % e)
        return None


def get_asset_file_type(asset_path):
    """Get the type of asset based on file extension."""
    ext = os.path.splitext(asset_path)[1].lower()
    if ext in (".ma", ".mb"):
        return "Scene"
    elif ext in (".obj", ".fbx", ".abc", ".usd", ".usda", ".usdc", ".usdz", ".stl", ".ply", ".dae", ".gltf", ".glb"):
        return "3D Model"
    elif ext in (".png", ".jpg", ".jpeg", ".tga", ".tif", ".tiff", ".bmp", ".exr", ".hdr", ".psd"):
        return "Texture"
    return "Unknown"


# ============================================================
#  CONTEXT MENU HELPERS
# ============================================================

def add_tag_actions(menu, asset_path, parent):
    """Add tag-related actions to a context menu."""
    tag_manager = TagManager.get_instance()
    
    # Tags submenu
    tag_menu = menu.addMenu("Tags")
    
    # All tags with checkmarks
    all_tags = tag_manager.get_all_tags()
    current_tags = tag_manager.get_tags(asset_path)
    
    for tag in all_tags:
        action = tag_menu.addAction(tag)
        action.setCheckable(True)
        action.setChecked(tag in current_tags)
        action.triggered.connect(lambda checked, t=tag, p=asset_path: toggle_tag(p, t))
    
    tag_menu.addSeparator()
    
    # Add new tag
    add_action = tag_menu.addAction("Add New Tag...")
    add_action.triggered.connect(lambda: add_new_tag_dialog(asset_path, parent))
    
    # Favorites
    menu.addSeparator()
    fav_text = "❌ Remove from Favorites" if tag_manager.is_favorite(asset_path) else "⭐ Add to Favorites"
    fav_action = menu.addAction(fav_text)
    fav_action.triggered.connect(lambda: toggle_favorite(asset_path))


def add_collection_actions(menu, asset_path, parent):
    """Add collection-related actions to a context menu."""
    coll_manager = CollectionManager.get_instance()
    
    # Collections submenu
    collection_menu = menu.addMenu("Add to Collection")
    
    collections = coll_manager.get_all_collections()
    for coll in collections:
        action = collection_menu.addAction(coll)
        action.triggered.connect(lambda checked, c=coll, p=asset_path: coll_manager.add_to_collection(c, p))
    
    collection_menu.addSeparator()
    
    # New collection
    new_action = collection_menu.addAction("New Collection...")
    new_action.triggered.connect(lambda: create_collection_dialog(asset_path, parent))


def add_metadata_actions(menu, asset_path, parent):
    """Add metadata-related actions to a context menu."""
    menu.addSeparator()
    meta_action = menu.addAction("Edit Metadata...")
    meta_action.triggered.connect(lambda: edit_metadata_dialog(asset_path, parent))


def toggle_tag(asset_path, tag):
    """Toggle a tag on an asset."""
    tag_manager = TagManager.get_instance()
    if tag_manager.has_tag(asset_path, tag):
        tag_manager.remove_tag(asset_path, tag)
    else:
        tag_manager.add_tag(asset_path, tag)


def toggle_favorite(asset_path):
    """Toggle favorite status for an asset."""
    TagManager.get_instance().toggle_favorite(asset_path)


def add_new_tag_dialog(asset_path, parent):
    """Show dialog to add a new tag."""
    tag, ok = QtWidgets.QInputDialog.getText(parent, "Add Tag", "Enter tag name:")
    if ok and tag.strip():
        TagManager.get_instance().add_tag(asset_path, tag.strip())


def create_collection_dialog(asset_path, parent):
    """Show dialog to create a new collection."""
    name, ok = QtWidgets.QInputDialog.getText(parent, "New Collection", "Collection name:")
    if ok and name.strip():
        CollectionManager.get_instance().create_collection(name.strip(), [asset_path])


def edit_metadata_dialog(asset_path, parent):
    """Show dialog to edit metadata."""
    dialog = QtWidgets.QDialog(parent)
    dialog.setWindowTitle("Edit Metadata")
    dialog.setFixedWidth(400)
    
    layout = QtWidgets.QVBoxLayout(dialog)
    
    # Current metadata
    metadata = MetadataManager.get_instance().get_all_metadata(asset_path)
    
    # Create widgets for each metadata entry
    metadata_widgets = []
    for key, value in metadata.items():
        row = QtWidgets.QHBoxLayout()
        key_edit = QtWidgets.QLineEdit(key)
        value_edit = QtWidgets.QLineEdit(str(value))
        delete_btn = QtWidgets.QPushButton("X")
        delete_btn.setFixedWidth(24)
        
        row.addWidget(key_edit)
        row.addWidget(value_edit)
        row.addWidget(delete_btn)
        layout.addLayout(row)
        metadata_widgets.append((key_edit, value_edit, delete_btn, row))
        
        delete_btn.clicked.connect(lambda checked, r=row: remove_metadata_row(layout, metadata_widgets, r))
    
    # Add new field button
    add_btn = QtWidgets.QPushButton("Add Field")
    add_btn.clicked.connect(lambda: add_metadata_row(layout, metadata_widgets))
    layout.addWidget(add_btn)
    
    # Save button
    save_btn = QtWidgets.QPushButton("Save")
    save_btn.clicked.connect(lambda: save_metadata(dialog, asset_path, metadata_widgets))
    layout.addWidget(save_btn)
    
    dialog.exec_()


def remove_metadata_row(layout, metadata_widgets, row):
    """Remove a metadata row from the dialog."""
    for i, (k, v, d, r) in enumerate(metadata_widgets[:]):
        if r == row:
            metadata_widgets.pop(i)
            row.setParent(None)
            break


def add_metadata_row(layout, metadata_widgets):
    """Add a new metadata row to the dialog."""
    row = QtWidgets.QHBoxLayout()
    key_edit = QtWidgets.QLineEdit()
    value_edit = QtWidgets.QLineEdit()
    delete_btn = QtWidgets.QPushButton("X")
    delete_btn.setFixedWidth(24)
    
    row.addWidget(key_edit)
    row.addWidget(value_edit)
    row.addWidget(delete_btn)
    layout.insertLayout(layout.count() - 2, row)  # Insert before Save button
    metadata_widgets.append((key_edit, value_edit, delete_btn, row))
    
    delete_btn.clicked.connect(lambda checked, r=row: remove_metadata_row(layout, metadata_widgets, r))


def save_metadata(dialog, asset_path, metadata_widgets):
    """Save metadata from the dialog."""
    meta_manager = MetadataManager.get_instance()
    
    for key_edit, value_edit, _, _ in metadata_widgets:
        key = key_edit.text().strip()
        value = value_edit.text()
        if key:
            meta_manager.set_metadata(asset_path, key, value)
    
    dialog.accept()


# ============================================================
#  SUMMARY
# ============================================================

print("""
================================================================================
ASSET BROWSER v3.0 ADDITIONS LOADED
================================================================================

This module provides the following new features:

1. TagManager - User-defined tags and favorites for assets
2. CollectionManager - Custom collections of assets
3. MetadataManager - Custom metadata for assets
4. AssetInfoPanel - Detailed information panel widget
5. EnhancedAssetTile - Asset tile with favorite star and tags
6. ExportToLibraryDialog - Dialog for exporting to library

UTILITY FUNCTIONS:
- export_selection_to_library() - Export selected objects to library
- get_asset_file_type() - Get asset type from file extension
- add_tag_actions() - Add tag actions to context menu
- add_collection_actions() - Add collection actions to context menu
- add_metadata_actions() - Add metadata actions to context menu
- toggle_tag() - Toggle a tag on an asset
- toggle_favorite() - Toggle favorite status
- add_new_tag_dialog() - Show add tag dialog
- create_collection_dialog() - Show create collection dialog
- edit_metadata_dialog() - Show edit metadata dialog

TO INTEGRATE:
1. Import this module in asset_browser.py
2. Replace AssetTile with EnhancedAssetTile
3. Add AssetInfoPanel to the UI
4. Update context menu creation to use the new helper functions
5. Add export to library functionality
6. Add filter for favorites in the type filter combo

================================================================================
""")
