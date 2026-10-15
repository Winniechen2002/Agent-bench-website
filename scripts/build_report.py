"""Compatibility entry point for the discussion-outline build.

The filled report and its former PDF generator are in archive/filled-v0.1.zip.
No PDF is generated until the content framework is agreed.
"""
from build_framework import build

if __name__ == "__main__":
    build()
    print("Discussion outlines updated. The historical PDF was not modified.")
