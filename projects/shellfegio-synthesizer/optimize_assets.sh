#!/bin/bash

# Asset Optimization Script for Shellfegio Synthesizer Project
# This script optimizes PNG images and video

set -e

PROJECT_DIR="/Users/oceaneboulais/Github/portfolly/projects/shellfegio-synthesizer"
cd "$PROJECT_DIR"

echo "🚀 Starting asset optimization for Shellfegio Synthesizer..."
echo ""

# Create optimized directory
mkdir -p imgs/optimized

# ============================================
# 1. OPTIMIZE PNG IMAGES (WebP + Compressed PNG)
# ============================================
echo "🖼️  Optimizing PNG images..."

IMAGES=(
    "angled_side_main_sunset.png"
    "IMG_2724.png"
    "IMG_2726.png"
    "main_front.png"
    "nadir_top_kelp.png"
    "side_main.png"
)

for img in "${IMAGES[@]}"; do
    if [ -f "imgs/$img" ]; then
        echo "  Processing $img..."
        
        # Create WebP version (best compression, 80-90% size reduction)
        convert "imgs/$img" -quality 85 -define webp:method=6 "imgs/optimized/${img%.png}.webp"
        
        # Create optimized PNG as fallback (strip metadata, optimize)
        convert "imgs/$img" -strip -quality 85 -define png:compression-level=9 "imgs/optimized/$img"
        
        echo "    ✓ Created WebP and optimized PNG"
    fi
done

echo ""
echo "📊 Image Optimization Results:"
original_size=$(du -ch imgs/*.png 2>/dev/null | tail -1 | awk '{print $1}')
webp_size=$(du -ch imgs/optimized/*.webp 2>/dev/null | tail -1 | awk '{print $1}')
png_size=$(du -ch imgs/optimized/*.png 2>/dev/null | tail -1 | awk '{print $1}')
echo "  Original PNGs:    $original_size"
echo "  Optimized WebP:   $webp_size"
echo "  Optimized PNGs:   $png_size"
echo ""

# ============================================
# 2. OPTIMIZE VIDEO (Re-encode for better compression)
# ============================================
echo "🎥 Optimizing video..."

if [ -f "imgs/rotated_shellfeggio.mp4" ]; then
    echo "  Recompressing rotated_shellfeggio.mp4..."
    
    # Re-encode with better compression settings
    ffmpeg -i imgs/rotated_shellfeggio.mp4 \
        -c:v libx264 \
        -crf 23 \
        -preset slow \
        -movflags +faststart \
        -c:a aac \
        -b:a 128k \
        imgs/optimized/rotated_shellfeggio.mp4 \
        -y -loglevel error
    
    echo "    ✓ Created optimized MP4"
    
    # Create WebM version for modern browsers
    ffmpeg -i imgs/rotated_shellfeggio.mp4 \
        -c:v libvpx-vp9 \
        -crf 30 \
        -b:v 0 \
        -c:a libopus \
        -b:a 96k \
        imgs/optimized/rotated_shellfeggio.webm \
        -y -loglevel error
    
    echo "    ✓ Created WebM version"
fi

echo ""
echo "📊 Video Optimization Results:"
original_video=$(du -sh imgs/rotated_shellfeggio.mp4 2>/dev/null | awk '{print $1}')
optimized_video=$(du -sh imgs/optimized/rotated_shellfeggio.mp4 2>/dev/null | awk '{print $1}')
webm_video=$(du -sh imgs/optimized/rotated_shellfeggio.webm 2>/dev/null | awk '{print $1}')
echo "  Original MP4:     $original_video"
echo "  Optimized MP4:    $optimized_video"
echo "  Optimized WebM:   $webm_video"
echo ""

# ============================================
# SUMMARY
# ============================================
echo "✅ Optimization complete!"
echo ""
echo "📁 Optimized assets saved to:"
echo "   - imgs/optimized/ (WebP & compressed images + optimized video)"
echo ""
echo "🎯 Next step: The HTML file will be updated to use these optimized assets"
echo "   with modern formats and lazy loading."
