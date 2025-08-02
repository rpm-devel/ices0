#!/bin/bash
# Script to build ices-0 RPM packages for RHEL 8-10 (amd64 and arm64)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_msg() {
  echo -e "${2}${1}${NC}"
}

# Function to check if command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to detect package manager
detect_package_manager() {
  if command_exists dnf; then
    echo "dnf"
  elif command_exists yum; then
    echo "yum"
  else
    print_msg "Error: Neither dnf nor yum found!" "$RED"
    exit 1
  fi
}

# Function to install package if not present
install_if_missing() {
  local pkg="$1"
  local pkg_mgr="$2"

  if ! rpm -q "$pkg" >/dev/null 2>&1; then
    print_msg "Installing $pkg..." "$YELLOW"
    sudo $pkg_mgr install -y "$pkg"
  else
    print_msg "$pkg is already installed" "$GREEN"
  fi
}

# Main script
main() {
  print_msg "Starting ices-0 RPM build process..." "$GREEN"

  # Detect package manager
  PKG_MGR=$(detect_package_manager)
  print_msg "Using package manager: $PKG_MGR" "$GREEN"

  # Check for required packages
  print_msg "Checking and installing required packages..." "$YELLOW"

  # Essential build tools
  install_if_missing "rpm-build" "$PKG_MGR"
  install_if_missing "rpmdevtools" "$PKG_MGR"
  install_if_missing "gcc" "$PKG_MGR"
  install_if_missing "gcc-c++" "$PKG_MGR"
  install_if_missing "make" "$PKG_MGR"
  install_if_missing "wget" "$PKG_MGR"
  install_if_missing "tar" "$PKG_MGR"

  # Development libraries commonly needed for ices
  install_if_missing "libshout-devel" "$PKG_MGR"
  install_if_missing "libxml2-devel" "$PKG_MGR"
  install_if_missing "libvorbis-devel" "$PKG_MGR"
  install_if_missing "libogg-devel" "$PKG_MGR"

  # Cross-compilation support for arm64
  if [ "$(uname -m)" = "x86_64" ]; then
    print_msg "Installing cross-compilation tools for arm64..." "$YELLOW"
    install_if_missing "gcc-aarch64-linux-gnu" "$PKG_MGR" || true
    install_if_missing "gcc-c++-aarch64-linux-gnu" "$PKG_MGR" || true
  fi

  # Setup RPM build environment
  print_msg "Setting up RPM build environment..." "$YELLOW"
  if [ ! -d "$HOME/rpmbuild" ]; then
    rpmdev-setuptree
  fi

  # Download ices-0 source
  print_msg "Downloading ices-0 source code..." "$YELLOW"
  ICES_VERSION="0.4"
  ICES_URL="http://downloads.xiph.org/releases/ices/ices-${ICES_VERSION}.tar.gz"

  cd "$HOME/rpmbuild/SOURCES"
  if [ ! -f "ices-${ICES_VERSION}.tar.gz" ]; then
    wget "$ICES_URL" || {
      print_msg "Failed to download ices-0 source!" "$RED"
      exit 1
    }
  else
    print_msg "Source tarball already exists" "$GREEN"
  fi

  # Check for user's spec file
  print_msg "Please provide the path to your .rpmspec file:" "$YELLOW"
  read -r SPEC_FILE

  if [ ! -f "$SPEC_FILE" ]; then
    print_msg "Error: Spec file not found at $SPEC_FILE" "$RED"
    exit 1
  fi

  # Copy spec file to SPECS directory
  cp "$SPEC_FILE" "$HOME/rpmbuild/SPECS/ices.spec"

  # Build for multiple architectures
  ARCHITECTURES=("x86_64" "aarch64")

  for ARCH in "${ARCHITECTURES[@]}"; do
    print_msg "Building RPM for $ARCH..." "$GREEN"

    # Set architecture-specific variables
    if [ "$ARCH" = "aarch64" ] && [ "$(uname -m)" = "x86_64" ]; then
      # Cross-compilation setup
      export CC=aarch64-linux-gnu-gcc
      export CXX=aarch64-linux-gnu-g++
      RPMBUILD_ARGS="--target=$ARCH"
    else
      unset CC CXX
      RPMBUILD_ARGS="--target=$ARCH"
    fi

    # Build the RPM
    cd "$HOME/rpmbuild/SPECS"
    rpmbuild -ba $RPMBUILD_ARGS ices.spec || {
      print_msg "Failed to build RPM for $ARCH" "$RED"
      continue
    }

    print_msg "Successfully built RPM for $ARCH" "$GREEN"
  done

  # Display results
  print_msg "\nBuild complete! RPMs are located in:" "$GREEN"
  echo "$HOME/rpmbuild/RPMS/"

  print_msg "\nListing built RPMs:" "$YELLOW"
  find "$HOME/rpmbuild/RPMS" -name "ices*.rpm" -type f | sort
}

# Run main function
main "$@"
