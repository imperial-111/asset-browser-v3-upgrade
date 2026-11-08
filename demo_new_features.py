#!/usr/bin/env python
"""
Asset Browser v3.0 - New Features Demo

This script demonstrates the new features that can be added to the Asset Browser.
Run this in Maya to see the new functionality in action.

Usage:
    import demo_new_features
    demo_new_features.show_demo_ui()
"""

import os
import json
from datetime import datetime

import maya.cmds as cmds

try:
    from PySide2 import QtWidgets, QtCore, QtGui
    _QT = "PySide2"
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    _QT = "PySide6"

# ============================================================
#  IMPORT THE NEW MANAGERS
# ============================================================

# First, make sure the additions file is accessible
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
additions_path = os.path.join(script_dir, "asset_browser_v3_additions.py")

if os.path.exists(additions_path):
    sys.path.insert(0, script_dir)
    from asset_browser_v3_additions import (
        TagManager, 
        CollectionManager, 
        MetadataManager,
        AssetInfoPanel,
        EnhancedAssetTile,
        ExportToLibraryDialog,
        export_selection_to_library,
        toggle_tag,
        toggle_favorite,
        add_new_tag_dialog,
        create_collection_dialog,
        edit_metadata_dialog
    )
else:
    print("Warning: asset_browser_v3_additions.py not found. Creating local versions.")
    
    # Create local versions of the managers
    class TagManager:
        _INSTANCE = None
        @classmethod
        def get_instance(cls):
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE
        def __init__(self):
            self.tags = {}
            self.favorites = set()
        def add_tag(self, asset_path, tag):
            if asset_path not in self.tags:
                self.tags[asset_path] = set()
            self.tags[asset_path].add(tag.lower())
        def remove_tag(self, asset_path, tag):
            if asset_path in self.tags:
                self.tags[asset_path].discard(tag.lower())
        def get_tags(self, asset_path):
            return sorted(self.tags.get(asset_path, set()))
        def has_tag(self, asset_path, tag):
            return tag.lower() in self.tags.get(asset_path, set())
        def get_all_tags(self):
            all_tags = set()
            for tags in self.tags.values():
                all_tags.update(tags)
            return sorted(all_tags)
        def toggle_favorite(self, asset_path):
            if asset_path in self.favorites:
                self.favorites.remove(asset_path)
            else:
                self.favorites.add(asset_path)
        def is_favorite(self, asset_path):
            return asset_path in self.favorites
        def get_favorites(self):
            return list(self.favorites)
    
    class CollectionManager:
        _INSTANCE = None
        @classmethod
        def get_instance(cls):
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE
        def __init__(self):
            self.collections = {}
        def create_collection(self, name, assets=None):
            if name not in self.collections:
                self.collections[name] = []
            if assets:
                self.collections[name].extend(assets)
        def get_collection(self, name):
            return list(self.collections.get(name, []))
        def get_all_collections(self):
            return sorted(self.collections.keys())
        def add_to_collection(self, collection_name, asset_path):
            if collection_name in self.collections:
                if asset_path not in self.collections[collection_name]:
                    self.collections[collection_name].append(asset_path)
    
    class MetadataManager:
        _INSTANCE = None
        @classmethod
        def get_instance(cls):
            if cls._INSTANCE is None:
                cls._INSTANCE = cls()
            return cls._INSTANCE
        def __init__(self):
            self.metadata = {}
        def set_metadata(self, asset_path, key, value):
            if asset_path not in self.metadata:
                self.metadata[asset_path] = {}
            self.metadata[asset_path][key] = value
        def get_metadata(self, asset_path, key=None):
            if key:
                return self.metadata.get(asset_path, {}).get(key)
            return self.metadata.get(asset_path, {})
        def get_all_metadata(self, asset_path):
            return self.metadata.get(asset_path, {})
    
    TAG_MANAGER = TagManager.get_instance()
    COLLECTION_MANAGER = CollectionManager.get_instance()
    METADATA_MANAGER = MetadataManager.get_instance()


# ============================================================
#  DEMO UI
# ============================================================

class DemoUI(QtWidgets.QDialog):
    """Demo UI to showcase the new features."""
    
    def __init__(self, parent=None):
        super(DemoUI, self).__init__(parent)
        self.setWindowTitle("Asset Browser v3.0 - New Features Demo")
        self.setFixedSize(600, 500)
        self.setup_ui()
        self.populate_demo_data()
    
    def setup_ui(self):
        """Set up the demo UI."""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Title
        title = QtWidgets.QLabel("Asset Browser v3.0 New Features")
        title.setStyleSheet("color: #eee; font-size: 18px; font-weight: bold;")
        title.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # Create tabs for different feature groups
        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #444; }")
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Tagging & Favorites
        self.tab_tags = QtWidgets.QWidget()
        self.setup_tags_tab()
        self.tabs.addTab(self.tab_tags, "Tagging & Favorites")
        
        # Tab 2: Collections
        self.tab_collections = QtWidgets.QWidget()
        self.setup_collections_tab()
        self.tabs.addTab(self.tab_collections, "Collections")
        
        # Tab 3: Metadata
        self.tab_metadata = QtWidgets.QWidget()
        self.setup_metadata_tab()
        self.tabs.addTab(self.tab_metadata, "Metadata")
        
        # Tab 4: Info Panel
        self.tab_info = QtWidgets.QWidget()
        self.setup_info_tab()
        self.tabs.addTab(self.tab_info, "Info Panel")
        
        # Tab 5: Batch Operations
        self.tab_batch = QtWidgets.QWidget()
        self.setup_batch_tab()
        self.tabs.addTab(self.tab_batch, "Batch Operations")
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("background-color: #444; color: #eee;")
        main_layout.addWidget(close_btn)
        
        # Set stylesheet
        self.setStyleSheet(self._get_stylesheet())
    
    def _get_stylesheet(self):
        return """
            QDialog { background-color: #2b2b2b; }
            QLabel { color: #ccc; }
            QPushButton { background-color: #444; color: #eee; border: 1px solid #222; padding: 5px 10px; border-radius: 3px; }
            QPushButton:hover { background-color: #555; }
            QLineEdit { background-color: #333; color: #eee; border: 1px solid #444; padding: 4px; border-radius: 3px; }
            QComboBox { background-color: #333; color: #eee; border: 1px solid #444; padding: 4px; border-radius: 3px; }
            QListWidget { background-color: #2d2d2d; color: #ddd; border: 1px solid #444; border-radius: 3px; }
            QTabWidget::tab-bar { alignment: center; }
            QTabBar::tab { background-color: #333; color: #ccc; padding: 6px 12px; }
            QTabBar::tab:selected { background-color: #4a7a4a; }
        """
    
    def populate_demo_data(self):
        """Add some demo data to the managers."""
        # Add some demo assets
        demo_assets = [
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
            "/projects/props/shield.obj",
            "/projects/environments/castle.usd",
            "/projects/textures/diffuse.png",
        ]
        
        # Add tags
        TAG_MANAGER.add_tag(demo_assets[0], "character")
        TAG_MANAGER.add_tag(demo_assets[0], "hero")
        TAG_MANAGER.add_tag(demo_assets[0], "final")
        TAG_MANAGER.toggle_favorite(demo_assets[0])
        
        TAG_MANAGER.add_tag(demo_assets[1], "character")
        TAG_MANAGER.add_tag(demo_assets[1], "villain")
        TAG_MANAGER.add_tag(demo_assets[1], "wip")
        
        TAG_MANAGER.add_tag(demo_assets[2], "prop")
        TAG_MANAGER.add_tag(demo_assets[2], "weapon")
        TAG_MANAGER.add_tag(demo_assets[2], "final")
        TAG_MANAGER.toggle_favorite(demo_assets[2])
        
        TAG_MANAGER.add_tag(demo_assets[3], "prop")
        TAG_MANAGER.add_tag(demo_assets[3], "shield")
        
        TAG_MANAGER.add_tag(demo_assets[4], "environment")
        TAG_MANAGER.add_tag(demo_assets[4], "building")
        
        TAG_MANAGER.add_tag(demo_assets[5], "texture")
        TAG_MANAGER.add_tag(demo_assets[5], "diffuse")
        
        # Add collections
        COLLECTION_MANAGER.create_collection("Characters", [demo_assets[0], demo_assets[1]])
        COLLECTION_MANAGER.create_collection("Props", [demo_assets[2], demo_assets[3]])
        COLLECTION_MANAGER.create_collection("Favorites", [demo_assets[0], demo_assets[2]])
        
        # Add metadata
        METADATA_MANAGER.set_metadata(demo_assets[0], "Author", "John Doe")
        METADATA_MANAGER.set_metadata(demo_assets[0], "Version", "2.1")
        METADATA_MANAGER.set_metadata(demo_assets[0], "License", "CC-BY")
        METADATA_MANAGER.set_metadata(demo_assets[0], "Date Created", "2024-01-15")
        
        METADATA_MANAGER.set_metadata(demo_assets[2], "Author", "Jane Smith")
        METADATA_MANAGER.set_metadata(demo_assets[2], "Version", "1.0")
        METADATA_MANAGER.set_metadata(demo_assets[2], "Material", "Steel")
        
        # Update the tabs with demo data
        self.refresh_all_tabs()
    
    def refresh_all_tabs(self):
        """Refresh all tabs with current data."""
        self.refresh_tags_tab()
        self.refresh_collections_tab()
        self.refresh_metadata_tab()
        self.refresh_info_tab()
    
    def setup_tags_tab(self):
        """Set up the tagging and favorites tab."""
        layout = QtWidgets.QVBoxLayout(self.tab_tags)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Description
        desc = QtWidgets.QLabel("Tag assets and mark favorites for easy filtering and organization.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)
        
        # Current tags
        layout.addWidget(QtWidgets.QLabel("All Tags:"))
        self.tags_list = QtWidgets.QListWidget()
        self.tags_list.setFixedHeight(100)
        layout.addWidget(self.tags_list)
        
        # Add tag section
        layout.addWidget(QtWidgets.QLabel("Add Tag to Asset:"))
        tag_layout = QtWidgets.QHBoxLayout()
        self.tag_asset_combo = QtWidgets.QComboBox()
        self.tag_asset_combo.setEditable(True)
        self.tag_asset_combo.addItems([
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
        ])
        tag_layout.addWidget(self.tag_asset_combo)
        
        self.tag_name_edit = QtWidgets.QLineEdit()
        self.tag_name_edit.setPlaceholderText("Enter tag name")
        tag_layout.addWidget(self.tag_name_edit)
        
        self.add_tag_btn = QtWidgets.QPushButton("Add Tag")
        self.add_tag_btn.clicked.connect(self.add_tag_clicked)
        tag_layout.addWidget(self.add_tag_btn)
        layout.addLayout(tag_layout)
        
        # Favorites section
        layout.addWidget(QtWidgets.QLabel("Favorites:"))
        self.favorites_list = QtWidgets.QListWidget()
        self.favorites_list.setFixedHeight(100)
        layout.addWidget(self.favorites_list)
        
        # Toggle favorite section
        fav_layout = QtWidgets.QHBoxLayout()
        self.fav_asset_combo = QtWidgets.QComboBox()
        self.fav_asset_combo.setEditable(True)
        self.fav_asset_combo.addItems([
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
        ])
        fav_layout.addWidget(self.fav_asset_combo)
        
        self.toggle_fav_btn = QtWidgets.QPushButton("Toggle Favorite")
        self.toggle_fav_btn.clicked.connect(self.toggle_fav_clicked)
        fav_layout.addWidget(self.toggle_fav_btn)
        layout.addLayout(fav_layout)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_tags_tab)
        layout.addWidget(refresh_btn)
        layout.addStretch()
    
    def refresh_tags_tab(self):
        """Refresh the tags tab with current data."""
        self.tags_list.clear()
        for tag in TAG_MANAGER.get_all_tags():
            self.tags_list.addItem(tag)
        
        self.favorites_list.clear()
        for fav in TAG_MANAGER.get_favorites():
            self.favorites_list.addItem(fav)
    
    def add_tag_clicked(self):
        """Add a tag to an asset."""
        asset = self.tag_asset_combo.currentText()
        tag = self.tag_name_edit.text().strip()
        if asset and tag:
            TAG_MANAGER.add_tag(asset, tag)
            self.tag_name_edit.clear()
            self.refresh_tags_tab()
    
    def toggle_fav_clicked(self):
        """Toggle favorite for an asset."""
        asset = self.fav_asset_combo.currentText()
        if asset:
            TAG_MANAGER.toggle_favorite(asset)
            self.refresh_tags_tab()
    
    def setup_collections_tab(self):
        """Set up the collections tab."""
        layout = QtWidgets.QVBoxLayout(self.tab_collections)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Description
        desc = QtWidgets.QLabel("Create collections of assets for easy access and organization.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)
        
        # Collections list
        layout.addWidget(QtWidgets.QLabel("Collections:"))
        self.collections_list = QtWidgets.QListWidget()
        self.collections_list.setFixedHeight(150)
        self.collections_list.itemClicked.connect(self.collection_clicked)
        layout.addWidget(self.collections_list)
        
        # Collection contents
        layout.addWidget(QtWidgets.QLabel("Collection Contents:"))
        self.collection_contents_list = QtWidgets.QListWidget()
        self.collection_contents_list.setFixedHeight(100)
        layout.addWidget(self.collection_contents_list)
        
        # Create collection section
        layout.addWidget(QtWidgets.QLabel("Create New Collection:"))
        coll_layout = QtWidgets.QHBoxLayout()
        self.coll_name_edit = QtWidgets.QLineEdit()
        self.coll_name_edit.setPlaceholderText("Collection name")
        coll_layout.addWidget(self.coll_name_edit)
        
        self.create_coll_btn = QtWidgets.QPushButton("Create")
        self.create_coll_btn.clicked.connect(self.create_collection_clicked)
        coll_layout.addWidget(self.create_coll_btn)
        layout.addLayout(coll_layout)
        
        # Add to collection section
        layout.addWidget(QtWidgets.QLabel("Add Asset to Collection:"))
        add_coll_layout = QtWidgets.QHBoxLayout()
        self.add_coll_combo = QtWidgets.QComboBox()
        add_coll_layout.addWidget(self.add_coll_combo)
        
        self.add_asset_combo = QtWidgets.QComboBox()
        self.add_asset_combo.setEditable(True)
        self.add_asset_combo.addItems([
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
            "/projects/props/shield.obj",
        ])
        add_coll_layout.addWidget(self.add_asset_combo)
        
        self.add_to_coll_btn = QtWidgets.QPushButton("Add")
        self.add_to_coll_btn.clicked.connect(self.add_to_collection_clicked)
        add_coll_layout.addWidget(self.add_to_coll_btn)
        layout.addLayout(add_coll_layout)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_collections_tab)
        layout.addWidget(refresh_btn)
        layout.addStretch()
    
    def refresh_collections_tab(self):
        """Refresh the collections tab with current data."""
        self.collections_list.clear()
        for coll in COLLECTION_MANAGER.get_all_collections():
            self.collections_list.addItem(coll)
        
        self.add_coll_combo.clear()
        self.add_coll_combo.addItems(COLLECTION_MANAGER.get_all_collections())
    
    def collection_clicked(self, item):
        """Show contents of selected collection."""
        coll_name = item.text()
        self.collection_contents_list.clear()
        for asset in COLLECTION_MANAGER.get_collection(coll_name):
            self.collection_contents_list.addItem(asset)
    
    def create_collection_clicked(self):
        """Create a new collection."""
        name = self.coll_name_edit.text().strip()
        if name:
            COLLECTION_MANAGER.create_collection(name)
            self.coll_name_edit.clear()
            self.refresh_collections_tab()
    
    def add_to_collection_clicked(self):
        """Add an asset to a collection."""
        coll_name = self.add_coll_combo.currentText()
        asset = self.add_asset_combo.currentText()
        if coll_name and asset:
            COLLECTION_MANAGER.add_to_collection(coll_name, asset)
            self.refresh_collections_tab()
            # Refresh the contents list if this collection is selected
            for i in range(self.collections_list.count()):
                item = self.collections_list.item(i)
                if item.text() == coll_name:
                    self.collection_clicked(item)
                    break
    
    def setup_metadata_tab(self):
        """Set up the metadata tab."""
        layout = QtWidgets.QVBoxLayout(self.tab_metadata)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Description
        desc = QtWidgets.QLabel("Add custom metadata to assets for better organization and search.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)
        
        # Metadata for asset
        layout.addWidget(QtWidgets.QLabel("View Metadata:"))
        self.meta_asset_combo = QtWidgets.QComboBox()
        self.meta_asset_combo.setEditable(True)
        self.meta_asset_combo.addItems([
            "/projects/characters/hero.ma",
            "/projects/props/sword.fbx",
        ])
        self.meta_asset_combo.currentIndexChanged.connect(self.refresh_metadata_tab)
        layout.addWidget(self.meta_asset_combo)
        
        self.metadata_list = QtWidgets.QListWidget()
        self.metadata_list.setFixedHeight(150)
        layout.addWidget(self.metadata_list)
        
        # Add metadata section
        layout.addWidget(QtWidgets.QLabel("Add Metadata:"))
        meta_layout = QtWidgets.QHBoxLayout()
        self.meta_asset_edit = QtWidgets.QComboBox()
        self.meta_asset_edit.setEditable(True)
        self.meta_asset_edit.addItems([
            "/projects/characters/hero.ma",
            "/projects/props/sword.fbx",
        ])
        meta_layout.addWidget(self.meta_asset_edit)
        
        self.meta_key_edit = QtWidgets.QLineEdit()
        self.meta_key_edit.setPlaceholderText("Key (e.g., Author)")
        self.meta_key_edit.setFixedWidth(100)
        meta_layout.addWidget(self.meta_key_edit)
        
        self.meta_value_edit = QtWidgets.QLineEdit()
        self.meta_value_edit.setPlaceholderText("Value")
        meta_layout.addWidget(self.meta_value_edit)
        
        self.add_meta_btn = QtWidgets.QPushButton("Add")
        self.add_meta_btn.clicked.connect(self.add_metadata_clicked)
        meta_layout.addWidget(self.add_meta_btn)
        layout.addLayout(meta_layout)
        
        # Edit metadata button
        self.edit_meta_btn = QtWidgets.QPushButton("Edit Metadata (Dialog)")
        self.edit_meta_btn.clicked.connect(self.edit_metadata_clicked)
        layout.addWidget(self.edit_meta_btn)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_metadata_tab)
        layout.addWidget(refresh_btn)
        layout.addStretch()
    
    def refresh_metadata_tab(self):
        """Refresh the metadata tab with current data."""
        asset = self.meta_asset_combo.currentText()
        self.metadata_list.clear()
        metadata = METADATA_MANAGER.get_all_metadata(asset)
        for key, value in sorted(metadata.items()):
            self.metadata_list.addItem(f"{key}: {value}")
    
    def add_metadata_clicked(self):
        """Add metadata to an asset."""
        asset = self.meta_asset_edit.currentText()
        key = self.meta_key_edit.text().strip()
        value = self.meta_value_edit.text()
        if asset and key:
            METADATA_MANAGER.set_metadata(asset, key, value)
            self.meta_key_edit.clear()
            self.meta_value_edit.clear()
            self.refresh_metadata_tab()
    
    def edit_metadata_clicked(self):
        """Show edit metadata dialog."""
        asset = self.meta_asset_combo.currentText()
        if asset:
            edit_metadata_dialog(asset, self)
            self.refresh_metadata_tab()
    
    def setup_info_tab(self):
        """Set up the info panel tab."""
        layout = QtWidgets.QVBoxLayout(self.tab_info)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Description
        desc = QtWidgets.QLabel("The Asset Info Panel shows detailed information about selected assets.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)
        
        # Asset selection
        layout.addWidget(QtWidgets.QLabel("Select Asset:"))
        self.info_asset_combo = QtWidgets.QComboBox()
        self.info_asset_combo.setEditable(True)
        self.info_asset_combo.addItems([
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
            "/projects/props/shield.obj",
        ])
        self.info_asset_combo.currentIndexChanged.connect(self.info_asset_changed)
        layout.addWidget(self.info_asset_combo)
        
        # Info panel
        self.info_panel = AssetInfoPanel()
        layout.addWidget(self.info_panel)
        
        # Refresh button
        refresh_btn = QtWidgets.QPushButton("Refresh")
        refresh_btn.clicked.connect(self.info_asset_changed)
        layout.addWidget(refresh_btn)
        layout.addStretch()
    
    def info_asset_changed(self):
        """Update info panel with selected asset."""
        asset = self.info_asset_combo.currentText()
        self.info_panel.update_info(asset)
    
    def setup_batch_tab(self):
        """Set up the batch operations tab."""
        layout = QtWidgets.QVBoxLayout(self.tab_batch)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Description
        desc = QtWidgets.QLabel("Batch operations allow you to perform actions on multiple assets at once.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #999; font-size: 12px;")
        layout.addWidget(desc)
        
        # Multi-selection demo
        layout.addWidget(QtWidgets.QLabel("Multi-Selection Demo:"))
        self.batch_assets_list = QtWidgets.QListWidget()
        self.batch_assets_list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)
        self.batch_assets_list.setFixedHeight(150)
        self.batch_assets_list.addItems([
            "/projects/characters/hero.ma",
            "/projects/characters/villain.ma",
            "/projects/props/sword.fbx",
            "/projects/props/shield.obj",
            "/projects/environments/castle.usd",
        ])
        layout.addWidget(self.batch_assets_list)
        
        # Selection info
        self.batch_selection_info = QtWidgets.QLabel("Selected: 0 assets")
        self.batch_selection_info.setStyleSheet("color: #999;")
        layout.addWidget(self.batch_selection_info)
        
        self.batch_assets_list.itemSelectionChanged.connect(self.batch_selection_changed)
        
        # Batch actions
        layout.addWidget(QtWidgets.QLabel("Batch Actions:"))
        
        self.batch_import_btn = QtWidgets.QPushButton("Batch Import (Simulated)")
        self.batch_import_btn.clicked.connect(self.batch_import_clicked)
        layout.addWidget(self.batch_import_btn)
        
        self.batch_tag_btn = QtWidgets.QPushButton("Batch Add Tag (Simulated)")
        self.batch_tag_btn.clicked.connect(self.batch_tag_clicked)
        layout.addWidget(self.batch_tag_btn)
        
        self.batch_delete_btn = QtWidgets.QPushButton("Batch Delete (Simulated)")
        self.batch_delete_btn.clicked.connect(self.batch_delete_clicked)
        layout.addWidget(self.batch_delete_btn)
        
        layout.addStretch()
    
    def batch_selection_changed(self):
        """Update selection info."""
        count = self.batch_assets_list.selectedItems()
        self.batch_selection_info.setText(f"Selected: {len(count)} asset(s)")
    
    def batch_import_clicked(self):
        """Simulate batch import."""
        items = self.batch_assets_list.selectedItems()
        if items:
            QtWidgets.QMessageBox.information(
                self, "Batch Import",
                f"Would import {len(items)} assets:\n\n" + "\n".join([item.text() for item in items])
            )
    
    def batch_tag_clicked(self):
        """Simulate batch tagging."""
        items = self.batch_assets_list.selectedItems()
        if items:
            tag, ok = QtWidgets.QInputDialog.getText(self, "Add Tag", "Enter tag name:")
            if ok and tag.strip():
                for item in items:
                    TAG_MANAGER.add_tag(item.text(), tag.strip())
                QtWidgets.QMessageBox.information(
                    self, "Batch Tag",
                    f"Added tag '{tag.strip()}' to {len(items)} assets"
                )
    
    def batch_delete_clicked(self):
        """Simulate batch delete."""
        items = self.batch_assets_list.selectedItems()
        if items:
            confirm = QtWidgets.QMessageBox.question(
                self, "Batch Delete",
                f"Delete {len(items)} selected assets?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if confirm == QtWidgets.QMessageBox.Yes:
                QtWidgets.QMessageBox.information(
                    self, "Batch Delete",
                    f"Would delete {len(items)} assets"
                )


# ============================================================
#  DEMO FUNCTIONS
# ============================================================

def show_demo_ui():
    """Show the demo UI."""
    # Close any existing demo
    for w in QtWidgets.QApplication.topLevelWidgets():
        if isinstance(w, DemoUI):
            w.close()
            w.deleteLater()
    
    try:
        from maya.OpenMayaUI import MQtUtil
        from shiboken2 import wrapInstance
    except ImportError:
        from maya.OpenMayaUI import MQtUtil
        from shiboken6 import wrapInstance
    
    ptr = MQtUtil.mainWindow()
    maya_win = wrapInstance(int(ptr), QtWidgets.QWidget) if ptr else None
    
    demo = DemoUI(maya_win)
    demo.show()
    demo.raise_()
    return demo


def demo_tagging():
    """Demonstrate the tagging system."""
    print("\n" + "="*60)
    print("TAGGING SYSTEM DEMO")
    print("="*60)
    
    tag_manager = TagManager.get_instance()
    
    # Add some tags
    tag_manager.add_tag("/projects/hero.ma", "character")
    tag_manager.add_tag("/projects/hero.ma", "main")
    tag_manager.add_tag("/projects/villain.ma", "character")
    tag_manager.add_tag("/projects/sword.fbx", "prop")
    tag_manager.add_tag("/projects/sword.fbx", "weapon")
    
    print("\nAdded tags to assets")
    
    # Get all tags
    all_tags = tag_manager.get_all_tags()
    print(f"\nAll tags: {all_tags}")
    
    # Get tags for specific asset
    hero_tags = tag_manager.get_tags("/projects/hero.ma")
    print(f"\nTags for /projects/hero.ma: {hero_tags}")
    
    # Check if asset has tag
    has_character = tag_manager.has_tag("/projects/hero.ma", "character")
    print(f"\nDoes /projects/hero.ma have 'character' tag? {has_character}")
    
    # Favorites
    tag_manager.toggle_favorite("/projects/hero.ma")
    tag_manager.toggle_favorite("/projects/sword.fbx")
    
    favorites = tag_manager.get_favorites()
    print(f"\nFavorites: {favorites}")
    
    is_fav = tag_manager.is_favorite("/projects/hero.ma")
    print(f"\nIs /projects/hero.ma a favorite? {is_fav}")


def demo_collections():
    """Demonstrate the collections system."""
    print("\n" + "="*60)
    print("COLLECTIONS SYSTEM DEMO")
    print("="*60)
    
    coll_manager = CollectionManager.get_instance()
    
    # Create collections
    coll_manager.create_collection("Characters", ["/projects/hero.ma", "/projects/villain.ma"])
    coll_manager.create_collection("Props", ["/projects/sword.fbx", "/projects/shield.obj"])
    
    print("\nCreated collections")
    
    # Get all collections
    collections = coll_manager.get_all_collections()
    print(f"\nAll collections: {collections}")
    
    # Get collection contents
    characters = coll_manager.get_collection("Characters")
    print(f"\nCharacters collection: {characters}")
    
    # Add to collection
    coll_manager.add_to_collection("Characters", "/projects/npc.ma")
    characters = coll_manager.get_collection("Characters")
    print(f"\nCharacters collection after adding: {characters}")
    
    # Check if asset in collection
    in_coll = coll_manager.asset_in_collection("Characters", "/projects/hero.ma")
    print(f"\nIs /projects/hero.ma in Characters collection? {in_coll}")


def demo_metadata():
    """Demonstrate the metadata system."""
    print("\n" + "="*60)
    print("METADATA SYSTEM DEMO")
    print("="*60)
    
    meta_manager = MetadataManager.get_instance()
    
    # Add metadata
    meta_manager.set_metadata("/projects/hero.ma", "Author", "John Doe")
    meta_manager.set_metadata("/projects/hero.ma", "Version", "2.1")
    meta_manager.set_metadata("/projects/hero.ma", "License", "CC-BY")
    meta_manager.set_metadata("/projects/hero.ma", "Date", "2024-01-15")
    
    print("\nAdded metadata to /projects/hero.ma")
    
    # Get specific metadata
    author = meta_manager.get_metadata("/projects/hero.ma", "Author")
    print(f"\nAuthor: {author}")
    
    # Get all metadata
    all_meta = meta_manager.get_all_metadata("/projects/hero.ma")
    print(f"\nAll metadata for /projects/hero.ma:")
    for key, value in all_meta.items():
        print(f"  {key}: {value}")
    
    # Remove metadata
    meta_manager.remove_metadata("/projects/hero.ma", "License")
    all_meta = meta_manager.get_all_metadata("/projects/hero.ma")
    print(f"\nMetadata after removing License:")
    for key, value in all_meta.items():
        print(f"  {key}: {value}")


def demo_info_panel():
    """Demonstrate the info panel."""
    print("\n" + "="*60)
    print("INFO PANEL DEMO")
    print("="*60)
    print("\nRun show_demo_ui() to see the info panel in action!")


def run_all_demos():
    """Run all demos."""
    demo_tagging()
    demo_collections()
    demo_metadata()
    demo_info_panel()
    print("\n" + "="*60)
    print("DEMOS COMPLETE")
    print("="*60)


# ============================================================
#  MAIN
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ASSET BROWSER v3.0 - NEW FEATURES DEMO")
    print("="*60)
    print("\nAvailable functions:")
    print("  show_demo_ui() - Show interactive demo UI")
    print("  demo_tagging() - Run tagging demo")
    print("  demo_collections() - Run collections demo")
    print("  demo_metadata() - Run metadata demo")
    print("  run_all_demos() - Run all demos")
    print("\n")
