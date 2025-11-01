#!/bin/bash
set -e

APP_NAME="clicky"
ICON_PATH="./assets/icons/app.icns"
ASSETS_PATH="assets:assets"
DIST_DIR="dist"
BUILD_DIR="build"

echo "🔧 Cleaning previous builds..."
rm -rf "$DIST_DIR" "$BUILD_DIR" "$APP_NAME.spec"

echo "🏗️ Building macOS app bundle..."
pyinstaller main.py \
    --windowed \
    --onedir \
    --name "$APP_NAME" \
    --icon "$ICON_PATH" \
    --add-data "$ASSETS_PATH" \
    --noupx \
    --noconfirm

APP_PATH="$DIST_DIR/$APP_NAME.app"
ZIP_NAME="${APP_NAME}_mac_$(date +%Y%m%d).zip"

if [ ! -d "$APP_PATH" ]; then
    echo "❌ Build failed — $APP_PATH not found."
    exit 1
fi

echo "🧹 Removing macOS quarantine flags..."
xattr -dr com.apple.quarantine "$APP_PATH" || true

echo "📦 Packaging $APP_PATH into $ZIP_NAME ..."
cd "$DIST_DIR"
zip -r "../$ZIP_NAME" "$APP_NAME.app" > /dev/null
cd ..

echo "✅ Build complete!"
echo "📁 App bundle:   $APP_PATH"
echo "📦 Distributable: $(pwd)/$ZIP_NAME"
echo "🚀 To test: open \"$APP_PATH\""
