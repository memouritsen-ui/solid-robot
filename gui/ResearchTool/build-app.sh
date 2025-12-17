#!/bin/bash
# Build script for Research Tool macOS app
# Creates a proper .app bundle from the Swift Package

set -e

# Configuration
APP_NAME="Research Tool"
BUNDLE_NAME="ResearchTool"
VERSION="1.0.0"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/.build/release"
APP_BUNDLE="${SCRIPT_DIR}/${BUNDLE_NAME}.app"
RESOURCES_DIR="${SCRIPT_DIR}/Resources"

echo "🔨 Building Research Tool..."
echo "   Script directory: ${SCRIPT_DIR}"

# Step 1: Build release binary
echo "📦 Step 1: Building release binary..."
cd "${SCRIPT_DIR}"
swift build -c release

if [ ! -f "${BUILD_DIR}/${BUNDLE_NAME}" ]; then
    echo "❌ Build failed: Binary not found at ${BUILD_DIR}/${BUNDLE_NAME}"
    exit 1
fi
echo "   ✅ Binary built successfully"

# Step 2: Create app bundle structure
echo "📁 Step 2: Creating app bundle structure..."
rm -rf "${APP_BUNDLE}"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# Step 3: Copy binary
echo "📋 Step 3: Copying binary..."
cp "${BUILD_DIR}/${BUNDLE_NAME}" "${APP_BUNDLE}/Contents/MacOS/"
chmod +x "${APP_BUNDLE}/Contents/MacOS/${BUNDLE_NAME}"

# Step 4: Copy Info.plist
echo "📋 Step 4: Copying Info.plist..."
if [ -f "${RESOURCES_DIR}/Info.plist" ]; then
    cp "${RESOURCES_DIR}/Info.plist" "${APP_BUNDLE}/Contents/"
else
    echo "⚠️  Warning: Info.plist not found, creating minimal version"
    cat > "${APP_BUNDLE}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>${BUNDLE_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.solidrobot.researchtool</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF
fi

# Step 5: Copy icon
echo "🎨 Step 5: Copying app icon..."
if [ -f "${RESOURCES_DIR}/AppIcon.icns" ]; then
    cp "${RESOURCES_DIR}/AppIcon.icns" "${APP_BUNDLE}/Contents/Resources/"
    echo "   ✅ Icon copied"
else
    echo "⚠️  Warning: AppIcon.icns not found in ${RESOURCES_DIR}"
fi

# Step 6: Create PkgInfo
echo "📄 Step 6: Creating PkgInfo..."
echo -n "APPL????" > "${APP_BUNDLE}/Contents/PkgInfo"

# Step 7: Touch to update modification date
touch "${APP_BUNDLE}"

# Step 8: Verify bundle
echo "🔍 Step 7: Verifying bundle..."
if [ -f "${APP_BUNDLE}/Contents/MacOS/${BUNDLE_NAME}" ] && \
   [ -f "${APP_BUNDLE}/Contents/Info.plist" ]; then
    echo "   ✅ Bundle structure verified"
else
    echo "❌ Bundle verification failed"
    exit 1
fi

# Done
echo ""
echo "✅ Build complete!"
echo "   App bundle: ${APP_BUNDLE}"
echo ""
echo "To install:"
echo "   cp -R \"${APP_BUNDLE}\" /Applications/"
echo ""
echo "To run:"
echo "   open \"${APP_BUNDLE}\""
echo ""

# Optional: Open the app
if [ "$1" == "--open" ]; then
    echo "🚀 Launching app..."
    open "${APP_BUNDLE}"
fi

# Optional: Install to Applications
if [ "$1" == "--install" ]; then
    echo "📥 Installing to /Applications..."
    rm -rf "/Applications/${BUNDLE_NAME}.app"
    cp -R "${APP_BUNDLE}" /Applications/
    echo "   ✅ Installed to /Applications/${BUNDLE_NAME}.app"
fi
