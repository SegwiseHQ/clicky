"""Splash screen component for ClickHouse Client."""

import os
import threading
import time
from typing import Callable, Optional

from dearpygui.dearpygui import *

from config import COLOR_BACKGROUND, COLOR_PRIMARY, COLOR_SURFACE
from icon_manager import icon_manager


class SplashScreen:
    """Manages the application splash screen during startup."""

    def __init__(self, theme_manager=None):
        """Initialize splash screen component."""
        self.theme_manager = theme_manager
        self.splash_window = None
        self.is_visible = False
        self.progress_bar = None
        self.status_text = None
        self.loading_dots = ""
        self.loading_thread = None
        self.should_animate = True

    def create_splash_window(self):
        """Create and configure the splash screen window."""
        # Load splash image
        splash_image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "assets", "splash.png"
        )
        splash_image_loaded = False

        try:
            if os.path.exists(splash_image_path):
                # Load the image into texture registry
                width, height, channels, data = load_image(splash_image_path)
                with texture_registry(show=False):
                    add_static_texture(
                        width=width,
                        height=height,
                        default_value=data,
                        tag="splash_image_texture",
                    )
                splash_image_loaded = True
        except Exception as e:
            print(f"Warning: Could not load splash image: {e}")

        # Splash screen dimensions - make it larger to accommodate image
        splash_width = 500
        splash_height = 400

        # Create splash window
        with window(
            label="Loading...",
            tag="splash_window",
            width=splash_width,
            height=splash_height,
            no_title_bar=True,
            no_resize=True,
            no_move=True,
            no_collapse=True,
            modal=True,
            no_close=True,
        ) as self.splash_window:

            # Center the content
            with group(horizontal=False):
                # Add some top spacing
                add_spacer(height=20)

                # Splash image (if loaded)
                if splash_image_loaded:
                    with group(horizontal=True):
                        add_spacer(width=(splash_width - 200) // 2)  # Center the image
                        add_image("splash_image_texture", width=200, height=150)
                    add_spacer(height=10)
                else:
                    add_spacer(height=20)

                # App title
                with group(horizontal=True):
                    add_spacer(width=120)
                    add_text(
                        f"{icon_manager.get('database')} ClickHouse Client",
                        tag="splash_title",
                    )

                add_spacer(height=10)

                # Version info
                with group(horizontal=True):
                    add_spacer(width=160)
                    add_text("Professional Database Client", tag="splash_subtitle")

                add_spacer(height=30)

                # Progress bar
                with group(horizontal=True):
                    add_spacer(width=75)
                    add_progress_bar(
                        tag="splash_progress", width=350, height=20, default_value=0.0
                    )

                add_spacer(height=15)

                # Status text
                with group(horizontal=True):
                    add_spacer(width=120)
                    add_text("Initializing application...", tag="splash_status")

                add_spacer(height=20)

                # Loading animation
                with group(horizontal=True):
                    add_spacer(width=220)
                    add_text("", tag="splash_loading_dots")

        # Apply theme if available
        if self.theme_manager:
            self._apply_splash_theme()

        # Center the splash window on screen
        self._center_splash_window(splash_width, splash_height)

        self.is_visible = True

    def _apply_splash_theme(self):
        """Apply theme styling to splash screen elements."""
        try:
            # Title styling
            with theme(tag="splash_title_theme"):
                with theme_component(mvText):
                    add_theme_color(mvThemeCol_Text, COLOR_PRIMARY)
                    add_theme_style(mvStyleVar_ItemSpacing, 10, 10)

            # Subtitle styling
            with theme(tag="splash_subtitle_theme"):
                with theme_component(mvText):
                    add_theme_color(mvThemeCol_Text, (180, 180, 180))

            # Progress bar styling
            with theme(tag="splash_progress_theme"):
                with theme_component(mvProgressBar):
                    add_theme_color(mvThemeCol_PlotHistogram, COLOR_PRIMARY)
                    add_theme_color(mvThemeCol_FrameBg, COLOR_SURFACE)

            # Window styling
            with theme(tag="splash_window_theme"):
                with theme_component(mvWindowAppItem):
                    add_theme_color(mvThemeCol_WindowBg, COLOR_BACKGROUND)
                    add_theme_color(mvThemeCol_Border, COLOR_PRIMARY)
                    add_theme_style(mvStyleVar_WindowBorderSize, 2)
                    add_theme_style(mvStyleVar_WindowRounding, 10)

            # Apply themes
            bind_item_theme("splash_title", "splash_title_theme")
            bind_item_theme("splash_subtitle", "splash_subtitle_theme")
            bind_item_theme("splash_progress", "splash_progress_theme")
            bind_item_theme("splash_window", "splash_window_theme")

        except Exception as e:
            print(f"Warning: Could not apply splash screen theme: {e}")

    def _center_splash_window(self, width: int, height: int):
        """Center the splash window on screen."""
        try:
            # Get viewport size
            viewport_width = get_viewport_width()
            viewport_height = get_viewport_height()

            # Calculate center position
            pos_x = (viewport_width - width) // 2
            pos_y = (viewport_height - height) // 2

            # Set window position
            set_item_pos("splash_window", [pos_x, pos_y])
        except Exception as e:
            print(f"Warning: Could not center splash window: {e}")

    def show(self):
        """Show the splash screen."""
        if not self.is_visible:
            self.create_splash_window()
            self._start_loading_animation()

    def hide(self):
        """Hide the splash screen."""
        if self.is_visible:
            self.should_animate = False
            if self.loading_thread and self.loading_thread.is_alive():
                self.loading_thread.join(timeout=0.5)

            try:
                if does_item_exist("splash_window"):
                    delete_item("splash_window")
                self.is_visible = False
            except Exception as e:
                print(f"Warning: Error hiding splash screen: {e}")

    def update_progress(self, progress: float, status: str = None):
        """Update the progress bar and status text.

        Args:
            progress: Progress value between 0.0 and 1.0
            status: Optional status message to display
        """
        if self.is_visible:
            try:
                if does_item_exist("splash_progress"):
                    set_value("splash_progress", progress)

                if status and does_item_exist("splash_status"):
                    set_value("splash_status", status)
            except Exception as e:
                print(f"Warning: Error updating splash progress: {e}")

    def _start_loading_animation(self):
        """Start the loading dots animation."""
        self.should_animate = True
        self.loading_thread = threading.Thread(
            target=self._animate_loading_dots, daemon=True
        )
        self.loading_thread.start()

    def _animate_loading_dots(self):
        """Animate the loading dots."""
        dots_count = 0
        while self.should_animate and self.is_visible:
            try:
                if does_item_exist("splash_loading_dots"):
                    dots = "." * (dots_count % 4)
                    loading_text = f"Loading{dots}"
                    set_value("splash_loading_dots", loading_text)

                dots_count += 1
                time.sleep(0.5)
            except Exception as e:
                print(f"Warning: Error in loading animation: {e}")
                break


class SplashScreenManager:
    """Convenience manager for splash screen operations."""

    def __init__(self, theme_manager=None):
        """Initialize splash screen manager."""
        self.splash = SplashScreen(theme_manager)
        self.initialization_steps = [
            ("Initializing DearPyGUI...", 0.1),
            ("Loading theme manager...", 0.2),
            ("Setting up database manager...", 0.3),
            ("Configuring credentials manager...", 0.4),
            ("Initializing UI components...", 0.6),
            ("Setting up callbacks...", 0.8),
            ("Finalizing setup...", 0.9),
            ("Ready!", 1.0),
        ]
        self.current_step = 0

    def show_splash(self):
        """Show the splash screen."""
        self.splash.show()

    def hide_splash(self):
        """Hide the splash screen."""
        self.splash.hide()

    def next_step(self, custom_message: str = None):
        """Advance to the next initialization step.

        Args:
            custom_message: Optional custom message instead of predefined step
        """
        if self.current_step < len(self.initialization_steps):
            message, progress = self.initialization_steps[self.current_step]
            if custom_message:
                message = custom_message

            self.splash.update_progress(progress, message)
            self.current_step += 1

    def update_progress(self, progress: float, message: str):
        """Update progress with custom values."""
        self.splash.update_progress(progress, message)

    def complete(self):
        """Mark initialization as complete and hide splash after a brief delay."""
        self.splash.update_progress(1.0, "Application ready!")

        # Add a small delay to show completion
        def delayed_hide():
            time.sleep(0.5)
            self.hide_splash()

        threading.Thread(target=delayed_hide, daemon=True).start()
